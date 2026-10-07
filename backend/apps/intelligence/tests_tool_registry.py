"""Regression tests for the canonical Rashid tool registry.

Fixes the documented duplicate-tool-registry finding (two independent
implementations of search_jobs/recommend_jobs — see tool_registry.py's
module docstring for the full history). These tests pin the structural
guarantees the directive required:

  1. every registered tool has a unique name
  2. no duplicate tool definitions/schemas
  3. the pydantic-ai agent wires onto the SAME canonical registry
  4. deterministic (non-auth) tools remain callable without a user
  5. auth-required tools are rejected centrally before the tool body runs
     (permissions enforced once, in the registry, not per tool)
"""
import datetime

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.career.models import CareerProfile
from apps.intelligence.evidence import ToolResult
from apps.intelligence.tool_registry import TOOL_REGISTRY, ToolContext, ToolDefinition
from apps.jobs.models import Company, Job, Source

User = get_user_model()


class TestRegistryStructure(TestCase):
    """No live DB/network needed — pure registry shape checks."""

    def test_every_tool_name_is_unique(self):
        names = TOOL_REGISTRY.names()
        self.assertEqual(len(names), len(set(names)), "duplicate tool names registered")

    def test_registering_a_duplicate_name_raises(self):
        from apps.intelligence.tool_registry import ToolRegistry

        registry = ToolRegistry()
        registry.register(ToolDefinition(name="dup", description="first", func=lambda ctx: ToolResult(text="a")))
        with self.assertRaises(ValueError):
            registry.register(ToolDefinition(name="dup", description="second", func=lambda ctx: ToolResult(text="b")))

    def test_expected_canonical_tools_are_all_present(self):
        """The full set ported from BOTH legacy registries (agent.py's
        9 live tools + rashid/tools.py's 5 unique ones minus the 2
        duplicated get_job/search_jobs/recommend_jobs collisions already
        covered by the live set) must exist exactly once each."""
        expected = {
            "search_jobs", "analyze_skill_gap", "get_career_profile",
            "get_recommendations", "prepare_interview", "get_salary_insights",
            "get_match_score", "tailor_resume", "find_referral_contacts",
            "cv_review", "cover_letter", "linkedin_optimizer", "course_advisor",
        }
        self.assertEqual(expected, set(TOOL_REGISTRY.names()))

    def test_agent_module_wires_onto_the_canonical_registry(self):
        """apps/intelligence/agent.py must import TOOL_REGISTRY from this
        module rather than defining its own tool bodies."""
        from apps.intelligence import agent as agent_module

        self.assertIs(agent_module.TOOL_REGISTRY, TOOL_REGISTRY)

    def test_rashid_tools_shim_resolves_through_the_same_registry(self):
        """apps/rashid/tools.py (the legacy REST entrypoint) must resolve
        through the SAME TOOL_REGISTRY, not a second one."""
        from apps.rashid.tools import get_available_tools

        shim_names = {t["name"] for t in get_available_tools()}
        self.assertEqual(shim_names, set(TOOL_REGISTRY.names()))

    def test_no_tool_name_collides_with_legacy_get_job_or_recommend_jobs_bugs(self):
        """The old apps/rashid/tools.py had buggy, divergent search_jobs/
        recommend_jobs implementations (status="active" filtering instead
        of quality_state; get_recommendation_engine() global-singleton
        pattern). Only ONE search_jobs and no separate recommend_jobs/get_job
        aliases should exist post-consolidation."""
        names = set(TOOL_REGISTRY.names())
        self.assertIn("search_jobs", names)
        self.assertNotIn("recommend_jobs", names)  # merged into get_recommendations
        self.assertNotIn("get_job", names)  # superseded by search_jobs + get_match_score


class TestPermissionEnforcement(TestCase):
    """Centralized auth enforcement: requires_auth=True tools must reject
    an unauthenticated ToolContext BEFORE the tool body runs, for every
    single auth-required tool, not just a hand-picked few."""

    def setUp(self):
        self.anon_ctx = ToolContext(user_id=None)

    def test_every_auth_required_tool_rejects_anonymous_context(self):
        for definition in TOOL_REGISTRY.all():
            if not definition.requires_auth:
                continue
            result = TOOL_REGISTRY.execute(definition.name, self.anon_ctx)
            self.assertEqual(
                result.text, "User not authenticated.",
                f"tool '{definition.name}' did not enforce auth centrally",
            )
            # The tool body must not have run at all - no sources leaked.
            self.assertEqual(result.sources, [])

    def test_deterministic_public_tools_remain_callable_without_auth(self):
        """search_jobs and get_salary_insights are intentionally public
        (no PII, read-only, same as unauthenticated job search on the
        site) - confirm they do NOT require auth and actually execute."""
        search_result = TOOL_REGISTRY.execute("search_jobs", ToolContext(user_id=None, args={"query": "nonexistent-xyz"}))
        self.assertNotEqual(search_result.text, "User not authenticated.")

        salary_result = TOOL_REGISTRY.execute(
            "get_salary_insights", ToolContext(user_id=None, args={"job_title": "nonexistent-xyz"})
        )
        self.assertNotEqual(salary_result.text, "User not authenticated.")

    def test_unknown_tool_name_does_not_crash(self):
        result = TOOL_REGISTRY.execute("not_a_real_tool", ToolContext(user_id=1))
        self.assertIn("not found", result.text)


class TestCrossUserAuthorizationBoundaries(TestCase):
    """Confirm a tool scoped to "the current user" can never read or cite
    another user's data, even if a caller tried to pass someone else's id
    as an argument alongside their own authenticated user_id."""

    def setUp(self):
        self.user_a = User.objects.create_user(email="user-a@example.com", password="pw-strong-123")
        self.user_b = User.objects.create_user(email="user-b@example.com", password="pw-strong-123")
        self.profile_a = CareerProfile.objects.create(user=self.user_a, current_role="Engineer A")
        self.profile_b = CareerProfile.objects.create(user=self.user_b, current_role="Engineer B")

    def test_get_career_profile_only_ever_reads_the_authenticated_users_profile(self):
        """get_career_profile takes NO job_id/profile_id argument - it is
        always scoped to ctx.user_id. Confirm user A's call cannot surface
        user B's data regardless of what's in ctx.args."""
        ctx = ToolContext(user_id=self.user_a.id, user_name="A", args={"profile_id": self.profile_b.pk})
        result = TOOL_REGISTRY.execute("get_career_profile", ctx)
        self.assertIn("A", result.text)
        self.assertNotIn("Engineer B", result.text)
        for source in result.sources:
            self.assertEqual(source.owner_user_id, self.user_a.id)

    def test_get_match_score_profile_lookup_is_scoped_to_ctx_user_id_not_args(self):
        """get_match_score resolves the CareerProfile via ctx.user_id only -
        there is no profile_id argument a caller could substitute to view
        another user's match breakdown."""
        import inspect

        from apps.intelligence.tool_registry import _get_match_score

        src = inspect.getsource(_get_match_score)
        self.assertIn("user_id=ctx.user_id", src)
        self.assertNotIn("profile_id", src)


class TestDeterministicToolsStillWork(TestCase):
    """End-to-end smoke test: a couple of the ported deterministic tools
    still produce real output against real DB rows, through the registry,
    not through either legacy call path."""

    def setUp(self):
        self.company = Company.objects.create(name="RegistryCo", slug="registryco-tools")
        self.source = Source.objects.create(name="RegistrySource", slug="registrysource-tools", url="https://example.com")
        self.job = Job.objects.create(
            company=self.company,
            source=self.source,
            title="Registry Test Engineer",
            slug="registry-test-engineer",
            location="Remote",
            location_type="remote",
            industry="technology",
            experience_level="mid",
            description="desc",
            source_url="https://example.com/jobs/registry-test-engineer",
            posted_at=datetime.date.today(),
            legitimacy_score=0.9,
        )

    def test_search_jobs_finds_the_seeded_job(self):
        result = TOOL_REGISTRY.execute("search_jobs", ToolContext(args={"query": "Registry Test Engineer"}))
        self.assertIn("Registry Test Engineer", result.text)
        self.assertTrue(any(s.source_type == "job" for s in result.sources))
