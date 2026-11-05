from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction


class Command(BaseCommand):
    help = "Desactiva una cuenta de gestor sin borrar su historial."

    def add_arguments(self, parser):
        parser.add_argument("username", help="Usuario exacto del gestor a desactivar")

    def handle(self, *args, **options):
        username = options["username"].strip()
        if not username:
            raise CommandError("Indica un usuario de gestor.")
        User = get_user_model()
        with transaction.atomic():
            try:
                user = User.objects.select_for_update().get(username=username)
            except User.DoesNotExist as exc:
                raise CommandError("No existe el usuario indicado.") from exc
            if not user.groups.filter(name="Gestores").exists():
                raise CommandError("El usuario no pertenece al grupo Gestores.")
            if not user.is_active:
                raise CommandError("El gestor ya está inactivo.")
            user.is_active = False
            user.save(update_fields=["is_active"])
        self.stdout.write(self.style.SUCCESS("Gestor desactivado; se conserva su historial."))
