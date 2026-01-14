import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("config")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

app.conf.beat_schedule = {
    "mailing-process-due-mailings-every-minute": {
        "task": "mailing.tasks.process_due_mailings",
        "schedule": 60.0,
    },
}
