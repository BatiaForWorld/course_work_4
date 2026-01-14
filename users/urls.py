from django.urls import path

from django.contrib.auth import views as auth_views

from .views import (
    ActivationView,
    ProfileDetailView,
    ProfileUpdateView,
    RegistrationView,
    ToggleUserActiveView,
    UserListView,
    UserLoginView,
    UserLogoutView,
)

app_name = "users"

urlpatterns = [
    path("login/", UserLoginView.as_view(), name="login"),
    path("logout/", UserLogoutView.as_view(), name="logout"),
    path("register/", RegistrationView.as_view(), name="register"),
    path("activate/<uidb64>/<token>/", ActivationView.as_view(), name="activate"),
    path("profile/", ProfileDetailView.as_view(), name="profile"),
    path("profile/edit/", ProfileUpdateView.as_view(), name="profile_edit"),
    path("list/", UserListView.as_view(), name="list"),
    path("toggle/<int:pk>/", ToggleUserActiveView.as_view(), name="toggle"),
    path("password-reset/", auth_views.PasswordResetView.as_view(template_name="users/password_reset_form.html"),
         name="password_reset"),
    path("password-reset/done/",
         auth_views.PasswordResetDoneView.as_view(template_name="users/password_reset_done.html"),
         name="password_reset_done"),
    path("reset/<uidb64>/<token>/",
         auth_views.PasswordResetConfirmView.as_view(template_name="users/password_reset_confirm.html"),
         name="password_reset_confirm"),
    path("reset/done/",
         auth_views.PasswordResetCompleteView.as_view(template_name="users/password_reset_complete.html"),
         name="password_reset_complete"),
]
