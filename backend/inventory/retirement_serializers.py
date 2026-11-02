"""Validación de entradas para los endpoints 005; no habilita rutas."""

from rest_framework import serializers
from .serializers import StrictSerializer


class NormalRetirementInput(StrictSerializer):
    expected_revision = serializers.IntegerField(min_value=0)
    reason = serializers.CharField(max_length=2000)


class RetirementRequestInput(NormalRetirementInput):
    reviewer_id = serializers.IntegerField(min_value=1)


class RetirementDecisionInput(StrictSerializer):
    expected_revision = serializers.IntegerField(min_value=0)
    decision = serializers.ChoiceField(choices=("approve", "reject"))
    reason = serializers.CharField(max_length=2000, required=False, allow_blank=True, default="")

    def validate(self, attrs):
        if attrs["decision"] == "reject" and not attrs["reason"].strip():
            raise serializers.ValidationError({"reason": ["Indica el motivo del rechazo."]})
        return attrs


class RetirementReassignmentInput(StrictSerializer):
    expected_revision = serializers.IntegerField(min_value=0)
    reviewer_id = serializers.IntegerField(min_value=1)


class ReviewerCreateInput(StrictSerializer):
    username = serializers.CharField(max_length=150)
    faculty_id = serializers.IntegerField(min_value=1)
    password = serializers.CharField(write_only=True, trim_whitespace=False)


class ReviewerDeactivateInput(StrictSerializer):
    active = serializers.BooleanField()

    def validate_active(self, value):
        if value:
            raise serializers.ValidationError("Esta operación solo desactiva la cuenta.")
        return value


class ReviewerPasswordChangeInput(StrictSerializer):
    current_password = serializers.CharField(write_only=True, trim_whitespace=False)
    new_password = serializers.CharField(write_only=True, trim_whitespace=False)
