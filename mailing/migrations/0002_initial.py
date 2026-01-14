import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ('mailing', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='mailing',
            name='owner',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='mailings',
                                    to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='mailingattempt',
            name='mailing',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attempts',
                                    to='mailing.mailing'),
        ),
        migrations.AddField(
            model_name='message',
            name='owner',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='messages',
                                    to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='mailing',
            name='message',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='mailings',
                                    to='mailing.message'),
        ),
        migrations.AddField(
            model_name='recipient',
            name='owner',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='recipients',
                                    to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='mailingattempt',
            name='recipient',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attempts',
                                    to='mailing.recipient'),
        ),
        migrations.AddField(
            model_name='mailing',
            name='recipients',
            field=models.ManyToManyField(related_name='mailings', to='mailing.recipient'),
        ),
    ]
