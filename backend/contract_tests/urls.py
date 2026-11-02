from django.urls import path
from inventory.auth_views import CsrfView
from inventory.retirement_api import *
urlpatterns=[
 path("api/auth/csrf/",CsrfView.as_view()),
 path("api/auth/login/",RetirementLoginView.as_view()),
 path("api/auth/me/",RetirementSessionView.as_view()),
 path("api/auth/logout/",RetirementLogoutView.as_view()),
 path("api/auth/change-password/",ReviewerPasswordView.as_view()),
 path("api/assets/<int:asset_id>/retire/",RetireView.as_view()),
 path("api/assets/<int:asset_id>/retirement-requests/",RetirementRequestsView.as_view()),
 path("api/reviewer/retirement-requests/",AssignedRequestsView.as_view()),
 path("api/retirement-requests/<int:request_id>/decision/",DecisionView.as_view()),
 path("api/retirement-requests/<int:request_id>/reassign/",ReassignView.as_view()),
 path("api/operator/reviewers/",ReviewersView.as_view()),
 path("api/operator/reviewers/<int:user_id>/",ReviewerView.as_view()),
]
