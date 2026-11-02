import { Form } from "./Form";

export function NormalRetirementForm({ revision, onSubmit }: {
  revision: number;
  onSubmit: (data: { reason: string; expected_revision: number }) => Promise<unknown>;
}) {
  return <Form submit="Registrar baja" onSubmit={async (fields) => {
    const reason = fields.reason?.trim();
    if (!reason) throw new Error("Indica el motivo de la baja.");
    await onSubmit({ reason, expected_revision: revision });
  }}>
    <p>El registro y su historial permanecerán disponibles para consulta.</p>
    <label>Motivo de la baja<textarea name="reason" required maxLength={2000} /></label>
  </Form>;
}
