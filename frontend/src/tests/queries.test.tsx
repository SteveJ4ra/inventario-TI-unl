import { expect, test } from "vitest";
import { render, screen } from "@testing-library/react";
import { History } from "../components/History";
import { movement } from "./fixtures";
test("historial conserva original, autor y vínculo de rectificación", () => {
  render(<History events={[{
    event_type: "movement", event_id: movement.id, data: movement,
    actor: movement.actor, occurred_at: movement.occurred_at,
    resulting_revision: movement.resulting_revision,
  }]} />);
  expect(screen.getByText("gestor")).toBeTruthy();
  expect(screen.getByText("Rectificado por #2")).toBeTruthy();
  expect(screen.getByText("Docente de prueba")).toBeTruthy();
});
test("historial vacío no inventa operaciones", () => {
  render(<History events={[]} />);
  expect(screen.getByText("Todavía no hay eventos.")).toBeTruthy();
});
