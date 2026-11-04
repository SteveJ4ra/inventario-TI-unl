import type { HistoryEntry, Movement, Snapshot } from "../types";
import { labels } from "../types";
function Situation({ value }: { value: Snapshot }) {
  return (
    <span>
      {labels[value.condition]} · {labels[value.assignment]} · {value.location}
      {value.custodian_id != null ? " · Custodio #" + value.custodian_id : ""}
    </span>
  );
}
function MovementDetails({ event }: { event: Movement }) {
  return (
    <>
      {event.custodian && <p className="event-person">{event.custodian.full_name}</p>}
      <div className="state-diff">
        <div>
          <small>Antes</small>
          <Situation value={event.before} />
        </div>
        <div>
          <small>Después</small>
          <Situation value={event.after} />
        </div>
      </div>
      {event.reason && <p><strong>Motivo:</strong> {event.reason}</p>}
      {event.note && <p>{event.note}</p>}
      {event.rectified_by_id && (
        <span className="tag warning">Rectificado por #{event.rectified_by_id}</span>
      )}
      {event.rectifies_id && (
        <span className="tag">Rectifica el movimiento #{event.rectifies_id}</span>
      )}
    </>
  );
}

const historyDate = new Intl.DateTimeFormat("es-EC", {
  dateStyle: "medium",
  timeStyle: "short",
  timeZone: "America/Guayaquil",
});

function title(entry: HistoryEntry) {
  switch (entry.event_type) {
    case "movement":
      return `${labels[entry.data.type]} #${entry.event_id}`;
    case "incident": {
      const event = entry.data.after.event;
      if (event.type === "lost" || event.type === "stolen") {
        return `Reporte de ${labels[event.type].toLowerCase()} #${entry.data.projection_id}`;
      }
      const action = event.status === "resolved" ? "Resolución" : "Registro";
      return `${action} de novedad · ${labels[event.type]} #${entry.data.projection_id}`;
    }
    case "maintenance": {
      const { status } = entry.data.after.event;
      const action = status === "completed" ? "Cierre"
        : status === "interrupted_unlocated" ? "Interrupción" : "Inicio";
      return `${action} de mantenimiento #${entry.data.projection_id}`;
    }
    case "recovery":
      return `Recuperación del activo · Reporte #${entry.data.after.event.incident_id}`;
  }
}

export function History({ events }: { events: HistoryEntry[] }) {
  return (
    <section className="history">
      <div className="section-heading">
        <h3>Historial del activo</h3>
        <span className="muted">{events.length} eventos</span>
      </div>
      {!events.length ? (
        <p className="empty">Todavía no hay eventos.</p>
      ) : (
        <ol>
          {events.map((event) => (
            <li key={`${event.event_type}-${event.event_id}`}>
              <div className="event-top">
                <strong>{title(event)}</strong>
                <time dateTime={event.occurred_at}>
                  {historyDate.format(new Date(event.occurred_at))}
                </time>
              </div>
              <p className="event-person">
                {event.event_type === "movement"
                  ? event.data.actor.recorded_label
                  : event.actor.username}
              </p>
              {event.event_type === "movement" && <MovementDetails event={event.data} />}
              {event.event_type === "maintenance" && (
                <>
                  <p>{event.data.after.event.description}</p>
                  <p>Taller: {event.data.after.event.workshop_location} · Ubicación previa: {event.data.after.event.previous_location}</p>
                  {event.data.after.event.status === "completed" && (
                    <p>Resultado: {event.data.after.event.result} · Recepción: {event.data.after.event.receiving_location}</p>
                  )}
                </>
              )}
              {event.event_type === "incident" && (
                <>
                  <p>{event.data.after.event.description}</p>
                  {event.data.after.event.last_location && (
                    <p>
                      Última ubicación: {event.data.after.event.last_location}
                      {event.data.after.event.last_custodian_snapshot && (
                        <> · Custodia anterior: {event.data.after.event.last_custodian_snapshot.full_name}</>
                      )}
                    </p>
                  )}
                  {event.data.after.event.resolution_note && (
                    <p><strong>Nota de resolución:</strong> {event.data.after.event.resolution_note}</p>
                  )}
                </>
              )}
              {event.event_type === "recovery" && (
                <>
                  <p>Condición tras inspección: {labels[event.data.after.event.inspected_condition]} · Ubicación: {event.data.after.event.recovered_location}</p>
                  {event.data.after.event.note && <p>{event.data.after.event.note}</p>}
                </>
              )}
            </li>
          ))}
        </ol>
      )}
    </section>
  );
}
