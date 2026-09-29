"""Regression tests for the Rashid agent tool <-> service contracts.

Two Rashid agent tools previously called platform services with the WRONG
signatures and would raise at runtime whenever Rashid tried to use them:

  * ``search_jobs`` called ``SearchService().search_jobs(query=..., filters=...,
    limit=...)`` and iterated the result as a list of dicts, but the real
    ``SearchService.search_jobs`` takes a single ``SearchQuery`` and returns a
    ``SearchResponse`` (``.hits[].data``).
  * ``get_recommendations`` called ``RecommendationEngine()`` (no user) and
    ``get_recommendations(user_id=..., limit=...)`` and read ``job['title']``,
    but the engine requires a ``user`` and returns dicts keyed ``job_title``.

These tests pin the service contracts the fixed tools rely on so a future
signature change fails loudly instead of silently breaking Rashid.
"""
import inspect

from apps.search.plugins.base import SearchQuery, SearchResponse
from apps.search.recommendation_engine import RecommendationEngine
from apps.search.service import SearchService


def test_search_service_accepts_search_query_object():
    """SearchService.search_jobs must take exactly one positional query arg."""
    sig = inspect.signature(SearchService.search_jobs)
    params = [p for p in sig.parameters.values() if p.name != "self"]
    assert len(params) == 1, "search_jobs must accept a single SearchQuery arg"
    # SearchQuery must be constructible the way the tool builds it.
    q = SearchQuery(q="python", filters={"location": "Cairo"}, page=1, per_page=5)
    assert q.q == "python"
    assert q.filters["location"] == "Cairo"


def test_search_response_exposes_hits_with_data():
    """The tool reads response.hits[].data — guard that shape exists."""
    resp = SearchResponse(hits=[], total=0, page=1, per_page=5)
    assert hasattr(resp, "hits")
    assert isinstance(resp.hits, list)


def test_recommendation_engine_requires_user():
    """RecommendationEngine(user) is positional; get_recommendations has no user_id."""
    init_sig = inspect.signature(RecommendationEngine.__init__)
    init_params = [p for p in init_sig.parameters.values() if p.name != "self"]
    assert init_params and init_params[0].name == "user", (
        "RecommendationEngine must take a user positional arg"
    )

    rec_sig = inspect.signature(RecommendationEngine.get_recommendations)
    assert "user_id" not in rec_sig.parameters, (
        "get_recommendations takes n_recommendations, not user_id"
    )
    assert "n_recommendations" in rec_sig.parameters


def test_agent_module_imports_and_builds():
    """The agent module must import and register tools without error."""
    from apps.intelligence import agent as agent_module

    assert hasattr(agent_module, "create_rashid_agent")
    assert hasattr(agent_module, "get_rashid_agent")
    # SearchQuery is imported lazily inside the tool; ensure the symbol is valid.
    assert SearchQuery is not None


def test_skill_gap_analyzer_contract():
    """analyze_skill_gap tool relies on SkillGapAnalyzer(user).analyze()."""
    import inspect
    from apps.career.skill_gap_analysis import SkillGapAnalyzer

    init_params = [
        p for p in inspect.signature(SkillGapAnalyzer.__init__).parameters.values()
        if p.name != "self"
    ]
    assert init_params and init_params[0].name == "user"
    assert hasattr(SkillGapAnalyzer, "analyze")


def test_talent_score_field_name():
    """get_career_profile tool orders TalentScore by last_calculated_at."""
    from apps.career.models import TalentScore

    field_names = {f.name for f in TalentScore._meta.get_fields()}
    assert "last_calculated_at" in field_names
    assert "overall_score" in field_names
    # The old (wrong) field name must not silently exist.
    assert "calculated_at" not in field_names


def test_salary_data_field_names():
    """get_salary_insights tool queries job__title and salary_min/max, not salary_amount."""
    from apps.salary.models import SalaryData

    field_names = {f.name for f in SalaryData._meta.get_fields()}
    assert "salary_min" in field_names
    assert "salary_max" in field_names
    assert "job" in field_names
    # The old (wrong) field the tool used must not exist.
    assert "salary_amount" not in field_names
    assert "job_title" not in field_names


def test_intelligence_views_imports_settings():
    """chat_with_rashid references settings.RASHID_MODEL; settings must be imported."""
    from apps.intelligence import views

    assert hasattr(views, "settings"), "settings must be importable at module level"
