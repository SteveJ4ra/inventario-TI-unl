from rest_framework import serializers

from inventory.models import ImportBatch


class ImportBatchOutput(serializers.ModelSerializer):
    batch_id = serializers.UUIDField(source="id", read_only=True)
    summary = serializers.JSONField(source="preview_summary")
    errors = serializers.JSONField(source="preview_errors")
    owner = serializers.SerializerMethodField()

    class Meta:
        model = ImportBatch
        fields = [
            "batch_id",
            "kind",
            "schema_version",
            "state",
            "content_hash",
            "summary",
            "errors",
            "rows_count",
            "owner",
            "created_at",
            "confirmed_at",
            "applied_at",
            "expires_at",
            "applied_result",
        ]

    def get_owner(self, batch):
        return {"id": batch.actor_id, "username": batch.actor.username}
