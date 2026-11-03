import { useState } from "react";
import { ApiError, request, upload } from "../api";
import type { ImportBatch, ImportIssue, ImportKind, ImportRow } from "../types";
import { ErrorNotice } from "./Form";

const PAGE_SIZE = 50;

const KINDS: {
  value: ImportKind;
  label: string;
  version: string;
  template: string;
}[] = [
  {
    value: "assets",
    label: "Activos",
    version: "assets-v1",
    template: "/api/imports/templates/assets/?schema_version=assets-v1",
  },
  {
    value: "license_lots",
    label: "Lotes de licencias",
    version: "license-lots-v1",
    template:
      "/api/imports/templates/license_lots/?schema_version=license-lots-v1",
  },
];

const COLUMNS: Record<
  ImportKind,
  { label: string; value: (row: ImportRow) => string | number | null }[]
> = {
  assets: [
    { label: "Nombre", value: (row) => row.values.name },
    { label: "Marca / modelo", value: (row) => `${row.values.brand ?? ""} ${row.values.model ?? ""}`.trim() },
    { label: "Serie", value: (row) => row.values.serial_number },
    { label: "Categoría", value: (row) => row.values.category },
    { label: "Condición", value: (row) => row.values.condition },
    { label: "Valor", value: (row) => row.values.item_value },
    {
      label: "Documento",
      value: (row) =>
        row.values.document_key ??
        row.values.acquisition_document_id ??
        null,
    },
  ],
  license_lots: [
    { label: "Producto", value: (row) => row.values.product_name },
    { label: "Proveedor", value: (row) => row.values.vendor },
    { label: "Tipo", value: (row) => row.values.license_model },
    { label: "Compradas", value: (row) => row.values.purchased_quantity },
    { label: "En uso", value: (row) => row.values.in_use_quantity },
    { label: "Inicio", value: (row) => row.values.starts_on },
    { label: "Fin", value: (row) => row.values.ends_on },
  ],
};

const SUMMARY_LABELS: Record<string, string> = {
  record_count: "Registros válidos",
  total_rows: "Filas leídas",
  new_documents: "Documentos nuevos",
  existing_documents: "Documentos existentes",
  purchased_total: "Licencias compradas",
  in_use_total: "Licencias en uso",
};

const STATE_LABELS: Record<string, string> = {
  INVALID: "Con errores",
  PREVIEW_READY: "Vista previa lista",
  CONFIRMED_ONCE: "Confirmado una vez",
  APPLIED: "Aplicado",
  EXPIRED: "Vencido",
  CANCELLED: "Cancelado",
};

function shown(value: string | number | null | undefined) {
  return value === null || value === undefined || value === "" ? "—" : value;
}

function place(issue: ImportIssue) {
  if (!issue.row) return "Archivo";
  return `Fila ${issue.row}`;
}

export function ImportPanel({
  onClose,
  onApplied,
}: {
  onClose: () => void;
  onApplied: () => void;
}) {
  const [kind, setKind] = useState<ImportKind>("assets");
  const [file, setFile] = useState<File | null>(null);
  const [batch, setBatch] = useState<ImportBatch | null>(null);
  const [finalStep, setFinalStep] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<unknown>(null);
  const [message, setMessage] = useState("");
  const [page, setPage] = useState(1);

  const info = KINDS.find((option) => option.value === kind)!;
  const issues = batch?.errors ?? [];
  const rows = batch?.rows ?? [];
  const pages = Math.max(1, Math.ceil(rows.length / PAGE_SIZE));
  const visible = rows.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);
  const created = batch?.applied_result?.created;

  function reset(next: ImportKind) {
    setKind(next);
    setBatch(null);
    setFinalStep(false);
    setError(null);
    setMessage("");
    setPage(1);
  }

  async function validate() {
    if (!file) return;
    setBusy(true);
    setError(null);
    setMessage("");
    try {
      const data = new FormData();
      data.set("kind", kind);
      data.set("schema_version", info.version);
      data.set("file", file);
      const result = await upload<ImportBatch>("/imports/previews/", data);
      setBatch(result);
      setFinalStep(false);
      setPage(1);
    } catch (caught) {
      setError(caught);
      if (caught instanceof ApiError && caught.payload) {
        const payload = caught.payload as ImportBatch;
        if (payload && payload.batch_id) {
          setBatch(payload);
          setFinalStep(false);
          setPage(1);
        }
      }
    } finally {
      setBusy(false);
    }
  }

  async function firstConfirmation() {
    if (!batch) return;
    setBusy(true);
    setError(null);
    setMessage("");
    try {
      const result = await request<ImportBatch>(
        `/imports/${batch.batch_id}/confirm/`,
        { body: { content_hash: batch.content_hash } },
      );
      setBatch(result);
      setFinalStep(true);
    } catch (caught) {
      conflict(caught);
    } finally {
      setBusy(false);
    }
  }

  async function applyFinal() {
    if (!batch) return;
    setBusy(true);
    setError(null);
    setMessage("");
    try {
      const result = await request<ImportBatch>(
        `/imports/${batch.batch_id}/apply/`,
        { body: { content_hash: batch.content_hash } },
      );
      setBatch(result);
      setFinalStep(false);
      setMessage(
        `${result.applied_result?.created ?? 0} registro(s) creado(s).`,
      );
      onApplied();
    } catch (caught) {
      conflict(caught);
    } finally {
      setBusy(false);
    }
  }

  async function cancel() {
    if (!batch) return;
    setBusy(true);
    setError(null);
    try {
      const result = await request<ImportBatch>(
        `/imports/${batch.batch_id}/cancel/`,
        { body: {} },
      );
      setBatch(result);
      setFinalStep(false);
      setMessage("Lote cancelado; no se creó ningún registro.");
    } catch (caught) {
      conflict(caught);
    } finally {
      setBusy(false);
    }
  }

  function conflict(caught: unknown) {
    setError(caught);
    if (caught instanceof ApiError && caught.status === 409) {
      setBatch(null);
      setFinalStep(false);
      setFile(null);
    }
  }

  const actions = (() => {
    if (!batch) return null;
    if (batch.state === "APPLIED")
      return (
        <div className="notice" role="status">
          <strong>Importación completada.</strong> Creados: {created ?? 0}.
          Referencia del lote: {batch.batch_id.slice(0, 8)}…
          <button onClick={onClose}>Cerrar y ver inventario</button>
        </div>
      );
    if (batch.state === "CANCELLED")
      return <p className="hint">Este lote fue cancelado y no crea registros.</p>;
    if (batch.state === "EXPIRED")
      return (
        <p className="hint" role="alert">
          La vista previa venció. Carga el archivo de nuevo.
        </p>
      );
    if (finalStep)
      return (
        <div className="confirm-final" role="region" aria-label="Confirmación final">
          <p>
            Vas a crear <strong>{batch.summary.record_count ?? 0}</strong>{" "}
            {Number(batch.summary.record_count) === 1 ? "registro" : "registros"}{" "}
            de tipo <strong>{info.label}</strong>. Esta es la segunda y última
            confirmación.
          </p>
          <div className="filter-actions">
            <button className="primary" onClick={applyFinal} disabled={busy}>
              {busy
                ? "Aplicando…"
                : `Crear ${batch.summary.record_count ?? 0} registro(s)`}
            </button>
            <button onClick={() => setFinalStep(false)} disabled={busy}>
              Volver a la vista previa
            </button>
          </div>
        </div>
      );
    if (batch.state === "PREVIEW_READY" && issues.length === 0)
      return (
        <div className="filter-actions">
          <button className="primary" onClick={firstConfirmation} disabled={busy}>
            Continuar a la confirmación
          </button>
          <button onClick={cancel} disabled={busy}>
            Cancelar lote
          </button>
        </div>
      );
    return null;
  })();

  return (
    <section className="import">
      <div className="section-heading">
        <h2>Importar desde CSV</h2>
        <button onClick={onClose}>Cerrar</button>
      </div>
      <div className="import-controls">
        <label>
          Tipo de importación
          <select
            value={kind}
            disabled={busy}
            onChange={(event) => reset(event.target.value as ImportKind)}
          >
            {KINDS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>
        <a className="button" href={info.template} download>
          Descargar plantilla {info.version}
        </a>
        <label>
          Archivo CSV
          <input
            type="file"
            accept=".csv,text/csv"
            disabled={busy}
            onChange={(event) => {
              setFile(event.target.files?.[0] ?? null);
              setBatch(null);
              setFinalStep(false);
              setError(null);
              setMessage("");
            }}
          />
        </label>
        <button
          className="primary"
          onClick={validate}
          disabled={busy || !file}
        >
          {busy ? "Validando…" : "Validar archivo"}
        </button>
      </div>
      <p className="hint">
        Se valida el archivo completo antes de escribir. Si hay un error no se
        crea ningún registro. La plantilla {info.version} usa la versión
        vigente del esquema.
      </p>
      {message && (
        <div className="notice" role="status">
          ✓ {message}
        </div>
      )}
      {error != null && <ErrorNotice error={error} />}
      {batch && (
        <div className="import-preview">
          <div className="section-heading">
            <h3>
              Vista previa · {STATE_LABELS[batch.state] ?? batch.state}
            </h3>
            <span className="muted">
              Lote {batch.batch_id.slice(0, 8)}… · {batch.schema_version}
            </span>
          </div>
          <dl className="facts import-summary">
            {Object.entries(batch.summary).map(([key, value]) => (
              <div key={key}>
                <dt>{SUMMARY_LABELS[key] ?? key}</dt>
                <dd>{value}</dd>
              </div>
            ))}
          </dl>
          {issues.length > 0 && (
            <div className="import-errors">
              <h4>Errores encontrados ({issues.length})</h4>
              <p className="hint">
                Corrige el archivo y vuelve a validarlo. No se puede confirmar
                una importación con errores.
              </p>
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>Fila</th>
                      <th>Campo</th>
                      <th>Motivo</th>
                    </tr>
                  </thead>
                  <tbody>
                    {issues.map((issue, index) => (
                      <tr key={`${issue.row}-${issue.field}-${index}`}>
                        <td>{place(issue)}</td>
                        <td>{issue.field || "Archivo"}</td>
                        <td>{issue.message}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
          {rows.length > 0 && (
            <>
              <h4>Filas validadas ({batch.row_count})</h4>
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>Fila</th>
                      {COLUMNS[batch.kind].map((column) => (
                        <th key={column.label}>{column.label}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {visible.map((row) => (
                      <tr key={row.row} className={row.valid === false ? "invalid" : ""}>
                        <td>{row.row}</td>
                        {COLUMNS[batch.kind].map((column) => (
                          <td key={column.label}>
                            {shown(column.value(row))}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              {pages > 1 && (
                <div className="pagination">
                  <button
                    disabled={page <= 1}
                    onClick={() => setPage((value) => value - 1)}
                  >
                    Anterior
                  </button>
                  <span>
                    Página {page} de {pages}
                  </span>
                  <button
                    disabled={page >= pages}
                    onClick={() => setPage((value) => value + 1)}
                  >
                    Siguiente
                  </button>
                </div>
              )}
            </>
          )}
          {actions}
        </div>
      )}
    </section>
  );
}
