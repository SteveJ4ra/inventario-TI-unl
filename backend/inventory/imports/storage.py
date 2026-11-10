from django.db import transaction

from inventory.models import ImportBatch, ImportBatchRow


def create_batch(*, actor, preview, expires_at):
    state = (
        ImportBatch.State.INVALID
        if preview.errors
        else ImportBatch.State.PREVIEW_READY
    )
    with transaction.atomic():
        batch = ImportBatch.objects.create(
            kind=preview.kind,
            schema_version=preview.schema_version,
            state=state,
            content_hash=preview.content_hash,
            preview_summary=preview.summary,
            preview_errors=[error.as_dict() for error in preview.errors],
            rows_count=len(preview.rows),
            actor=actor,
            expires_at=expires_at,
        )
        ImportBatchRow.objects.bulk_create(
            [
                ImportBatchRow(
                    batch=batch,
                    row_number=row["row_number"],
                    normalized=row,
                )
                for row in preview.rows
            ]
        )
    return batch


def rows_for(batch):
    return [
        item.normalized for item in batch.rows.order_by("row_number")
    ]


def clear_rows(batch):
    ImportBatchRow.objects.filter(batch=batch).delete()
