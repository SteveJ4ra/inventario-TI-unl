import { useEffect, useState } from "react";
import { ApiError, request } from "./api";
import type {
  Action,
  Asset,
  Body,
  Custodian,
  Fields,
  Movement,
  Options,
  Page,
  User,
} from "./types";
import { Form, Field, ErrorNotice } from "./components/Form";
import { AssetForm, CustodianForm } from "./components/Registration";
import { AssetFacts, Badge, Filters, Inventory } from "./components/Inventory";
import { Movements } from "./components/Movements";
import { History } from "./components/History";
import { ImportPanel } from "./components/Import";
const emptyOptions: Options = {
  categories: [],
  conditions: [],
  assignments: [],
  locations: [],
};
const aborted = (e: unknown) =>
  e instanceof DOMException && e.name === "AbortError";

export default function App() {
  const [user, setUser] = useState<User | null>(null);
  const [checking, setChecking] = useState(true);
  const [error, setError] = useState<unknown>(null);
  useEffect(() => {
    const controller = new AbortController();
    const clear = () => setUser(null);
    window.addEventListener("session-expired", clear);
    request<User>("/auth/me/", { signal: controller.signal })
      .then(setUser)
      .catch((e) => {
        if (!aborted(e) && !(e instanceof ApiError && e.status === 403))
          setError(e);
      })
      .finally(() => setChecking(false));
    return () => {
      controller.abort();
      window.removeEventListener("session-expired", clear);
    };
  }, []);
  if (checking)
    return (
      <main className="startup" role="status">
        Preparando el inventario…
      </main>
    );
  if (!user)
    return (
      <main className="login">
        <section className="login-story">
          <div className="brand">
            <span className="brand-icon">TI</span>
            <div>
              UNL <small>Inventario de tecnología</small>
            </div>
          </div>
          <div>
            <span className="eyebrow">CADA ACTIVO, EN SU LUGAR</span>
            <h1>
              Tu inventario,
              <br />
              <em>al día.</em>
            </h1>
            <p>
              Registra equipos, conoce quién los tiene y conserva el recorrido
              de cada entrega.
            </p>
            <div className="login-art" aria-hidden="true">
              <div className="screen-shape">
                <span />
                <span />
                <span />
              </div>
              <div className="asset-card">
                TI-000001 <i>✓</i>
              </div>
            </div>
          </div>
          <small>Universidad Nacional de Loja · Grupo 5</small>
        </section>
        <section className="login-form">
          <div>
            <span className="eyebrow">ACCESO DE GESTORES</span>
            <h2>Bienvenido al inventario</h2>
            <p className="muted">Ingresa con tu cuenta autorizada.</p>
            {error != null && <ErrorNotice error={error} />}
            <Form
              submit="Ingresar"
              onSubmit={async (data) => {
                setError(null);
                const result = await request<User>("/auth/login/", {
                  body: data,
                });
                setUser(result);
              }}
            >
              <Field label="Usuario" name="username" maxLength={150} />
              <Field
                label="Contraseña"
                name="password"
                type="password"
                maxLength={256}
              />
            </Form>
          </div>
        </section>
      </main>
    );
  return <Workspace user={user} onExit={() => setUser(null)} />;
}

function Workspace({ user, onExit }: { user: User; onExit: () => void }) {
  const [options, setOptions] = useState(emptyOptions);
  const [people, setPeople] = useState<Custodian[]>([]);
  const [page, setPage] = useState<Page | null>(null);
  const [query, setQuery] = useState<Fields>({});
  const [pageNumber, setPageNumber] = useState(1);
  const [refresh, setRefresh] = useState(0);
  const [selected, setSelected] = useState<number | null>(null);
  const [asset, setAsset] = useState<Asset | null>(null);
  const [events, setEvents] = useState<Movement[]>([]);
  const [detailLoading, setDetailLoading] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<unknown>(null);
  const [message, setMessage] = useState("");
  const [modal, setModal] = useState<"asset" | "person" | null>(null);
  const [importOpen, setImportOpen] = useState(false);
  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    const params = new URLSearchParams({ ...query, page: String(pageNumber) });
    Promise.all([
      request<Page>("/assets/?" + params, { signal: controller.signal }),
      request<Options>("/options/", { signal: controller.signal }),
      request<Custodian[]>("/custodians/", { signal: controller.signal }),
    ])
      .then(([list, opts, persons]) => {
        setPage(list);
        setOptions(opts);
        setPeople(persons);
      })
      .catch((e) => {
        if (!aborted(e)) {
          setError(e);
          setPage(null);
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [query, pageNumber, refresh]);
  useEffect(() => {
    if (selected === null) {
      setAsset(null);
      setEvents([]);
      setDetailLoading(false);
      return;
    }
    const controller = new AbortController();
    setDetailLoading(true);
    setAsset(null);
    Promise.all([
      request<Asset>(`/assets/${selected}/`, { signal: controller.signal }),
      request<Movement[]>(`/assets/${selected}/movements/`, {
        signal: controller.signal,
      }),
    ])
      .then(([value, history]) => {
        setAsset(value);
        setEvents(history);
      })
      .catch((e) => {
        if (!aborted(e)) setError(e);
      })
      .finally(() => {
        if (!controller.signal.aborted) setDetailLoading(false);
      });
    return () => controller.abort();
  }, [selected, refresh]);
  async function operation(action: Action, body: Body) {
    if (!asset) return;
    setError(null);
    setMessage("");
    try {
      await request(`/assets/${asset.id}/${action}/`, { body });
      setMessage(
        "Movimiento registrado. La ficha y el historial están actualizados.",
      );
      setRefresh((n) => n + 1);
    } catch (e) {
      if (e instanceof ApiError && e.status === 409) {
        setError(e);
        setRefresh((n) => n + 1);
      } else throw e;
    }
  }
  return (
    <div className="workspace">
      <aside className="sidebar">
        <div className="brand">
          <span className="brand-icon">TI</span>
          <div>
            UNL<small>Inventario tecnológico</small>
          </div>
        </div>
        <span className="nav-label">ESPACIO DE TRABAJO</span>
        <button
          className="nav-active"
          onClick={() => {
            setSelected(null);
            setModal(null);
            setImportOpen(false);
          }}
        >
          ▦ <span>Inventario</span>
        </button>
        <div className="sidebar-bottom">
          <span className="avatar">
            {user.username.slice(0, 2).toUpperCase()}
          </span>
          <div>
            <strong>{user.username}</strong>
            <small>Gestor autorizado</small>
          </div>
        </div>
      </aside>
      <div className="main-area">
        <header className="topbar">
          <span>
            Gestión de activos <span className="separator">/</span> Inventario
            TI
          </span>
          <button
            onClick={async () => {
              try {
                await request("/auth/logout/", { body: {} });
                onExit();
              } catch (e) {
                setError(e);
              }
            }}
          >
            Cerrar sesión ↗
          </button>
        </header>
        <main className="content">
          <div className="page-heading">
            <div>
              <span className="eyebrow">INVENTARIO TI</span>
              <h1>Equipos bajo control.</h1>
              <p>Consulta su estado, ubicación y custodia en un solo lugar.</p>
            </div>
            <div className="heading-actions">
              <button
                onClick={() => {
                  setImportOpen(true);
                  setSelected(null);
                  setModal(null);
                  setError(null);
                  setMessage("");
                }}
              >
                Importar CSV
              </button>
              <button onClick={() => setModal("person")}>Nuevo custodio</button>
              <button className="primary" onClick={() => setModal("asset")}>
                ＋ Registrar activo
              </button>
            </div>
          </div>
          {message && (
            <div className="notice" role="status">
              ✓ {message}
              <button
                onClick={() => setMessage("")}
                aria-label="Ocultar mensaje"
              >
                ×
              </button>
            </div>
          )}
          {error != null && <ErrorNotice error={error} />}
          {modal && (
            <section className="panel registration">
              <div className="section-heading">
                <h2>
                  {modal === "asset"
                    ? "Registrar activo"
                    : "Registrar custodio"}
                </h2>
                <button onClick={() => setModal(null)}>Cerrar</button>
              </div>
              {modal === "asset" ? (
                <AssetForm
                  options={options}
                  onSubmit={async (data) => {
                    const created = await request<Asset>("/assets/", {
                      body: data,
                    });
                    setSelected(created.id);
                    setModal(null);
                    setRefresh((n) => n + 1);
                    setMessage(
                      "Activo registrado con código " + created.code + ".",
                    );
                  }}
                />
              ) : (
                <CustodianForm
                  onSubmit={async (data) => {
                    await request("/custodians/", { body: data });
                    setModal(null);
                    setRefresh((n) => n + 1);
                    setMessage(
                      "Custodio registrado. Ya puedes seleccionarlo al entregar un activo.",
                    );
                  }}
                />
              )}
            </section>
          )}
          {importOpen ? (
            <section className="panel">
              <ImportPanel
                onClose={() => {
                  setImportOpen(false);
                  setRefresh((n) => n + 1);
                }}
                onApplied={() => setRefresh((n) => n + 1)}
              />
            </section>
          ) : selected === null ? (
            <>
              <section className="panel filter-panel">
                <div className="section-heading">
                  <h2>Encuentra un activo</h2>
                  <span className="muted">Búsqueda y filtros</span>
                </div>
                <Filters
                  options={options}
                  people={people}
                  onApply={(data) => {
                    setQuery(data);
                    setPageNumber(1);
                  }}
                />
              </section>
              <Inventory
                page={page}
                loading={loading}
                pageNumber={pageNumber}
                onPage={setPageNumber}
                onSelect={(id) => {
                  setError(null);
                  setMessage("");
                  setSelected(id);
                }}
              />
            </>
          ) : (
            <section className="panel detail">
              <button
                className="back"
                onClick={() => {
                  setSelected(null);
                  setError(null);
                }}
              >
                ← Volver al inventario
              </button>
              {detailLoading ? (
                <p className="empty" role="status">
                  Cargando ficha…
                </p>
              ) : asset ? (
                <>
                  <div className="detail-heading">
                    <div>
                      <span className="code">{asset.code}</span>
                      <h2>{asset.name}</h2>
                      <p>{asset.description}</p>
                    </div>
                    <div className="badges">
                      <Badge value={asset.condition} />
                      <Badge value={asset.assignment} />
                    </div>
                  </div>
                  <AssetFacts asset={asset} />
                  <Movements
                    key={`${asset.id}-${asset.revision}`}
                    asset={asset}
                    people={people}
                    options={options}
                    onSubmit={operation}
                  />
                  <History events={events} />
                </>
              ) : (
                <p className="empty">
                  No fue posible cargar la ficha. Revisa el mensaje o vuelve al
                  listado.
                </p>
              )}
            </section>
          )}
          <footer>
            Universidad Nacional de Loja{" "}
            <span>Inventario de tecnologías de información · Grupo 5</span>
          </footer>
        </main>
      </div>
    </div>
  );
}
