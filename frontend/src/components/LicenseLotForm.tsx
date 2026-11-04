import { useState } from "react";
import type { Body, LicenseLot, LicenseStatus } from "../types";
import { Form } from "./Form";

export const licenseModels = { USER_SEAT: "Por usuario", DEVICE_SEAT: "Por dispositivo" };
export const licenseStatuses = { NOT_STARTED: "Por iniciar", CURRENT: "Vigente", EXPIRED: "Vencido" };
export const licenseFields = {
  product_name: "Producto", vendor: "Proveedor", license_model: "Modalidad",
  purchased_quantity: "Compradas", in_use_quantity: "En uso",
  starts_on: "Inicio de vigencia", ends_on: "Fin de vigencia",
};
export const isAborted = (error: unknown) => error instanceof DOMException && error.name === "AbortError";

export function LicenseStatusBadge({ status }: { status: LicenseStatus }) {
  return <span className={`tag ${status}`}>{licenseStatuses[status]}</span>;
}

export function LicensePagination({ page, number, onPage, label }: {
  page: { next: string | null; previous: string | null };
  number: number; onPage: (value: number) => void; label: string;
}) {
  return <nav className="pagination" aria-label={label}>
    <button disabled={!page.previous} onClick={() => onPage(number - 1)}>Anterior</button>
    <span>Página {number}</span>
    <button disabled={!page.next} onClick={() => onPage(number + 1)}>Siguiente</button>
  </nav>;
}

export function LicenseLotForm({ lot, onSubmit }: {
  lot?: LicenseLot; onSubmit: (body: Body) => Promise<unknown>;
}) {
  const [purchased, setPurchased] = useState(String(lot?.purchased_quantity ?? ""));
  const [used, setUsed] = useState(String(lot?.in_use_quantity ?? ""));
  const remaining = purchased !== "" && used !== "" ? Number(purchased) - Number(used) : null;
  return <Form submit={lot ? "Guardar cambios" : "Registrar lote"} onSubmit={async (data) => {
    const quantity = Number(data.purchased_quantity);
    const inUse = Number(data.in_use_quantity);
    if (!Number.isInteger(quantity) || !Number.isInteger(inUse) || quantity < 0 || inUse < 0 || inUse > quantity)
      throw new Error("Las cantidades deben ser enteros no negativos; el uso no puede superar la compra.");
    if (data.ends_on && data.ends_on < data.starts_on)
      throw new Error("La fecha de fin no puede ser anterior a la de inicio.");
    await onSubmit({
      product_name: data.product_name, vendor: data.vendor, license_model: data.license_model,
      purchased_quantity: quantity, in_use_quantity: inUse,
      starts_on: data.starts_on, ends_on: data.ends_on || null,
      ...(lot ? { expected_revision: lot.revision } : {}),
    });
  }}>
    <div className="form-grid">
      <label>Producto<input name="product_name" required maxLength={160} defaultValue={lot?.product_name} /></label>
      <label>Proveedor<input name="vendor" required maxLength={160} defaultValue={lot?.vendor} /></label>
      <label>Modalidad<select name="license_model" required defaultValue={lot?.license_model ?? ""}>
        <option value="" disabled>Selecciona una modalidad</option>
        {Object.entries(licenseModels).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
      </select></label>
      <label>Cantidad comprada<input name="purchased_quantity" type="number" min={0} max={2147483647} step={1} required value={purchased} onChange={e => setPurchased(e.target.value)} /></label>
      <label>Cantidad en uso<input name="in_use_quantity" type="number" min={0} max={2147483647} step={1} required value={used} onChange={e => setUsed(e.target.value)} /></label>
      <label>Inicio de vigencia<input name="starts_on" type="date" required defaultValue={lot?.starts_on} /></label>
      <label>Fin de vigencia · opcional<input name="ends_on" type="date" defaultValue={lot?.ends_on ?? ""} /></label>
      <p className="wide" aria-live="polite">Remanentes calculados: <strong>{remaining ?? "Completa las cantidades"}</strong></p>
    </div>
  </Form>;
}

