import { createContext, useContext, useId, useRef, useState, type ReactNode } from "react";
import type { Fields } from "../types";
import { ApiError } from "../api";
const FieldErrors = createContext<Record<string, string[]> | undefined>(undefined);
const names: Record<string, string> = {
  support_type: "Tipo de respaldo", estimated_value: "Valor estimado",
  reference: "Referencia del documento", document_date: "Fecha de factura", supplier: "Proveedor",
  invoice_total: "Total de factura", faculty_id: "Facultad responsable", acquisition_document_id: "Documento de adquisición",
  item_value: "Valor individual", acquired_on: "Fecha de adquisición", date_unknown_reason: "Motivo de fecha desconocida",
  name: "Nombre",
  description: "Descripción",
  category: "Categoría",
  brand: "Marca",
  model: "Modelo",
  serial_number: "Número de serie",
  location: "Ubicación",
  condition: "Condición",
  full_name: "Nombre completo",
  email: "Correo",
  department: "Dependencia",
  destination: "Destino",
  reception_location: "Lugar de recepción",
  reason: "Motivo",
  resolution_note: "Nota de resolución",
  workshop_location: "Ubicación del taller",
  receiving_location: "Ubicación de recepción",
  location_confirmed: "Confirmación de ubicación",
  result: "Resultado",
  inspected_condition: "Condición tras la inspección",
  recovered_location: "Ubicación de recuperación",
  inspection_confirmed: "Confirmación de inspección",
  custodian_id: "Custodio",
};
export function ErrorNotice({ error }: { error: unknown }) {
  return (
    <div role="alert" className="error">
      <strong>
        {error instanceof Error
          ? error.message
          : "No se pudo completar la operación."}
      </strong>
      {error instanceof ApiError && error.fields && (
        <ul>
          {Object.entries(error.fields).map(([key, values]) => (
            <li key={key}>
              {names[key] || key}:{" "}
              {Array.isArray(values) ? values.join(" ") : String(values)}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
export function Form({
  children,
  onSubmit,
  submit,
  disabled = false,
}: {
  children: ReactNode;
  onSubmit: (data: Fields) => Promise<unknown>;
  submit: string;
  disabled?: boolean;
}) {
  const [busy, setBusy] = useState(false);
  const lock = useRef(false);
  const [error, setError] = useState<unknown>(null);
  return (
    <form
      onSubmit={async (e) => {
        e.preventDefault();
        if (disabled || lock.current) return;
        lock.current = true;
        const data: Fields = {};
        new FormData(e.currentTarget).forEach(
          (v, k) => (data[k] = k === "password" ? String(v) : String(v).trim()),
        );
        setBusy(true);
        setError(null);
        try {
          await onSubmit(data);
        } catch (e) {
          setError(e);
        } finally {
          lock.current = false;
          setBusy(false);
        }
      }}
    >
      <FieldErrors.Provider value={error instanceof ApiError ? error.fields : undefined}>
        <fieldset disabled={busy || disabled}>{children}</fieldset>
      </FieldErrors.Provider>
      {error != null && <ErrorNotice error={error} />}
      <button className="primary" disabled={busy || disabled}>
        {busy ? "Guardando…" : submit}
      </button>
    </form>
  );
}
export function Field({
  label,
  name,
  maxLength = 160,
  optional = false,
  type = "text",
  defaultValue,
}: {
  label: string;
  name: string;
  maxLength?: number;
  optional?: boolean;
  type?: string;
  defaultValue?: string;
}) {
  const errors = useContext(FieldErrors)?.[name];
  const errorId = useId();
  return (
    <label>
      {label}
      {optional && <small> · opcional</small>}
      <input
        name={name}
        defaultValue={defaultValue}
        aria-label={label}
        aria-invalid={Boolean(errors?.length)}
        aria-describedby={errors?.length ? errorId : undefined}
        type={type}
        required={!optional}
        maxLength={maxLength}
      />
      <FieldError name={name} id={errorId} />
    </label>
  );
}

export function FieldError({ name, id }: { name: string; id?: string }) {
  const errors = useContext(FieldErrors)?.[name];
  return errors?.length ? <small className="field-error" id={id}>{errors.join(" ")}</small> : null;
}
