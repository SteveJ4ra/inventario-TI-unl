import { afterEach, expect, test, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ImportPanel } from "../components/Import";
import type { ImportBatch } from "../types";

const hash = "a".repeat(64);

const invalid: ImportBatch = {
  batch_id: "11111111-1111-1111-1111-111111111111",
  kind: "assets",
  schema_version: "assets-v1",
  state: "INVALID",
  content_hash: hash,
  summary: { record_count: 0, total_rows: 1 },
  errors: [
    {
      row: 3,
      field: "serial_number",
      message: "El número de serie se repite en el archivo.",
    },
  ],
  rows: [],
  row_count: 0,
  page: 1,
  next: null,
  previous: null,
  created_at: "2026-01-01T00:00:00Z",
  expires_at: "2026-01-02T00:00:00Z",
  confirmed_at: null,
  applied_at: null,
  applied_result: null,
};

const ready: ImportBatch = {
  ...invalid,
  state: "PREVIEW_READY",
  summary: { record_count: 1, total_rows: 1 },
  errors: [],
  rows: [
    {
      row: 2,
      valid: true,
      values: {
        name: "Portátil de práctica",
        brand: "Ejemplo",
        model: "A1",
        serial_number: "LAB-001",
        category: "portatil",
        condition: "operativo",
        item_value: "1200.00",
        document_key: "COMPRA-001",
      },
    },
  ],
  row_count: 1,
};

const confirmed: ImportBatch = { ...ready, state: "CONFIRMED_ONCE" };
const applied: ImportBatch = {
  ...confirmed,
  state: "APPLIED",
  applied_result: { kind: "assets", created: 1 },
};

function reply(data: unknown, status = 200) {
  return Promise.resolve(
    new Response(JSON.stringify(data), {
      status,
      headers: { "Content-Type": "application/json" },
    }),
  );
}

function file() {
  return new File(
    ["name,brand\nPortátil,Ejemplo\n"],
    "activos.csv",
    { type: "text/csv" },
  );
}

afterEach(() => vi.unstubAllGlobals());

test("ofrece la plantilla del tipo elegido", async () => {
  const user = userEvent.setup();
  render(<ImportPanel onClose={vi.fn()} onApplied={vi.fn()} />);
  const assets = screen.getByRole("link", {
    name: /Descargar plantilla assets-v1/,
  });
  expect(assets.getAttribute("href")).toContain("/imports/templates/assets/");
  await user.selectOptions(
    screen.getByLabelText("Tipo de importación"),
    "license_lots",
  );
  const lots = screen.getByRole("link", {
    name: /Descargar plantilla license-lots-v1/,
  });
  expect(lots.getAttribute("href")).toContain(
    "/imports/templates/license_lots/",
  );
});

test("muestra los errores del archivo y no permite confirmar", async () => {
  const fetchMock = vi
    .fn()
    .mockImplementationOnce(() => reply({ csrfToken: "token" }))
    .mockImplementationOnce(() => reply(invalid, 400));
  vi.stubGlobal("fetch", fetchMock);
  const user = userEvent.setup();
  render(<ImportPanel onClose={vi.fn()} onApplied={vi.fn()} />);
  await user.upload(screen.getByLabelText("Archivo CSV"), file());
  await user.click(screen.getByRole("button", { name: "Validar archivo" }));
  expect(
    await screen.findByText("El número de serie se repite en el archivo."),
  ).toBeTruthy();
  expect(screen.getByText("Fila 3")).toBeTruthy();
  expect(
    screen.queryByRole("button", { name: "Continuar a la confirmación" }),
  ).toBeNull();
});

test("exige dos confirmaciones con el mismo hash y permite aplicar", async () => {
  const fetchMock = vi
    .fn()
    .mockImplementationOnce(() => reply({ csrfToken: "token" }))
    .mockImplementationOnce(() => reply(ready))
    .mockImplementationOnce(() => reply({ csrfToken: "token" }))
    .mockImplementationOnce(() => reply(confirmed))
    .mockImplementationOnce(() => reply({ csrfToken: "token" }))
    .mockImplementationOnce(() => reply(applied));
  vi.stubGlobal("fetch", fetchMock);
  const user = userEvent.setup();
  const onApplied = vi.fn();
  const onClose = vi.fn();
  render(<ImportPanel onClose={onClose} onApplied={onApplied} />);
  await user.upload(screen.getByLabelText("Archivo CSV"), file());
  await user.click(screen.getByRole("button", { name: "Validar archivo" }));
  await user.click(
    await screen.findByRole("button", {
      name: "Continuar a la confirmación",
    }),
  );
  expect(await screen.findByText(/Vas a crear/)).toBeTruthy();
  await user.click(
    screen.getByRole("button", { name: "Crear 1 registro(s)" }),
  );
  expect(await screen.findByText(/Importación completada/)).toBeTruthy();
  expect(onApplied).toHaveBeenCalledTimes(1);
  const writes = fetchMock.mock.calls
    .filter(([url]) => /\/(confirm|apply)\/$/.test(String(url)))
    .map(([, init]) => JSON.parse(String((init as RequestInit).body)));
  expect(writes).toEqual([
    { content_hash: hash },
    { content_hash: hash },
  ]);
  expect(
    fetchMock.mock.calls.some(([url]) => String(url).endsWith("/confirm/")),
  ).toBe(true);
  expect(
    fetchMock.mock.calls.some(([url]) => String(url).endsWith("/apply/")),
  ).toBe(true);
  await user.click(
    screen.getByRole("button", { name: "Cerrar y ver inventario" }),
  );
  expect(onClose).toHaveBeenCalledTimes(1);
});
