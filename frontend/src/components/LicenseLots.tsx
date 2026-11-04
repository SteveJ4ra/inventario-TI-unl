import { useEffect, useState } from "react";
import { request } from "../api";
import type { Fields, LicenseLot, LicensePage } from "../types";
import { ErrorNotice } from "./Form";
import { LicenseLotDetail } from "./LicenseLotDetail";
import { isAborted, licenseModels, licenseStatuses, LicenseLotForm, LicensePagination, LicenseStatusBadge } from "./LicenseLotForm";

export function LicenseLots() {
  const [query, setQuery] = useState<Fields>({});
  const [number, setNumber] = useState(1);
  const [refresh, setRefresh] = useState(0);
  const [page, setPage] = useState<LicensePage<LicenseLot> | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<unknown>(null);
  const [creating, setCreating] = useState(false);
  const [selected, setSelected] = useState<number | null>(null);
  const [message, setMessage] = useState("");
  useEffect(() => {
    if (selected !== null) return;
    const controller = new AbortController();
    setLoading(true);
    setError(null);
    setPage(null);
    request<LicensePage<LicenseLot>>("/license-lots/?" + new URLSearchParams({ ...query, page: String(number) }), { signal: controller.signal })
      .then(setPage)
      .catch(e => { if (!isAborted(e)) setError(e); })
      .finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [query, number, refresh, selected]);
  return <>
    <div className="page-heading">
      <div><span className="eyebrow">LICENCIAS DE SOFTWARE</span><h1>Lotes de licencias</h1>
        <p>Consulta cantidades, vigencia y cambios de cada lote.</p></div>
      {selected === null && <button className="primary" onClick={() => { setCreating(true); setMessage(""); }}>＋ Registrar lote</button>}
    </div>
    {message && <p className="notice" role="status">{message}</p>}
    {selected !== null ? <LicenseLotDetail lotId={selected} onBack={() => { setSelected(null); setMessage(""); }} /> : <>
      {creating && <section className="panel registration">
        <div className="section-heading"><h2>Registrar lote de licencias</h2><button onClick={() => setCreating(false)}>Cancelar</button></div>
        <LicenseLotForm onSubmit={async body => {
          const created = await request<LicenseLot>("/license-lots/", { body });
          setCreating(false); setSelected(created.id); setMessage("Lote registrado correctamente.");
        }} />
      </section>}
      <section className="panel filter-panel">
        <h2>Encuentra un lote</h2>
        <form className="filters" onReset={() => { setQuery({}); setNumber(1); }} onSubmit={e => {
          e.preventDefault(); const values: Fields = {};
          new FormData(e.currentTarget).forEach((value, key) => { if (String(value).trim()) values[key] = String(value).trim(); });
          setQuery(values); setNumber(1); setMessage("");
        }}>
          <label className="search">Buscar lotes<input name="search" maxLength={240} placeholder="Producto o proveedor…" /></label>
          <div className="form-grid">
            <label>Filtrar modalidad<select name="license_model"><option value="">Todas</option>{Object.entries(licenseModels).map(([value, label]) => <option value={value} key={value}>{label}</option>)}</select></label>
            <label>Filtrar estado<select name="temporal_status"><option value="">Todos</option>{Object.entries(licenseStatuses).map(([value, label]) => <option value={value} key={value}>{label}</option>)}</select></label>
          </div>
          <div className="filter-actions"><button className="primary">Aplicar</button><button type="reset">Limpiar</button></div>
        </form>
      </section>
      {error != null && <><ErrorNotice error={error} /><button onClick={() => setRefresh(n => n + 1)}>Volver a consultar lotes</button></>}
      <section className="panel inventory-list">
        <div className="section-heading"><h2>Lotes registrados</h2>{page && <span>{page.count} encontrados</span>}</div>
        {loading ? <p role="status" className="empty">Cargando lotes…</p> : error != null ? <p className="empty">No se pudo cargar el listado.</p> : !page?.results.length ? <p className="empty">No hay lotes que mostrar. Registra uno o revisa los filtros.</p> : <>
          <div className="table-wrap"><table><thead><tr>
            <th>Producto / proveedor</th><th>Modalidad</th><th>Compradas</th><th>En uso</th><th>Remanentes</th><th>Vigencia / estado</th><th>Detalle</th>
          </tr></thead><tbody>{page.results.map(lot => <tr key={lot.id}>
            <td><strong>{lot.product_name}</strong><small>{lot.vendor}</small></td>
            <td>{licenseModels[lot.license_model]}</td><td>{lot.purchased_quantity}</td><td>{lot.in_use_quantity}</td><td>{lot.remaining_quantity}</td>
            <td><small>{lot.starts_on} — {lot.ends_on ?? "Sin fecha de fin"}</small><LicenseStatusBadge status={lot.temporal_status} /></td>
            <td><button aria-label={`Ver lote ${lot.product_name}`} onClick={() => { setSelected(lot.id); setMessage(""); }}>Ver lote ↗</button></td>
          </tr>)}</tbody></table></div>
          <p className="muted">Los remanentes son un conteo; en lotes vencidos no representan puestos utilizables.</p>
          <LicensePagination page={page} number={number} onPage={setNumber} label="Páginas de lotes" />
        </>}
      </section>
    </>}
  </>;
}
