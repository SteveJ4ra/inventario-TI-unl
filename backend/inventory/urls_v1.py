"""Recorrido base versionado; las rutas históricas conservan su contrato."""
from django.urls import path

from .auth_views import CsrfView, LoginView, LogoutView, MeView
from .views import AssetsView, AssetView, CustodiansView, MovementsView, OperationView

urlpatterns = [
    path("auth/csrf/", CsrfView.as_view()),
    path("auth/login/", LoginView.as_view()),
    path("auth/me/", MeView.as_view()),
    path("auth/logout/", LogoutView.as_view()),
    path("assets/", AssetsView.as_view()),
    path("assets/<int:asset_id>/", AssetView.as_view(http_method_names=["get", "head", "options"])),
    path("assets/<int:asset_id>/movements/", MovementsView.as_view()),
    path("assets/<int:asset_id>/deliver/", OperationView.as_view(), {"operation": "deliver"}),
    path("assets/<int:asset_id>/return/", OperationView.as_view(), {"operation": "return"}),
    path("custodians/", CustodiansView.as_view()),
]
