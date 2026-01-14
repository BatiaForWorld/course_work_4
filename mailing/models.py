import calendar
from datetime import datetime, timedelta

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class Recipient(models.Model):
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=255)
    comment = models.TextField(blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="recipients",
    )

    class Meta:
        verbose_name = "Получатель"
        verbose_name_plural = "Получатели"
        ordering = ("email",)
        permissions = (
            ("can_view_all_recipients", "Может просматривать всех получателей"),
        )

    def __str__(self):
        return f"{self.full_name} <{self.email}>"


class Message(models.Model):
    subject = models.CharField(max_length=255)
    body = models.TextField()
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="messages",
    )

    class Meta:
        verbose_name = "Сообщение"
        verbose_name_plural = "Сообщения"
        permissions = (
            ("can_view_all_messages", "Может просматривать все сообщения"),
        )

    def __str__(self):
        return self.subject


class Mailing(models.Model):
    STATUS_CREATED = "created"
    STATUS_RUNNING = "running"
    STATUS_FINISHED = "finished"

    PERIODICITY_ONCE = "once"
    PERIODICITY_EVERY_10_MINUTES = "10min"
    PERIODICITY_HOURLY = "hourly"
    PERIODICITY_DAILY = "daily"
    PERIODICITY_WEEKLY = "weekly"
    PERIODICITY_MONTHLY = "monthly"

    STATUS_CHOICES = (
        (STATUS_CREATED, "Создана"),
        (STATUS_RUNNING, "Запущена"),
        (STATUS_FINISHED, "Завершена"),
    )

    PERIODICITY_CHOICES = (
        (PERIODICITY_ONCE, "Один раз"),
        (PERIODICITY_EVERY_10_MINUTES, "Каждые 10 минут"),
        (PERIODICITY_HOURLY, "Каждый час"),
        (PERIODICITY_DAILY, "Ежедневно"),
        (PERIODICITY_WEEKLY, "Еженедельно"),
        (PERIODICITY_MONTHLY, "Ежемесячно"),
    )

    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_CREATED)
    periodicity = models.CharField(max_length=10, choices=PERIODICITY_CHOICES, default=PERIODICITY_ONCE)
    is_active = models.BooleanField(default=True)
    last_run_at = models.DateTimeField(null=True, blank=True)
    next_run_at = models.DateTimeField(null=True, blank=True, db_index=True)
    message = models.ForeignKey(Message, on_delete=models.PROTECT, related_name="mailings")
    recipients = models.ManyToManyField(Recipient, related_name="mailings")
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="mailings",
    )

    class Meta:
        verbose_name = "Рассылка"
        verbose_name_plural = "Рассылки"
        ordering = ("-start_time",)
        permissions = (
            ("can_view_all_mailings", "Может просматривать все рассылки"),
            ("can_toggle_mailings", "Может отключать рассылки"),
        )

    def __str__(self):
        return f"Рассылка {self.pk}"

    def save(self, *args, **kwargs):
        # Для плановой обработки (Celery beat) нужно, чтобы у новой рассылки
        # была заполнена next_run_at. Миграция 0003 проставляла это только для
        # уже существовавших записей; новые рассылки иначе остаются с NULL.
        update_fields = kwargs.get("update_fields")
        update_fields_set = None
        if update_fields is not None:
            update_fields_set = set(update_fields)

        if self.next_run_at is None and self.last_run_at is None and self.is_active:
            computed = self.compute_next_run_at()
            if computed is not None:
                self.next_run_at = computed
                if update_fields_set is not None:
                    update_fields_set.add("next_run_at")
                    kwargs["update_fields"] = list(update_fields_set)

        return super().save(*args, **kwargs)

    def clean(self):
        super().clean()
        now = timezone.now()
        original_start = None
        if self.pk:
            original_start = (
                self.__class__.objects.filter(pk=self.pk)
                .values_list("start_time", flat=True)
                .first()
            )
        if self.start_time < now and (original_start is None or self.start_time != original_start):
            raise ValidationError({"start_time": "Дата начала не может быть в прошлом."})
        if self.end_time <= self.start_time:
            raise ValidationError({"end_time": "Дата окончания должна быть позже даты начала."})

    @staticmethod
    def _add_months(dt: datetime, months: int) -> datetime:
        month_index = dt.month - 1 + months
        year = dt.year + month_index // 12
        month = month_index % 12 + 1
        day = min(dt.day, calendar.monthrange(year, month)[1])
        return dt.replace(year=year, month=month, day=day)

    def _step_forward(self, dt: datetime) -> datetime | None:
        if self.periodicity == self.PERIODICITY_EVERY_10_MINUTES:
            return dt + timedelta(minutes=10)
        if self.periodicity == self.PERIODICITY_HOURLY:
            return dt + timedelta(hours=1)
        if self.periodicity == self.PERIODICITY_DAILY:
            return dt + timedelta(days=1)
        if self.periodicity == self.PERIODICITY_WEEKLY:
            return dt + timedelta(days=7)
        if self.periodicity == self.PERIODICITY_MONTHLY:
            return self._add_months(dt, 1)
        return None

    def _interval_for_periodicity(self) -> timedelta | None:
        if self.periodicity == self.PERIODICITY_EVERY_10_MINUTES:
            return timedelta(minutes=10)
        if self.periodicity == self.PERIODICITY_HOURLY:
            return timedelta(hours=1)
        if self.periodicity == self.PERIODICITY_DAILY:
            return timedelta(days=1)
        if self.periodicity == self.PERIODICITY_WEEKLY:
            return timedelta(days=7)
        return None

    def compute_next_run_at(self, now: datetime | None = None) -> datetime | None:
        now = now or timezone.now()

        if not self.is_active:
            return None

        if self.periodicity == self.PERIODICITY_ONCE:
            candidate = self.start_time if self.last_run_at is None else None
        else:
            interval = self._interval_for_periodicity()
            if interval is not None:
                # Интервальные расписания считаем слотами от start_time:
                # start_time, start_time+interval, start_time+2*interval, ...
                # next_run_at — первый слот строго ПОСЛЕ max(now, last_run_at).
                anchor = self.start_time
                effective_now = now
                if self.last_run_at is not None and self.last_run_at > effective_now:
                    effective_now = self.last_run_at

                if effective_now < anchor:
                    candidate = anchor
                else:
                    delta_seconds = int((effective_now - anchor).total_seconds())
                    interval_seconds = int(interval.total_seconds())
                    steps = (delta_seconds // interval_seconds) + 1
                    candidate = anchor + interval * steps
            else:
                if self.last_run_at is None:
                    candidate = self.start_time
                else:
                    candidate = self._step_forward(self.last_run_at)

                step = self._step_forward
                while candidate is not None and candidate <= now:
                    candidate = step(candidate)

        if candidate is None:
            return None

        if candidate < self.start_time:
            candidate = self.start_time

        if candidate > self.end_time:
            return None

        return candidate

    def register_run(self, run_at: datetime | None = None, save: bool = True) -> None:
        run_at = run_at or timezone.now()
        self.last_run_at = run_at
        self.next_run_at = self.compute_next_run_at(now=run_at)
        if save:
            self.save(update_fields=["last_run_at", "next_run_at"])

    def update_status(self, save=True):
        now = timezone.now()
        new_status = self.status
        if now < self.start_time:
            new_status = self.STATUS_CREATED
        elif self.start_time <= now <= self.end_time:
            new_status = self.STATUS_RUNNING
        else:
            new_status = self.STATUS_FINISHED
        if new_status != self.status:
            self.status = new_status
            if save:
                self.save(update_fields=["status"])
        return self.status


class MailingAttempt(models.Model):
    STATUS_SUCCESS = "success"
    STATUS_FAILED = "failed"

    STATUS_CHOICES = (
        (STATUS_SUCCESS, "Успешно"),
        (STATUS_FAILED, "Не успешно"),
    )

    mailing = models.ForeignKey(Mailing, on_delete=models.CASCADE, related_name="attempts")
    recipient = models.ForeignKey(Recipient, on_delete=models.CASCADE, related_name="attempts")
    attempt_time = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    server_response = models.TextField(blank=True)

    class Meta:
        verbose_name = "Попытка рассылки"
        verbose_name_plural = "Попытки рассылки"
        ordering = ("-attempt_time",)

    def __str__(self):
        return f"Попытка #{self.pk} для рассылки {self.mailing_id}"
