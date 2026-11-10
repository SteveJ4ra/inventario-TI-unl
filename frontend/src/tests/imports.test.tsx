import { afterEach, expect, test, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Imports } from "../components/Imports";
import type { ImportBatch } from "../types";

const hash = "a".repeat(64);
const base: ImportBatch = {
  batch_id: "0f0f0f0f-0f0f-0f0f-0f0f-0f0f0f0f0f0f",
  kind: "assets",
  schema_version: "v1",
  state: "PREVIEW_READY",
  content_hash: hash,
  summary: {
    row_count: 1,
    valid_rows: 1,
    invalid_rows: 0,
    error_count: 0,
    document_count: 1,
  },
  errors: [],
  rows_count: 1,
  owner: { id: 1, username: "gestor" },
  created_at: "2026-11-01T12:00:00Z",
  confirmed_at: null,
  applied_at: null,
  expires_at: "2026-11-01T12:30:00Z",
  applied_result: null,
};
const row = {
  row_number: 2,
  values: {
    name: "Portátil",
    description: "Equipo de práctica",
    category: "portatil",
    brand: "Marca",
    model: "M1",
    serial_number: "S-001",
    location: "Laboratorio",
    condition: "operativo",
    faculty_id: "1",
    acquisition_document_id: "",
    document_key: "doc-1",
    acquisition_source: "purchase",
    document_reference: "FAC-001",
    document_date: "2026-01-01",
    supplier: "Proveedor",
    invoice_total: "100.00",
    donation_support_type: "",
    acquired_on: "2026-01-02",
    date_unknown_reason: "",
    item_value: "50.00",
  },
};

function response(data: unknown, status = 200) {
  return Promise.resolve(
    new Response(JSON.stringify(data), {
      status,
      headers: { "Content-Type": "application/json" },
    }),
  );
}

function batchWithRows(current: ImportBatch) {
  return {
    ...current,
    rows: { count: 1, next: null, previous: null, results: [row] },
  };
}

function mockApi(initial: ImportBatch) {
  let current = initial;
  const fetcher = vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
    const url = String(input);
    const method = init?.method || "GET";
    if (url.endsWith("/api/auth/csrf/"))
      return response({ csrfToken: "fixture-token" });
    if (url.endsWith("/api/imports/previews"))
      return response(current, current.state === "INVALID" ? 400 : 201);
    if (method === "POST" && url.endsWith("/confirm")) {
      current = {
        ...current,
        state: "CONFIRMED_ONCE",
        confirmed_at: "2026-11-01T12:01:00Z",
      };
      return response(current);
    }
    if (method === "POST" && url.endsWith("/apply")) {
      current = {
        ...current,
        state: "APPLIED",
        applied_at: "2026-11-01T12:02:00Z",
        rows_count: 0,
        applied_result: { created: 1 },
      };
      return response(current, 201);
    }
    if (method === "GET" && url.includes("/api/imports/"))
      return response(batchWithRows(current));
    return response({ code: "not_found", detail: "No encontrado." }, 404);
  });
  vi.stubGlobal("fetch", fetcher);
  return fetcher;
}

async function chooseFile(user: ReturnType<typeof userEvent.setup>) {
  const file = new File(["name,description"], "assets.csv", {
    type: "text/csv",
  });
  await user.upload(screen.getByLabelText(/Archivo CSV/), file);
}

afterEach(() => vi.unstubAllGlobals());

test("flujo válido exige revisión, confirmación y aplicación final", async () => {
  mockApi(base);
  const user = userEvent.setup();
  render(<Imports />);
  await chooseFile(user);
  await user.click(screen.getByRole("button", { name: "Validar archivo" }));
  expect(await screen.findByText("Vista previa del lote")).toBeTruthy();
  expect(await screen.findByText("Portátil")).toBeTruthy();
  expect(screen.getByText(/Se crearán/)).toBeTruthy();
  const confirm = screen.getByRole("button", {
    name: "Confirmar vista previa",
  }) as HTMLButtonElement;
  expect(confirm.disabled).toBe(true);
  await user.click(screen.getByLabelText("Revisé todas las filas y el resumen."));
  expect(confirm.disabled).toBe(false);
  await user.click(confirm);
  expect(await screen.findByText("Confirmación final")).toBeTruthy();
  await user.click(screen.getByRole("button", { name: "Crear 1 activos" }));
  expect(await screen.findByText("Importación aplicada")).toBeTruthy();
  expect(screen.getByText("Importación aplicada correctamente.")).toBeTruthy();
});

test("preview inválido muestra todos los errores y no permite confirmar", async () => {
  mockApi({
    ...base,
    state: "INVALID",
    summary: { ...base.summary, valid_rows: 0, invalid_rows: 1, error_count: 1 },
    errors: [
      {
        row: 2,
        field: "acquisition_document_id",
        message: "Indica un documento existente o una document_key nueva, no ambos.",
      },
    ],
  });
  const user = userEvent.setup();
  render(<Imports />);
  await chooseFile(user);
  await user.click(screen.getByRole("button", { name: "Validar archivo" }));
  expect(
    await screen.findByText("El archivo necesita correcciones"),
  ).toBeTruthy();
  expect(screen.getAllByText("Documento").length).toBeGreaterThan(0);
  expect(
    screen.getByText(
      "Indica un documento existente o una document_key nueva, no ambos.",
    ),
  ).toBeTruthy();
  expect(
    screen.queryByRole("button", { name: "Confirmar vista previa" }),
  ).toBeNull();
});

test("la plantilla usa el tipo seleccionado y la descarga es directa", async () => {
  const user = userEvent.setup();
  render(<Imports />);
  await user.click(screen.getByRole("tab", { name: "Lotes de licencias" }));
  const link = screen.getByRole("link", { name: "Descargar plantilla" });
  expect(link.getAttribute("href")).toBe(
    "/api/imports/templates/license_lots/",
  );
});
