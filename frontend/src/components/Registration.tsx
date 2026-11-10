import { useState } from "react";
import type { Fields, Options, Faculty } from "../types";
import { Field, FieldError, Form } from "./Form";
export function AssetForm({
  options,
  onSubmit,
  purchase,
  disabled = false,
}: {
  options: Options;
  purchase?: { faculties: Faculty[]; currency?: string; estimated?: boolean };
  disabled?: boolean;
  onSubmit: (data: Fields) => Promise<unknown>;
}) {
  const [unknownDate, setUnknownDate] = useState(false);
  return (
    <Form onSubmit={onSubmit} submit="Registrar activo" disabled={disabled}>
      <div className="form-grid">
        <Field label="Nombre" name="name" />
        <label className="wide">
          Descripción
          <textarea name="description" required maxLength={2000} />
          <FieldError name="description" />
        </label>
        <label>
          Categoría
          <select name="category" required defaultValue="">
            <option value="" disabled>
              Selecciona una categoría
            </option>
            {options.categories.map((c) => (
              <option key={c.value} value={c.value}>
                {c.label}
              </option>
            ))}
          </select>
          <FieldError name="category" />
        </label>
        <label>
          Condición
          <select name="condition" required defaultValue="">
            <option value="" disabled>
              Selecciona la condición
            </option>
            {options.conditions.map((c) => (
              <option key={c.value} value={c.value}>
                {c.label}
              </option>
            ))}
          </select>
          <FieldError name="condition" />
        </label>
        <Field label="Marca" name="brand" maxLength={120} />
        <Field label="Modelo" name="model" maxLength={120} />
        <Field label="Número de serie" name="serial_number" />
        <Field label="Ubicación" name="location" maxLength={240} />
        {purchase && <>
          <label>Facultad responsable
            <select name="faculty_id" aria-label="Facultad responsable" required defaultValue="">
              <option value="" disabled>Selecciona una facultad</option>
              {purchase.faculties.map(faculty => <option key={faculty.id} value={faculty.id}>{faculty.name}</option>)}
            </select>
            <FieldError name="faculty_id" />
          </label>
          <Field label={(purchase.estimated ? "Valor estimado individual (" : "Valor individual (") + (purchase.currency || "USD") + ")"} name="item_value" />
          <label className="wide">
            <input type="checkbox" checked={unknownDate} onChange={event => setUnknownDate(event.target.checked)} />
            Fecha de adquisición desconocida
          </label>
          {unknownDate
            ? <Field label="Motivo de fecha desconocida" name="date_unknown_reason" maxLength={2000} />
            : <Field label="Fecha de adquisición" name="acquired_on" type="date" />}
        </>}
      </div>
      <p className="hint">
        Se registrará Disponible y sin custodio. El código de inventario se
        genera al guardar.
      </p>
    </Form>
  );
}
export function CustodianForm({
  onSubmit,
}: {
  onSubmit: (data: Fields) => Promise<unknown>;
}) {
  return (
    <Form onSubmit={onSubmit} submit="Registrar custodio">
      <div className="form-grid">
        <Field label="Nombre completo" name="full_name" />
        <Field label="Correo" name="email" type="email" maxLength={254} />
        <Field label="Dependencia" name="department" optional />
      </div>
      <p className="hint">
        La persona podrá recibir activos. Este registro no crea una cuenta de
        acceso.
      </p>
    </Form>
  );
}
