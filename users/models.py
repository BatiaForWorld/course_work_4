from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.validators import RegexValidator
from django.db import models


class UserManager(BaseUserManager):

	use_in_migrations = True

	def _create_user(self, email, password, **extra_fields):
		if not email:
			raise ValueError("Email must be provided")
		email = self.normalize_email(email)
		user = self.model(email=email, **extra_fields)
		user.set_password(password)
		user.save(using=self._db)
		return user

	def create_user(self, email, password=None, **extra_fields):
		extra_fields.setdefault("is_staff", False)
		extra_fields.setdefault("is_superuser", False)
		return self._create_user(email, password, **extra_fields)

	def create_superuser(self, email, password=None, **extra_fields):
		extra_fields.setdefault("is_staff", True)
		extra_fields.setdefault("is_superuser", True)

		if extra_fields.get("is_staff") is not True:
			raise ValueError("Superuser must have is_staff=True")
		if extra_fields.get("is_superuser") is not True:
			raise ValueError("Superuser must have is_superuser=True")

		return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
	username = None
	email = models.EmailField("email address", unique=True)
	avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)
	phone_regex = RegexValidator(
		regex=r"^\+?1?\d{9,15}$",
		message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.",
	)
	phone = models.CharField(validators=[phone_regex], max_length=17, blank=True)
	country = models.CharField(max_length=100, blank=True)

	USERNAME_FIELD = "email"
	REQUIRED_FIELDS = []

	objects = UserManager()

	def __str__(self):
		return self.email
