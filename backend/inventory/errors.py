from django.http import JsonResponse
from rest_framework.exceptions import APIException
from rest_framework.views import exception_handler


class Conflict(APIException):
    status_code = 409

    def __init__(self, detail, code="invalid_state"):
        self.error_code = code
        super().__init__(detail, code=code)


def api_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is None:
        return None
    data = response.data
    fields = data if isinstance(data, dict) and "detail" not in data else None
    code = getattr(exc, "error_code", getattr(exc, "default_code", "request_error"))
    detail = (
        data.get("detail", "Revisa los datos indicados.")
        if isinstance(data, dict)
        else "Solicitud inválida."
    )
    if "CSRF" in str(detail):
        code = "csrf_failed"
    response.data = {"code": code, "detail": str(detail)}
    if fields:
        response.data["fields"] = fields
    return response


def csrf_failure(request, reason=""):
    return JsonResponse(
        {"code": "csrf_failed", "detail": "Actualiza la sesión y vuelve a intentarlo."},
        status=403,
    )


class DependencyUnavailable(APIException):
    status_code = 503
    default_code = "dependency_unavailable"
    error_code = "dependency_unavailable"
