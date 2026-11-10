import { useEffect, useRef, useState } from "react";
import { ApiError, request } from "../api";
import type { ImportBatch, ImportError, ImportPage } from "../types";
import { ErrorNotice } from "./Form";

const ASSET_COLUMNS = [
  "name",
  "description",
  "category",
  "brand",
  "model",
  "serial_number",
  "location",
  "condition",
  "faculty_id",
  "acquisition_document_id",
  "document_key",
  "acquisition_source",
  "document_reference",
  "document_date",
  "supplier",
  "invoice_total",
  "donation_support_type",
  "acquired_on",
  "date_unknown_reason",
  "item_value",
];
const LICENSE_COLUMNS = [
  "product_name",
  "vendor",
  "license_model",
  "purchased_quantity",
  "in_use_quantity",
  "starts_on",
  "ends_on",
];
const columnLabels: Record<string, string> = {
  name: "Nombre",
  description: "Descripción",
  category: "Categoría",
  brand: "Marca",
  model: "Modelo",
  serial_number: "Serie",
  location: "Ubicación",
  condition: "Condición",
  faculty_id: "Facultad",
  acquisition_document_id: "Documento",
  document_key: "Clave de documento",
  acquisition_source: "Origen",
  document_reference: "Referencia",
  document_date: "Fecha del documento",
  supplier: "Proveedor",
  invoice_total: "Total factura",
  donation_support_type: "Respaldo de donación",
  acquired_on: "Fecha de adquisición",
  date_unknown_reason: "Motivo sin fecha",
  item_value: "Valor del bien",
  product_name: "Producto",
  vendor: "Proveedor",
  license_model: "Modelo de licencia",
  purchased_quantity: "Compradas",
  in_use_quantity: "En uso",
  starts_on: "Inicio",
  ends_on: "Fin",
};
const emptyRows: ImportPage = {
  count: 0,
  next: null,
  previous: null,
  results: [],
};
const isBatch = (value: unknown): value is ImportBatch =>
  value != null &&
  typeof value === "object" &&
  "batch_id" in value &&
  "state" in value;
const canShowRows = (state: ImportBatch["state"]) =>
  ["INVALID", "PREVIEW_READY", "CONFIRMED_ONCE"].includes(state);

function downloadErrors(batch: ImportBatch) {
  const cell = (value: string | number) =>
    `"${String(value).replace(/"/g, '""')}"`;
  const lines = [
    ["fila", "campo", "motivo"].map(cell).join(","),
    ...batch.errors.map((error) =>
      [
        error.row,
        columnLabels[error.field] || error.field,
        error.message,
      ]
        .map(cell)
        .join(","),
    ),
  ];
  const blob = new Blob(["\ufeff" + lines.join("\r\n")], {
    type: "text/csv;charset=utf-8",
  });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `errores-${batch.kind}-${batch.batch_id.slice(0, 8)}.csv`;
  link.click();
  URL.revokeObjectURL(url);
}

function Summary({ batch }: { batch: ImportBatch }) {
  const valid = batch.summary.valid_rows ?? 0;
  const cards: [string, number][] = [
    ["Filas", batch.summary.row_count ?? 0],
    ["Válidas", valid],
    ["Con errores", batch.summary.invalid_rows ?? 0],
  ];
  if (batch.kind === "assets")
    cards.push(["Documentos", batch.summary.document_count ?? 0]);
  else
    cards.push(
      ["Compradas", batch.summary.purchased_quantity ?? 0],
      ["En uso", batch.summary.in_use_quantity ?? 0],
    );
  return (
    <div className="import-summary-grid">
      {cards.map(([label, value]) => (
        <div key={label}>
          <span>{label}</span>
          <strong>{value}</strong>
        </div>
      ))}
    </div>
  );
}

function ErrorList({ errors }: { errors: ImportError[] }) {
  if (!errors.length) return null;
  return (
    <div className="table-wrap">
      <table className="import-errors-table">
        <caption className="sr-only">Errores encontrados en el archivo</caption>
        <thead>
          <tr>
            <th>Fila</th>
            <th>Campo</th>
            <th>Problema</th>
          </tr>
        </thead>
        <tbody>
          {errors.map((error, index) => (
            <tr key={`${error.row}-${error.field}-${index}`}>
              <td>{error.row}</td>
              <td>{columnLabels[error.field] || error.field}</td>
              <td>{error.message}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function RowsTable({
  kind,
  rows,
  page,
  loading,
  onPage,
}: {
  kind: ImportBatch["kind"];
  rows: ImportPage;
  page: number;
  loading: boolean;
  onPage: (page: number) => void;
}) {
  const columns = kind === "assets" ? ASSET_COLUMNS : LICENSE_COLUMNS;
  return (
    <section className="panel import-rows">
      <div className="section-heading">
        <h2>Contenido validado</h2>
        <span className="muted">{rows.count} filas</span>
      </div>
      {loading ? (
        <p className="empty" role="status">
          Cargando filas…
        </p>
      ) : rows.results.length === 0 ? (
        <p className="empty">No hay filas para mostrar.</p>
      ) : (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Fila</th>
                {columns.map((column) => (
                  <th key={column}>{columnLabels[column] || column}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.results.map((row) => (
                <tr key={row.row_number}>
                  <td>{row.row_number}</td>
                  {columns.map((column) => (
                    <td key={column}>{row.values[column] || "—"}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {rows.count > 50 && (
        <div className="pagination">
          <button disabled={!rows.previous || loading} onClick={() => onPage(page - 1)}>
            Anterior
          </button>
          <span>Página {page}</span>
          <button disabled={!rows.next || loading} onClick={() => onPage(page + 1)}>
            Siguiente
          </button>
        </div>
      )}
    </section>
  );
}

export function Imports() {
  const [kind, setKind] = useState<ImportBatch["kind"]>("assets");
  const [file, setFile] = useState<File | null>(null);
  const [batch, setBatch] = useState<ImportBatch | null>(null);
  const [rows, setRows] = useState<ImportPage>(emptyRows);
  const [rowsLoading, setRowsLoading] = useState(false);
  const [page, setPage] = useState(1);
  const [busy, setBusy] = useState(false);
  const [action, setAction] = useState<"confirm" | "apply" | "cancel" | null>(
    null,
  );
  const [reviewed, setReviewed] = useState(false);
  const [error, setError] = useState<unknown>(null);
  const [message, setMessage] = useState("");
  const input = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (!batch || !canShowRows(batch.state)) {
      setRows(emptyRows);
      setRowsLoading(false);
      return;
    }
    const controller = new AbortController();
    setRowsLoading(true);
    request<ImportBatch>(`/imports/${batch.batch_id}?page=${page}`, {
      signal: controller.signal,
    })
      .then((fresh) => {
        setBatch((current) =>
          current && current.batch_id === fresh.batch_id ? fresh : current,
        );
        setRows(fresh.rows ?? emptyRows);
      })
      .catch((reason) => {
        if (!(reason instanceof DOMException && reason.name === "AbortError"))
          setError(reason);
      })
      .finally(() => {
        if (!controller.signal.aborted) setRowsLoading(false);
      });
    return () => controller.abort();
  }, [batch?.batch_id, batch?.state, page]);

  function reset(changeKind = kind) {
    setKind(changeKind);
    setFile(null);
    setBatch(null);
    setRows(emptyRows);
    setPage(1);
    setReviewed(false);
    setError(null);
    setMessage("");
    setAction(null);
    if (input.current) input.current.value = "";
  }

  async function upload(event: React.FormEvent) {
    event.preventDefault();
    if (!file) {
      setError(new Error("Selecciona un archivo CSV para continuar."));
      return;
    }
    setBusy(true);
    setError(null);
    setMessage("");
    setAction(null);
    const form = new FormData();
    form.append("kind", kind);
    form.append("schema_version", "v1");
    form.append("file", file);
    try {
      const result = await request<ImportBatch>("/imports/previews", {
        body: form,
      });
      setBatch(result);
      setPage(1);
      setReviewed(false);
    } catch (reason) {
      if (
        reason instanceof ApiError &&
        reason.status === 400 &&
        isBatch(reason.payload)
      ) {
        setBatch(reason.payload);
        setPage(1);
        setReviewed(false);
      } else setError(reason);
    } finally {
      setBusy(false);
    }
  }

  async function act(next: "confirm" | "apply" | "cancel") {
    if (!batch) return;
    setBusy(true);
    setAction(next);
    setError(null);
    setMessage("");
    try {
      const result = await request<ImportBatch>(
        `/imports/${batch.batch_id}/${next}`,
        {
          body: next === "cancel" ? {} : { content_hash: batch.content_hash },
        },
      );
      setBatch(result);
      if (next === "cancel" || next === "apply") setRows(emptyRows);
      if (next === "confirm")
        setMessage("Vista previa confirmada. Falta la confirmación final.");
      if (next === "apply") setMessage("Importación aplicada correctamente.");
      if (next === "cancel") setMessage("Lote descartado. No se creó ningún registro.");
    } catch (reason) {
      setError(reason);
    } finally {
      setBusy(false);
      setAction(null);
    }
  }

  const total = batch?.summary.valid_rows ?? 0;
  return (
    <>
      <div className="page-heading import-heading">
        <div>
          <span className="eyebrow">IMPORTACIÓN CSV</span>
          <h1>Carga masiva, con control.</h1>
          <p>
            Valida el archivo completo antes de crear registros. Nada se guarda
            en el inventario hasta la confirmación final.
          </p>
        </div>
      </div>
      {message && (
        <div className="notice" role="status">
          {message}
          <button onClick={() => setMessage("")} aria-label="Ocultar mensaje">
            ×
          </button>
        </div>
      )}
      {error != null && <ErrorNotice error={error} />}

      {!batch ? (
        <section className="panel import-panel">
          <div className="section-heading">
            <div>
              <h2>Preparar importación</h2>
              <span className="muted">Máximo 5 MiB y 1.000 filas</span>
            </div>
            <a
              className="button-link"
              href={`/api/imports/templates/${kind}/`}
              download
            >
              Descargar plantilla
            </a>
          </div>
          <div className="kind-switch" role="tablist" aria-label="Tipo de importación">
            <button
              type="button"
              role="tab"
              aria-selected={kind === "assets"}
              className={kind === "assets" ? "active" : ""}
              onClick={() => reset("assets")}
            >
              Activos
            </button>
            <button
              type="button"
              role="tab"
              aria-selected={kind === "license_lots"}
              className={kind === "license_lots" ? "active" : ""}
              onClick={() => reset("license_lots")}
            >
              Lotes de licencias
            </button>
          </div>
          <form className="import-form" onSubmit={upload}>
            <label className="file-field">
              Archivo CSV
              <input
                ref={input}
                type="file"
                accept=".csv,text/csv"
                onChange={(event) => {
                  setFile(event.target.files?.[0] ?? null);
                  setError(null);
                }}
              />
              <small>
                Usa la plantilla «{kind === "assets" ? "assets-v1" : "license-lots-v1"}»
                y conserva las cabeceras.
              </small>
            </label>
            {file && (
              <p className="file-name">
                {file.name} · {(file.size / 1024).toFixed(1)} KiB
              </p>
            )}
            <button className="primary" disabled={busy || !file}>
              {busy ? "Validando…" : "Validar archivo"}
            </button>
          </form>
        </section>
      ) : (
        <>
          <section className="panel import-panel">
            <div className="section-heading">
              <div>
                <h2>
                  {batch.state === "INVALID"
                    ? "El archivo necesita correcciones"
                    : batch.state === "APPLIED"
                      ? "Importación aplicada"
                      : "Vista previa del lote"}
                </h2>
                <span className="muted">
                  {batch.kind === "assets" ? "Activos" : "Lotes de licencias"} ·{" "}
                  {batch.schema_version} · {batch.batch_id.slice(0, 8)}
                </span>
              </div>
              <button onClick={() => reset()}>Elegir otro archivo</button>
            </div>
            {batch.state !== "APPLIED" && (
              <>
                <Summary batch={batch} />
                {batch.state !== "INVALID" && (
                  <p className="import-warning">
                    Se crearán <strong>{total}</strong>{" "}
                    {batch.kind === "assets" ? "activos" : "lotes de licencias"} en
                    una sola operación. Revisa todas las filas antes de continuar.
                  </p>
                )}
              </>
            )}
            {batch.errors.length > 0 && (
              <>
                <ErrorList errors={batch.errors} />
                <div className="import-actions">
                  <button
                    className="button-link"
                    onClick={() => downloadErrors(batch)}
                  >
                    Descargar errores CSV
                  </button>
                </div>
              </>
            )}
            {(batch.state === "PREVIEW_READY" ||
              batch.state === "CONFIRMED_ONCE") && (
              <p className="hint">
                Vista previa válida hasta{" "}
                {new Date(batch.expires_at).toLocaleString()}.
              </p>
            )}
            {batch.state === "EXPIRED" && (
              <p className="error">
                La vista previa venció. Vuelve a cargar el archivo para revisarlo.
              </p>
            )}
            {batch.state === "CANCELLED" && (
              <p className="empty">Este lote fue descartado y no creó registros.</p>
            )}
            {batch.state === "APPLIED" && (
              <div className="import-result">
                <p>
                  Se crearon <strong>{batch.summary.valid_rows ?? 0}</strong>{" "}
                  {batch.kind === "assets" ? "activos" : "lotes"} el{" "}
                  {batch.applied_at
                    ? new Date(batch.applied_at).toLocaleString()
                    : "ahora"}
                  . El resultado queda asociado al lote{" "}
                  <span className="code">{batch.batch_id}</span>.
                </p>
                {batch.applied_result && (
                  <pre>{JSON.stringify(batch.applied_result, null, 2)}</pre>
                )}
              </div>
            )}
            {(batch.state === "PREVIEW_READY" ||
              batch.state === "CONFIRMED_ONCE") && (
              <div className="import-actions">
                {batch.state === "PREVIEW_READY" ? (
                  <>
                    <label className="check">
                      <input
                        type="checkbox"
                        checked={reviewed}
                        onChange={(event) => setReviewed(event.target.checked)}
                      />
                      Revisé todas las filas y el resumen.
                    </label>
                    <button
                      className="primary"
                      disabled={busy || !reviewed}
                      onClick={() => act("confirm")}
                    >
                      {action === "confirm"
                        ? "Confirmando…"
                        : "Confirmar vista previa"}
                    </button>
                  </>
                ) : (
                  <div className="final-confirmation">
                    <div>
                      <h3>Confirmación final</h3>
                      <p>
                        Se crearán {total}{" "}
                        {batch.kind === "assets" ? "activos" : "lotes"} al aplicar.
                        Esta acción no se puede deshacer.
                      </p>
                    </div>
                    <button
                      className="primary"
                      disabled={busy}
                      onClick={() => act("apply")}
                    >
                      {action === "apply"
                        ? "Aplicando…"
                        : `Crear ${total} ${
                            batch.kind === "assets" ? "activos" : "lotes"
                          }`}
                    </button>
                  </div>
                )}
                <button
                  className="danger-link"
                  disabled={busy}
                  onClick={() => act("cancel")}
                >
                  {action === "cancel" ? "Descartando…" : "Descartar lote"}
                </button>
              </div>
            )}
          </section>
          {canShowRows(batch.state) && (
            <RowsTable
              kind={batch.kind}
              rows={rows}
              page={page}
              loading={rowsLoading}
              onPage={setPage}
            />
          )}
        </>
      )}
      <footer>
        Universidad Nacional de Loja{" "}
        <span>Inventario de tecnologías de información · Grupo 5</span>
      </footer>
    </>
  );
}
