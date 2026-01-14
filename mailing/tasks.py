import logging

from celery import shared_task
from django.db import transaction
from django.utils import timezone

from .models import Mailing
from .services import can_send_mailing, send_mailing_now

logger = logging.getLogger("mailing")


@shared_task
def process_due_mailings(limit: int = 100) -> dict:
    now = timezone.now()
    due_ids = (
        Mailing.objects.filter(
            is_active=True,
            next_run_at__isnull=False,
            next_run_at__lte=now,
            start_time__lte=now,
            end_time__gte=now,
        )
        .order_by("next_run_at")
        .values_list("id", flat=True)[:limit]
    )

    processed = 0
    sent = 0
    failed = 0

    for mailing_id in due_ids:
        with transaction.atomic():
            mailing = Mailing.objects.select_for_update().get(pk=mailing_id)

            if mailing.next_run_at is None or mailing.next_run_at > timezone.now():
                continue

            mailing.update_status(save=True)
            if not can_send_mailing(mailing):
                mailing.next_run_at = mailing.compute_next_run_at(now=timezone.now())
                mailing.save(update_fields=["next_run_at"])
                continue

            logger.info("Запуск рассылки по расписанию: id=%s", mailing.pk)
            result = send_mailing_now(mailing)
            processed += 1
            sent += int(result.get("sent", 0))
            failed += int(result.get("failed", 0))

    return {"processed": processed, "sent": sent, "failed": failed}
