"""Validaciones de dominio sin aplicar migraciones; integridad SQL pendiente T004."""
from unittest.mock import patch
from datetime import date
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.db import models
from django.test import SimpleTestCase, TestCase, override_settings
from inventory.models import (
    AcquisitionDocument, AcquisitionLine, AssetChange, Faculty, Asset,
    AssetFacultyChange, AcquisitionDocumentChange, CustodianChange, Custodian,
)


class AcquisitionModelTests(SimpleTestCase):
    def test_purchase_requires_invoice_fields_and_donation_requires_support(self):
        doc = AcquisitionDocument(source="PURCHASE", reference="TEST", supplier="Ficticio",
                                  document_date=date(2026, 1, 15), invoice_total=Decimal("1000.00"))
        doc.clean()
        doc.supplier = "  "
        with self.assertRaises(ValidationError):
            doc.clean()
        donation = AcquisitionDocument(source="DONATION", reference="TEST-ACTA", support_type="Acta")
        donation.clean()
        donation.invoice_total = Decimal("10.00")
        with self.assertRaises(ValidationError):
            donation.clean()

    def test_unknown_date_never_gets_a_sentinel_date(self):
        line = AcquisitionLine(item_value=Decimal("12.00"), date_unknown_reason="No consta")
        line.clean()
        self.assertIsNone(line.acquired_on)
        line.acquired_on = date(2026, 1, 15)
        with self.assertRaises(ValidationError):
            line.clean()
        line.date_unknown_reason = ""
        line.clean()
        line.acquired_on = None
        line.date_unknown_reason = "   "
        with self.assertRaises(ValidationError):
            line.clean()

    def test_currency_default_does_not_relabel_existing_documents(self):
        doc = AcquisitionDocument()
        self.assertEqual(doc.currency, "USD")
        with override_settings(ASSET_CURRENCY_CODE="EUR"):
            self.assertEqual(doc.currency, "USD")
            self.assertEqual(AcquisitionDocument().currency, "EUR")

    def test_audit_refuses_rewrite_and_delete_before_database_access(self):
        event = AssetChange()
        event._state.adding = False
        with self.assertRaises(ValidationError):
            event.save()
        with self.assertRaises(ValidationError):
            event.delete()

    def test_faculty_rejects_blank_name(self):
        with self.assertRaises(ValidationError):
            Faculty(name="   ").clean()


class AcquisitionConstraintPredicateTests(TestCase):
    """Evalúa los CHECK declarados con SELECT en PostgreSQL, sin crear tablas 003.

    No demuestra instalación de constraints ni rechazo de INSERT directo: T004.
    """

    def assert_checks_reject(self, instance):
        with self.assertRaises(ValidationError):
            for constraint in instance._meta.constraints:
                if isinstance(constraint, models.CheckConstraint):
                    constraint.validate(type(instance), instance)

    def test_whitespace_only_required_text_is_rejected_by_sql_predicate(self):
        for text in ["", "   ", "\t\r\n"]:
            with self.subTest(text=repr(text)):
                self.assert_checks_reject(Faculty(name=text))
                self.assert_checks_reject(AcquisitionDocument(
                    source="PURCHASE", reference=text, supplier="Proveedor ficticio",
                    document_date=date(2026, 1, 15), invoice_total=Decimal("10.00")))
                self.assert_checks_reject(AcquisitionDocument(
                    source="PURCHASE", reference="TEST", supplier=text,
                    document_date=date(2026, 1, 15), invoice_total=Decimal("10.00")))
                self.assert_checks_reject(AcquisitionDocument(
                    source="DONATION", reference="TEST", support_type=text))
                self.assert_checks_reject(AcquisitionLine(date_unknown_reason=text))
                for audit in [AssetChange, AssetFacultyChange, AcquisitionDocumentChange]:
                    self.assert_checks_reject(audit(reason=text, resulting_revision=1)
                                             if audit is not AcquisitionDocumentChange
                                             else audit(reason=text))

    def test_base_002_required_text_checks_reject_whitespace_without_rewriting_data(self):
        cases = [(Asset, field, f"asset_{field}_required") for field in
                 ["code", "name", "description", "brand", "model", "serial_number", "location"]]
        cases += [(Custodian, "full_name", "custodian_name_required"),
                  (Custodian, "email", "custodian_email_required")]
        for model, field, name in cases:
            constraint = next(c for c in model._meta.constraints if c.name == name)
            for text in ["", "   ", "\t\r\n"]:
                with self.subTest(model=model.__name__, field=field, text=repr(text)):
                    with self.assertRaises(ValidationError):
                        constraint.validate(model, model(**{field: text}))
            constraint.validate(model, model(**{field: "Texto válido"}))

    def test_valid_text_and_date_alternatives_pass_the_sql_predicates(self):
        instances = [
            Faculty(name="Facultad ficticia"),
            AcquisitionDocument(source="PURCHASE", reference="TEST", supplier="Proveedor",
                                document_date=date(2026, 1, 15), invoice_total=Decimal("10.00")),
            AcquisitionDocument(source="DONATION", reference="TEST", support_type="Acta"),
            AcquisitionLine(acquired_on=date(2026, 1, 15)),
            AcquisitionLine(date_unknown_reason="No consta en respaldo ficticio"),
            AssetChange(reason="Corrección", resulting_revision=1),
            AssetFacultyChange(reason="Corrección", resulting_revision=1),
            AcquisitionDocumentChange(reason="Corrección"),
        ]
        for instance in instances:
            with self.subTest(model=type(instance).__name__):
                for constraint in instance._meta.constraints:
                    if isinstance(constraint, models.CheckConstraint):
                        constraint.validate(type(instance), instance)

    def test_zero_resulting_revision_is_not_a_mutation(self):
        for audit in [AssetChange, AssetFacultyChange]:
            with self.subTest(audit=audit.__name__):
                self.assert_checks_reject(audit(reason="Corrección", resulting_revision=0))


class ConservationGuardTests(SimpleTestCase):
    def test_queryset_rewrite_and_bulk_update_of_audit_are_rejected(self):
        for audit in [AssetChange, AssetFacultyChange, CustodianChange, AcquisitionDocumentChange]:
            with self.subTest(audit=audit.__name__):
                with self.assertRaises(ValidationError):
                    audit.objects.filter(pk=1).update(before_json={})
                with self.assertRaises(ValidationError):
                    audit.objects.bulk_update([audit(pk=1)], ["before_json"])

    def test_model_and_queryset_delete_cannot_remove_domain_or_audit(self):
        for model in [Asset, AcquisitionDocument, AcquisitionLine, AssetChange,
                      AssetFacultyChange, CustodianChange, AcquisitionDocumentChange]:
            with self.subTest(model=model.__name__):
                with self.assertRaises(ValidationError):
                    model(pk=1).delete()
                with self.assertRaises(ValidationError):
                    model.objects.filter(pk=1).delete()

    def test_new_audit_with_explicit_pk_uses_insert_instead_of_overwriting(self):
        event = AssetChange(pk=123, reason="Corrección", resulting_revision=1)
        with patch.object(models.Model, "save") as save:
            event.save()
            self.assertTrue(save.call_args.kwargs["force_insert"])
        with self.assertRaises(ValidationError):
            event.save(force_update=True)

    def test_bulk_upsert_cannot_overwrite_audit(self):
        with self.assertRaises(ValidationError):
            AssetChange.objects.bulk_create([AssetChange(pk=1)], update_conflicts=True,
                                            update_fields=["reason"], unique_fields=["id"])
