from django.core.management.base import BaseCommand
from django.utils import timezone

from mailing.models import Mailing


class Command(BaseCommand):
    help = "Backfill/refresh next_run_at for active mailings"

    def add_arguments(self, parser):
        parser.add_argument(
            "--all",
            action="store_true",
            help="Recompute next_run_at for all active mailings (not only NULL)",
        )

    def handle(self, *args, **options):
        now = timezone.now()
        qs = Mailing.objects.filter(is_active=True)
        if not options["all"]:
            qs = qs.filter(next_run_at__isnull=True)

        updated = 0
        for mailing in qs.iterator():
            mailing.next_run_at = mailing.compute_next_run_at(now=now)
            mailing.save(update_fields=["next_run_at"])
            updated += 1

        self.stdout.write(self.style.SUCCESS(f"Updated schedules: {updated}"))
