"""Telemetría técnica sin cuerpos, credenciales, consultas ni identificadores de URL."""
import json
import logging
import time
import uuid
from datetime import datetime, timezone
from django.db import DatabaseError, connection
from django.http import JsonResponse
from django.views.decorators.http import require_GET

logger = logging.getLogger("inventory.http")


class JsonRequestFormatter(logging.Formatter):
    def format(self, record):
        return json.dumps({
            "timestamp": datetime.fromtimestamp(record.created, timezone.utc).isoformat(),
            "level": record.levelname,
            **getattr(record, "event", {"event": "application_log"}),
        }, ensure_ascii=False)


class RequestLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        started = time.monotonic()
        request.request_id = uuid.uuid4().hex
        response = self.get_response(request)
        response["X-Request-ID"] = request.request_id
        match = getattr(request, "resolver_match", None)
        route = match.route if match else "unresolved"
        # route contiene la plantilla resuelta, nunca parámetros o query string.
        logger.log(logging.ERROR if response.status_code >= 500 else logging.INFO,
                   "http_request", extra={"event": {
                       "event": "http_request", "request_id": request.request_id,
                       "method": request.method, "route": route,
                       "status": response.status_code,
                       "duration_ms": round((time.monotonic() - started) * 1000, 2),
                   }})
        return response


@require_GET
def readiness(request):
    """Disponibilidad de aplicación y conexión SQL; no expone configuración."""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except DatabaseError:
        response = JsonResponse({"success": False, "message": "Servicio no disponible.",
                             "data": None, "errors": {"code": "not_ready"}, "meta": {}}, status=503)
        response["Cache-Control"] = "no-store"
        return response
    response = JsonResponse({"success": True, "message": "Servicio disponible.",
                             "data": {"status": "ready"}, "errors": None, "meta": {}})
    response["Cache-Control"] = "no-store"
    return response
