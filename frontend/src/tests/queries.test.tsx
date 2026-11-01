import { expect, test } from "vitest";
import { render, screen } from "@testing-library/react";
import { History } from "../components/History";
import { movement } from "./fixtures";
test("historial conserva original, autor y vínculo de rectificación", () => {
  render(<History events={[movement]} />);
  expect(screen.getByText("gestor")).toBeTruthy();
  expect(screen.getByText("Rectificado por #2")).toBeTruthy();
  expect(screen.getByText("Docente de prueba")).toBeTruthy();
});
test("historial vacío no inventa operaciones", () => {
  render(<History events={[]} />);
  expect(screen.getByText("Todavía no hay movimientos.")).toBeTruthy();
});
