from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.core.cache import cache
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_control
from django.views import View
from django.views.generic import DetailView, ListView, TemplateView
from django.views.generic.edit import CreateView, DeleteView, UpdateView

from .forms import MailingForm, MessageForm, RecipientForm
from .models import Mailing, MailingAttempt, Message, Recipient
from .services import can_send_mailing, send_mailing_now


class OwnerQuerySetMixin:
	owner_field = "owner"
	manager_permission = ""

	def get_queryset(self):
		qs = super().get_queryset()
		if self.manager_permission and self.request.user.has_perm(self.manager_permission):
			return qs
		return qs.filter(**{self.owner_field: self.request.user})


class OwnerFormValidMixin:
	def form_valid(self, form):
		form.instance.owner = self.request.user
		return super().form_valid(form)



@method_decorator(cache_control(max_age=60, private=True), name="dispatch")
class DashboardView(TemplateView):
	template_name = "mailing/dashboard.html"

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		now = timezone.now()
		totals = cache.get("dashboard_totals")
		if totals is None:
			totals = {
				"total_mailings": Mailing.objects.count(),
				"active_mailings": Mailing.objects.filter(
					start_time__lte=now,
					end_time__gte=now,
					status=Mailing.STATUS_RUNNING,
				).count(),
				"unique_recipients": Recipient.objects.values("email").distinct().count(),
			}
			cache.set("dashboard_totals", totals, 60)
		user_stats = []
		user_sent = 0
		if self.request.user.is_authenticated:
			user_stats = (
				MailingAttempt.objects.filter(mailing__owner=self.request.user)
				.values("status")
				.annotate(total=Count("id"))
			)
			user_sent = sum(item["total"] for item in user_stats)
		context.update(
			{
				"total_mailings": totals["total_mailings"],
				"active_mailings": totals["active_mailings"],
				"unique_recipients": totals["unique_recipients"],
				"user_attempts": list(user_stats),
				"user_sent": user_sent,
			}
		)
		return context


class RecipientListView(LoginRequiredMixin, OwnerQuerySetMixin, ListView):
	model = Recipient
	template_name = "mailing/recipient_list.html"
	manager_permission = "mailing.can_view_all_recipients"


class RecipientCreateView(LoginRequiredMixin, OwnerFormValidMixin, CreateView):
	model = Recipient
	form_class = RecipientForm
	template_name = "mailing/recipient_form.html"
	success_url = reverse_lazy("mailing:recipient_list")


class RecipientUpdateView(LoginRequiredMixin, OwnerQuerySetMixin, UpdateView):
	model = Recipient
	form_class = RecipientForm
	template_name = "mailing/recipient_form.html"
	success_url = reverse_lazy("mailing:recipient_list")


class RecipientDeleteView(LoginRequiredMixin, OwnerQuerySetMixin, DeleteView):
	model = Recipient
	template_name = "mailing/confirm_delete.html"
	success_url = reverse_lazy("mailing:recipient_list")


class MessageListView(LoginRequiredMixin, OwnerQuerySetMixin, ListView):
	model = Message
	template_name = "mailing/message_list.html"
	manager_permission = "mailing.can_view_all_messages"


class MessageCreateView(LoginRequiredMixin, OwnerFormValidMixin, CreateView):
	model = Message
	form_class = MessageForm
	template_name = "mailing/message_form.html"
	success_url = reverse_lazy("mailing:message_list")


class MessageUpdateView(LoginRequiredMixin, OwnerQuerySetMixin, UpdateView):
	model = Message
	form_class = MessageForm
	template_name = "mailing/message_form.html"
	success_url = reverse_lazy("mailing:message_list")


class MessageDeleteView(LoginRequiredMixin, OwnerQuerySetMixin, DeleteView):
	model = Message
	template_name = "mailing/confirm_delete.html"
	success_url = reverse_lazy("mailing:message_list")


class MailingListView(LoginRequiredMixin, OwnerQuerySetMixin, ListView):
	model = Mailing
	template_name = "mailing/mailing_list.html"
	manager_permission = "mailing.can_view_all_mailings"

	def get_queryset(self):
		qs = super().get_queryset().select_related("message").prefetch_related("recipients")
		for mailing in qs:
			mailing.update_status(save=True)
		return qs


class MailingDetailView(LoginRequiredMixin, OwnerQuerySetMixin, DetailView):
	model = Mailing
	template_name = "mailing/mailing_detail.html"
	manager_permission = "mailing.can_view_all_mailings"

	def get_object(self, queryset=None):
		obj = super().get_object(queryset)
		obj.update_status(save=True)
		return obj

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context["can_send"] = can_send_mailing(self.object)
		return context


class MailingCreateView(LoginRequiredMixin, OwnerFormValidMixin, CreateView):
	model = Mailing
	form_class = MailingForm
	template_name = "mailing/mailing_form.html"
	success_url = reverse_lazy("mailing:mailing_list")

	def get_form(self, form_class=None):
		form = super().get_form(form_class)
		user = self.request.user
		form.fields["message"].queryset = Message.objects.filter(owner=user)
		form.fields["recipients"].queryset = Recipient.objects.filter(owner=user)
		return form


class MailingUpdateView(LoginRequiredMixin, OwnerQuerySetMixin, UpdateView):
	model = Mailing
	form_class = MailingForm
	template_name = "mailing/mailing_form.html"
	success_url = reverse_lazy("mailing:mailing_list")

	def get_form(self, form_class=None):
		form = super().get_form(form_class)
		user = self.request.user
		form.fields["message"].queryset = Message.objects.filter(owner=user)
		form.fields["recipients"].queryset = Recipient.objects.filter(owner=user)
		return form


class MailingDeleteView(LoginRequiredMixin, OwnerQuerySetMixin, DeleteView):
	model = Mailing
	template_name = "mailing/confirm_delete.html"
	success_url = reverse_lazy("mailing:mailing_list")


class MailingAttemptListView(LoginRequiredMixin, ListView):
	model = MailingAttempt
	template_name = "mailing/attempt_list.html"

	def get_queryset(self):
		qs = super().get_queryset().select_related("mailing", "recipient")
		if self.request.user.has_perm("mailing.can_view_all_mailings"):
			return qs
		return qs.filter(mailing__owner=self.request.user)


class MailingReportView(LoginRequiredMixin, OwnerQuerySetMixin, ListView):
	model = Mailing
	template_name = "mailing/report_list.html"
	manager_permission = "mailing.can_view_all_mailings"

	def get_queryset(self):
		qs = super().get_queryset()
		return (
			qs.select_related("message")
			.annotate(
				success_count=Count(
					"attempts",
					filter=Q(attempts__status=MailingAttempt.STATUS_SUCCESS),
				),
				failed_count=Count(
					"attempts",
					filter=Q(attempts__status=MailingAttempt.STATUS_FAILED),
				),
				total_count=Count("attempts"),
			)
			.order_by("-start_time")
		)


class ToggleMailingView(PermissionRequiredMixin, View):
	permission_required = "mailing.can_toggle_mailings"

	def post(self, request, pk, *args, **kwargs):
		mailing = get_object_or_404(Mailing, pk=pk)
		mailing.is_active = not mailing.is_active
		mailing.save(update_fields=["is_active"])
		messages.success(request, "Статус рассылки обновлён.")
		return redirect("mailing:mailing_list")


class MailingSendView(LoginRequiredMixin, View):
	def post(self, request, pk, *args, **kwargs):
		mailing = get_object_or_404(Mailing.objects.filter(owner=request.user), pk=pk)
		if not can_send_mailing(mailing):
			messages.error(request, "Рассылка недоступна для отправки в данный момент.")
			return redirect("mailing:mailing_detail", pk=mailing.pk)
		result = send_mailing_now(mailing)
		messages.success(
			request,
			f"Рассылка выполнена. Отправлено: {result['sent']}, ошибок: {result['failed']}.",
		)
		return redirect("mailing:mailing_detail", pk=mailing.pk)
