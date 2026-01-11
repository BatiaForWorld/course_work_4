from django.core.mail import send_mail
from django.utils import timezone

from .models import Mailing, MailingAttempt


def can_send_mailing(mailing: Mailing) -> bool:
    now = timezone.now()
    return mailing.is_active and mailing.start_time <= now <= mailing.end_time


def send_mailing_now(mailing: Mailing) -> dict:
    mailing.update_status(save=True)
    if not can_send_mailing(mailing):
        return {"sent": 0, "failed": mailing.recipients.count(), "error": "Рассылка недоступна для отправки."}
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
            MailingAttempt.objects.create(
                mailing=mailing,
                recipient=recipient,
                status=MailingAttempt.STATUS_FAILED,
                server_response=str(exc),
            )
            failed += 1
    mailing.update_status(save=True)
    return {"sent": success, "failed": failed}
