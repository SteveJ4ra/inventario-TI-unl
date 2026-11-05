import { DocumentEditForm } from "./DocumentEditForm";
import { ExistingPurchaseItems } from "./ExistingPurchaseItems";
import { useEffect, useState, type Dispatch, type SetStateAction } from "react";
import { purchases, donations } from "../api";
import type { AcquisitionDocument, PurchasedAsset, Faculty, Options, PurchaseAssetInput, PurchaseExistingItem } from "../types";
import { ErrorNotice, Field, FieldError, Form } from "./Form";
import { AssetForm } from "./Registration";

export function AcquisitionForm({ options, document, onDocument, onCreated, onSelect, onDocumentChanged, source = "PURCHASE" }: {
  source?: "PURCHASE" | "DONATION";
  options: Options;
  document: AcquisitionDocument | null;
  onDocument: Dispatch<SetStateAction<AcquisitionDocument | null>>;
  onCreated: (asset: PurchasedAsset) => void;
  onSelect?: (id: number) => void;
  onDocumentChanged?: () => void;
}) {
  const donation = source === "DONATION";
  const noun = donation ? "respaldo" : "factura";
  const title = donation ? "Respaldo" : "Factura";
  const [editingDocument, setEditingDocument] = useState(false);
  const [items, setItems] = useState<(PurchaseExistingItem & { code: string })[]>([]);
  const [mode, setMode] = useState<"new" | "existing">("new");
  const [faculties, setFaculties] = useState<Faculty[] | null>(null);
  const [error, setError] = useState<unknown>(null);
  const [catalogError, setCatalogError] = useState<unknown>(null);
  const [busy, setBusy] = useState(false);
  const [reload, setReload] = useState(0);
  const [formKey, setFormKey] = useState(0);
  useEffect(() => {
    const controller = new AbortController();
    setCatalogError(null);
    purchases.faculties(controller.signal).then(setFaculties).catch(error => {
      if (!controller.signal.aborted) setCatalogError(error);
    });
    return () => controller.abort();
  }, [reload]);

  function selectInvoice(value: AcquisitionDocument) {
    if (value.source !== source) throw new Error(donation
      ? "El documento seleccionado no es un respaldo de donación."
      : "El documento seleccionado no es una factura de compra.");
    setError(null);
    onDocument(value);
    setEditingDocument(false);
    setItems([]);
  }

  return <div className="purchase-flow">
    <p className="hint">{donation ? "Donación: guarda primero el respaldo textual y registra después cada activo con su valor estimado individual. No se adjuntan imágenes."
      : "Compra: guarda primero la factura y registra después cada activo con su valor individual. No se adjuntan imágenes."}</p>
    {error != null && <ErrorNotice error={error} />}
    {catalogError != null && <><ErrorNotice error={catalogError} /><button type="button" disabled={busy} onClick={() => setReload(n => n + 1)}>Reintentar consulta de facultades</button></>}
    {!document ? <>
      <div className="heading-actions">
        <button type="button" disabled={busy} aria-pressed={mode === "new"} onClick={() => setMode("new")}>{"Crear " + noun}</button>
        <button type="button" disabled={busy} aria-pressed={mode === "existing"} onClick={() => setMode("existing")}>{"Usar " + noun + " existente"}</button>
      </div>
      {mode === "new" ? <><ExistingPurchaseItems donation={donation} items={items} onChange={setItems} disabled={busy} /><Form submit={"Guardar " + noun} disabled={busy} onSubmit={async data => {
        setBusy(true);
        try { selectInvoice(donation ? await donations.createSupport({
          reference: data.reference, support_type: data.support_type,
          ...(items.length ? { items: items.map(({ code: _code, item_value, ...item }) => ({ ...item, estimated_value: item_value })) } : {}),
        }) : await purchases.createInvoice({ reference: data.reference, document_date: data.document_date,
          supplier: data.supplier, invoice_total: data.invoice_total,
          ...(items.length ? { items: items.map(({ code: _code, ...item }) => item) } : {}) })); }
        finally { setBusy(false); }
      }}>
        <div className="form-grid">
          <Field label={donation ? "Referencia del respaldo" : "Referencia de factura"} name="reference" />
          {donation ? <Field label="Tipo de respaldo" name="support_type" /> : <>
          <Field label="Fecha de factura" name="document_date" type="date" />
          <Field label="Proveedor" name="supplier" />
          <Field label="Total de factura (USD)" name="invoice_total" /></>}
        </div>
        <FieldError name="items" />
        {items.map((item, index) => <div key={item.asset_id} aria-label={"Errores de asociación " + item.code}>
          <strong>{item.code}</strong>
          {["asset_id", "expected_revision", "reason", "item_value", "estimated_value", "acquired_on", "date_unknown_reason", "non_field_errors"].map(field => <FieldError key={field} name={"items." + index + "." + field} />)}
        </div>)}
        <p className="hint">{donation ? "El respaldo se comparte. Cada activo conserva su valor estimado y su fecha o motivo de desconocimiento."
          : "El total se guarda una vez para la factura compartida. La fecha de adquisición se confirma por activo."}</p>
      </Form></> : <Form submit={"Cargar " + noun} disabled={busy} onSubmit={async data => {
        const id = Number(data.document_id);
        if (!Number.isSafeInteger(id) || id < 1) throw new Error("Indica un identificador de documento válido.");
        setBusy(true);
        try { selectInvoice(await purchases.invoice(id)); }
        finally { setBusy(false); }
      }}>
        <Field label="Identificador del documento" name="document_id" />
        <p className="hint">Usa el identificador mostrado al guardar el documento para seguir vinculando activos.</p>
      </Form>}
    </> : <>
      <section className="invoice-summary" aria-label={title + " seleccionado"}>
        <h3>{title} {document.reference}</h3>
        <p>Documento #{document.id} · {donation ? document.support_type : document.supplier + " · " + document.document_date}</p>
        {!donation && <p><strong>Total compartido: {document.currency} {document.invoice_total}</strong></p>}
        <div className="heading-actions">
          <button type="button" disabled={busy} onClick={() => { setError(null); setEditingDocument(false); onDocument(null); }}>{"Cambiar " + noun}</button>
          <button type="button" disabled={busy} onClick={async () => {
            setBusy(true); setError(null);
            try { selectInvoice(await purchases.invoice(document.id)); }
            catch (error) { setError(error); }
            finally { setBusy(false); }
          }}>{"Consultar " + noun}</button>
        </div>
        <button type="button" disabled={busy} onClick={async () => {
          setBusy(true); setError(null);
          try { selectInvoice(await purchases.invoice(document.id)); setEditingDocument(true); }
          catch (error) { setError(error); }
          finally { setBusy(false); }
        }}>Editar documento compartido</button>
        {editingDocument && <DocumentEditForm key={document.id} document={document} onBusy={setBusy} onSaved={updated => {
          onDocument(updated); setEditingDocument(false); onDocumentChanged?.();
        }} />}
        {document.items.length > 0 && <>
          <h4>Activos vinculados</h4>
          <ul>{document.items.map(item => <li key={item.asset_id}>
            {onSelect ? <button type="button" disabled={busy} onClick={() => onSelect(item.asset_id)}>{item.asset_code || "Activo #" + item.asset_id}</button>
              : <strong>{item.asset_code || "Activo #" + item.asset_id}</strong>}
            {(donation ? " · Valor estimado individual: " : " · Valor individual: ") + document.currency + " " + item.item_value}
          </li>)}</ul>
        </>}
      </section>
      <h3>{donation ? "Registrar un activo en este respaldo" : "Registrar un activo en esta factura"}</h3>
      {faculties === null ? <p role="status">{catalogError ? "No fue posible consultar las facultades." : "Cargando facultades…"}</p>
        : !faculties.length ? <p>No hay facultades activas. Solicita al Operador que las registre.</p>
        : <AssetForm key={formKey} options={options} purchase={{ faculties, currency: document.currency, estimated: donation }} disabled={busy} onSubmit={async data => {
          const payload: PurchaseAssetInput = {
            name: data.name, description: data.description, category: data.category, brand: data.brand,
            model: data.model, serial_number: data.serial_number, location: data.location, condition: data.condition,
            faculty_id: Number(data.faculty_id), acquisition_document_id: document.id, item_value: data.item_value,
            ...(data.acquired_on ? { acquired_on: data.acquired_on } : { date_unknown_reason: data.date_unknown_reason }),
          };
          setBusy(true);
          try {
            const created = await purchases.register(payload);
            onDocument(current => current?.id === document.id ? { ...current, items: [...current.items, {
              asset_id: created.id, asset_code: created.code, asset_revision: created.revision, item_value: created.acquisition.item_value,
              acquired_on: created.acquisition.acquired_on, date_unknown_reason: created.acquisition.date_unknown_reason,
            }] } : current);
            setFormKey(key => key + 1);
            onCreated(created);
          } finally { setBusy(false); }
        }} />}
    </>}
  </div>;
}
