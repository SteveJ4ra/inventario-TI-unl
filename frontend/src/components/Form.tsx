import { useState, type ReactNode } from "react";
import type { Fields } from "../types";
import { ApiError } from "../api";
const names: Record<string, string> = {
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
}: {
  children: ReactNode;
  onSubmit: (data: Fields) => Promise<unknown>;
  submit: string;
}) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<unknown>(null);
  return (
    <form
      onSubmit={async (e) => {
        e.preventDefault();
        if (busy) return;
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
          setBusy(false);
        }
      }}
    >
      <fieldset disabled={busy}>{children}</fieldset>
      {error != null && <ErrorNotice error={error} />}
      <button className="primary" disabled={busy}>
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
}: {
  label: string;
  name: string;
  maxLength?: number;
  optional?: boolean;
  type?: string;
}) {
  return (
    <label>
      {label}
      {optional && <small> · opcional</small>}
      <input
        name={name}
        type={type}
        required={!optional}
        maxLength={maxLength}
      />
    </label>
  );
}
