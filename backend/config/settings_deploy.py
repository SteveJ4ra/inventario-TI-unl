"""Perfil de despliegue. HTTP local por defecto; HTTPS requiere infraestructura real."""
import os
from django.core.exceptions import ImproperlyConfigured
from .runtime_secrets import load_runtime_secrets

load_runtime_secrets()
from .settings import *  # noqa: E402,F403

if os.environ.get("DJANGO_DEBUG", "false").lower() == "true":
    raise ImproperlyConfigured("El perfil de despliegue exige DJANGO_DEBUG=false")
DEBUG = False
ALLOWED_HOSTS = [x.strip() for x in os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",") if x.strip()]
if not ALLOWED_HOSTS or "*" in ALLOWED_HOSTS:
    raise ImproperlyConfigured("Configura hosts explícitos, sin comodines")
STATIC_ROOT = BASE_DIR / "staticfiles"
MIDDLEWARE = list(MIDDLEWARE)
MIDDLEWARE.insert(MIDDLEWARE.index("django.middleware.security.SecurityMiddleware") + 1, "whitenoise.middleware.WhiteNoiseMiddleware")
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}
HTTPS_ENABLED = os.environ.get("DJANGO_HTTPS", "false").lower() == "true"
SESSION_COOKIE_SECURE = HTTPS_ENABLED
CSRF_COOKIE_SECURE = HTTPS_ENABLED
SECURE_SSL_REDIRECT = HTTPS_ENABLED
SECURE_HSTS_SECONDS = 31536000 if HTTPS_ENABLED else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False
# No confiar en cabeceras de proxy sin una infraestructura validada.

# Excepción explícita para demostración local; nunca admite destinos HTTP externos.
QR_ALLOW_LOCAL_HTTP = (not HTTPS_ENABLED and os.environ.get("QR_ALLOW_LOCAL_HTTP", "false").lower() == "true")
