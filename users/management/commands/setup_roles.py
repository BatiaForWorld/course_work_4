from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand

MANAGER_PERMISSIONS = [
    "view_user",
    "change_user",
    "can_view_all_mailings",
    "can_view_all_recipients",
    "can_view_all_messages",
    "can_toggle_mailings",
]


class Command(BaseCommand):
    help = "Create default user groups and assign permissions"

    def handle(self, *args, **options):
        user_model = get_user_model()

        managers, created = Group.objects.get_or_create(name="Менеджеры")
        permissions = Permission.objects.filter(codename__in=MANAGER_PERMISSIONS)
        managers.permissions.set(permissions)
        managers.save()
        if created:
            self.stdout.write(self.style.SUCCESS("Группа 'Менеджеры' создана."))
        else:
            self.stdout.write(self.style.SUCCESS("Группа 'Менеджеры' обновлена."))

        admin_email = "admin@mail.ru"
        admin_password = "admin"
        admin_defaults = {
            "is_active": True,
            "is_staff": True,
            "is_superuser": True,
        }

        admin_user, created = user_model.objects.get_or_create(email=admin_email, defaults=admin_defaults)
        if created:
            admin_user.set_password(admin_password)
            admin_user.save()
            self.stdout.write(self.style.SUCCESS("Администратор 'admin@mail.ru' создан."))
        else:
            updated = False
            for field, value in admin_defaults.items():
                if getattr(admin_user, field) != value:
                    setattr(admin_user, field, value)
                    updated = True
            if updated:
                admin_user.save()
            if not admin_user.check_password(admin_password):
                admin_user.set_password(admin_password)
                admin_user.save(update_fields=["password"])
            self.stdout.write(self.style.SUCCESS("Администратор 'admin@mail.ru' обновлен."))
