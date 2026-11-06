"""Contrato JSON de v1, sin modificar las representaciones históricas."""
import json

from django.utils.deprecation import MiddlewareMixin


class EnvelopeMiddleware(MiddlewareMixin):
    def process_response(self, request, response):
        if not request.path_info.startswith("/api/v1/"):
            return response
        if response.status_code in (204, 304) or request.method == "HEAD":
            return response
        if getattr(response, "streaming", False):
            return response
        content_type = response.get("Content-Type", "").split(";", 1)[0].lower()
        if content_type != "application/json":
            if response.status_code < 400:
                return response
            payload = {"code": "request_error", "detail": "No se pudo procesar la solicitud."}
        else:
            try:
                payload = json.loads(response.content)
            except (ValueError, UnicodeDecodeError):
                return response
        success = response.status_code < 400
        envelope = {
            "success": success,
            "message": "Operación realizada correctamente." if success else "No se pudo completar la operación.",
            "data": payload if success else None,
            "errors": None if success else payload,
            "meta": {},
        }
        response.content = json.dumps(envelope, ensure_ascii=False).encode("utf-8")
        response["Content-Type"] = "application/json; charset=utf-8"
        response["Content-Length"] = str(len(response.content))
        return response
