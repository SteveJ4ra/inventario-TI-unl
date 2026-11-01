from rest_framework import serializers
from .models import Asset, Assignment, Category, Condition, Custodian, Movement


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
    current_custodian = CustodianOutput()
    created_by = serializers.SerializerMethodField()
    rectifiable_movement_id = serializers.SerializerMethodField()

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
            "assignment",
            "current_custodian",
            "revision",
            "created_at",
            "created_by",
            "rectifiable_movement_id",
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
