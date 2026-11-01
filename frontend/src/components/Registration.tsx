import type { Fields, Options } from "../types";
import { Field, Form } from "./Form";
export function AssetForm({
  options,
  onSubmit,
}: {
  options: Options;
  onSubmit: (data: Fields) => Promise<unknown>;
}) {
  return (
    <Form onSubmit={onSubmit} submit="Registrar activo">
      <div className="form-grid">
        <Field label="Nombre" name="name" />
        <label className="wide">
          Descripción
          <textarea name="description" required maxLength={2000} />
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
        </label>
        <Field label="Marca" name="brand" maxLength={120} />
        <Field label="Modelo" name="model" maxLength={120} />
        <Field label="Número de serie" name="serial_number" />
        <Field label="Ubicación" name="location" maxLength={240} />
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
