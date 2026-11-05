from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("inventory", "0004_acquisition_expansion"),
        ("inventory", "0005_asset_transition_evidence"),
        ("inventory", "0005_license_lot_audit_immutable"),
    ]

    operations = []
