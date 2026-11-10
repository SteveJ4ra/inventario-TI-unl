import { useState } from "react";
import { request } from "../api";
import type { AcquisitionDocument, Body, DocumentSnapshot } from "../types";
import { Field, Form } from "./Form";
import { ReviewChanges } from "./ReviewChanges";
export function DocumentEditForm({ document, onSaved, onBusy }: {
  document: AcquisitionDocument; onSaved: (document: AcquisitionDocument) => void; onBusy?: (busy: boolean) => void;
}) {
  const [pending, setPending] = useState<Body | null>(null);
  const before: DocumentSnapshot = { source: document.source, reference: document.reference, document_date: document.document_date,
    supplier: document.supplier, invoice_total: document.invoice_total, support_type: document.support_type, currency: document.currency };
  const purchase = document.source === "PURCHASE";
  return <section aria-label="Edición documental">
    <p>Esta corrección afecta a {document.items.length} activos y aumentará sus revisiones. Sus movimientos anteriores se conservan.</p>
    <div hidden={pending !== null}><Form submit="Revisar cambios" onSubmit={async data => {
      const revisions: Record<string, number> = {};
      for (const item of document.items) {
        if (!Number.isSafeInteger(item.asset_revision) || item.asset_revision! < 0)
          throw new Error("Consulta nuevamente el documento para obtener las revisiones completas.");
        revisions[String(item.asset_id)] = item.asset_revision!;
      }
      const changes: Body = {};
      for (const field of purchase ? ["reference", "document_date", "supplier", "invoice_total"] as const
          : ["reference", "support_type"] as const)
        if (data[field] !== before[field]) changes[field] = data[field];
      if (!Object.keys(changes).length) throw new Error("No hay cambios para guardar.");
      setPending({ ...changes, reason: data.reason, expected_document: { ...before }, expected_revisions: revisions });
    }}>
      <Field label="Referencia documental" name="reference" defaultValue={document.reference} />
      {purchase ? <>
        <Field label="Fecha del documento" name="document_date" type="date" defaultValue={document.document_date || ""} />
        <Field label="Proveedor documental" name="supplier" defaultValue={document.supplier} />
        <Field label={"Total documental (" + document.currency + ")"} name="invoice_total" defaultValue={document.invoice_total || ""} />
      </> : <Field label="Tipo de respaldo documental" name="support_type" defaultValue={document.support_type} />}
      <Field label="Motivo de edición" name="reason" maxLength={2000} />
    </Form></div>
    {pending && <ReviewChanges before={{ ...before }} after={pending} onCancel={() => setPending(null)} onConfirm={async () => {
      onBusy?.(true);
      try {
        const updated = await request<AcquisitionDocument>("/acquisitions/" + document.id + "/", { body: pending, method: "PATCH" });
        if (updated.id !== document.id || updated.source !== document.source || !Array.isArray(updated.items))
          throw new Error("No se pudo confirmar el documento. Consúltalo antes de repetir.");
        onSaved(updated);
      } finally { onBusy?.(false); }
    }} />}
  </section>;
}
