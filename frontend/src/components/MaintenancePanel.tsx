import { useId } from "react";
import type { Asset, Body, HistoryEntry, Maintenance } from "../types";
import { Form } from "./Form";

function locationSuggestions(locations: string[], history: HistoryEntry[]) {
  const values = new Set(locations);
  for (const entry of history) {
    if (entry.event_type === "movement") {
      values.add(entry.data.before.location);
      values.add(entry.data.after.location);
    } else if (entry.event_type === "maintenance") {
      const event = entry.data.after.event;
      values.add(event.previous_location);
      values.add(event.workshop_location);
      values.add(event.receiving_location);
    }
  }
  return [...values].filter(Boolean);
}

export function MaintenancePanel({
  asset,
  active,
  history,
  locations,
  onWrite,
}: {
  asset: Asset;
  active: Maintenance | null;
  history: HistoryEntry[];
  locations: string[];
  onWrite: (path: string, body: Body, message: string) => Promise<unknown>;
}) {
  const locationsId = useId();
  const suggestions = locationSuggestions(
    active ? [active.previous_location, ...locations] : locations,
    history,
  );
  const inProgress = active?.status === "in_progress";
  const canStart = asset.assignment === "disponible" && !asset.current_custodian && asset.active_maintenance_id == null;
  return (
    <section className="history" aria-label="Mantenimiento">
      <h3>Mantenimiento</h3>
      <datalist id={locationsId}>
        {suggestions.map((value) => <option key={value} value={value} />)}
      </datalist>
      {inProgress ? (
        <>
          <p className="tag warning">Mantenimiento en curso</p>
          <p>Taller: {active.workshop_location}</p>
          <p>Ubicación previa al taller: {active.previous_location}</p>
          <p>{active.description}</p>
          <Form submit="Cerrar mantenimiento" onSubmit={(data) => {
            if (!data.result || !data.receiving_location || !data.location_confirmed) {
              throw new Error("Completa el resultado y confirma la ubicación de recepción.");
            }
            return onWrite(
              `/maintenance/${active.id}/close/`,
              {
                result: data.result,
                receiving_location: data.receiving_location,
                location_confirmed: true,
                expected_revision: active.revision,
              },
              "Mantenimiento cerrado.",
            );
          }}>
            <label>
              Resultado
              <textarea name="result" required maxLength={2000} />
            </label>
            <label>
              Ubicación de recepción
              <input name="receiving_location" required maxLength={240}
                defaultValue={active.previous_location} list={locationsId} />
            </label>
            <label className="maintenance-confirmation">
              <input type="checkbox" name="location_confirmed" required />
              ¿Estás seguro? Confirmo la ubicación de recepción.
            </label>
          </Form>
        </>
      ) : (
        <>
          <p className="muted">Sin mantenimiento en curso.</p>
          {canStart && (
            <Form submit="Iniciar mantenimiento" onSubmit={(data) => {
              if (!data.description || !data.workshop_location) {
                throw new Error("Escribe una descripción y la ubicación del taller.");
              }
              return onWrite(
                `/assets/${asset.id}/maintenance/`,
                {
                  description: data.description,
                  workshop_location: data.workshop_location,
                  expected_revision: asset.revision,
                },
                "Mantenimiento iniciado.",
              );
            }}>
              <label>
                Descripción del mantenimiento
                <textarea name="description" required maxLength={2000} />
              </label>
              <label>
                Ubicación del taller
                <input name="workshop_location" required maxLength={240} list={locationsId} />
              </label>
            </Form>
          )}
        </>
      )}
    </section>
  );
}
