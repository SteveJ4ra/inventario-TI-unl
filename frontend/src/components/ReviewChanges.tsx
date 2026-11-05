import { useState } from "react";
import { FieldError, Form } from "./Form";
import type { Body } from "../types";
const labels: Record<string, string> = { reference: "Referencia", document_date: "Fecha documental", supplier: "Proveedor", invoice_total: "Total compartido", support_type: "Tipo de respaldo", name: "Nombre", description: "Descripción", category: "Categoría",
  brand: "Marca", model: "Modelo", serial_number: "Número de serie", item_value: "Valor individual",
  acquired_on: "Fecha de adquisición", date_unknown_reason: "Motivo de fecha desconocida", reason: "Motivo",
  full_name: "Nombre del custodio", email: "Correo", department: "Dependencia", active: "Facultad activa" };
export function ReviewChanges({ before, after, onConfirm, onCancel }: {
  before: Body; after: Body; onConfirm: () => Promise<unknown>; onCancel: () => void;
}) {
  const [busy, setBusy] = useState(false);
  return <section aria-label="Confirmación de cambios">
    <h4>Revisa antes de confirmar</h4>
    <Form submit="Confirmar cambios" onSubmit={async () => { setBusy(true); try { await onConfirm(); } finally { setBusy(false); } }}>
      <dl>{Object.entries(after).filter(([key]) => !["expected_revision", "expected_profile", "expected_document", "expected_revisions"].includes(key)).map(([key, value]) =>
        <div key={key}><dt>{labels[key] || key}</dt><dd>{String(before[key] ?? "—")} → {String(value ?? "—")}<FieldError name={key} /></dd></div>)}</dl>
      <p>Se conservará la información histórica.</p>
    </Form>
    <button type="button" disabled={busy} onClick={onCancel}>Volver a editar</button>
  </section>;
}
