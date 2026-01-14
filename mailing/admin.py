from django.contrib import admin

from .models import Mailing, MailingAttempt, Message, Recipient


@admin.register(Recipient)
class RecipientAdmin(admin.ModelAdmin):
    list_display = ("email", "full_name", "owner")
    search_fields = ("email", "full_name")
    list_filter = ("owner",)


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("subject", "owner")
    search_fields = ("subject", "body")
    list_filter = ("owner",)


class MailingAttemptInline(admin.TabularInline):
    model = MailingAttempt
    extra = 0
    readonly_fields = ("recipient", "attempt_time", "status", "server_response")


@admin.register(Mailing)
class MailingAdmin(admin.ModelAdmin):
    list_display = ("id", "start_time", "end_time", "periodicity", "next_run_at", "status", "is_active", "owner")
    list_filter = ("status", "is_active", "start_time")
    search_fields = ("message__subject",)
    filter_horizontal = ("recipients",)
    inlines = (MailingAttemptInline,)


@admin.register(MailingAttempt)
class MailingAttemptAdmin(admin.ModelAdmin):
    list_display = ("mailing", "recipient", "attempt_time", "status")
    list_filter = ("status", "attempt_time")
    search_fields = ("mailing__message__subject", "recipient__email")
