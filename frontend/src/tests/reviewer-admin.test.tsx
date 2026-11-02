import { expect, test, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ReviewerAdmin } from "../components/ReviewerAdmin";

test("no solicita desactivar un revisor con solicitudes pendientes", async () => {
  const deactivate = vi.fn().mockResolvedValue(undefined);
  const user = userEvent.setup();
  render(<ReviewerAdmin faculties={[]} reviewers={[{ id: 2, username: "revisor", faculty_id: 1, active: true, pending_count: 1 }]} onCreate={vi.fn()} onDeactivate={deactivate} onReassign={vi.fn()} />);
  await user.click(screen.getByRole("button", { name: "Desactivar" }));
  expect(deactivate).not.toHaveBeenCalled();
  expect((await screen.findByRole("alert")).textContent).toContain("Reasigna primero");
});

test("crea revisor con facultad y contraseña temporal", async () => {
  const create = vi.fn().mockResolvedValue(undefined);
  const user = userEvent.setup();
  render(<ReviewerAdmin faculties={[{ id: 5, name: "Otra facultad" }]} reviewers={[]} onCreate={create} onDeactivate={vi.fn()} onReassign={vi.fn()} />);
  await user.type(screen.getByLabelText("Usuario"), "revisor");
  await user.selectOptions(screen.getByLabelText("Facultad"), "5");
  await user.type(screen.getByLabelText("Contraseña temporal"), "Ejemplo-Temporal-42");
  await user.click(screen.getByRole("button", { name: "Crear revisor" }));
  expect(create).toHaveBeenCalledWith({ username: "revisor", faculty_id: 5, password: "Ejemplo-Temporal-42" });
  expect((screen.getByLabelText("Contraseña temporal") as HTMLInputElement).value).toBe("");
});
