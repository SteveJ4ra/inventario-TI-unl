import { useState } from "react";
import { request } from "../api";
import type { Body, Custodian } from "../types";
import { Field, Form } from "./Form";
import { ReviewChanges } from "./ReviewChanges";
export function CustodianEditor({ people, onSaved, onReload }: {
  people: Custodian[]; onSaved: (person: Custodian) => void; onReload: () => void;
}) {
  const [person, setPerson] = useState<Custodian | null>(null);
  const [pending, setPending] = useState<Body | null>(null);
  return <section aria-label="Editar custodios">
    <p>La corrección conserva los datos personales capturados en movimientos anteriores.</p>
    {!person ? <ul>{people.map(row => <li key={row.id}>{row.full_name} · {row.email}
      <button onClick={() => setPerson(row)}>{"Editar " + row.full_name}</button></li>)}</ul> : <>
      <button onClick={() => { setPending(null); setPerson(null); onReload(); }}>Volver a consultar perfiles</button>
      <div hidden={pending !== null}><Form submit="Revisar cambios" onSubmit={async data => {
        const profile = { full_name: person.full_name, email: person.email, department: person.department };
        const changes: Body = {};
        for (const key of ["full_name", "email", "department"] as const)
          if (data[key] !== profile[key]) changes[key] = data[key];
        if (!Object.keys(changes).length) throw new Error("No hay cambios para guardar.");
        setPending({ ...changes, expected_profile: profile, reason: data.reason });
      }}>
        <Field label="Nombre del custodio" name="full_name" defaultValue={person.full_name} />
        <Field label="Correo del custodio" name="email" type="email" maxLength={254} defaultValue={person.email} />
        <Field label="Dependencia" name="department" optional defaultValue={person.department} />
        <Field label="Motivo de edición" name="reason" maxLength={2000} />
      </Form></div>
      {pending && <ReviewChanges before={{ full_name: person.full_name, email: person.email, department: person.department }}
        after={pending} onCancel={() => setPending(null)} onConfirm={async () => {
          const updated = await request<Custodian>("/custodians/" + person.id + "/", { body: pending, method: "PATCH" });
          if (updated.id !== person.id || typeof updated.full_name !== "string") throw new Error("No se pudo confirmar el perfil. Consúltalo antes de repetir.");
          onSaved(updated); setPerson(null); setPending(null);
        }} />}
    </>}
  </section>;
}
