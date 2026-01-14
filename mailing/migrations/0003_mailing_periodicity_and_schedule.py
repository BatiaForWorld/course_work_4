from django.db import migrations, models
from django.db.models import F


def set_initial_next_run_at(apps, schema_editor):
    Mailing = apps.get_model("mailing", "Mailing")
    Mailing.objects.filter(next_run_at__isnull=True, last_run_at__isnull=True).update(next_run_at=F("start_time"))


def unset_initial_next_run_at(apps, schema_editor):
    Mailing = apps.get_model("mailing", "Mailing")
    Mailing.objects.filter(last_run_at__isnull=True).update(next_run_at=None)


class Migration(migrations.Migration):
    dependencies = [
        ("mailing", "0002_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="mailing",
            name="periodicity",
            field=models.CharField(
                choices=[
                    ("once", "Один раз"),
                    ("daily", "Ежедневно"),
                    ("weekly", "Еженедельно"),
                    ("monthly", "Ежемесячно"),
                ],
                default="once",
                max_length=10,
            ),
        ),
        migrations.AddField(
            model_name="mailing",
            name="last_run_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="mailing",
            name="next_run_at",
            field=models.DateTimeField(blank=True, db_index=True, null=True),
        ),
        migrations.RunPython(set_initial_next_run_at, reverse_code=unset_initial_next_run_at),
    ]
