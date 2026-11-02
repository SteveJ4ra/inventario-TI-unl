import { useState } from "react";
import { Form } from "./Form";

export interface AssignedRetirementRequest { id: number; asset_code: string; reason: string; status: string; expected_revision: number }

export function RetirementRequests({ requests, onDecision }: {
  requests: AssignedRetirementRequest[];
  onDecision: (id: number, data: { decision: "approve" | "reject"; reason: string; expected_revision: number }) => Promise<unknown>;
}) {
  const [selected, setSelected] = useState<{ id: number; decision: "approve" | "reject" } | null>(null);
  return <section><h2>Solicitudes asignadas</h2>{requests.length === 0 && <p>No hay solicitudes asignadas.</p>}
    {requests.map((item) => <article key={item.id}><h3>{item.asset_code}</h3><p>{item.reason}</p><p>Estado: {item.status}</p>
      {item.status === "pending" && <><button onClick={() => setSelected({ id: item.id, decision: "approve" })}>Aprobar</button><button onClick={() => setSelected({ id: item.id, decision: "reject" })}>Rechazar</button></>}
      {selected?.id === item.id && <Form key={selected.decision} submit={selected.decision === "approve" ? "Confirmar aprobación" : "Confirmar rechazo"} onSubmit={async (fields) => {
        const reason = fields.reason?.trim() || "";
        if (selected.decision === "reject" && !reason) throw new Error("Indica el motivo del rechazo.");
        await onDecision(item.id, { decision: selected.decision, reason, expected_revision: item.expected_revision });
        setSelected(null);
      }}>
        {selected.decision === "reject" ? <label>Motivo de rechazo<textarea name="reason" required maxLength={2000} /></label> : <p>La aprobación registrará la baja del activo.</p>}
        <button type="button" onClick={() => setSelected(null)}>Cancelar</button>
      </Form>}
    </article>)}
  </section>;
}
