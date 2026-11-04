import { useEffect, useState } from "react";
import { ApiError, request } from "../api";
import type {
  LicenseLot,
  LicenseLotAudit,
  LicenseLotValues,
  LicensePage,
} from "../types";
import { ErrorNotice } from "./Form";
import {
  isAborted,
  licenseFields,
  licenseModels,
  LicenseLotForm,
  LicensePagination,
  LicenseStatusBadge,
} from "./LicenseLotForm";

function Values({ values }: { values: Partial<LicenseLotValues> }) {
  return (
    <dl className="license-values">
      {Object.entries(licenseFields).map(([key, label]) => {
        const name = key as keyof LicenseLotValues;
        const value = values[name];
        return (
          <div key={key}>
            <dt>{label}</dt>
            <dd>
              {name === "license_model" && value
                ? licenseModels[value as keyof typeof licenseModels]
                : (value ?? "Sin fecha de fin")}
            </dd>
          </div>
        );
      })}
    </dl>
  );
}

export function LicenseLotDetail({
  lotId,
  onBack,
}: {
  lotId: number;
  onBack: () => void;
}) {
  const [lot, setLot] = useState<LicenseLot | null>(null);
  const [history, setHistory] = useState<LicensePage<LicenseLotAudit> | null>(
    null,
  );
  const [number, setNumber] = useState(1);
  const [refresh, setRefresh] = useState(0);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(false);
  const [error, setError] = useState<unknown>(null);
  const [message, setMessage] = useState("");
  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setLot(null);
    setHistory(null);
    Promise.all([
      request<LicenseLot>(`/license-lots/${lotId}/`, {
        signal: controller.signal,
      }),
      request<LicensePage<LicenseLotAudit>>(
        `/license-lots/${lotId}/history/?page=${number}`,
        { signal: controller.signal },
      ),
    ])
      .then(([value, events]) => {
        setLot(value);
        setHistory(events);
      })
      .catch((e) => {
        if (!isAborted(e)) setError(e);
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [lotId, number, refresh]);
  return (
    <section className="panel detail">
      <button className="back" onClick={onBack}>
        ← Volver a los lotes
      </button>
      {error != null && <ErrorNotice error={error} />}
      {message && (
        <p className="notice" role="status">
          {message}
        </p>
      )}
      {loading ? (
        <p role="status" className="empty">
          Cargando lote e historial…
        </p>
      ) : !lot || !history ? (
        <>
          <p className="empty">No se pudo cargar el lote y su historial.</p>
          <button
            onClick={() => {
              setError(null);
              setRefresh((n) => n + 1);
            }}
          >
            Volver a cargar
          </button>
        </>
      ) : (
        <>
          <div className="detail-heading">
            <div>
              <h2>{lot.product_name}</h2>
              <p>{lot.vendor}</p>
            </div>
            <LicenseStatusBadge status={lot.temporal_status} />
          </div>
          <Values values={lot} />
          <p>
            <strong>Remanentes: {lot.remaining_quantity}</strong>
          </p>
          {lot.temporal_status === "EXPIRED" && (
            <p className="notice">
              Lote vencido: los remanentes no representan puestos utilizables.
            </p>
          )}
          <p className="muted">
            Registrado por {lot.created_by.username} · Revisión {lot.revision}
          </p>
          <button
            onClick={() => {
              setEditing((value) => !value);
              setError(null);
              setMessage("");
            }}
          >
            {editing ? "Cancelar edición" : "Editar lote"}
          </button>
          {editing && (
            <section className="registration">
              <h3>Editar lote</h3>
              <LicenseLotForm
                key={`${lot.id}-${lot.revision}`}
                lot={lot}
                onSubmit={async (body) => {
                  try {
                    await request<LicenseLot>(`/license-lots/${lot.id}/`, {
                      method: "PATCH",
                      body,
                    });
                    setEditing(false);
                    setNumber(1);
                    setRefresh((n) => n + 1);
                    setMessage(
                      "Cambios guardados. El historial está actualizado.",
                    );
                  } catch (e) {
                    if (e instanceof ApiError && e.status === 409) {
                      setError(
                        new Error(
                          "El lote cambió. Se recargó la ficha; revisa los datos y vuelve a editar. No se reenviaron tus cambios.",
                        ),
                      );
                      setEditing(false);
                      setNumber(1);
                      setRefresh((n) => n + 1);
                    } else throw e;
                  }
                }}
              />
            </section>
          )}
          <section className="history">
            <div className="section-heading">
              <h3>Historial del lote</h3>
              <span>{history.count} registros</span>
            </div>
            <ol>
              {history.results.map((event) => (
                <li key={event.id}>
                  <div className="event-top">
                    <strong>
                      {event.resulting_revision === 0
                        ? "Alta del lote"
                        : "Edición del lote"}{" "}
                      · Revisión {event.resulting_revision}
                    </strong>
                    <time dateTime={event.timestamp}>
                      {new Intl.DateTimeFormat("es-EC", {
                        dateStyle: "medium",
                        timeStyle: "short",
                        timeZone: "America/Guayaquil",
                      }).format(new Date(event.timestamp))}
                    </time>
                  </div>
                  <p>{event.actor.recorded_label}</p>
                  <div className="state-diff">
                    <div>
                      <small>Antes</small>
                      {event.resulting_revision === 0 ? (
                        <p>Sin registro previo</p>
                      ) : (
                        <Values values={event.before_json} />
                      )}
                    </div>
                    <div>
                      <small>Después</small>
                      <Values values={event.after_json} />
                    </div>
                  </div>
                </li>
              ))}
            </ol>
            {!history.results.length && <p>No hay registros de historial.</p>}
            <LicensePagination
              page={history}
              number={number}
              onPage={(value) => {
                setNumber(value);
                setEditing(false);
                setError(null);
                setMessage("");
              }}
              label="Páginas del historial"
            />
          </section>
        </>
      )}
    </section>
  );
}
