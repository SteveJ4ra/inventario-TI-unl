import { expect, test, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { RetirementRequestForm } from "../components/RetirementRequestForm";
import { RetirementRequests } from "../components/RetirementRequests";
import { NormalRetirementForm } from "../components/NormalRetirementForm";
import { ReviewerPasswordChange } from "../components/ReviewerPasswordChange";

test("solicitud envía revisor, motivo y revisión", async () => {
  const submit = vi.fn().mockResolvedValue(undefined);
  const user = userEvent.setup();
  render(<RetirementRequestForm reviewers={[{ id: 2, username: "revisor", faculty: "Otra facultad" }]} revision={4} onSubmit={submit} />);
  await user.selectOptions(screen.getByLabelText("Revisor"), "2");
  await user.type(screen.getByLabelText("Motivo"), "Pérdida documentada");
  await user.click(screen.getByRole("button", { name: "Solicitar baja" }));
  expect(submit).toHaveBeenCalledWith({ reviewer_id: 2, reason: "Pérdida documentada", expected_revision: 4 });
});

test("rechazo requiere motivo y conserva revisión", async () => {
  const submit = vi.fn().mockResolvedValue(undefined);
  const user = userEvent.setup();
  render(<RetirementRequests requests={[{ id: 7, asset_code: "TI-000001", reason: "Pérdida", status: "pending", expected_revision: 3 }]} onDecision={submit} />);
  await user.click(screen.getByRole("button", { name: "Rechazar" }));
  await user.type(screen.getByLabelText("Motivo de rechazo"), "Falta información");
  await user.click(screen.getByRole("button", { name: "Confirmar rechazo" }));
  expect(submit).toHaveBeenCalledWith(7, { decision: "reject", reason: "Falta información", expected_revision: 3 });
});

test("solicitud cancelada no ofrece decisiones", () => {
  render(<RetirementRequests requests={[{ id: 7, asset_code: "TI-000001", reason: "Pérdida", status: "cancelled", expected_revision: 4 }]} onDecision={vi.fn()} />);
  expect(screen.queryByRole("button", { name: "Aprobar" })).toBeNull();
  expect(screen.queryByRole("button", { name: "Rechazar" })).toBeNull();
});

test("baja normal envía motivo y revisión", async () => {
  const submit = vi.fn().mockResolvedValue(undefined); const user = userEvent.setup();
  render(<NormalRetirementForm revision={5} onSubmit={submit} />);
  await user.type(screen.getByLabelText("Motivo de la baja"), "Obsolescencia");
  await user.click(screen.getByRole("button", { name: "Registrar baja" }));
  expect(submit).toHaveBeenCalledWith({ reason: "Obsolescencia", expected_revision: 5 });
});

test("cambio inicial rechaza confirmación distinta y limpia contraseñas al completar", async () => {
  const submit = vi.fn().mockResolvedValue(undefined); const user = userEvent.setup();
  render(<ReviewerPasswordChange onSubmit={submit} />);
  await user.type(screen.getByLabelText("Contraseña temporal"), "Temporal 42!");
  await user.type(screen.getByLabelText("Nueva contraseña"), "Nueva 42!");
  await user.type(screen.getByLabelText("Confirmar nueva contraseña"), "Distinta 42!");
  await user.click(screen.getByRole("button", { name: "Cambiar contraseña" }));
  expect(submit).not.toHaveBeenCalled();
  await user.clear(screen.getByLabelText("Confirmar nueva contraseña"));
  await user.type(screen.getByLabelText("Confirmar nueva contraseña"), "Nueva 42!");
  await user.click(screen.getByRole("button", { name: "Cambiar contraseña" }));
  expect(submit).toHaveBeenCalledWith({ current_password: "Temporal 42!", new_password: "Nueva 42!" });
  expect((screen.getByLabelText("Contraseña temporal") as HTMLInputElement).value).toBe("");
});
