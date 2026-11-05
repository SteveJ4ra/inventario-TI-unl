from rest_framework import serializers
from .models import (
    Asset, AssetTransition, Assignment, Category, Condition, Custodian,
    Incident, MaintenanceEvent, Movement, RecoveryEvent,
)
from .models import Faculty, AcquisitionLine, AcquisitionDocument
from .models import SoftwareLicenseLot, LicenseLotAudit


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
    faculty_id = serializers.IntegerField(read_only=True, allow_null=True)
    acquisition = serializers.SerializerMethodField()

    def get_acquisition(self, asset):
        from .acquisition_services import acquisition_snapshot
        return acquisition_snapshot(asset)

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
            "faculty_id",
            "acquisition",
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


class AcquisitionDateInput(StrictSerializer):
    acquired_on = serializers.DateField(required=False, allow_null=True, default=None)
    date_unknown_reason = serializers.CharField(max_length=2000, required=False, allow_blank=True, default="")

    def validate(self, attrs):
        if bool(attrs.get("acquired_on")) == bool(attrs.get("date_unknown_reason")):
            raise serializers.ValidationError({"acquired_on": ["Indica fecha o motivo de desconocimiento, exclusivamente."]})
        return attrs


class AcquisitionLineInput(AcquisitionDateInput):
    # Solo precisión/finito: signo y cero siguen pendientes de decisión funcional.
    item_value = serializers.DecimalField(max_digits=12, decimal_places=2)


class AcquisitionAssetInput(AssetInput, AcquisitionLineInput):
    faculty_id = serializers.IntegerField(min_value=1)
    acquisition_document_id = serializers.IntegerField(min_value=1)

    def validate(self, attrs):
        return AcquisitionDateInput.validate(self, attrs)


class AcquisitionAssociationInput(AcquisitionLineInput):
    expected_revision = serializers.IntegerField(min_value=0)
    reason = serializers.CharField(max_length=2000)


class ExistingPurchaseItemInput(AcquisitionAssociationInput):
    asset_id = serializers.IntegerField(min_value=1)


class ExistingDonationItemInput(AcquisitionDateInput):
    asset_id = serializers.IntegerField(min_value=1)
    expected_revision = serializers.IntegerField(min_value=0)
    reason = serializers.CharField(max_length=2000)
    estimated_value = serializers.DecimalField(max_digits=12, decimal_places=2, source="item_value")


class AcquisitionDocumentInput(StrictSerializer):
    items = ExistingPurchaseItemInput(many=True, required=False, default=list)
    source = serializers.ChoiceField(choices=["PURCHASE", "DONATION"])
    reference = serializers.CharField(max_length=160)
    document_date = serializers.DateField(required=False, allow_null=True)
    supplier = serializers.CharField(max_length=160, required=False, allow_blank=True, default="")
    invoice_total = serializers.DecimalField(max_digits=12, decimal_places=2, required=False, allow_null=True, default=None)
    support_type = serializers.CharField(max_length=160, required=False, allow_blank=True, default="")

    def get_fields(self):
        fields = super().get_fields()
        if isinstance(getattr(self, "initial_data", None), dict) and self.initial_data.get("source") == "DONATION":
            fields["items"] = ExistingDonationItemInput(many=True, required=False, default=list)
        return fields

    def validate(self, attrs):
        errors = {}
        ids = [item["asset_id"] for item in attrs["items"]]
        if len(ids) != len(set(ids)):
            errors["items"] = ["No se permite repetir un activo."]
        if attrs["source"] == "PURCHASE":
            for field in ["document_date", "supplier", "invoice_total"]:
                if attrs.get(field) in (None, ""):
                    errors[field] = ["Obligatorio para compra."]
            if "support_type" in self.initial_data:
                errors["support_type"] = ["No corresponde a una compra."]
        else:
            if not attrs.get("support_type"):
                errors["support_type"] = ["El tipo de respaldo es obligatorio."]
            for field in ["supplier", "invoice_total"]:
                if field in self.initial_data:
                    errors[field] = ["No corresponde a una donación."]
        if errors:
            raise serializers.ValidationError(errors)
        return attrs


class AssetEditInput(StrictSerializer):
    expected_revision = serializers.IntegerField(min_value=0)
    reason = serializers.CharField(max_length=2000)
    name = serializers.CharField(max_length=160, required=False)
    description = serializers.CharField(max_length=2000, required=False)
    category = serializers.ChoiceField(choices=Category.choices, required=False)
    brand = serializers.CharField(max_length=120, required=False)
    model = serializers.CharField(max_length=120, required=False)
    serial_number = serializers.CharField(max_length=160, required=False)
    item_value = serializers.DecimalField(max_digits=12, decimal_places=2, required=False)
    acquired_on = serializers.DateField(required=False, allow_null=True)
    date_unknown_reason = serializers.CharField(max_length=2000, required=False, allow_blank=True)

    def validate(self, attrs):
        if "acquired_on" in attrs or "date_unknown_reason" in attrs:
            AcquisitionDateInput.validate(self, attrs)
            attrs.setdefault("acquired_on", None)
            attrs.setdefault("date_unknown_reason", "")
        return attrs


class FacultyInput(StrictSerializer):
    name = serializers.CharField(max_length=160)
    active = serializers.BooleanField(required=False, default=True)


class FacultyOutput(serializers.ModelSerializer):
    class Meta:
        model = Faculty
        fields = ["id", "name", "active"]


class AcquisitionLineOutput(serializers.ModelSerializer):
    asset_revision = serializers.IntegerField(source="asset.revision", read_only=True)
    asset_code = serializers.CharField(source="asset.code", read_only=True)

    class Meta:
        model = AcquisitionLine
        fields = ["asset_id", "asset_code", "asset_revision", "item_value", "acquired_on", "date_unknown_reason"]


class AcquisitionDocumentOutput(serializers.ModelSerializer):
    items = AcquisitionLineOutput(many=True, read_only=True)
    created_by = serializers.SerializerMethodField()

    class Meta:
        model = AcquisitionDocument
        fields = ["id", "source", "reference", "document_date", "supplier", "invoice_total",
                  "support_type", "currency", "created_by", "created_at", "items"]

    def get_created_by(self, document):
        return {"id": document.created_by_id, "username": document.created_by.username}


class FacultyChangeInput(StrictSerializer):
    faculty_id = serializers.IntegerField(min_value=1)
    expected_revision = serializers.IntegerField(min_value=0)
    reason = serializers.CharField(max_length=2000)


class CustodianProfileInput(StrictSerializer):
    # Snapshot exacto: no normalizar silenciosamente el dato consultado.
    full_name = serializers.CharField(max_length=160, allow_blank=True, trim_whitespace=False)
    email = serializers.CharField(max_length=254, allow_blank=True, trim_whitespace=False)
    department = serializers.CharField(max_length=160, allow_blank=True, trim_whitespace=False)


class CustodianEditInput(StrictSerializer):
    expected_profile = CustodianProfileInput()
    reason = serializers.CharField(max_length=2000)
    full_name = serializers.CharField(max_length=160, required=False)
    email = serializers.EmailField(max_length=254, required=False)
    department = serializers.CharField(max_length=160, allow_blank=True, required=False)


class DocumentSnapshotInput(StrictSerializer):
    source = serializers.ChoiceField(choices=["PURCHASE", "DONATION"])
    reference = serializers.CharField(max_length=160, trim_whitespace=False)
    document_date = serializers.DateField(allow_null=True)
    supplier = serializers.CharField(max_length=160, allow_blank=True, trim_whitespace=False)
    invoice_total = serializers.DecimalField(max_digits=12, decimal_places=2, allow_null=True)
    support_type = serializers.CharField(max_length=160, allow_blank=True, trim_whitespace=False)
    currency = serializers.CharField(max_length=3, trim_whitespace=False)


class DocumentEditInput(StrictSerializer):
    reason = serializers.CharField(max_length=2000)
    expected_document = DocumentSnapshotInput()
    expected_revisions = serializers.DictField(child=serializers.IntegerField(min_value=0))
    reference = serializers.CharField(max_length=160, required=False)
    document_date = serializers.DateField(allow_null=True, required=False)
    supplier = serializers.CharField(max_length=160, required=False)
    invoice_total = serializers.DecimalField(max_digits=12, decimal_places=2, required=False)
    support_type = serializers.CharField(max_length=160, required=False)

    def validate_expected_revisions(self, value):
        if any(not key.isascii() or not key.isdigit() or int(key) < 1 or str(int(key)) != key for key in value):
            raise serializers.ValidationError("Las claves deben ser ids positivos de activos.")
        return value
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
