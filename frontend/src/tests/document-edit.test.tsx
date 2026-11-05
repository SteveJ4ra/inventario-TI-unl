import { afterEach, expect, test, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { DocumentEditForm } from "../components/DocumentEditForm";
import type { AcquisitionDocument } from "../types";
const doc: AcquisitionDocument = { id: 4, source: "PURCHASE", reference: "PREVIA", document_date: "2026-01-15",
  supplier: "Proveedor", invoice_total: "100.00", support_type: "", currency: "USD",
  created_by: { id: 1, username: "fixture" }, created_at: "2026-01-15T12:00:00Z",
  items: [{ asset_id: 8, asset_revision: 3, item_value: "35.00", acquired_on: "2026-01-15", date_unknown_reason: "" }] };
const response = (data: unknown, status = 200) => new Response(JSON.stringify(data), { status });
afterEach(() => vi.unstubAllGlobals());
test("documento compartido envía snapshot y revisiones completas solo al confirmar", async () => {
  const bodies: unknown[] = [], saved = vi.fn();
  vi.stubGlobal("fetch", vi.fn(async (input, init) => {
    if (String(input) === "/api/auth/csrf/") return response({ csrfToken: "fixture-csrf" });
    bodies.push(JSON.parse(String(init?.body))); expect(init?.method).toBe("PATCH");
    return response({ ...doc, reference: "CORREGIDA" });
  }));
  const user = userEvent.setup(); render(<DocumentEditForm document={doc} onSaved={saved} />);
  const field = screen.getByLabelText("Referencia documental"); await user.clear(field); await user.type(field, "CORREGIDA");
  await user.type(screen.getByLabelText("Motivo de edición"), "Respaldo cotejado");
  await user.click(screen.getByRole("button", { name: "Revisar cambios" }));
  expect(bodies).toHaveLength(0);
  await user.click(screen.getByRole("button", { name: "Confirmar cambios" }));
  await waitFor(() => expect(saved).toHaveBeenCalledTimes(1));
  expect(bodies[0]).toMatchObject({ reference: "CORREGIDA", reason: "Respaldo cotejado",
    expected_document: { source: "PURCHASE", reference: "PREVIA", invoice_total: "100.00", currency: "USD" },
    expected_revisions: { "8": 3 } });
});
test("conflicto documental conserva borrador sin actualizar revisión automáticamente", async () => {
  const saved = vi.fn();
  vi.stubGlobal("fetch", vi.fn(async input => String(input) === "/api/auth/csrf/"
    ? response({ csrfToken: "fixture" }) : response({ code: "stale_document", detail: "El documento cambió." }, 409)));
  const user = userEvent.setup(); render(<DocumentEditForm document={doc} onSaved={saved} />);
  const field = screen.getByLabelText("Referencia documental"); await user.clear(field); await user.type(field, "BORRADOR");
  await user.type(screen.getByLabelText("Motivo de edición"), "Verificación");
  await user.click(screen.getByRole("button", { name: "Revisar cambios" }));
  await user.click(screen.getByRole("button", { name: "Confirmar cambios" }));
  expect((await screen.findByRole("alert")).textContent).toContain("El documento cambió");
  expect(saved).not.toHaveBeenCalled();
  await user.click(screen.getByRole("button", { name: "Volver a editar" }));
  expect((screen.getByLabelText("Referencia documental") as HTMLInputElement).value).toBe("BORRADOR");
});
test("donación vacía permite respaldo sin añadir fecha documental ni cambio de origen", async () => {
  render(<DocumentEditForm document={{ ...doc, source: "DONATION", supplier: "", invoice_total: null,
    document_date: null, support_type: "Acta", items: [] }} onSaved={() => {}} />);
  expect(screen.getByLabelText("Tipo de respaldo documental")).toBeDefined();
  expect(screen.queryByLabelText("Fecha del documento")).toBeNull();
  expect(screen.queryByLabelText("Origen")).toBeNull();
});
