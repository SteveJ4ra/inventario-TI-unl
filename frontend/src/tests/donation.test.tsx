import { afterEach, expect, test, vi } from "vitest";
import { render, screen, within, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useState } from "react";
import { AcquisitionForm } from "../components/AcquisitionForm";
import { AssetFacts } from "../components/Inventory";
import App from "../App";
import type { AcquisitionDocument } from "../types";
import { asset, options } from "./fixtures";

const doc: AcquisitionDocument = { id: 29, source: "DONATION", reference: "TEST-ACTA",
  support_type: "Acta ficticia", document_date: null, supplier: "", invoice_total: null,
  currency: "USD", created_by: { id: 1, username: "gestor" }, created_at: "2026-11-04T12:00:00Z", items: [] };
const response = (data: unknown, status = 200) => new Response(JSON.stringify(data), { status });
afterEach(() => vi.unstubAllGlobals());
function Harness() {
  const [document, setDocument] = useState<AcquisitionDocument | null>(null);
  return <AcquisitionForm source="DONATION" options={options} document={document} onDocument={setDocument} onCreated={() => {}} />;
}
function server() {
  const documents: Record<string, unknown>[] = [], assets: Record<string, unknown>[] = [];
  const fetch = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const path = String(input);
    if (path === "/api/auth/csrf/") return response({ csrfToken: "test-csrf" });
    if (path === "/api/auth/me/") return response({ id: 1, username: "gestor", permissions: ["inventory.manage"], must_change_password: false });
    if (path === "/api/options/") return response(options);
    if (path === "/api/custodians/") return response([]);
    if (path.startsWith("/api/assets/?")) return response({ count: 0, results: [], next: null, previous: null });
    if (path === "/api/faculties/") return response([{ id: 3, name: "Facultad ficticia", active: true }]);
    if (path === "/api/acquisitions/29/") return response(doc);
    if (path === "/api/assets/9/") return response({ ...asset, id: 9, revision: 3, acquisition: null });
    if (path === "/api/acquisitions/" && init?.method === "POST") {
      const body = JSON.parse(String(init.body)); documents.push(body);
      return response({ ...doc, items: (body.items || []).map((i: { estimated_value: string; asset_id: number }) => ({
        ...i, item_value: i.estimated_value, asset_code: "EX-" + i.asset_id })) }, 201);
    }
    if (path === "/api/assets/" && init?.method === "POST") {
      const body = JSON.parse(String(init.body)); assets.push(body);
      return response({ ...asset, id: assets.length, code: "DON-" + assets.length, faculty_id: 3,
        acquisition: { ...doc, document_id: 29, item_value: body.item_value,
          acquired_on: body.acquired_on ?? null, date_unknown_reason: body.date_unknown_reason ?? "" } }, 201);
    }
    throw new Error("Unexpected request " + path);
  });
  vi.stubGlobal("fetch", fetch);
  return { fetch, documents, assets };
}
async function metadata(user: ReturnType<typeof userEvent.setup>) {
  await user.type(screen.getByLabelText("Referencia del respaldo"), "TEST-ACTA");
  await user.type(screen.getByLabelText("Tipo de respaldo"), "Acta ficticia");
}
async function newAsset(user: ReturnType<typeof userEvent.setup>, serial: string, value: string, unknown = false) {
  const form = within(screen.getByRole("button", { name: "Registrar activo" }).closest("form")!);
  for (const [label, text] of [["Nombre", "Portátil"], ["Descripción", "Fixture"], ["Marca", "Ejemplo"],
      ["Modelo", "A1"], ["Número de serie", serial], ["Ubicación", "Laboratorio"]])
    await user.type(form.getByLabelText(label), text);
  await user.selectOptions(form.getByLabelText("Categoría"), "portatil");
  await user.selectOptions(form.getByLabelText("Condición"), "operativo");
  await user.selectOptions(form.getByLabelText("Facultad responsable"), "3");
  await user.type(form.getByLabelText("Valor estimado individual (USD)"), value);
  if (unknown) {
    await user.click(form.getByLabelText("Fecha de adquisición desconocida"));
    await user.type(form.getByLabelText("Motivo de fecha desconocida"), "No consta en respaldo");
  } else await user.type(form.getByLabelText("Fecha de adquisición"), "2026-01-15");
}
test("donación comparte respaldo para dos activos nuevos con valores estimados separados", async () => {
  const api = server(), user = userEvent.setup(); render(<Harness />);
  expect(screen.queryByLabelText("Proveedor")).toBeNull();
  expect(screen.queryByLabelText("Fecha de factura")).toBeNull();
  await metadata(user); await user.click(screen.getByRole("button", { name: "Guardar respaldo" }));
  await screen.findByRole("heading", { name: "Respaldo TEST-ACTA" });
  await newAsset(user, "DON-A", "35.25"); await user.click(screen.getByRole("button", { name: "Registrar activo" }));
  await screen.findByText("DON-1", { exact: true });
  await newAsset(user, "DON-B", "80.50", true); await user.click(screen.getByRole("button", { name: "Registrar activo" }));
  await screen.findByText("DON-2", { exact: true });
  expect(api.documents).toEqual([{ source: "DONATION", reference: "TEST-ACTA", support_type: "Acta ficticia" }]);
  expect(api.assets).toHaveLength(2);
  const write = api.fetch.mock.calls.find(([path]) => path === "/api/acquisitions/")!;
  expect(write[1]?.credentials).toBe("same-origin");
  expect(write[1]?.headers).toMatchObject({ "X-CSRFToken": "test-csrf" });
  expect(api.assets[0]).toMatchObject({ acquisition_document_id: 29, item_value: "35.25", acquired_on: "2026-01-15" });
  expect(api.assets[1]).toMatchObject({ acquisition_document_id: 29, item_value: "80.50", date_unknown_reason: "No consta en respaldo" });
}, 15000);
test("donación usa estimated_value y revisión consultada al asociar activo existente", async () => {
  const api = server(), user = userEvent.setup(); render(<Harness />);
  await user.type(screen.getByLabelText("Identificador del activo existente"), "9");
  await user.click(screen.getByRole("button", { name: "Consultar activo existente" }));
  await screen.findByRole("button", { name: "Añadir asociación" });
  await user.type(screen.getByLabelText("Valor estimado del activo existente (USD)"), "55.50");
  await user.type(screen.getByLabelText("Motivo de asociación"), "Acta verificada");
  await user.type(screen.getByLabelText("Fecha de adquisición del activo existente"), "2026-01-15");
  await user.click(screen.getByRole("button", { name: "Añadir asociación" }));
  await metadata(user); await user.click(screen.getByRole("button", { name: "Guardar respaldo" }));
  await screen.findByText("EX-9");
  expect(api.documents[0]).toMatchObject({ items: [{ asset_id: 9, estimated_value: "55.50",
    expected_revision: 3, reason: "Acta verificada", acquired_on: "2026-01-15" }] });
  expect(JSON.stringify(api.documents[0])).not.toContain("item_value");
  expect(api.assets).toHaveLength(0);
});
test("rechazo del respaldo conserva datos y muestra error junto al campo", async () => {
  const api = server(), base = api.fetch.getMockImplementation()!, user = userEvent.setup();
  api.fetch.mockImplementation(async (input, init) => String(input) === "/api/acquisitions/"
    ? response({ detail: "Datos inválidos", fields: { support_type: ["Tipo requerido"] } }, 400) : base(input, init));
  render(<Harness />); await metadata(user);
  await user.click(screen.getByRole("button", { name: "Guardar respaldo" }));
  expect((await screen.findByRole("alert")).textContent).toContain("Tipo requerido");
  expect((screen.getByLabelText("Referencia del respaldo") as HTMLInputElement).value).toBe("TEST-ACTA");
  expect(screen.getByLabelText("Tipo de respaldo").getAttribute("aria-invalid")).toBe("true");
  expect(screen.queryByRole("button", { name: "Registrar activo" })).toBeNull();
});
test("doble envío del respaldo no duplica la escritura ni reintenta", async () => {
  const api = server(), base = api.fetch.getMockImplementation()!, user = userEvent.setup();
  let finish!: (value: Response) => void, posts = 0;
  api.fetch.mockImplementation(async (input, init) => {
    if (String(input) === "/api/acquisitions/") { posts++; return new Promise(resolve => { finish = resolve; }); }
    return base(input, init);
  });
  render(<Harness />); await metadata(user);
  await user.dblClick(screen.getByRole("button", { name: "Guardar respaldo" }));
  await waitFor(() => expect(posts).toBe(1)); finish(response(doc, 201));
  await screen.findByRole("heading", { name: "Respaldo TEST-ACTA" }); expect(posts).toBe(1);
});
test("cargar compra desde donaciones rechaza el tipo sin convertir el documento", async () => {
  const api = server(), base = api.fetch.getMockImplementation()!, user = userEvent.setup();
  api.fetch.mockImplementation(async (input, init) => String(input) === "/api/acquisitions/29/"
    ? response({ ...doc, source: "PURCHASE" }) : base(input, init));
  render(<Harness />); await user.click(screen.getByRole("button", { name: "Usar respaldo existente" }));
  await user.type(screen.getByLabelText("Identificador del documento"), "29");
  await user.click(screen.getByRole("button", { name: "Cargar respaldo" }));
  expect((await screen.findByRole("alert")).textContent).toContain("no es un respaldo de donación");
  expect(api.documents).toHaveLength(0); expect(api.assets).toHaveLength(0);
});
test("App abre donaciones y conserva el formulario al cerrar y reabrir", async () => {
  server(); const user = userEvent.setup(); render(<App />);
  await user.click(await screen.findByRole("button", { name: "Registrar donación" }));
  await metadata(user); await user.click(screen.getByRole("button", { name: "Cerrar" }));
  await user.click(screen.getByRole("button", { name: "Registrar donación" }));
  expect((screen.getByLabelText("Referencia del respaldo") as HTMLInputElement).value).toBe("TEST-ACTA");
});
test("ficha muestra respaldo y valor estimado de donación sin total de factura", () => {
  render(<AssetFacts asset={{ ...asset, acquisition: { ...doc, document_id: 29, item_value: "45.00",
    acquired_on: null, date_unknown_reason: "No consta" } }} />);
  expect(screen.getByText("Acta ficticia")).toBeDefined();
  expect(screen.getByText("USD 45.00")).toBeDefined();
  expect(screen.queryByText("Total compartido de factura")).toBeNull();
});

test("rechazo del activo conserva respaldo y datos sin anunciar éxito", async () => {
  const api = server(), base = api.fetch.getMockImplementation()!, user = userEvent.setup();
  api.fetch.mockImplementation(async (input, init) => String(input) === "/api/assets/"
    ? response({ detail: "Valor rechazado", fields: { item_value: ["Revisa la estimación"] } }, 400) : base(input, init));
  render(<Harness />); await metadata(user);
  await user.click(screen.getByRole("button", { name: "Guardar respaldo" }));
  await screen.findByRole("heading", { name: "Respaldo TEST-ACTA" });
  await newAsset(user, "DON-REJECT", "35.00");
  await user.click(screen.getByRole("button", { name: "Registrar activo" }));
  expect((await screen.findByRole("alert")).textContent).toContain("Revisa la estimación");
  expect((screen.getByLabelText("Número de serie") as HTMLInputElement).value).toBe("DON-REJECT");
  expect((screen.getByLabelText("Valor estimado individual (USD)") as HTMLInputElement).value).toBe("35.00");
  expect(screen.getByRole("heading", { name: "Respaldo TEST-ACTA" })).toBeDefined();
  expect(api.documents).toHaveLength(1); expect(api.assets).toHaveLength(0);
});
test("error incierto del respaldo conserva la entrada y no reintenta", async () => {
  const api = server(), base = api.fetch.getMockImplementation()!, user = userEvent.setup();
  let posts = 0;
  api.fetch.mockImplementation(async (input, init) => {
    if (String(input) === "/api/acquisitions/") { posts++; throw new TypeError("Failed to fetch"); }
    return base(input, init);
  });
  render(<Harness />); await metadata(user);
  await user.click(screen.getByRole("button", { name: "Guardar respaldo" }));
  expect((await screen.findByRole("alert")).textContent).toContain("No se pudo confirmar");
  expect((screen.getByLabelText("Referencia del respaldo") as HTMLInputElement).value).toBe("TEST-ACTA");
  expect(posts).toBe(1); expect(screen.queryByRole("button", { name: "Registrar activo" })).toBeNull();
});
