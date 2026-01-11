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

	STATUS_CHOICES = (
		(STATUS_CREATED, "Создана"),
		(STATUS_RUNNING, "Запущена"),
		(STATUS_FINISHED, "Завершена"),
	)

	start_time = models.DateTimeField()
	end_time = models.DateTimeField()
	status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_CREATED)
	is_active = models.BooleanField(default=True)
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
