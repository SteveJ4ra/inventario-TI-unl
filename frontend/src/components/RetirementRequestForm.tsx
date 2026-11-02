import { Form } from "./Form";

export interface EligibleReviewer { id: number; username: string; faculty: string }

export function RetirementRequestForm({ reviewers, revision, onSubmit }: {
  reviewers: EligibleReviewer[]; revision: number;
  onSubmit: (data: { reviewer_id: number; reason: string; expected_revision: number }) => Promise<unknown>;
}) {
  return <Form submit="Solicitar baja" onSubmit={async (fields) => {
    const reason = fields.reason?.trim();
    const reviewer = Number(fields.reviewer_id);
    if (!reason || !reviewers.some((item) => item.id === reviewer)) throw new Error("Indica un motivo y selecciona un revisor elegible.");
    await onSubmit({ reviewer_id: reviewer, reason, expected_revision: revision });
  }}>
    <label>Revisor<select name="reviewer_id" required defaultValue=""><option value="" disabled>Selecciona un revisor</option>{reviewers.map((item) => <option key={item.id} value={item.id}>{item.username} · {item.faculty}</option>)}</select></label>
    {!reviewers.length && <p className="hint">No hay revisores elegibles disponibles.</p>}
    <label>Motivo<textarea name="reason" required maxLength={2000} /></label>
  </Form>;
}
