from django.contrib.auth import authenticate, login, logout
from django.middleware.csrf import get_token
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from .permissions import is_manager


@method_decorator(ensure_csrf_cookie, name="dispatch")
class CsrfView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        return Response({"csrfToken": get_token(request)})


@method_decorator(csrf_protect, name="dispatch")
class LoginView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        if (
            not isinstance(request.data, dict)
            or set(request.data) != {"username", "password"}
            or not all(isinstance(value, str) for value in request.data.values())
        ):
            raise ValidationError("Indica usuario y contraseña.")
        user = authenticate(
            request,
            username=request.data["username"],
            password=request.data["password"],
        )
        if user is None:
            raise ValidationError("Usuario o contraseña incorrectos.")
        if not is_manager(user):
            raise PermissionDenied("Se requiere acceso de gestor autorizado.")
        login(request, user)
        return Response({"id": user.pk, "username": user.username})


class MeView(APIView):
    def get(self, request):
        return Response({"id": request.user.pk, "username": request.user.username})


class LogoutView(APIView):
    def post(self, request):
        logout(request)
        return Response({"detail": "Sesión cerrada."})
