import { useEffect, useState } from "react";
import { request } from "../api";
import type { Body, Faculty } from "../types";
import { ErrorNotice, Field, Form } from "./Form";
import { ReviewChanges } from "./ReviewChanges";
export function FacultyManagement({ onExit, onBack }: { onExit: () => void; onBack?: () => void }) {
  const [rows, setRows] = useState<Faculty[]>([]);
  const [error, setError] = useState<unknown>(null);
  const [reload, setReload] = useState(0);
  const [selected, setSelected] = useState<Faculty | null>(null);
  const [pending, setPending] = useState<Body | null>(null);
  useEffect(() => {
    const controller = new AbortController();
    setError(null);
    request<Faculty[]>("/operator/faculties/", { signal: controller.signal }).then(value => { if (!Array.isArray(value)) throw new Error("No se pudo confirmar el catálogo de facultades."); setRows(value); })
      .catch(e => { if (!controller.signal.aborted) setError(e); });
    return () => controller.abort();
  }, [reload]);
  return <main className="content"><section className="panel">
    <h1>Administrar facultades</h1>
    {onBack && <button type="button" onClick={onBack}>Volver al inventario</button>}
    <Form submit="Cerrar sesión" onSubmit={async () => { await request("/auth/logout/", { body: {} }); onExit(); }}><p>Acceso de Operador.</p></Form>
    {error != null && <ErrorNotice error={error} />}
    <button onClick={() => setReload(n => n + 1)}>Actualizar catálogo</button>
    <Form submit="Crear facultad" onSubmit={async data => {
      await request("/operator/faculties/", { body: { name: data.name } });
      setReload(n => n + 1);
    }}><Field label="Nombre de nueva facultad" name="name" /></Form>
    <ul>{rows.map(row => <li key={row.id}>{row.name} · {row.active ? "Activa" : "Inactiva"}
      <button onClick={() => { setSelected(row); setPending(null); }}>{"Editar " + row.name}</button>
    </li>)}</ul>
    {selected && <section key={selected.id}>
      <h2>Editar facultad</h2>
      <div hidden={pending !== null}><Form submit="Revisar cambios" onSubmit={async data => {
        setPending({ name: data.name, active: data.active === "on" });
      }}>
        <Field label="Nombre de facultad" name="name" defaultValue={selected.name} />
        <label><input type="checkbox" name="active" defaultChecked={selected.active} />Facultad activa</label>
      </Form></div>
      {pending && <ReviewChanges before={{ name: selected.name, active: selected.active }} after={pending}
        onCancel={() => setPending(null)} onConfirm={async () => {
          await request("/operator/faculties/" + selected.id + "/", { body: pending, method: "PATCH" });
          setPending(null); setSelected(null); setReload(n => n + 1);
        }} />}
    </section>}
    <h2>Cambio de facultad de un activo</h2>
    <p>No disponible: falta integrar la protección real de solicitudes de baja pendientes del paquete 005. No se ha cambiado ninguna facultad.</p>
  </section></main>;
}
