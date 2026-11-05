import { afterEach, expect, test, vi } from "vitest";
import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useState } from "react";
import { AcquisitionForm } from "../components/AcquisitionForm";
import App from "../App";
import type { AcquisitionDocument } from "../types";
import { asset, options } from "./fixtures";

const invoice: AcquisitionDocument = {
  id: 17, source: "PURCHASE", reference: "TEST-FACTURA", document_date: "2026-01-15",
  supplier: "Proveedor ficticio", invoice_total: "1000.00", support_type: "", currency: "USD",
  created_at: "2026-11-04T12:00:00Z", created_by: { id: 1, username: "gestor" }, items: [],
};
const response = (data: unknown, status = 200) => new Response(JSON.stringify(data), {
  status, headers: { "Content-Type": "application/json" },
});
afterEach(() => vi.unstubAllGlobals());

function Harness({ initial = null }: { initial?: AcquisitionDocument | null }) {
  const [document, setDocument] = useState(initial);
  return <AcquisitionForm options={options} document={document} onDocument={setDocument} onCreated={() => {}} />;
}
function server() {
  const documents: unknown[] = [];
  const assets: Record<string, unknown>[] = [];
  const fetch = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const path = String(input);
    if (path === "/api/auth/csrf/") return response({ csrfToken: "csrf-fixture" });
    if (path === "/api/faculties/") return response([{ id: 3, name: "Facultad ficticia", active: true }]);
    if (path === "/api/acquisitions/17/") return response(invoice);
    if (path === "/api/acquisitions/" && init?.method === "POST") {
      documents.push(JSON.parse(String(init.body)));
      return response(invoice, 201);
    }
    if (path === "/api/assets/" && init?.method === "POST") {
      const body = JSON.parse(String(init.body));
      assets.push(body);
      const id = assets.length;
      return response({ ...asset, id, code: "TI-00000" + id, serial_number: body.serial_number,
        faculty_id: body.faculty_id, acquisition: { document_id: 17, currency: "USD", source: "PURCHASE",
          reference: invoice.reference, document_date: invoice.document_date, supplier: invoice.supplier,
          invoice_total: invoice.invoice_total, support_type: "", item_value: body.item_value,
          acquired_on: body.acquired_on ?? null, date_unknown_reason: body.date_unknown_reason ?? "" } }, 201);
    }
    throw new Error("Unexpected test request: " + path);
  });
  vi.stubGlobal("fetch", fetch);
  return { fetch, documents, assets };
}
async function fillInvoice(user: ReturnType<typeof userEvent.setup>) {
  await user.type(screen.getByLabelText("Referencia de factura"), "TEST-FACTURA");
  await user.type(screen.getByLabelText("Fecha de factura"), "2026-01-15");
  await user.type(screen.getByLabelText("Proveedor"), "Proveedor ficticio");
  await user.type(screen.getByLabelText("Total de factura (USD)"), "1000.00");
}
async function fillAsset(user: ReturnType<typeof userEvent.setup>, serial: string, value: string, unknown = false) {
  const scope = within(screen.getByRole("button", { name: "Registrar activo" }).closest("form")!);
  for (const [label, text] of [["Nombre", "Portátil"], ["Descripción", "Equipo ficticio"],
    ["Marca", "Ejemplo"], ["Modelo", "A1"], ["Número de serie", serial], ["Ubicación", "Laboratorio"]])
    await user.type(scope.getByLabelText(label), text);
  await user.selectOptions(scope.getByLabelText("Categoría"), "portatil");
  await user.selectOptions(scope.getByLabelText("Condición"), "operativo");
  await user.selectOptions(scope.getByLabelText("Facultad responsable"), "3");
  await user.type(scope.getByLabelText("Valor individual (USD)"), value);
  if (unknown) {
    await user.click(scope.getByLabelText("Fecha de adquisición desconocida"));
    await user.type(scope.getByLabelText("Motivo de fecha desconocida"), "No consta en el respaldo");
  } else await user.type(scope.getByLabelText("Fecha de adquisición"), "2026-01-15");
}

test("guarda factura primero y dos activos con valores propios, sin duplicar documento", async () => {
  const api = server();
  const user = userEvent.setup();
  render(<Harness />);
  await user.click(screen.getByRole("button", { name: "Guardar factura" }));
  expect(api.documents).toHaveLength(0);
  await fillInvoice(user);
  await user.click(screen.getByRole("button", { name: "Guardar factura" }));
  await screen.findByText("TEST-FACTURA", { exact: false });
  await fillAsset(user, "TEST-A", "300.25");
  await user.click(screen.getByRole("button", { name: "Registrar activo" }));
  await screen.findByText("TI-000001", { exact: false });
  await fillAsset(user, "TEST-B", "400.50", true);
  await user.click(screen.getByRole("button", { name: "Registrar activo" }));
  await screen.findByText("TI-000002", { exact: false });
  expect(api.documents).toHaveLength(1);
  expect(api.assets).toHaveLength(2);
  expect(api.assets[0]).toMatchObject({ acquisition_document_id: 17, faculty_id: 3, item_value: "300.25", acquired_on: "2026-01-15" });
  expect(api.assets[1]).toMatchObject({ acquisition_document_id: 17, item_value: "400.50", date_unknown_reason: "No consta en el respaldo" });
  expect(api.assets[1].acquired_on).toBeUndefined();
  expect(api.documents[0]).toMatchObject({ source: "PURCHASE", invoice_total: "1000.00" });
  const write = api.fetch.mock.calls.find(([path]) => path === "/api/assets/")!;
  expect(write[1]?.credentials).toBe("same-origin");
  expect(write[1]?.headers).toMatchObject({ "X-CSRFToken": "csrf-fixture" });
}, 15000);

test("un rechazo al registrar activo conserva factura y datos sin mostrar éxito", async () => {
  const api = server();
  const baseFetch = api.fetch.getMockImplementation()!;
  api.fetch.mockImplementation(async (input, init) => String(input) === "/api/assets/"
    ? response({ code: "invalid", detail: "Revisa el importe.", fields: { item_value: ["Importe rechazado"] } }, 400)
    : baseFetch(input, init));
  const user = userEvent.setup();
  render(<Harness initial={invoice} />);
  await screen.findByRole("option", { name: "Facultad ficticia" });
  await fillAsset(user, "TEST-A", "300.00");
  await user.click(screen.getByRole("button", { name: "Registrar activo" }));
  await screen.findByRole("alert");
  expect(screen.getByLabelText("Valor individual (USD)").getAttribute("aria-invalid")).toBe("true");
  expect((screen.getByLabelText("Número de serie") as HTMLInputElement).value).toBe("TEST-A");
  expect(screen.queryByText("TI-000001", { exact: false })).toBeNull();
  expect(api.documents).toHaveLength(0);
  expect(screen.queryByRole("button", { name: "Guardar factura" })).toBeNull();
});

test("carga una factura existente para registrar sin crear otro documento", async () => {
  const api = server();
  const user = userEvent.setup();
  render(<Harness />);
  await user.click(screen.getByRole("button", { name: "Usar factura existente" }));
  await user.type(screen.getByLabelText("Identificador del documento"), "17");
  await user.click(screen.getByRole("button", { name: "Cargar factura" }));
  await screen.findByText("TEST-FACTURA", { exact: false });
  expect(api.documents).toHaveLength(0);
  expect(screen.getByRole("button", { name: "Registrar activo" })).not.toBeNull();
});

test("la navegación conserva la factura al cerrar y reabrir el registro", async () => {
  const api = server();
  const baseFetch = api.fetch.getMockImplementation()!;
  api.fetch.mockImplementation(async (input, init) => {
    const path = String(input);
    if (path === "/api/auth/me/") return response({ id: 1, username: "gestor", permissions: ["inventory.manage"], must_change_password: false });
    if (path.startsWith("/api/assets/?")) return response({ count: 0, results: [], next: null, previous: null });
    if (path === "/api/options/") return response(options);
    if (path === "/api/custodians/") return response([]);
    return baseFetch(input, init);
  });
  const user = userEvent.setup();
  render(<App />);
  await user.click(await screen.findByRole("button", { name: /Registrar activo/ }));
  await fillInvoice(user);
  await user.click(screen.getByRole("button", { name: "Guardar factura" }));
  await screen.findByText("TEST-FACTURA", { exact: false });
  await user.click(screen.getByRole("button", { name: "Cerrar" }));
  await user.click(screen.getByRole("button", { name: /Registrar activo/ }));
  await screen.findByText("TEST-FACTURA", { exact: false });
  expect(api.documents).toHaveLength(1);
});

test("Operador sin permiso Gestor no carga el inventario ni el formulario de compra", async () => {
  const fetch = vi.fn(async (input: RequestInfo | URL) => String(input) === "/api/operator/faculties/"
    ? response([]) : response({ id: 2, username: "operator", permissions: ["faculties.manage"], must_change_password: false }));
  vi.stubGlobal("fetch", fetch);
  render(<App />);
  await screen.findByRole("heading", { name: "Administrar facultades" });
  expect(screen.queryByRole("button", { name: /Registrar activo/ })).toBeNull();
  expect(fetch.mock.calls.map(([path]) => String(path))).toEqual(["/api/auth/me/", "/api/operator/faculties/"]);
});


test("factura inválida muestra error por campo y no habilita el registro", async () => {
  const api = server();
  const baseFetch = api.fetch.getMockImplementation()!;
  api.fetch.mockImplementation(async (input, init) => String(input) === "/api/acquisitions/"
    ? response({ code: "invalid", detail: "Revisa la factura.", fields: { invoice_total: ["Total inválido"] } }, 400)
    : baseFetch(input, init));
  const user = userEvent.setup();
  render(<Harness />);
  await fillInvoice(user);
  await user.click(screen.getByRole("button", { name: "Guardar factura" }));
  await screen.findByRole("alert");
  expect(screen.getByLabelText("Total de factura (USD)").getAttribute("aria-invalid")).toBe("true");
  expect(screen.queryByRole("button", { name: "Registrar activo" })).toBeNull();
  expect(api.assets).toHaveLength(0);
});

test("doble envío mientras se guarda la factura solo hace una escritura", async () => {
  const api = server();
  const baseFetch = api.fetch.getMockImplementation()!;
  let finish!: (value: Response) => void;
  let posts = 0;
  api.fetch.mockImplementation(async (input, init) => {
    if (String(input) === "/api/acquisitions/") {
      posts++;
      return new Promise<Response>(resolve => { finish = resolve; });
    }
    return baseFetch(input, init);
  });
  const user = userEvent.setup();
  render(<Harness />);
  await fillInvoice(user);
  await user.dblClick(screen.getByRole("button", { name: "Guardar factura" }));
  await waitFor(() => expect(posts).toBe(1));
  expect(screen.getByRole("button", { name: "Guardando…" }).hasAttribute("disabled")).toBe(true);
  finish(response(invoice, 201));
  await screen.findByText("TEST-FACTURA", { exact: false });
  expect(posts).toBe(1);
});

test("error de red de factura no anuncia éxito ni reintenta automáticamente", async () => {
  const api = server();
  const baseFetch = api.fetch.getMockImplementation()!;
  let posts = 0;
  api.fetch.mockImplementation(async (input, init) => {
    if (String(input) === "/api/acquisitions/") { posts++; throw new TypeError("Failed to fetch"); }
    return baseFetch(input, init);
  });
  const user = userEvent.setup();
  render(<Harness />);
  await fillInvoice(user);
  await user.click(screen.getByRole("button", { name: "Guardar factura" }));
  const error = await screen.findByRole("alert");
  expect(error.textContent).toContain("No se pudo confirmar");
  expect(posts).toBe(1);
  expect(screen.queryByRole("button", { name: "Registrar activo" })).toBeNull();
});

test("documento de donación no se convierte en compra ficticia", async () => {
  const api = server();
  const baseFetch = api.fetch.getMockImplementation()!;
  api.fetch.mockImplementation(async (input, init) => {
    if (String(input) === "/api/acquisitions/17/") return response({ ...invoice, source: "DONATION", invoice_total: null });
    if (String(input) === "/api/faculties/") return response([]);
    return baseFetch(input, init);
  });
  const user = userEvent.setup();
  render(<Harness />);
  await user.click(screen.getByRole("button", { name: "Usar factura existente" }));
  await user.type(screen.getByLabelText("Identificador del documento"), "17");
  await user.click(screen.getByRole("button", { name: "Cargar factura" }));
  expect((await screen.findByRole("alert")).textContent).toContain("no es una factura de compra");
  expect(api.documents).toHaveLength(0);
  expect(screen.queryByRole("button", { name: "Registrar activo" })).toBeNull();
});


test("sin facultades activas no inventa una selección ni permite registrar", async () => {
  const api = server();
  const baseFetch = api.fetch.getMockImplementation()!;
  api.fetch.mockImplementation(async (input, init) => String(input) === "/api/faculties/" ? response([]) : baseFetch(input, init));
  render(<Harness initial={invoice} />);
  await screen.findByText("No hay facultades activas. Solicita al Operador que las registre.");
  expect(screen.queryByRole("button", { name: "Registrar activo" })).toBeNull();
  expect(api.assets).toHaveLength(0);
});

test("JSON de éxito incompleto no produce una factura confirmada", async () => {
  const api = server();
  const baseFetch = api.fetch.getMockImplementation()!;
  let posts = 0;
  api.fetch.mockImplementation(async (input, init) => {
    if (String(input) === "/api/acquisitions/") { posts++; return response({}, 201); }
    return baseFetch(input, init);
  });
  const user = userEvent.setup();
  render(<Harness />);
  await fillInvoice(user);
  await user.click(screen.getByRole("button", { name: "Guardar factura" }));
  expect((await screen.findByRole("alert")).textContent).toContain("No se pudo confirmar");
  expect(screen.queryByRole("button", { name: "Registrar activo" })).toBeNull();
  expect(posts).toBe(1);
});

test("cerrar y reabrir mientras se guarda conserva el bloqueo y no duplica la factura", async () => {
  const api = server();
  const baseFetch = api.fetch.getMockImplementation()!;
  let finish!: (value: Response) => void;
  let posts = 0;
  api.fetch.mockImplementation(async (input, init) => {
    const path = String(input);
    if (path === "/api/auth/me/") return response({ id: 1, username: "gestor", permissions: ["inventory.manage"], must_change_password: false });
    if (path.startsWith("/api/assets/?")) return response({ count: 0, results: [], next: null, previous: null });
    if (path === "/api/options/") return response(options);
    if (path === "/api/custodians/") return response([]);
    if (path === "/api/acquisitions/") { posts++; return new Promise<Response>(resolve => { finish = resolve; }); }
    return baseFetch(input, init);
  });
  const user = userEvent.setup();
  render(<App />);
  await user.click(await screen.findByRole("button", { name: /Registrar activo/ }));
  await fillInvoice(user);
  await user.click(screen.getByRole("button", { name: "Guardar factura" }));
  await waitFor(() => expect(posts).toBe(1));
  await user.click(screen.getByRole("button", { name: "Cerrar" }));
  await user.click(screen.getByRole("button", { name: /Registrar activo/ }));
  expect(screen.getByRole("button", { name: "Guardando…" }).hasAttribute("disabled")).toBe(true);
  finish(response(invoice, 201));
  await screen.findByText("TEST-FACTURA", { exact: false });
  expect(posts).toBe(1);
});

test("App registra la compra, muestra la ficha y mantiene la factura para otro activo", async () => {
  const api = server();
  const baseFetch = api.fetch.getMockImplementation()!;
  api.fetch.mockImplementation(async (input, init) => {
    const path = String(input);
    if (path === "/api/auth/me/") return response({ id: 1, username: "gestor", permissions: ["inventory.manage"], must_change_password: false });
    if (path.startsWith("/api/assets/?")) return response({ count: 0, results: [], next: null, previous: null });
    if (path === "/api/options/") return response(options);
    if (path === "/api/custodians/") return response([]);
    if (path === "/api/assets/1/") return response({ ...asset, faculty_id: 3, acquisition: { document_id: 17,
      source: "PURCHASE", reference: invoice.reference, invoice_total: invoice.invoice_total, currency: "USD",
      item_value: "300.00", acquired_on: "2026-01-15", date_unknown_reason: "" } });
    if (path === "/api/assets/1/history/" || path === "/api/assets/1/incidents/") return response([]);
    return baseFetch(input, init);
  });
  const user = userEvent.setup();
  render(<App />);
  await user.click(await screen.findByRole("button", { name: /Registrar activo/ }));
  await fillInvoice(user);
  await user.click(screen.getByRole("button", { name: "Guardar factura" }));
  await screen.findByRole("button", { name: "Registrar activo" });
  await fillAsset(user, "APP-A", "300.00");
  await user.click(screen.getByRole("button", { name: "Registrar activo" }));
  await screen.findByRole("heading", { name: "Portátil" });
  expect(screen.getByText("Total compartido de factura")).not.toBeNull();
  expect(screen.getByRole("button", { name: "Registrar activo" })).not.toBeNull();
  expect(api.documents).toHaveLength(1);
  expect(api.assets).toHaveLength(1);
});


test("si falla el segundo activo conserva el primero y reutiliza la misma factura", async () => {
  const api = server();
  const baseFetch = api.fetch.getMockImplementation()!;
  let attempts = 0;
  api.fetch.mockImplementation(async (input, init) => {
    if (String(input) === "/api/assets/" && ++attempts > 1)
      return response({ code: "duplicate_asset", detail: "Ya existe ese activo." }, 409);
    return baseFetch(input, init);
  });
  const user = userEvent.setup();
  render(<Harness />);
  await fillInvoice(user);
  await user.click(screen.getByRole("button", { name: "Guardar factura" }));
  await screen.findByRole("button", { name: "Registrar activo" });
  await fillAsset(user, "TEST-A", "300.00");
  await user.click(screen.getByRole("button", { name: "Registrar activo" }));
  await screen.findByText("TI-000001", { exact: false });
  await fillAsset(user, "TEST-A", "400.00");
  await user.click(screen.getByRole("button", { name: "Registrar activo" }));
  expect((await screen.findByRole("alert")).textContent).toContain("Ya existe ese activo");
  expect(screen.getByText("TI-000001", { exact: false })).not.toBeNull();
  expect(api.documents).toHaveLength(1);
  expect(api.assets).toHaveLength(1);
  expect(attempts).toBe(2);
});

async function queueExisting(user: ReturnType<typeof userEvent.setup>, id: number, unknown = false) {
  const idField = screen.getByLabelText("Identificador del activo existente");
  await user.clear(idField); await user.type(idField, String(id));
  await user.click(screen.getByRole("button", { name: "Consultar activo existente" }));
  await screen.findByRole("button", { name: "Añadir asociación" });
  await user.type(screen.getByLabelText("Valor del activo existente (USD)"), "45.50");
  await user.type(screen.getByLabelText("Motivo de asociación"), "Respaldo verificado");
  if (unknown) {
    await user.click(screen.getByLabelText("Fecha desconocida del activo existente"));
    await user.type(screen.getByLabelText("Motivo de fecha desconocida del activo existente"), "No consta");
  } else await user.type(screen.getByLabelText("Fecha de adquisición del activo existente"), "2026-01-15");
  await user.click(screen.getByRole("button", { name: "Añadir asociación" }));
}
test("asocia dos activos existentes en un único POST sin crear activos", async () => {
  const api = server(); const base = api.fetch.getMockImplementation()!;
  api.fetch.mockImplementation(async (input, init) => {
    const match = String(input).match(/^\/api\/assets\/(\d+)\/$/);
    if (match) return response({ ...asset, id: Number(match[1]), code: "EX-" + match[1], revision: 4, acquisition: null });
    if (String(input) === "/api/acquisitions/" && init?.method === "POST") {
      const body = JSON.parse(String(init.body)); api.documents.push(body);
      return response({ ...invoice, items: body.items.map((item: { asset_id: number }) => ({ ...item, asset_code: "EX-" + item.asset_id })) }, 201);
    }
    return base(input, init);
  });
  const user = userEvent.setup(); render(<Harness />);
  await queueExisting(user, 9); await queueExisting(user, 10, true);
  expect(api.documents).toHaveLength(0);
  await fillInvoice(user); await user.click(screen.getByRole("button", { name: "Guardar factura" }));
  await screen.findByText("Activos vinculados");
  expect(api.documents).toHaveLength(1); expect(api.assets).toHaveLength(0);
  expect(api.documents[0]).toMatchObject({ items: [
    { asset_id: 9, expected_revision: 4, item_value: "45.50", reason: "Respaldo verificado", acquired_on: "2026-01-15" },
    { asset_id: 10, expected_revision: 4, date_unknown_reason: "No consta" },
  ] });
  expect(JSON.stringify(api.documents[0])).not.toContain('"code"');
});
test("un conflicto conserva factura y asociaciones sin reintento automático", async () => {
  const api = server(); const base = api.fetch.getMockImplementation()!;
  api.fetch.mockImplementation(async (input, init) => {
    if (String(input) === "/api/assets/9/") return response({ ...asset, id: 9, revision: 2, acquisition: null });
    if (String(input) === "/api/acquisitions/") { api.documents.push({}); return response({ code: "stale_revision", detail: "La ficha cambió." }, 409); }
    return base(input, init);
  });
  const user = userEvent.setup(); render(<Harness />);
  await queueExisting(user, 9); await fillInvoice(user);
  await user.click(screen.getByRole("button", { name: "Guardar factura" }));
  expect((await screen.findByRole("alert")).textContent).toContain("La ficha cambió.");
  expect((screen.getByLabelText("Referencia de factura") as HTMLInputElement).value).toBe("TEST-FACTURA");
  expect((screen.getByRole("button", { name: "Quitar " + asset.code }) as HTMLButtonElement).disabled).toBe(false);
  expect(api.documents).toHaveLength(1); expect(api.assets).toHaveLength(0);
});
test("rechaza una ficha con adquisición y presenta errores anidados de items", async () => {
  const api = server(); const base = api.fetch.getMockImplementation()!;
  api.fetch.mockImplementation(async (input, init) => {
    if (String(input) === "/api/assets/9/") return response({ ...asset, acquisition: { document_id: 3 } });
    if (String(input) === "/api/acquisitions/") return response({ detail: "Datos inválidos", fields: { items: [{ acquired_on: ["Fecha inválida"] }] } }, 400);
    return base(input, init);
  });
  const user = userEvent.setup(); render(<Harness />);
  await user.type(screen.getByLabelText("Identificador del activo existente"), "9");
  await user.click(screen.getByRole("button", { name: "Consultar activo existente" }));
  expect((await screen.findByRole("alert")).textContent).toContain("ya tiene adquisición");
  expect(screen.queryByRole("button", { name: "Añadir asociación" })).toBeNull();
  await fillInvoice(user); await user.click(screen.getByRole("button", { name: "Guardar factura" }));
  await screen.findByText(/items.0.acquired_on: Fecha inválida/);
  expect(screen.queryByText(/\[object Object\]/)).toBeNull();
});
