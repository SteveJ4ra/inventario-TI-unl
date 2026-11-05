from getpass import getpass
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction


class Command(BaseCommand):
    help = "Crea un operador con contraseña interactiva y permisos exclusivos de operador."

    def handle(self, *args, **options):
        username = input("Usuario del nuevo operador: ").strip()
        User = get_user_model()
        user = User(username=username)
        try:
            user.full_clean(exclude=["password"])
            password = getpass("Contraseña: ")
            if password != getpass("Repite la contraseña: "):
                raise CommandError("Las contraseñas no coinciden.")
            validate_password(password, user)
        except ValidationError as exc:
            raise CommandError("; ".join(exc.messages)) from exc
        with transaction.atomic():
            user.set_password(password)
            user.save()
            group, _ = Group.objects.get_or_create(name="Operadores")
            user.groups.add(group)
        self.stdout.write(
            self.style.SUCCESS(
                "Operador creado. No tiene permisos administrativos generales."
            )
        )
