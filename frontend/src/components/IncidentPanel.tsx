import type { Asset, Body, Choice, Incident } from "../types";
import { labels } from "../types";
import { Form } from "./Form";

export function IncidentPanel({
  asset,
  incidents,
  onWrite,
  conditions,
}: {
  asset: Asset;
  incidents: Incident[];
  conditions?: Choice[];
  onWrite: (path: string, body: Body, message: string) => Promise<unknown>;
}) {
  const pending = incidents.filter((incident) =>
    incident.status === "open" && (incident.type === "damage" || incident.type === "observation")
  );
  const loss = incidents.find((incident) =>
    incident.status === "open" && (incident.type === "lost" || incident.type === "stolen")
  );
  const canReport = asset.lifecycle_status === "localizado";

  return (
    <section className="history" aria-label="Daños y observaciones">
      <h3>Daños y observaciones</h3>
      {pending.length ? (
        <p role="status" className="tag warning">
          {pending.length === 1 ? "1 novedad pendiente" : `${pending.length} novedades pendientes`}
        </p>
      ) : (
        <p className="muted">Sin novedades pendientes.</p>
      )}
      {pending.map((incident) => (
        <article key={incident.id} className="incident-card">
          <h4>{labels[incident.type]} #{incident.id}</h4>
          <p>{incident.description}</p>
          <p className="muted">Reportado por {incident.reported_by.username}</p>
          <Form
            submit="Resolver novedad"
            onSubmit={(data) => {
              if (!data.resolution_note) throw new Error("Escribe una nota de resolución.");
              return onWrite(
                `/incidents/${incident.id}/resolve/`,
                { resolution_note: data.resolution_note, expected_revision: asset.revision },
                "Novedad resuelta.",
              );
            }}
          >
            <label>
              Nota de resolución
              <textarea name="resolution_note" required maxLength={2000} />
            </label>
          </Form>
        </article>
      ))}
      {canReport && (
        <Form
          submit="Registrar novedad"
          onSubmit={(data) => {
            if (!data.description) throw new Error("Escribe una descripción.");
            return onWrite(
              `/assets/${asset.id}/incidents/`,
              { type: data.type, description: data.description, expected_revision: asset.revision },
              "Novedad registrada.",
            );
          }}
        >
          <label>
            Tipo de novedad
            <select name="type" defaultValue="damage">
              <option value="damage">Daño</option>
              <option value="observation">Observación</option>
              <option value="lost">Pérdida</option>
              <option value="stolen">Robo</option>
            </select>
          </label>
          <label>
            Descripción de la novedad
            <textarea name="description" required maxLength={2000} />
          </label>
        </Form>
      )}
      {asset.lifecycle_status === "no_localizado" && (
        <>
          {loss && (
            <p className="tag warning">{labels[loss.type]} pendiente · Reporte #{loss.id}</p>
          )}
          <Form submit="Registrar recuperación" onSubmit={(data) => {
            if (!data.inspection_confirmed || !data.inspected_condition || !data.recovered_location) {
              throw new Error("Confirma la inspección e indica la condición y la ubicación.");
            }
            return onWrite(
              `/assets/${asset.id}/recover/`,
              {
                expected_revision: asset.revision,
                inspection_confirmed: true,
                inspected_condition: data.inspected_condition,
                recovered_location: data.recovered_location,
                note: data.note,
              },
              "Recuperación registrada.",
            );
          }}>
            <label>
              Condición tras la inspección
              <select name="inspected_condition" required defaultValue="">
                <option value="" disabled>Selecciona la condición</option>
                {(conditions ?? []).map((condition) => (
                  <option key={condition.value} value={condition.value}>{condition.label}</option>
                ))}
              </select>
            </label>
            <label>
              Ubicación de recuperación
              <input name="recovered_location" required maxLength={240} />
            </label>
            <label>
              Nota de recuperación <small>· opcional</small>
              <textarea name="note" maxLength={2000} />
            </label>
            <label className="maintenance-confirmation">
              <input type="checkbox" name="inspection_confirmed" required />
              Confirmo que inspeccioné el activo.
            </label>
          </Form>
        </>
      )}
    </section>
  );
}
