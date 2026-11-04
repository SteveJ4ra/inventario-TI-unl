from django.urls import path
from .auth_views import CsrfView, LoginView, LogoutView, MeView
from .imports.views import (
    ApplyView,
    BatchView,
    CancelView,
    ConfirmView,
    PreviewsView,
    TemplatesView,
)
from .views import (

    AssetQrView,
    AssetByCodeView,
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
path(
    "assets/by-code/<str:code>/",
    AssetByCodeView.as_view(),
),
path(
    "assets/<int:asset_id>/qr.svg",
    AssetQrView.as_view(),
),
    path("assets/<int:asset_id>/movements/", MovementsView.as_view()),
    path("custodians/", CustodiansView.as_view()),
    path("options/", OptionsView.as_view()),
    path("imports/templates/<str:kind>/", TemplatesView.as_view()),
    path("imports/previews/", PreviewsView.as_view()),
    path("imports/<uuid:batch_id>/", BatchView.as_view()),
    path("imports/<uuid:batch_id>/confirm/", ConfirmView.as_view()),
    path("imports/<uuid:batch_id>/apply/", ApplyView.as_view()),
    path("imports/<uuid:batch_id>/cancel/", CancelView.as_view()),
]
for operation in ["deliver", "return", "condition", "rectify"]:
    urlpatterns.append(
        path(
            "assets/<int:asset_id>/" + operation + "/",
            OperationView.as_view(),
            {"operation": operation},
        )
    )
