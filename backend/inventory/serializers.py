from rest_framework import serializers
from .models import (
    Asset, AssetTransition, Assignment, Category, Condition, Custodian,
    Incident, MaintenanceEvent, Movement, RecoveryEvent,
)


class StrictSerializer(serializers.Serializer):
    def to_internal_value(self, data):
        if not isinstance(data, dict):
            raise serializers.ValidationError("Se requiere un objeto JSON.")
        extra = set(data) - set(self.fields)
        if extra:
            raise serializers.ValidationError(
                {key: ["Campo no permitido."] for key in sorted(extra)}
            )
        return super().to_internal_value(data)


class AssetInput(StrictSerializer):
    name = serializers.CharField(max_length=160)
    description = serializers.CharField(max_length=2000)
    category = serializers.ChoiceField(choices=Category.choices)
    brand = serializers.CharField(max_length=120)
    model = serializers.CharField(max_length=120)
    serial_number = serializers.CharField(max_length=160)
    location = serializers.CharField(max_length=240)
    condition = serializers.ChoiceField(choices=Condition.choices)


class CustodianInput(StrictSerializer):
    full_name = serializers.CharField(max_length=160)
    email = serializers.EmailField(max_length=254)
    department = serializers.CharField(
        max_length=160, required=False, allow_blank=True, default=""
    )


class CustodianOutput(serializers.ModelSerializer):
    class Meta:
        model = Custodian
        fields = ["id", "full_name", "email", "department"]


class AssetOutput(serializers.ModelSerializer):
    active_maintenance_id = serializers.IntegerField(read_only=True, default=None)
    current_custodian = CustodianOutput()
    created_by = serializers.SerializerMethodField()
    rectifiable_movement_id = serializers.SerializerMethodField()
    last_lifecycle_status = serializers.CharField(source="last_known.lifecycle_status", read_only=True, default=None)
    last_assignment = serializers.CharField(source="last_known.assignment", read_only=True, default=None)
    last_condition = serializers.CharField(source="last_known.condition", read_only=True, default=None)
    last_location = serializers.CharField(source="last_known.location", read_only=True, default=None)
    last_custodian = serializers.JSONField(source="last_known.custodian", read_only=True, default=None)

    class Meta:
        model = Asset
        fields = [
            "id",
            "code",
            "name",
            "description",
            "category",
            "brand",
            "model",
            "serial_number",
            "location",
            "condition",
            "lifecycle_status",
            "assignment",
            "active_maintenance_id",
            "current_custodian",
            "revision",
            "created_at",
            "created_by",
            "rectifiable_movement_id",
            "last_lifecycle_status",
            "last_assignment",
            "last_condition",
            "last_location",
            "last_custodian",
        ]

    def get_created_by(self, asset):
        return {"id": asset.created_by_id, "username": asset.created_by.username}

    def get_rectifiable_movement_id(self, asset):
        return getattr(asset, "latest_rectifiable_id", None)


class MovementOutput(serializers.ModelSerializer):
    actor = serializers.SerializerMethodField()
    custodian = serializers.JSONField(source="custodian_snapshot")
    rectified_by_id = serializers.SerializerMethodField()

    class Meta:
        model = Movement
        fields = [
            "id",
            "asset_id",
            "type",
            "occurred_at",
            "actor",
            "custodian",
            "before",
            "after",
            "note",
            "reason",
            "rectifies_id",
            "rectified_by_id",
            "resulting_revision",
        ]

    def get_actor(self, movement):
        return {
            "id": movement.actor_id,
            "username": movement.actor.username,
            "recorded_label": movement.actor_label,
        }

    def get_rectified_by_id(self, movement):
        reverse = getattr(movement, "rectified_by", None)
        return reverse.pk if reverse else None


class OperationInput(StrictSerializer):
    expected_revision = serializers.IntegerField(min_value=0)
    note = serializers.CharField(
        max_length=2000, required=False, allow_blank=True, default=""
    )


class IncidentInput(StrictSerializer):
    expected_revision = serializers.IntegerField(min_value=0)
    type = serializers.ChoiceField(choices=Incident.Type.choices)
    description = serializers.CharField(max_length=2000)


class IncidentResolutionInput(StrictSerializer):
    expected_revision = serializers.IntegerField(min_value=0)
    resolution_note = serializers.CharField(max_length=2000)


class RecoveryInput(StrictSerializer):
    expected_revision = serializers.IntegerField(min_value=0)
    inspection_confirmed = serializers.JSONField()
    inspected_condition = serializers.ChoiceField(choices=Condition.choices)
    recovered_location = serializers.CharField(max_length=240)
    note = serializers.CharField(max_length=2000, required=False, allow_blank=True, default="")

    def validate_inspection_confirmed(self, value):
        if value is not True:
            raise serializers.ValidationError("Confirma la inspección del activo.")
        return value


class RecoveryOutput(serializers.ModelSerializer):
    class Meta:
        model = RecoveryEvent
        fields = [
            "id", "asset_id", "incident_id", "found_at", "found_by_id",
            "inspected_condition", "recovered_location", "note",
        ]


class IncidentOutput(serializers.ModelSerializer):
    reported_by = serializers.SerializerMethodField()
    resolved_by = serializers.SerializerMethodField()

    class Meta:
        model = Incident
        fields = [
            "id", "asset_id", "type", "description", "status",
            "reported_by", "reported_at", "resolution_note", "resolved_by", "resolved_at",
        ]

    def get_reported_by(self, incident):
        return {"id": incident.reported_by_id, "username": incident.reported_by.username}

    def get_resolved_by(self, incident):
        if incident.resolved_by_id is None:
            return None
        return {"id": incident.resolved_by_id, "username": incident.resolved_by.username}


class MaintenanceStartInput(StrictSerializer):
    expected_revision = serializers.IntegerField(min_value=0)
    description = serializers.CharField(max_length=2000)
    workshop_location = serializers.CharField(max_length=240)


class MaintenanceCloseInput(StrictSerializer):
    expected_revision = serializers.IntegerField(min_value=0)
    result = serializers.CharField(max_length=2000)
    receiving_location = serializers.CharField(max_length=240)
    location_confirmed = serializers.JSONField()

    def validate_location_confirmed(self, value):
        if value is not True:
            raise serializers.ValidationError("Confirma la ubicación de recepción.")
        return value


class MaintenanceDetail(serializers.ModelSerializer):
    revision = serializers.IntegerField(source="asset.revision")

    class Meta:
        model = MaintenanceEvent
        fields = [
            "id", "asset_id", "status", "description", "previous_location",
            "workshop_location", "started_by_id", "started_at",
            "closed_by_id", "closed_at", "result",
            "receiving_location", "location_confirmed", "revision",
        ]


class HistoryEntry(serializers.Serializer):
    event_type = serializers.CharField()
    event_id = serializers.IntegerField()
    occurred_at = serializers.DateTimeField()
    actor = serializers.DictField()
    resulting_revision = serializers.IntegerField()
    data = serializers.DictField()

    def to_representation(self, event):
        if isinstance(event, AssetTransition):
            entry = {
                "event_type": event.event_type,
                "actor": {"id": event.actor_id, "username": event.actor_label},
                "data": {
                    "projection_id": event.event_id,
                    "before": event.before,
                    "after": event.after,
                },
            }
        else:
            data = MovementOutput(event).data
            entry = {"event_type": "movement", "actor": data["actor"], "data": data}
        return super().to_representation({
            **entry,
            "event_id": event.pk,
            "occurred_at": event.occurred_at,
            "resulting_revision": event.resulting_revision,
        })


class DeliveryInput(OperationInput):
    custodian_id = serializers.IntegerField(min_value=1)
    destination = serializers.CharField(max_length=240)


class ReturnInput(OperationInput):
    condition = serializers.ChoiceField(choices=Condition.choices)
    reception_location = serializers.CharField(max_length=240)


class ConditionInput(OperationInput):
    condition = serializers.ChoiceField(choices=Condition.choices)
    reason = serializers.CharField(max_length=2000)


class RectificationInput(OperationInput):
    movement_id = serializers.IntegerField(min_value=1)
    reason = serializers.CharField(max_length=2000)


class QueryInput(StrictSerializer):
    page = serializers.IntegerField(min_value=1, default=1)
    search = serializers.CharField(required=False, allow_blank=True, max_length=240)
    category = serializers.ChoiceField(choices=Category.choices, required=False)
    condition = serializers.ChoiceField(choices=Condition.choices, required=False)
    assignment = serializers.ChoiceField(choices=Assignment.choices, required=False)
    location = serializers.CharField(required=False, max_length=240)
    custodian = serializers.IntegerField(min_value=1, required=False)
