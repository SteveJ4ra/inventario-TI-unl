from django.urls import path
from .auth_views import CsrfView, LoginView, LogoutView, MeView
from .imports.views import (
    ImportApplyView,
    ImportBatchView,
    ImportCancelView,
    ImportConfirmView,
    ImportPreviewsView,
    ImportTemplateView,
)
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
    path("imports/templates/<str:kind>/", ImportTemplateView.as_view()),
    path("imports/previews", ImportPreviewsView.as_view()),
    path("imports/<uuid:batch_id>", ImportBatchView.as_view()),
    path("imports/<uuid:batch_id>/confirm", ImportConfirmView.as_view()),
    path("imports/<uuid:batch_id>/apply", ImportApplyView.as_view()),
    path("imports/<uuid:batch_id>/cancel", ImportCancelView.as_view()),
]
for operation in ["deliver", "return", "condition", "rectify"]:
    urlpatterns.append(
        path(
            "assets/<int:asset_id>/" + operation + "/",
            OperationView.as_view(),
            {"operation": operation},
        )
    )
