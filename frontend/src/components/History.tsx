import type { Movement, Snapshot } from "../types";
import { labels } from "../types";
function Situation({ value }: { value: Snapshot }) {
  return (
    <span>
      {labels[value.condition]} · {labels[value.assignment]} · {value.location}
      {value.custodian_id != null ? " · Custodio #" + value.custodian_id : ""}
    </span>
  );
}
export function History({ events }: { events: Movement[] }) {
  return (
    <section className="history">
      <div className="section-heading">
        <h3>Historial del activo</h3>
        <span className="muted">{events.length} movimientos</span>
      </div>
      {!events.length ? (
        <p className="empty">Todavía no hay movimientos.</p>
      ) : (
        <ol>
          {events.map((event) => (
            <li key={event.id}>
              <div className="event-top">
                <strong>
                  {labels[event.type]}{" "}
                  <span className="muted">#{event.id}</span>
                </strong>
                <time>
                  {new Intl.DateTimeFormat("es-EC", {
                    dateStyle: "medium",
                    timeStyle: "short",
                    timeZone: "America/Guayaquil",
                  }).format(new Date(event.occurred_at))}
                </time>
              </div>
              <p className="event-person">
                <span>{event.actor.recorded_label}</span>
                {event.custodian && (
                  <>
                    {" "}
                    · <span>{event.custodian.full_name}</span>
                  </>
                )}
              </p>
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
              {event.reason && (
                <p>
                  <strong>Motivo:</strong> {event.reason}
                </p>
              )}
              {event.note && <p>{event.note}</p>}
              {event.rectified_by_id && (
                <span className="tag warning">
                  Rectificado por #{event.rectified_by_id}
                </span>
              )}
              {event.rectifies_id && (
                <span className="tag">
                  Rectifica el movimiento #{event.rectifies_id}
                </span>
              )}
            </li>
          ))}
        </ol>
      )}
    </section>
  );
}
