import { useState } from "react";
import type { Action, Asset, Body, Custodian, Fields, Options } from "../types";
import { Field, Form } from "./Form";
const titles: Record<Action, string> = {
  deliver: "Entregar activo",
  return: "Registrar devolución",
  condition: "Cambiar condición",
  rectify: "Rectificar último movimiento",
};
const submits: Record<Action, string> = {
  deliver: "Confirmar entrega",
  return: "Confirmar devolución",
  condition: "Guardar condición",
  rectify: "Anular efecto del movimiento",
};
export function Movements({
  asset,
  people,
  options,
  onSubmit,
}: {
  asset: Asset;
  people: Custodian[];
  options: Options;
  onSubmit: (action: Action, data: Body) => Promise<unknown>;
}) {
  const [action, setAction] = useState<Action | null>(null);
  async function save(fields: Fields) {
    if (!action) return;
    const body: Body = { ...fields, expected_revision: asset.revision };
    if (action === "deliver") body.custodian_id = Number(fields.custodian_id);
    if (action === "rectify") body.movement_id = asset.rectifiable_movement_id!;
    await onSubmit(action, body);
    setAction(null);
  }
  return (
    <section className="actions">
      <div className="action-buttons">
        {asset.assignment === "disponible" &&
          asset.active_maintenance_id == null &&
          asset.condition === "operativo" && (
            <button className="primary" onClick={() => setAction("deliver")}>
              Entregar
            </button>
          )}
        {asset.assignment === "asignado" && (
          <button className="primary" onClick={() => setAction("return")}>
            Devolver
          </button>
        )}
        {asset.assignment === "disponible" && (
          <button onClick={() => setAction("condition")}>
            Cambiar condición
          </button>
        )}
        {asset.rectifiable_movement_id != null && (
          <button onClick={() => setAction("rectify")}>
            Rectificar último movimiento
          </button>
        )}
      </div>
      {action && (
        <div className="action-form">
          <div className="section-heading">
            <h3>{titles[action]}</h3>
            <button onClick={() => setAction(null)}>Cancelar</button>
          </div>
          <Form key={action} onSubmit={save} submit={submits[action]}>
            {action === "deliver" && (
              <>
                <label>
                  Custodio
                  <select name="custodian_id" required defaultValue="">
                    <option value="" disabled>
                      Selecciona una persona
                    </option>
                    {people.map((p) => (
                      <option key={p.id} value={p.id}>
                        {p.full_name} · {p.email}
                      </option>
                    ))}
                  </select>
                </label>
                <Field label="Destino" name="destination" maxLength={240} />
                {!people.length && (
                  <p className="hint">
                    Registra primero una persona con el botón «Nuevo custodio».
                  </p>
                )}
              </>
            )}
            {(action === "return" || action === "condition") && (
              <label>
                {action === "return"
                  ? "Condición de recepción"
                  : "Nueva condición"}
                <select name="condition" required defaultValue="">
                  <option value="" disabled>
                    Selecciona la condición
                  </option>
                  {options.conditions
                    .filter(
                      (c) => action === "return" || c.value !== asset.condition,
                    )
                    .map((c) => (
                      <option key={c.value} value={c.value}>
                        {c.label}
                      </option>
                    ))}
                </select>
              </label>
            )}
            {action === "return" && (
              <Field
                label="Lugar de recepción"
                name="reception_location"
                maxLength={240}
              />
            )}
            {action === "rectify" && (
              <p className="hint">
                Se anulará el efecto del movimiento #
                {asset.rectifiable_movement_id} y se restaurará su situación
                anterior. El original permanecerá en el historial. Registra
                después la operación correcta por separado.
              </p>
            )}
            {(action === "condition" || action === "rectify") && (
              <label>
                Motivo
                <textarea name="reason" required maxLength={2000} />
              </label>
            )}
            <label>
              Observación <small>· opcional</small>
              <textarea name="note" maxLength={2000} />
            </label>
          </Form>
        </div>
      )}
    </section>
  );
}
