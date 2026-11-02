import { useState } from "react";
import { Form } from "./Form";

export interface FacultyOption { id: number; name: string }
export interface ReviewerSummary { id: number; username: string; faculty_id: number; active: boolean; pending_count: number }

export function ReviewerAdmin({ faculties, reviewers, onCreate, onDeactivate, onReassign }: {
  faculties: FacultyOption[]; reviewers: ReviewerSummary[];
  onCreate: (data: { username: string; faculty_id: number; password: string }) => Promise<unknown>;
  onDeactivate: (id: number) => Promise<unknown>;
  onReassign: (requestId: number, reviewerId: number) => Promise<unknown>;
}) {
  const [createKey, setCreateKey] = useState(0);
  return <section><h2>Administrar revisores</h2>
    <Form key={createKey} submit="Crear revisor" onSubmit={async (fields) => {
      const username = fields.username?.trim();
      const facultyId = Number(fields.faculty_id);
      if (!username || !fields.password || !faculties.some((item) => item.id === facultyId)) throw new Error("Completa usuario, facultad y contraseña temporal.");
      await onCreate({ username, faculty_id: facultyId, password: fields.password });
      setCreateKey((key) => key + 1);
    }}>
      <label>Usuario<input name="username" required maxLength={150} autoComplete="off" /></label>
      <label>Facultad<select name="faculty_id" required defaultValue=""><option value="" disabled>Selecciona una facultad</option>{faculties.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label>
      <label>Contraseña temporal<input name="password" type="password" required autoComplete="new-password" /></label>
    </Form>
    <h3>Revisores</h3>
    {reviewers.map((item) => <article key={item.id}><p>{item.username} · {item.active ? "Activo" : "Inactivo"} · Pendientes: {item.pending_count}</p>
      {item.active && <Form submit="Desactivar" onSubmit={async () => { if (item.pending_count > 0) throw new Error("Reasigna primero todas las solicitudes pendientes."); await onDeactivate(item.id); }}>
        {item.pending_count > 0 && <p>Reasigna primero las solicitudes pendientes.</p>}
      </Form>}
    </article>)}
    <h3>Reasignar solicitud</h3>
    <Form submit="Reasignar" onSubmit={async (fields) => {
      const requestId = Number(fields.request_id); const reviewerId = Number(fields.reviewer_id);
      if (!Number.isSafeInteger(requestId) || requestId <= 0 || !reviewers.some((item) => item.id === reviewerId && item.active)) throw new Error("Selecciona una solicitud y un revisor activo.");
      await onReassign(requestId, reviewerId);
    }}>
      <label>Identificador de solicitud<input name="request_id" type="number" min="1" step="1" required /></label>
      <label>Nuevo revisor<select name="reviewer_id" required defaultValue=""><option value="" disabled>Selecciona un revisor</option>{reviewers.filter((item) => item.active).map((item) => <option key={item.id} value={item.id}>{item.username}</option>)}</select></label>
    </Form>
  </section>;
}
