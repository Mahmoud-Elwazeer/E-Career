"""End-to-end pipeline verification (§15/§16/§25) — run on the server.

Produces the evidence chain the platform actually needs:
  PERSISTED -> INDEXED -> SEARCHABLE -> MATCHABLE.

Unlike connector_matrix (which proves ingestion), this proves what happens to
jobs ALREADY in the DB: are they indexed, do they come back from search, and do
they flow into the matching engine for a candidate. Read-only by default; use
--reindex to (re)push visible jobs to the search backend first.

Usage:
  python manage.py verify_pipeline_e2e
  python manage.py verify_pipeline_e2e --reindex                    # sync ALL visible jobs (can be slow/large - prefer --limit first)
  python manage.py verify_pipeline_e2e --reindex --limit 10         # sync only 10 jobs - safe bounded test
  python manage.py verify_pipeline_e2e --reindex --job-id <job_id>  # sync exactly one job - smallest possible test
  python manage.py verify_pipeline_e2e --query "engineer"           # search probe term
  python manage.py verify_pipeline_e2e --profile <user_id>          # match jobs for a candidate

Fail-fast: if the first 3 reindex attempts all fail (e.g. Typesense 401), the
--reindex loop stops immediately with ONE diagnostic line instead of repeating
the same error for every remaining job. Always test with --job-id or a small
--limit before running --reindex against the full job table.
"""
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Verify DB -> index -> search -> matching end to end (read-only by default)."

    def add_arguments(self, parser):
        parser.add_argument("--reindex", action="store_true")
        parser.add_argument("--limit", type=int, default=0,
                             help="Max number of jobs to reindex (0 = no limit, all visible jobs)")
        parser.add_argument("--job-id", type=str, default="",
                             help="Reindex exactly one job by id (smallest possible test)")
        parser.add_argument("--query", type=str, default="engineer")
        parser.add_argument("--profile", type=str, default="")
        parser.add_argument("--match-limit", type=int, default=10)

    def handle(self, *args, **opts):
        from apps.jobs.models import Job

        # 1) PERSISTED — DB counts by quality_state.
        total = Job.objects.count()
        visible = Job.objects.visible().count() if hasattr(Job.objects, "visible") else None
        self.stdout.write("== PERSISTED ==")
        self.stdout.write(f"total jobs: {total}")
        if visible is not None:
            self.stdout.write(f"visible jobs: {visible}")
        try:
            from django.db.models import Count
            by_state = (Job.objects.values("quality_state")
                        .annotate(n=Count("id")).order_by("-n"))
            for row in by_state:
                self.stdout.write(f"  {row['quality_state']:20} {row['n']}")
        except Exception as e:
            self.stdout.write(f"  (quality_state breakdown failed: {e})")

        # data-quality spot checks the ingestion fixes target
        missing_apply = Job.objects.filter(direct_apply_url="").count()
        missing_source_url = Job.objects.filter(source_url="").count()
        self.stdout.write(f"jobs missing direct_apply_url: {missing_apply}")
        self.stdout.write(f"jobs missing source_url: {missing_source_url}")

        # 2) INDEXED — optionally (re)sync, then report.
        self.stdout.write("\n== INDEXED ==")
        try:
            from apps.search.service import SearchService
            svc = SearchService()
            if opts["reindex"]:
                qs = Job.objects.visible() if hasattr(Job.objects, "visible") else Job.objects.all()
                if opts["job_id"]:
                    qs = qs.filter(id=opts["job_id"])
                elif opts["limit"]:
                    qs = qs[: opts["limit"]]
                else:
                    self.stdout.write(self.style.WARNING(
                        "no --limit or --job-id given: reindexing ALL visible jobs. "
                        "If this is the first run after a config change, Ctrl+C and "
                        "retry with --job-id <id> or --limit 10 first."
                    ))

                synced, failed, attempted = 0, 0, 0
                FAIL_FAST_THRESHOLD = 3
                last_error = None
                for job in qs.iterator():
                    attempted += 1
                    try:
                        ok = svc.sync_job(job)
                    except Exception as e:
                        ok = False
                        last_error = str(e)
                    if ok:
                        synced += 1
                    else:
                        failed += 1
                        if failed >= FAIL_FAST_THRESHOLD and synced == 0:
                            self.stdout.write(self.style.ERROR(
                                f"reindex: ABORTING after {attempted} attempts, "
                                f"{failed} consecutive failures, 0 successes. "
                                f"Likely cause: Typesense auth/connectivity is broken, "
                                f"not per-job data issues. Last error: {last_error}\n"
                                f"Fix TYPESENSE_API_KEY / connectivity, then retry with "
                                f"--job-id <id> to confirm one job indexes before "
                                f"attempting a larger --limit or a full reindex."
                            ))
                            break
                self.stdout.write(f"reindex: attempted={attempted} synced={synced} failed={failed}")
            # health of the backends
            try:
                self.stdout.write(f"primary healthy: {svc.primary.health_check()}")
            except Exception as e:
                self.stdout.write(f"primary health check error: {type(e).__name__}: {e}")
        except Exception as e:
            self.stdout.write(f"search service unavailable: {type(e).__name__}: {e}")

        # 3) SEARCHABLE — run a query and report hit count + a sample.
        self.stdout.write("\n== SEARCHABLE ==")
        try:
            from apps.search.service import SearchService
            from apps.search.plugins.base import SearchQuery
            svc = SearchService()
            resp = svc.search_jobs(SearchQuery(q=opts["query"], page=1, per_page=5))
            self.stdout.write(f"query='{opts['query']}' hits={resp.total}")
            for h in (resp.hits or [])[:3]:
                doc = h.data if hasattr(h, "data") else (h if isinstance(h, dict) else {})
                self.stdout.write(f"  - {doc.get('title')} @ {doc.get('company_name')} "
                                  f"[{doc.get('ats_platform')}] apply={bool(doc.get('direct_apply_url'))}")
        except Exception as e:
            self.stdout.write(f"search query error: {type(e).__name__}: {e}")

        # 4) MATCHABLE — match some jobs for a candidate profile.
        self.stdout.write("\n== MATCHABLE ==")
        if not opts["profile"]:
            self.stdout.write("(skipped: pass --profile <user_id> to test matching)")
            return
        try:
            from apps.matching.engine import unified_matching_engine as eng
            from apps.profiles.models import Profile
            profile = Profile.objects.filter(user_id=opts["profile"]).first() \
                or Profile.objects.filter(id=opts["profile"]).first()
            if not profile:
                self.stdout.write(f"profile not found: {opts['profile']}")
                return
            qs = (Job.objects.visible() if hasattr(Job.objects, "visible") else Job.objects.all())
            scored = []
            for job in qs[: opts["match_limit"]]:
                try:
                    r = eng.match(profile, job)
                    scored.append((r.overall_score, r.eligible, job.title, job.company.name))
                except Exception as e:
                    self.stdout.write(f"  match error on {job.id}: {type(e).__name__}: {e}")
            scored.sort(reverse=True)
            self.stdout.write(f"matched {len(scored)} jobs for profile {opts['profile']}:")
            for score, eligible, title, company in scored[:10]:
                self.stdout.write(f"  {score:5.1f}  elig={eligible!s:5}  {title} @ {company}")
        except Exception as e:
            self.stdout.write(f"matching error: {type(e).__name__}: {e}")
