"""Límite compartido entre procesos y versiones de la API."""
import math
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import authenticate
from django.db import transaction
from django.utils import timezone
from django.utils.crypto import salted_hmac
from rest_framework.exceptions import Throttled

from .models import LoginAttempt
from .permissions import is_manager, is_operator
from .retirement_permissions import reviewer_has_account


def authenticate_limited(request, *, username, password):
    # No se confía en X-Forwarded-For aportado por el cliente.
    key = salted_hmac('inventory.login.limit', username+'\0'+request.META.get('REMOTE_ADDR', ''), algorithm='sha256').hexdigest()
    window = timedelta(seconds=settings.LOGIN_FAILURE_WINDOW_SECONDS)
    with transaction.atomic():
        attempt, _ = LoginAttempt.objects.select_for_update().get_or_create(
            key=key, defaults={'window_started': timezone.now()})
        now = timezone.now()
        if now >= attempt.window_started + window:
            attempt.failures = 0
            attempt.window_started = now
        if attempt.failures >= settings.LOGIN_FAILURE_LIMIT:
            retry = max(1, math.ceil((attempt.window_started + window - now).total_seconds()))
            raise Throttled(wait=retry, detail='Demasiados intentos de acceso. Espera antes de volver a intentarlo.')
        user = authenticate(request, username=username, password=password)
        allowed = user is not None and (is_manager(user) or is_operator(user) or reviewer_has_account(user))
        if allowed:
            attempt.failures = 0
            attempt.window_started = now
        else:
            if attempt.failures == 0:
                attempt.window_started = now
            attempt.failures += 1
        attempt.save(update_fields=['failures', 'window_started'])
        return user
