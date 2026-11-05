from django.contrib.auth import authenticate, login, logout, get_user_model
from django.middleware.csrf import get_token
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from .permissions import is_manager, is_operator, IsManagerOrOperator, session_payload


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
        # Un intento rechazado no conserva una sesión anterior autorizada.
        logout(request)
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
            User = get_user_model()
            try:
                inactive = User._default_manager.get_by_natural_key(request.data["username"])
            except User.DoesNotExist:
                inactive = None
            if inactive is not None and not inactive.is_active and inactive.check_password(request.data["password"]):
                raise PermissionDenied("Se requiere una cuenta activa autorizada.")
            raise ValidationError("Usuario o contraseña incorrectos.")
        if not (is_manager(user) or is_operator(user)):
            raise PermissionDenied("Se requiere acceso de gestor autorizado.")
        login(request, user)
        return Response(session_payload(user))


class MeView(APIView):
    permission_classes = [IsManagerOrOperator]

    def get(self, request):
        return Response(session_payload(request.user))


class LogoutView(APIView):
    permission_classes = [IsManagerOrOperator]

    def post(self, request):
        logout(request)
        return Response({"detail": "Sesión cerrada."})
