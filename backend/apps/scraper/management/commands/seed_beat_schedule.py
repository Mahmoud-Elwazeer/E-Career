"""
Seed the Celery-beat DATABASE schedule (PeriodicTask rows).

The project sets CELERY_BEAT_SCHEDULER = DatabaseScheduler, which reads schedules
from the DB (django_celery_beat PeriodicTask), NOT from the static
`app.conf.beat_schedule` in config/celery.py. Without these rows the scraper,
apply-URL verification, and job expiry never run automatically.

This command creates/updates the PeriodicTask rows to match the intended
schedule. Idempotent — safe to run repeatedly. Requires a running Celery beat +
worker to actually execute.
"""
from django.core.management.base import BaseCommand


SCHEDULES = [
    # (name, task, crontab dict)
    ("scrape-all-sources", "apps.scraper.tasks.scrape_all_sources", {"minute": "0", "hour": "*/6"}),
    ("verify-apply-urls", "apps.scraper.tasks.verify_apply_urls", {"minute": "0", "hour": "2"}),
    ("expire-old-jobs", "apps.scraper.tasks.expire_old_jobs", {"minute": "0", "hour": "3"}),
]


class Command(BaseCommand):
    help = "Seed Celery-beat PeriodicTask rows so scraping/verification/expiry run automatically."

    def add_arguments(self, parser):
        parser.add_argument("--disable", action="store_true",
                            help="Create the tasks but leave them disabled")

    def handle(self, *args, **options):
        try:
            from django_celery_beat.models import PeriodicTask, CrontabSchedule
        except ImportError:
            self.stderr.write("django_celery_beat is not installed.")
            return

        enabled = not options["disable"]
        created = 0
        for name, task, cron in SCHEDULES:
            schedule, _ = CrontabSchedule.objects.get_or_create(
                minute=cron["minute"], hour=cron["hour"],
                day_of_week="*", day_of_month="*", month_of_year="*",
            )
            obj, is_new = PeriodicTask.objects.get_or_create(
                name=name,
                defaults={"task": task, "crontab": schedule, "enabled": enabled},
            )
            if not is_new:
                # Keep it aligned to the intended task + schedule.
                obj.task = task
                obj.crontab = schedule
                obj.enabled = enabled
                obj.save(update_fields=["task", "crontab", "enabled"])
                self.stdout.write(f"Updated: {name} ({'enabled' if enabled else 'disabled'})")
            else:
                created += 1
                self.stdout.write(f"Created: {name} ({'enabled' if enabled else 'disabled'})")

        self.stdout.write(self.style.SUCCESS(
            f"\nBeat schedule seeded. {created} new. "
            f"Ensure `celery -A config beat` and a worker are running."
        ))
