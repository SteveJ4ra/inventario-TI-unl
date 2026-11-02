import { useState, type FormEvent } from "react";
import { ErrorNotice } from "./Form";

export function ReviewerPasswordChange({ onSubmit }: {
  onSubmit: (data: { current_password: string; new_password: string }) => Promise<unknown>;
}) {
  const [current, setCurrent] = useState("");
  const [next, setNext] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState<unknown>(null);
  const [busy, setBusy] = useState(false);
  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (busy) return;
    if (!current || !next || next !== confirm) { setError(new Error("Completa las contraseñas y confirma que coincidan.")); return; }
    setBusy(true); setError(null);
    try { await onSubmit({ current_password: current, new_password: next }); setCurrent(""); setNext(""); setConfirm(""); }
    catch (failure) { setError(failure); }
    finally { setBusy(false); }
  }
  return <form onSubmit={save}><h2>Cambiar contraseña temporal</h2><fieldset disabled={busy}>
    <label>Contraseña temporal<input type="password" value={current} onChange={(e) => setCurrent(e.target.value)} autoComplete="current-password" required /></label>
    <label>Nueva contraseña<input type="password" value={next} onChange={(e) => setNext(e.target.value)} autoComplete="new-password" required /></label>
    <label>Confirmar nueva contraseña<input type="password" value={confirm} onChange={(e) => setConfirm(e.target.value)} autoComplete="new-password" required /></label>
  </fieldset>{error != null && <ErrorNotice error={error} />}<button className="primary" disabled={busy}>Cambiar contraseña</button></form>;
}
