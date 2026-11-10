from urllib.parse import quote, urlsplit

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


def build_asset_qr_url(asset_code: str) -> str:
    """
    Construye la URL canónica de un activo para su código QR.
    No utiliza encabezados HTTP ni datos personales.
    """

    base_url = settings.PUBLIC_APP_URL.strip().rstrip("/")
    parsed = urlsplit(base_url)

    # Comprobar que la dirección pública es válida.
    if (
        parsed.scheme not in ("http", "https")
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
    ):
        raise ImproperlyConfigured(
            "PUBLIC_APP_URL debe ser una URL HTTP/HTTPS válida."
        )

    # HTTP solo para loopback y con permiso explícito de despliegue local.
    local_http = (parsed.scheme == "http" and parsed.hostname in {"localhost", "127.0.0.1", "::1"}
                  and getattr(settings, "QR_ALLOW_LOCAL_HTTP", False))
    if not settings.DEBUG and parsed.scheme != "https" and not local_http:
        raise ImproperlyConfigured(
            "PUBLIC_APP_URL debe utilizar HTTPS en producción."
        )

    if not isinstance(asset_code, str) or not asset_code:
        raise ValueError("El código TI no puede estar vacío.")

    # Construir el enlace utilizando el código del activo.
    safe_code = quote(asset_code, safe="")

    return f"{base_url}/assets/code/{safe_code}"