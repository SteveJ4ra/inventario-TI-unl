from django.urls import path
from .auth_views import CsrfView, LoginView, LogoutView, MeView
from .views import (
    AssetsView,
    AssetView,
    CustodiansView,
    MovementsView,
    OperationView,
    OptionsView,
)

urlpatterns = [
    path("auth/csrf/", CsrfView.as_view()),
    path("auth/login/", LoginView.as_view()),
    path("auth/me/", MeView.as_view()),
    path("auth/logout/", LogoutView.as_view()),
    path("assets/", AssetsView.as_view()),
    path("assets/<int:asset_id>/", AssetView.as_view()),
    path("assets/<int:asset_id>/movements/", MovementsView.as_view()),
    path("custodians/", CustodiansView.as_view()),
    path("options/", OptionsView.as_view()),
]
for operation in ["deliver", "return", "condition", "rectify"]:
    urlpatterns.append(
        path(
            "assets/<int:asset_id>/" + operation + "/",
            OperationView.as_view(),
            {"operation": operation},
        )
    )
