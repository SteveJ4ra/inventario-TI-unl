import { CustodianEditor } from "./components/CustodianEditForm";
import { AssetEditForm } from "./components/AssetEditForm";
import { FacultyManagement } from "./components/FacultyManagement";
import { useEffect, useState } from "react";
import { ApiError, request } from "./api";
import type {
  Action,
  Asset,
  Body,
  Custodian,
  Fields,
  HistoryEntry,
  Incident,
  Maintenance,
  Options,
  Page,
  SessionUser,
  AcquisitionDocument,
} from "./types";
import { Form, Field, ErrorNotice } from "./components/Form";
import { CustodianForm } from "./components/Registration";
import { AssetFacts, AssetStatusBadge, Badge, Filters, Inventory } from "./components/Inventory";
import { Movements } from "./components/Movements";
import { History } from "./components/History";
import { IncidentPanel } from "./components/IncidentPanel";
import { MaintenancePanel } from "./components/MaintenancePanel";
import { LicenseLots } from "./components/LicenseLots";
import { ImportPanel } from "./components/Import";
import { AcquisitionForm } from "./components/AcquisitionForm";
const emptyOptions: Options = {
  categories: [],
  conditions: [],
  assignments: [],
  locations: [],
};
const aborted = (e: unknown) =>
  e instanceof DOMException && e.name === "AbortError";

// Solo se conserva una ruta interna; nunca se acepta una URL de retorno externa.
function isQrAssetRoute(): boolean {
  const path = window.location.pathname;
  return path === "/assets/code" || path.startsWith("/assets/code/");
}

function getQrAssetCode(): string | null {
  const path = window.location.pathname;

  const match = /^\/assets\/code\/([^/]+)\/?$/.exec(path);

  if (!match) {
    return null;
  }

  try {
    const code = decodeURIComponent(match[1]);

    if (!/^TI-[0-9]+$/.test(code)) {
      return null;
    }

    return code;
  } catch {
    return null;
  }
}

export default function App() {
  const [user, setUser] = useState<SessionUser | null>(null);
  const [checking, setChecking] = useState(true);
  const [error, setError] = useState<unknown>(null);
  useEffect(() => {
    const controller = new AbortController();
    const clear = () => setUser(null);
    window.addEventListener("session-expired", clear);
    request<SessionUser>("/auth/me/", { signal: controller.signal })
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
            <span className="eyebrow">ACCESO AUTORIZADO</span>
            <h2>Bienvenido al inventario</h2>
            <p className="muted">Ingresa con tu cuenta autorizada.</p>
            {error != null && <ErrorNotice error={error} />}
            <Form
              submit="Ingresar"
              onSubmit={async (data) => {
                setError(null);
                const result = await request<SessionUser>("/auth/login/", {
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
  if (user.permissions?.includes("faculties.manage") && !user.permissions?.includes("inventory.manage"))
    return <FacultyManagement key={user.id} onExit={() => setUser(null)} />;
  if (!user.permissions?.includes("inventory.manage")) return <main className="login">
    <section className="panel">
      <h1>Acceso restringido</h1>
      <p>Tu cuenta no tiene acceso al inventario de Gestores.</p>
      <Form submit="Cerrar sesión" onSubmit={async () => { await request("/auth/logout/", { body: {} }); setUser(null); }}>
        <p>Sesión de {user.username}</p>
      </Form>
    </section>
  </main>;
  return <Workspace key={user.id} user={user} onExit={() => setUser(null)} />;
}

function Workspace({ user, onExit }: { user: SessionUser; onExit: () => void }) {
  const [adminOpen, setAdminOpen] = useState(false);
  const [section, setSection] = useState<"assets" | "licenses">("assets");
  const [options, setOptions] = useState(emptyOptions);
  const [people, setPeople] = useState<Custodian[]>([]);
  const [page, setPage] = useState<Page | null>(null);
  const [query, setQuery] = useState<Fields>({});
  const [pageNumber, setPageNumber] = useState(1);
  const [refresh, setRefresh] = useState(0);
  const [selected, setSelected] = useState<number | null>(null);
  const [asset, setAsset] = useState<Asset | null>(null);
  const [editing, setEditing] = useState(false);
  const [events, setEvents] = useState<HistoryEntry[]>([]);
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [maintenance, setMaintenance] = useState<Maintenance | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<unknown>(null);
  const [message, setMessage] = useState("");
  const [modal, setModal] = useState<"asset" | "donation" | "person" | "custodian-edit" | null>(null);
  const [custodianOpened, setCustodianOpened] = useState(false);
  const [importOpen, setImportOpen] = useState(false);
  const [purchaseDocument, setPurchaseDocument] = useState<AcquisitionDocument | null>(null);
  const [donationDocument, setDonationDocument] = useState<AcquisitionDocument | null>(null);
  const [donationOpened, setDonationOpened] = useState(false);
  const [purchaseOpened, setPurchaseOpened] = useState(false);
  // El enlace del QR se conserva en la barra de direcciones durante el login.
  // Workspace se monta tras iniciar sesión y resuelve entonces el código TI.
  const [qrStatus, setQrStatus] = useState<
    "normal" | "loading" | "not-found" | "denied" | "error"
  >(isQrAssetRoute() ? "loading" : "normal");

  useEffect(() => {
    if (!isQrAssetRoute()) return;

    const code = getQrAssetCode();
    if (!code) {
      setQrStatus("not-found");
      return;
    }

    const controller = new AbortController();
    request<Asset>(`/assets/by-code/${encodeURIComponent(code)}/`, {
      signal: controller.signal,
    })
      .then((result) => {
        if (controller.signal.aborted) return;
        setModal(null);
        setImportOpen(false);
        setSelected(result.id);
        setQrStatus("normal");
      })
      .catch((e: unknown) => {
        if (controller.signal.aborted || aborted(e)) return;
        if (e instanceof ApiError && e.status === 403) {
          setQrStatus("denied");
        } else if (e instanceof ApiError && e.status === 404) {
          setQrStatus("not-found");
        } else {
          setQrStatus("error");
        }
      });

    return () => controller.abort();
  }, []);

  function clearQrRoute() {
    if (isQrAssetRoute()) {
      window.history.replaceState(null, "", "/");
    }
    setQrStatus("normal");
  }

  function goToInventory() {
    clearQrRoute();
    setSelected(null);
    setModal(null);
    setImportOpen(false);
    setError(null);
    setMessage("");
  }

  useEffect(() => {
    const controller = new AbortController();
    if (section !== "assets") return;
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
  }, [query, pageNumber, refresh, section]);
  useEffect(() => setEditing(false), [selected, refresh]);
  useEffect(() => {
    if (selected === null) {
      setAsset(null);
      setEvents([]);
      setIncidents([]);
      setMaintenance(null);
      setDetailLoading(false);
      return;
    }
    const controller = new AbortController();
    setDetailLoading(true);
    setAsset(null);
    Promise.all([
      request<Asset>(`/assets/${selected}/`, { signal: controller.signal }),
      request<HistoryEntry[]>(`/assets/${selected}/history/`, {
        signal: controller.signal,
      }),
      request<Incident[]>(`/assets/${selected}/incidents/`, {
        signal: controller.signal,
      }),
    ])
      .then(async ([value, history, reports]) => {
        if (controller.signal.aborted) return;
        const active = value.active_maintenance_id == null ? null
          : await request<Maintenance>(`/maintenance/${value.active_maintenance_id}/`, {
            signal: controller.signal,
          });
        if (controller.signal.aborted) return;
        setAsset(value);
        setEvents(history);
        setIncidents(reports);
        setMaintenance(active);
      })
      .catch((e) => {
        if (!aborted(e)) setError(e);
      })
      .finally(() => {
        if (!controller.signal.aborted) setDetailLoading(false);
      });
    return () => controller.abort();
  }, [selected, refresh]);
  async function writeToAsset(path: string, body: Body, successMessage: string) {
    setError(null);
    setMessage("");
    try {
      await request(path, { body });
      setMessage(successMessage);
      setRefresh((n) => n + 1);
    } catch (e) {
      if (e instanceof ApiError && e.status === 409) {
        setError(e);
        setRefresh((n) => n + 1);
      } else throw e;
    }
  }
  async function operation(action: Action, body: Body) {
    if (!asset) return;
    await writeToAsset(
      `/assets/${asset.id}/${action}/`,
      body,
      "Movimiento registrado. La ficha y el historial están actualizados.",
    );
  }
  return (
    <><div hidden={adminOpen}><div className="workspace">
      <aside className="sidebar">
        <div className="brand">
          <span className="brand-icon">TI</span>
          <div>
            UNL<small>Inventario tecnológico</small>
          </div>
        </div>
        <span className="nav-label">ESPACIO DE TRABAJO</span>
        <button
          className={
            section === "assets" ? "workspace-nav nav-active" : "workspace-nav"
          }
          aria-pressed={section === "assets"}
          onClick={() => {
            setSection("assets");
            goToInventory();
          }}
        >
          ▦ <span>Inventario</span>
        </button>
        <button
          className={
            section === "licenses"
              ? "workspace-nav nav-active"
              : "workspace-nav"
          }
          aria-pressed={section === "licenses"}
          onClick={() => {
            setSection("licenses");
            setSelected(null);
            setModal(null);
            setImportOpen(false);
            setError(null);
            setMessage("");
          }}
        >
          ▤ <span>Licencias</span>
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
            {section === "licenses"
              ? "Gestión de licencias"
              : "Gestión de activos"}{" "}
            <span className="separator">/</span> Inventario TI
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
          {section === "licenses" ? <LicenseLots /> : <>
          <div className="page-heading">
            <div>
              <span className="eyebrow">INVENTARIO TI</span>
              <h1>Equipos bajo control.</h1>
              <p>Consulta su estado, ubicación y custodia en un solo lugar.</p>
            </div>
            <div className="heading-actions">
              <button
                onClick={() => {
                  goToInventory();
                  setImportOpen(true);
                }}
              >
                Importar CSV
              </button>
              {user.permissions.includes("faculties.manage") && <button onClick={() => setAdminOpen(true)}>Administrar facultades</button>}
              <button onClick={() => setModal("person")}>Nuevo custodio</button>
              <button onClick={() => { setCustodianOpened(true); setModal("custodian-edit"); }}>Editar custodios</button>
              <button onClick={() => { setDonationOpened(true); setModal("donation"); }}>Registrar donación</button>
              <button className="primary" onClick={() => { setPurchaseOpened(true); setModal("asset"); }}>
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
          {purchaseOpened && (
            <section className="panel registration purchase-panel" hidden={modal !== "asset"}>
              <div className="section-heading"><h2>Registrar activo por compra</h2>
                <button onClick={() => setModal(null)}>Cerrar</button></div>
              <AcquisitionForm options={options} document={purchaseDocument} onDocument={setPurchaseDocument} onDocumentChanged={() => setRefresh(n => n + 1)}
                onSelect={id => { setSelected(id); setError(null); }} onCreated={created => {
                  setSelected(created.id);
                  setRefresh(n => n + 1);
                  setMessage("Activo registrado con código " + created.code + " · Factura " + created.acquisition.reference + ".");
                }} />
            </section>
          )}
          {donationOpened && <section className="panel registration purchase-panel" hidden={modal !== "donation"}>
            <div className="section-heading"><h2>Registrar activo por donación</h2>
              <button onClick={() => setModal(null)}>Cerrar</button></div>
            <AcquisitionForm source="DONATION" options={options} document={donationDocument} onDocument={setDonationDocument} onDocumentChanged={() => setRefresh(n => n + 1)}
              onSelect={id => { setSelected(id); setError(null); }} onCreated={created => {
                setSelected(created.id); setRefresh(n => n + 1);
                setMessage("Activo registrado con código " + created.code + " · Respaldo " + created.acquisition.reference + ".");
              }} />
          </section>}
          {custodianOpened && <section className="panel registration purchase-panel" hidden={modal !== "custodian-edit"}>
            <div className="section-heading"><h2>Editar custodios</h2><button onClick={() => setModal(null)}>Cerrar</button></div>
            <CustodianEditor people={people} onReload={() => setRefresh(n => n + 1)} onSaved={person => {
              setPeople(rows => rows.map(row => row.id === person.id ? person : row)); setRefresh(n => n + 1);
              setMessage("Perfil de custodio actualizado.");
            }} />
          </section>}
          {modal === "person" && (
            <section className="panel registration">
              <div className="section-heading"><h2>Registrar custodio</h2>
                <button onClick={() => setModal(null)}>Cerrar</button></div>
              <CustodianForm onSubmit={async data => {
                await request("/custodians/", { body: data });
                setModal(null); setRefresh(n => n + 1);
                setMessage("Custodio registrado. Ya puedes seleccionarlo al entregar un activo.");
              }} />
            </section>
          )}
          {qrStatus === "loading" ? (
            <section className="panel">
              <p className="empty" role="status">
                Buscando el activo del código QR…
              </p>
            </section>
          ) : qrStatus === "not-found" ? (
            <section className="panel">
              <p className="empty" role="alert">
                No se encontró el activo solicitado.
              </p>
              <button type="button" onClick={goToInventory}>
                ← Volver al inventario
              </button>
            </section>
          ) : qrStatus === "denied" ? (
            <section className="panel">
              <p className="empty" role="alert">
                No tienes permiso para consultar este activo.
              </p>
              <button type="button" onClick={goToInventory}>
                ← Volver al inventario
              </button>
            </section>
          ) : qrStatus === "error" ? (
            <section className="panel">
              <p className="empty" role="alert">
                No fue posible consultar el activo. Comprueba la conexión.
              </p>
              <button type="button" onClick={goToInventory}>
                ← Volver al inventario
              </button>
            </section>
          ) : importOpen ? (
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
                onClick={goToInventory}
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
                      {asset.lifecycle_status === "localizado" && <Badge value={asset.condition} />}
                      <AssetStatusBadge asset={asset} />
                    </div>
                  </div>
                  <button
                    type="button"
                    onClick={async () => {
                      setError(null);
                      try {
                        const response = await fetch(
                          `/api/assets/${asset.id}/qr.svg`,
                          { credentials: "same-origin" },
                        );
                        if (!response.ok) {
                          if (response.status === 403) {
                            throw new Error(
                              "No tienes permisos para descargar este QR.",
                            );
                          }
                          if (response.status === 404) {
                            throw new Error("No se encontró el activo.");
                          }
                          throw new Error("No se pudo descargar el código QR.");
                        }
                        if (
                          !response.headers
                            .get("Content-Type")
                            ?.includes("image/svg+xml")
                        ) {
                          throw new Error(
                            "El servidor no devolvió un archivo SVG válido.",
                          );
                        }

                        const blob = await response.blob();
                        const url = URL.createObjectURL(blob);
                        const link = document.createElement("a");
                        link.href = url;
                        link.download = `${asset.code.replace(/[^A-Za-z0-9_-]/g, "_")}.svg`;
                        document.body.appendChild(link);
                        link.click();
                        link.remove();
                        window.setTimeout(() => URL.revokeObjectURL(url), 1000);
                      } catch (e) {
                        setError(e);
                      }
                    }}
                  >
                    ↓ Descargar QR (SVG)
                  </button>
                  <AssetFacts asset={asset} />
                <button onClick={() => setEditing(value => !value)}>Editar ficha</button>
                <button onClick={() => setRefresh(n => n + 1)}>Recargar ficha</button>
                {editing && <AssetEditForm key={asset.id + ":" + asset.revision} asset={asset} options={options} onSaved={updated => {
                  setAsset(updated); setEditing(false); setRefresh(n => n + 1); setMessage("Ficha actualizada.");
                }} />}
                  <IncidentPanel
                    key={`incidents-${asset.id}-${asset.revision}`}
                    asset={asset}
                    incidents={incidents}
                    conditions={options.conditions}
                    onWrite={writeToAsset}
                  />
                  <MaintenancePanel
                    key={`maintenance-${asset.id}-${asset.revision}-${maintenance?.revision}`}
                    asset={asset}
                    active={maintenance}
                    history={events}
                    locations={options.locations}
                    onWrite={writeToAsset}
                  />
                  {asset.lifecycle_status === "localizado" && <Movements
                    key={`${asset.id}-${asset.revision}`}
                    asset={asset}
                    people={people}
                    options={options}
                    onSubmit={operation}
                  />}
                  <History events={events} />
                </>
              ) : <p className="empty">No fue posible cargar la ficha.</p>}
            </section>
          )}
          </>}
          <footer>
            Universidad Nacional de Loja{" "}
            <span>Inventario de tecnologías de información · Grupo 5</span>
          </footer>
        </main>
      </div>
    </div></div>
    {adminOpen && <FacultyManagement onExit={onExit} onBack={() => setAdminOpen(false)} />}
    </>
  );
}
