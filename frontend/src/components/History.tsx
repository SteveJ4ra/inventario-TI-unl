import type { HistoryEvent, Movement, Snapshot } from "../types";
import { labels } from "../types";
function Situation({ value }: { value: Snapshot }) {
  return <span>{labels[value.condition]} · {labels[value.assignment]} · {value.location}
    {value.custodian_id != null ? " · Custodio #" + value.custodian_id : ""}</span>;
}
function EventTime({ value }: { value: string }) {
  return <time>{new Intl.DateTimeFormat("es-EC", { dateStyle: "medium", timeStyle: "short",
    timeZone: "America/Guayaquil" }).format(new Date(value))}</time>;
}
function MovementEntry({ event }: { event: Movement }) {
  return <>
    <div className="event-top"><strong>{labels[event.type]} <span className="muted">#{event.id}</span></strong><EventTime value={event.occurred_at} /></div>
    <p className="event-person"><span>{event.actor.recorded_label}</span>{event.custodian && <> · <span>{event.custodian.full_name}</span></>}</p>
    <div className="state-diff"><div><small>Antes</small><Situation value={event.before} /></div>
      <div><small>Después</small><Situation value={event.after} /></div></div>
    {event.reason && <p><strong>Motivo:</strong> {event.reason}</p>}
    {event.note && <p>{event.note}</p>}
    {event.rectified_by_id && <span className="tag warning">Rectificado por #{event.rectified_by_id}</span>}
    {event.rectifies_id && <span className="tag">Rectifica el movimiento #{event.rectifies_id}</span>}
  </>;
}
const snapshotLabels: Record<string, string> = { name: "Nombre", description: "Descripción", category: "Categoría",
  brand: "Marca", model: "Modelo", serial_number: "Número de serie", acquisition: "Adquisición", document_id: "Documento",
  source: "Origen", reference: "Referencia", document_date: "Fecha documental", supplier: "Proveedor",
  support_type: "Tipo de respaldo", invoice_total: "Total compartido", currency: "Moneda", item_value: "Valor individual",
  acquired_on: "Fecha de adquisición", date_unknown_reason: "Motivo de fecha desconocida", faculty_id: "Facultad (id)", faculty_name: "Facultad" };
function SnapshotData({ value }: { value: unknown }) {
  if (value === null || typeof value !== "object") return <span>{value == null ? "Sin dato" : String(value)}</span>;
  return <dl>{Object.entries(value).map(([key, entry]) => <div key={key}>
    <dt>{snapshotLabels[key] || key}</dt><dd><SnapshotData value={entry} /></dd>
  </div>)}</dl>;
}
export function History({ events, combined }: { events: Movement[]; combined?: HistoryEvent[] | null }) {
  const rows: HistoryEvent[] = combined ?? events.map(event => ({ event_type: "movement", event_id: event.id,
    occurred_at: event.occurred_at, actor: event.actor, resulting_revision: event.resulting_revision, data: event }));
  return <section className="history">
    <div className="section-heading"><h3>Historial del activo</h3><span className="muted">{rows.length} {combined ? "eventos" : "movimientos"}</span></div>
    {!rows.length ? <p className="empty">{combined ? "Todavía no hay eventos." : "Todavía no hay movimientos."}</p>
      : <ol>{rows.map(event => <li key={event.event_type + ":" + event.event_id}>
        {event.event_type === "movement" ? <MovementEntry event={event.data as Movement} /> : <>
          <div className="event-top"><strong>{event.event_type === "asset_change" ? "Edición de ficha" : event.event_type === "faculty_change" ? "Cambio de facultad" : event.event_type} #{event.event_id}</strong><EventTime value={event.occurred_at} /></div>
          <p>{event.actor.username} · Revisión {event.resulting_revision ?? "—"}</p>
          {(() => {
            const data = event.data as { before?: unknown; after?: unknown; reason?: string };
            return <><p>{data.reason}</p><div className="state-diff"><div><small>Antes</small><SnapshotData value={data.before} /></div>
              <div><small>Después</small><SnapshotData value={data.after} /></div></div></>;
          })()}
        </>}
      </li>)}</ol>}
  </section>;
}
