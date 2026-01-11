from django.urls import path

from .views import (
    DashboardView,
    MailingReportView,
    MailingAttemptListView,
    MailingCreateView,
    MailingDeleteView,
    MailingDetailView,
    MailingListView,
    MailingSendView,
    MailingUpdateView,
    MessageCreateView,
    MessageDeleteView,
    MessageListView,
    MessageUpdateView,
    RecipientCreateView,
    RecipientDeleteView,
    RecipientListView,
    RecipientUpdateView,
    ToggleMailingView,
)

app_name = "mailing"

urlpatterns = [
    path("", DashboardView.as_view(), name="dashboard"),
    path("reports/", MailingReportView.as_view(), name="report_list"),
    path("recipients/", RecipientListView.as_view(), name="recipient_list"),
    path("recipients/create/", RecipientCreateView.as_view(), name="recipient_create"),
    path("recipients/<int:pk>/edit/", RecipientUpdateView.as_view(), name="recipient_edit"),
    path("recipients/<int:pk>/delete/", RecipientDeleteView.as_view(), name="recipient_delete"),
    path("messages/", MessageListView.as_view(), name="message_list"),
    path("messages/create/", MessageCreateView.as_view(), name="message_create"),
    path("messages/<int:pk>/edit/", MessageUpdateView.as_view(), name="message_edit"),
    path("messages/<int:pk>/delete/", MessageDeleteView.as_view(), name="message_delete"),
    path("mailings/", MailingListView.as_view(), name="mailing_list"),
    path("mailings/create/", MailingCreateView.as_view(), name="mailing_create"),
    path("mailings/<int:pk>/", MailingDetailView.as_view(), name="mailing_detail"),
    path("mailings/<int:pk>/edit/", MailingUpdateView.as_view(), name="mailing_edit"),
    path("mailings/<int:pk>/delete/", MailingDeleteView.as_view(), name="mailing_delete"),
    path("mailings/<int:pk>/toggle/", ToggleMailingView.as_view(), name="mailing_toggle"),
    path("mailings/<int:pk>/send/", MailingSendView.as_view(), name="mailing_send"),
    path("attempts/", MailingAttemptListView.as_view(), name="attempt_list"),
]
