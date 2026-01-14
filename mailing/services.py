import logging

from django.core.mail import send_mail
from django.utils import timezone

from .models import Mailing, MailingAttempt


logger = logging.getLogger("mailing")


def can_send_mailing(mailing: Mailing) -> bool:
    now = timezone.now()
    return mailing.is_active and mailing.start_time <= now <= mailing.end_time


def send_mailing_now(mailing: Mailing) -> dict:
    mailing.update_status(save=True)
    if not can_send_mailing(mailing):
        logger.info("Рассылка %s недоступна для отправки (окно времени/активность)", mailing.pk)
        return {
            "sent": 0,
            "failed": mailing.recipients.count(),
            "error": "Рассылка недоступна для отправки.",
        }
    logger.info("Старт отправки рассылки %s. Получателей: %s", mailing.pk, mailing.recipients.count())
    success = 0
    failed = 0
    for recipient in mailing.recipients.all():
        try:
            send_mail(
                mailing.message.subject,
                mailing.message.body,
                None,
                [recipient.email],
                fail_silently=False,
            )
            MailingAttempt.objects.create(
                mailing=mailing,
                recipient=recipient,
                status=MailingAttempt.STATUS_SUCCESS,
                server_response="OK",
            )
            success += 1
        except Exception as exc:  # noqa: BLE001
            logger.exception(
                "Ошибка отправки рассылки %s получателю %s: %s",
                mailing.pk,
                recipient.email,
                exc,
            )
            MailingAttempt.objects.create(
                mailing=mailing,
                recipient=recipient,
                status=MailingAttempt.STATUS_FAILED,
                server_response=str(exc),
            )
            failed += 1
    mailing.update_status(save=True)
    mailing.register_run(run_at=timezone.now(), save=True)
    logger.info("Завершена рассылка %s: отправлено=%s ошибок=%s", mailing.pk, success, failed)
    return {"sent": success, "failed": failed}
