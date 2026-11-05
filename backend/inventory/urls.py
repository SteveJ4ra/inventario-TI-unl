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
    AssetsView,
    AssetRecoveryView,
    AssetView,
    CustodiansView,
    HistoryView,
    IncidentsView,
    IncidentResolutionView,
    MaintenanceDetailView,
    MaintenanceStartView,
    MaintenanceCloseView,
    MovementsView,
    OperationView,
    OptionsView,
    FacultiesView, OperatorFacultiesView, OperatorFacultyView, OperatorAssetFacultyView,
    AcquisitionsView, AcquisitionView, CustodianView, AssetHistoryView,
)

urlpatterns = [
    path("auth/csrf/", CsrfView.as_view()),
    path("auth/login/", LoginView.as_view()),
    path("auth/me/", MeView.as_view()),
    path("auth/logout/", LogoutView.as_view()),
    path("assets/", AssetsView.as_view()),
    path("assets/<int:asset_id>/", AssetView.as_view()),
    path("assets/<int:asset_id>/movements/", MovementsView.as_view()),
    path("assets/<int:asset_id>/history/", HistoryView.as_view()),
    path("assets/<int:asset_id>/incidents/", IncidentsView.as_view()),
    path("assets/<int:asset_id>/recover/", AssetRecoveryView.as_view()),
    path("incidents/<int:incident_id>/resolve/", IncidentResolutionView.as_view()),
    path("maintenance/<int:maintenance_id>/", MaintenanceDetailView.as_view()),
    path("assets/<int:asset_id>/maintenance/", MaintenanceStartView.as_view()),
    path("maintenance/<int:maintenance_id>/close/", MaintenanceCloseView.as_view()),
    path("custodians/", CustodiansView.as_view()),
    path("options/", OptionsView.as_view()),
    path("faculties/", FacultiesView.as_view()),
    path("operator/faculties/", OperatorFacultiesView.as_view()),
    path("operator/faculties/<int:faculty_id>/", OperatorFacultyView.as_view()),
    path("operator/assets/<int:asset_id>/faculty/", OperatorAssetFacultyView.as_view()),
    path("acquisitions/", AcquisitionsView.as_view()),
    path("acquisitions/<int:document_id>/", AcquisitionView.as_view()),
    path("custodians/<int:custodian_id>/", CustodianView.as_view()),
    path("assets/<int:asset_id>/history/", AssetHistoryView.as_view()),
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
