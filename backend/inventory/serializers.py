from rest_framework import serializers
from .models import (
    Asset,
    Assignment,
    Category,
    Condition,
    Custodian,
    Movement,
    SoftwareLicenseLot,
    LicenseLotAudit,
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


class JsonIntegerField(serializers.IntegerField):
    """No convierte booleanos, decimales o cadenas en cantidades JSON."""

    def to_internal_value(self, data):
        if type(data) is not int:
            self.fail("invalid")
        return super().to_internal_value(data)


class LicenseLotInput(StrictSerializer):
    product_name = serializers.CharField(max_length=160)
    vendor = serializers.CharField(max_length=160)
    license_model = serializers.ChoiceField(choices=["USER_SEAT", "DEVICE_SEAT"])
    purchased_quantity = JsonIntegerField(min_value=0, max_value=2147483647)
    in_use_quantity = JsonIntegerField(min_value=0, max_value=2147483647)
    starts_on = serializers.DateField()
    ends_on = serializers.DateField(required=False, allow_null=True)

    def to_internal_value(self, data):
        if not isinstance(data, dict):
            raise serializers.ValidationError(
                {"non_field_errors": ["Se requiere un objeto JSON."]}
            )
        try:
            for key in data:
                if not isinstance(key, str):
                    raise ValueError("Nombre de campo inválido")
                key.encode("utf-8")
        except (UnicodeEncodeError, ValueError):
            raise serializers.ValidationError(
                {
                    "non_field_errors": [
                        "Los nombres de campos deben ser texto UTF-8 válido."
                    ]
                }
            )
        return super().to_internal_value(data)

    def validate(self, attrs):
        merged = (
            {name: getattr(self.instance, name) for name in LicenseLotInput().fields}
            if self.instance is not None
            else {}
        )
        merged.update(attrs)
        if merged["in_use_quantity"] > merged["purchased_quantity"]:
            raise serializers.ValidationError(
                {
                    "in_use_quantity": [
                        "La cantidad en uso no puede superar la comprada."
                    ]
                }
            )
        if (
            merged.get("ends_on") is not None
            and merged["ends_on"] < merged["starts_on"]
        ):
            raise serializers.ValidationError(
                {"ends_on": ["La fecha de fin no puede ser anterior a la de inicio."]}
            )
        return attrs


class LicenseLotPatchInput(LicenseLotInput):
    expected_revision = JsonIntegerField(min_value=0, max_value=9223372036854775806)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in LicenseLotInput().fields:
            self.fields[name].required = False

    def validate(self, attrs):
        if set(attrs) <= {"expected_revision"}:
            raise serializers.ValidationError(
                "Indica al menos un campo del lote para editar."
            )
        return super().validate(attrs)


class LicenseLotQuery(StrictSerializer):
    page = serializers.IntegerField(min_value=1, max_value=2147483647, default=1)
    search = serializers.CharField(max_length=240, required=False, allow_blank=True)
    license_model = serializers.ChoiceField(
        choices=["USER_SEAT", "DEVICE_SEAT"], required=False
    )
    temporal_status = serializers.ChoiceField(
        choices=["NOT_STARTED", "CURRENT", "EXPIRED"], required=False
    )


class LicenseHistoryQuery(StrictSerializer):
    page = serializers.IntegerField(min_value=1, max_value=2147483647, default=1)


class LicenseLotOutput(serializers.ModelSerializer):
    created_by = serializers.SerializerMethodField()
    remaining_quantity = serializers.IntegerField(read_only=True)
    temporal_status = serializers.SerializerMethodField()

    class Meta:
        model = SoftwareLicenseLot
        fields = [
            "id",
            "product_name",
            "vendor",
            "license_model",
            "purchased_quantity",
            "in_use_quantity",
            "remaining_quantity",
            "starts_on",
            "ends_on",
            "temporal_status",
            "revision",
            "created_at",
            "created_by",
        ]

    def get_created_by(self, lot):
        return {"id": lot.created_by_id, "username": lot.created_by.username}

    def get_temporal_status(self, lot):
        return lot.status_on(self.context.get("today"))


class LicenseLotAuditOutput(serializers.ModelSerializer):
    actor = serializers.SerializerMethodField()

    class Meta:
        model = LicenseLotAudit
        fields = [
            "id",
            "lot_id",
            "actor",
            "timestamp",
            "before_json",
            "after_json",
            "resulting_revision",
        ]

    def get_actor(self, event):
        return {
            "id": event.actor_id,
            "username": event.actor.username,
            "recorded_label": event.actor_label,
        }
