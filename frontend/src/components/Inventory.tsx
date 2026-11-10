import type { Asset, Custodian, Fields, Options, Page } from "../types";
import { labels } from "../types";
export function Badge({ value }: { value: string }) {
  return <span className={"tag " + value}>{labels[value] || value}</span>;
}
export function AssetStatusBadge({ asset }: { asset: Asset }) {
  const value = asset.lifecycle_status !== "localizado" ? asset.lifecycle_status
    : asset.active_maintenance_id != null ? "in_progress"
    : asset.assignment ?? "localizado";
  return <Badge value={value} />;
}
export function Filters({
  options,
  onApply,
}: {
  options: Options;
  people: Custodian[];
  onApply: (data: Fields) => void;
}) {
  return (
    <form
      className="filters"
      onReset={() => onApply({})}
      onSubmit={(e) => {
        e.preventDefault();
        const result: Fields = {};
        new FormData(e.currentTarget).forEach((v, k) => {
          if (String(v).trim()) result[k] = String(v).trim();
        });
        onApply(result);
      }}
    >
      <label className="search">
        Buscar activos
        <input
          name="search"
          placeholder="Código, nombre, serie o custodio…"
          maxLength={240}
        />
      </label>
      <div className="filter-grid">
        {(
          [
            ["Categoría", "category", options.categories],
            ["Condición", "condition", options.conditions],
            ["Situación", "situation", [
              { value: "disponible", label: "Disponible" },
              { value: "asignado", label: "Asignado" },
              { value: "no_localizado", label: "No localizado" },
              { value: "baja", label: "Baja" },
            ]],
          ] as const
        ).map(([label, name, choices]) => (
          <label key={name}>
            {label}
            <select name={name} defaultValue="">
              <option value="">Todas</option>
              {choices.map((c) => (
                <option key={c.value} value={c.value}>
                  {c.label}
                </option>
              ))}
            </select>
          </label>
        ))}
      </div>
      <div className="filter-actions">
        <button className="primary">Aplicar</button>
        <button type="reset">Limpiar</button>
        <span>Se cumplen todos los criterios seleccionados.</span>
      </div>
    </form>
  );
}
export function Inventory({
  page,
  loading,
  onSelect,
  onPage,
  pageNumber,
}: {
  page: Page | null;
  loading: boolean;
  onSelect: (id: number) => void;
  onPage: (n: number) => void;
  pageNumber: number;
}) {
  return (
    <section className="panel inventory-list">
      <div className="section-heading">
        <h2>Activos registrados</h2>
        <span className="muted">{page?.count ?? 0} encontrados</span>
      </div>
      {loading ? (
        <p role="status" className="empty">
          Cargando activos…
        </p>
      ) : !page?.results.length ? (
        <div className="empty">
          <strong>No hay activos que mostrar</strong>
          <p>Registra un activo o revisa los criterios de búsqueda.</p>
        </div>
      ) : (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Activo</th>
                <th>Categoría</th>
                <th>Condición</th>
                <th>Asignación</th>
                <th>Ubicación</th>
                <th>
                  <span className="sr-only">Consultar</span>
                </th>
              </tr>
            </thead>
            <tbody>
              {page.results.map((asset) => (
                <tr key={asset.id}>
                  <td>
                    <strong>{asset.name}</strong>
                    <small className="code">{asset.code}</small>
                  </td>
                  <td>{labels[asset.category]}</td>
                  <td>
                    <Badge value={asset.condition} />
                  </td>
                  <td>
                    <AssetStatusBadge asset={asset} />
                  </td>
                  <td>{asset.location}</td>
                  <td>
                    <button
                      onClick={() => onSelect(asset.id)}
                      aria-label={"Ver ficha de " + asset.code}
                    >
                      Ver ficha ↗
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {page && (page.next || page.previous) && (
        <div className="pagination">
          <button
            disabled={!page.previous || loading}
            onClick={() => onPage(pageNumber - 1)}
          >
            Anterior
          </button>
          <span>Página {pageNumber}</span>
          <button
            disabled={!page.next || loading}
            onClick={() => onPage(pageNumber + 1)}
          >
            Siguiente
          </button>
        </div>
      )}
    </section>
  );
}
export function AssetFacts({ asset }: { asset: Asset }) {
  const custody = asset.lifecycle_status === "no_localizado"
    ? [
        ["Último estado conocido", labels[asset.last_lifecycle_status ?? ""] || "—"],
        ["Última asignación conocida", labels[asset.last_assignment ?? ""] || "—"],
        ["Última condición conocida", labels[asset.last_condition ?? ""] || "—"],
        ["Última ubicación conocida", asset.last_location ?? "—"],
        ["Último custodio conocido", asset.last_custodian?.full_name ?? "Sin custodio"],
      ]
    : [
        ["Ubicación actual", asset.location],
        ["Custodio actual", asset.current_custodian?.full_name || "Sin custodio"],
        ["Correo del custodio", asset.current_custodian?.email || "—"],
      ];
  return (
    <dl className="facts">
      {[
        ["Categoría", labels[asset.category]],
        ["Marca", asset.brand],
        ["Modelo", asset.model],
        ["Número de serie", asset.serial_number],
        ...custody,
        ["Registrado por", asset.created_by.username],
        ...(asset.acquisition?.source === "PURCHASE" ? [
          ["Factura de compra", asset.acquisition.reference],
          ["Identificador del documento", String(asset.acquisition.document_id)],
          ["Total compartido de factura", asset.acquisition.currency + " " + asset.acquisition.invoice_total],
          ["Valor individual", asset.acquisition.currency + " " + asset.acquisition.item_value],
          ["Fecha de adquisición", asset.acquisition.acquired_on || "Desconocida: " + asset.acquisition.date_unknown_reason],
        ] : asset.acquisition?.source === "DONATION" ? [
          ["Respaldo de donación", asset.acquisition.reference],
          ["Tipo de respaldo", asset.acquisition.support_type],
          ["Identificador del documento", String(asset.acquisition.document_id)],
          ["Valor estimado individual", asset.acquisition.currency + " " + asset.acquisition.item_value],
          ["Fecha de adquisición", asset.acquisition.acquired_on || "Desconocida: " + asset.acquisition.date_unknown_reason],
        ] : []),
      ].map(([key, value]) => (
        <div key={key}>
          <dt>{key}</dt>
          <dd>{value}</dd>
        </div>
      ))}
    </dl>
  );
}
