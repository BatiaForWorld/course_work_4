from django.core.management.base import BaseCommand, CommandError

from mailing.models import Mailing
from mailing.services import can_send_mailing, send_mailing_now


class Command(BaseCommand):
    help = "Send a mailing by its ID"

    def add_arguments(self, parser):
        parser.add_argument("mailing_id", type=int, help="ID of the mailing to send")

    def handle(self, *args, **options):
        mailing_id = options["mailing_id"]
        try:
            mailing = Mailing.objects.get(pk=mailing_id)
        except Mailing.DoesNotExist as exc:  # noqa: F841
            raise CommandError(f"Mailing with id={mailing_id} does not exist")
        if not can_send_mailing(mailing):
            raise CommandError("Mailing is not active or outside the allowed time window")
        result = send_mailing_now(mailing)
        self.stdout.write(self.style.SUCCESS(
            f"Mailing #{mailing_id} processed. Sent: {result['sent']}, failed: {result['failed']}"
        ))
