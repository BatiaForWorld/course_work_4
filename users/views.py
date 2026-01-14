from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404, redirect
from django.template.loader import render_to_string
from django.urls import reverse, reverse_lazy
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.views import View
from django.views.generic import DetailView, FormView, ListView, UpdateView

from .forms import LoginForm, ProfileForm, RegistrationForm

User = get_user_model()


class UserLoginView(LoginView):
    template_name = "users/login.html"
    authentication_form = LoginForm


class UserLogoutView(LogoutView):
    next_page = reverse_lazy("users:login")


class RegistrationView(FormView):
    template_name = "users/register.html"
    form_class = RegistrationForm
    success_url = reverse_lazy("users:login")

    def form_valid(self, form):
        user = form.save(commit=False)
        user.is_active = False
        user.save()
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        activation_link = self.request.build_absolute_uri(
            reverse("users:activate", kwargs={"uidb64": uid, "token": token})
        )
        context = {
            "user": user,
            "activation_link": activation_link,
        }
        subject = "Activate your account"
        message = render_to_string("users/email/activation_email.txt", context)
        send_mail(subject, message, None, [user.email], fail_silently=False)
        messages.success(self.request, "Please confirm your email address to complete registration.")
        return super().form_valid(form)


class ActivationView(View):
    def get(self, request, uidb64, token, *args, **kwargs):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None
        if user is not None and default_token_generator.check_token(user, token):
            user.is_active = True
            user.save()
            messages.success(request, "Account successfully activated. You may log in now.")
            return redirect("users:login")
        messages.error(request, "Activation link is invalid or has expired.")
        return redirect("users:login")


class ProfileDetailView(LoginRequiredMixin, DetailView):
    model = User
    template_name = "users/profile_detail.html"

    def get_object(self, queryset=None):
        return self.request.user


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = ProfileForm
    template_name = "users/profile_form.html"
    success_url = reverse_lazy("users:profile")

    def get_object(self, queryset=None):
        return self.request.user


class UserListView(PermissionRequiredMixin, ListView):
    model = User
    template_name = "users/user_list.html"
    permission_required = "users.view_user"
    context_object_name = "users"


class ToggleUserActiveView(PermissionRequiredMixin, View):
    permission_required = "users.change_user"

    def post(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        if user == request.user:
            messages.error(request, "You cannot modify your own status.")
            return redirect("users:list")
        user.is_active = not user.is_active
        user.save(update_fields=["is_active"])
        messages.success(request, "User status updated.")
        return redirect("users:list")
