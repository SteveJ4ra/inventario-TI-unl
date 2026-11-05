import { afterEach, expect, test, vi } from "vitest";
import { render, screen, within, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import App from "../App";
import { ApiError, request } from "../api";
import { LicenseLots } from "../components/LicenseLots";
import { LicenseLotForm } from "../components/LicenseLotForm";
import { LicenseLotDetail } from "../components/LicenseLotDetail";
import type { LicenseLot, LicenseLotAudit } from "../types";

const lot: LicenseLot = {
  id: 1,
  product_name: "Suite académica",
  vendor: "Proveedor",
  license_model: "USER_SEAT",
  purchased_quantity: 10,
  in_use_quantity: 4,
  starts_on: "2026-01-01",
  ends_on: null,
  remaining_quantity: 6,
  temporal_status: "CURRENT",
  revision: 0,
  created_at: "2026-01-01T12:00:00Z",
  created_by: { id: 1, username: "gestor" },
};
function event(value = lot): LicenseLotAudit {
  const {
    product_name,
    vendor,
    license_model,
    purchased_quantity,
    in_use_quantity,
    starts_on,
    ends_on,
    revision,
  } = value;
  return {
    id: revision + 1,
    lot_id: value.id,
    actor: { id: 1, username: "gestor", recorded_label: "Gestor registrado" },
    timestamp: "2026-01-01T12:00:00Z",
    resulting_revision: revision,
    before_json: revision ? { ...lot } : {},
    after_json: {
      product_name,
      vendor,
      license_model,
      purchased_quantity,
      in_use_quantity,
      starts_on,
      ends_on,
      revision,
    },
  };
}
const page = <T,>(results: T[], extra = {}) => ({
  count: results.length,
  next: null,
  previous: null,
  results,
  ...extra,
});
const reply = (data: unknown, status = 200) =>
  Promise.resolve(
    new Response(JSON.stringify(data), {
      status,
      headers: { "Content-Type": "application/json" },
    }),
  );
function server(
  handler: (path: string, options: RequestInit) => Promise<Response>,
) {
  const fetcher = vi.fn((url: string, options: RequestInit = {}) =>
    url === "/api/auth/csrf/"
      ? reply({ csrfToken: "fixture-token" })
      : handler(url, options),
  );
  vi.stubGlobal("fetch", fetcher);
  return fetcher;
}
async function fillForm(
  user: ReturnType<typeof userEvent.setup>,
  quantity = "10",
  used = "4",
) {
  await user.type(screen.getByLabelText("Producto"), "Suite académica");
  await user.type(screen.getByLabelText("Proveedor"), "Proveedor");
  await user.selectOptions(screen.getByLabelText("Modalidad"), "USER_SEAT");
  await user.type(screen.getByLabelText("Cantidad comprada"), quantity);
  await user.type(screen.getByLabelText("Cantidad en uso"), used);
  await user.type(screen.getByLabelText("Inicio de vigencia"), "2026-01-01");
}
afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

test("exige los campos requeridos y admite cero con fin opcional", async () => {
  const user = userEvent.setup();
  const submit = vi.fn().mockResolvedValue(undefined);
  render(<LicenseLotForm onSubmit={submit} />);
  await user.click(screen.getByRole("button", { name: "Registrar lote" }));
  expect(submit).not.toHaveBeenCalled();
  await fillForm(user, "0", "0");
  expect(screen.getByText("Remanentes calculados:").textContent).toContain("0");
  await user.click(screen.getByRole("button", { name: "Registrar lote" }));
  expect(submit).toHaveBeenCalledWith({
    product_name: "Suite académica",
    vendor: "Proveedor",
    license_model: "USER_SEAT",
    purchased_quantity: 0,
    in_use_quantity: 0,
    starts_on: "2026-01-01",
    ends_on: null,
  });
  expect(
    screen.queryByLabelText(/clave|factura|custodio|equipo destino/i),
  ).toBeNull();
});

test("rechaza uso superior y fecha final anterior sin enviar datos", async () => {
  const user = userEvent.setup();
  const submit = vi.fn().mockResolvedValue(undefined);
  render(<LicenseLotForm onSubmit={submit} />);
  await fillForm(user, "10", "11");
  await user.click(screen.getByRole("button", { name: "Registrar lote" }));
  expect(screen.getByRole("alert").textContent).toContain(
    "el uso no puede superar",
  );
  await user.clear(screen.getByLabelText("Cantidad en uso"));
  await user.type(screen.getByLabelText("Cantidad en uso"), "4");
  await user.type(
    screen.getByLabelText("Fin de vigencia · opcional"),
    "2025-12-31",
  );
  await user.click(screen.getByRole("button", { name: "Registrar lote" }));
  expect(screen.getByRole("alert").textContent).toContain(
    "fecha de fin no puede ser anterior",
  );
  expect(submit).not.toHaveBeenCalled();
});

test("muestra error de campo del servidor y conserva los valores", async () => {
  const user = userEvent.setup();
  const submit = vi
    .fn()
    .mockRejectedValue(
      new ApiError(400, "invalid", "Revisa los datos.", {
        vendor: ["Valor inválido."],
      }),
    );
  render(<LicenseLotForm lot={lot} onSubmit={submit} />);
  await user.click(screen.getByRole("button", { name: "Guardar cambios" }));
  expect((await screen.findByRole("alert")).textContent).toContain(
    "Proveedor: Valor inválido.",
  );
  expect((screen.getByLabelText("Producto") as HTMLInputElement).value).toBe(
    lot.product_name,
  );
  expect(submit.mock.calls[0][0].expected_revision).toBe(0);
});

test("deshabilita el envío mientras se guarda y evita doble solicitud", async () => {
  const user = userEvent.setup();
  let finish: () => void = () => {};
  const submit = vi.fn(
    () =>
      new Promise<void>((resolve) => {
        finish = resolve;
      }),
  );
  render(<LicenseLotForm lot={lot} onSubmit={submit} />);
  await user.dblClick(screen.getByRole("button", { name: "Guardar cambios" }));
  expect(submit).toHaveBeenCalledTimes(1);
  expect(
    (screen.getByRole("button", { name: "Guardando…" }) as HTMLButtonElement)
      .disabled,
  ).toBe(true);
  finish();
  await screen.findByRole("button", { name: "Guardar cambios" });
});

test("PATCH incluye sesión, CSRF, revisión y fin nulo", async () => {
  const fetcher = server(() => reply({ ...lot, revision: 1 }));
  await request("/license-lots/1/", {
    method: "PATCH",
    body: { expected_revision: 0, ends_on: null },
  });
  expect(fetcher.mock.calls[1][1]).toMatchObject({
    method: "PATCH",
    credentials: "same-origin",
    headers: {
      "X-CSRFToken": "fixture-token",
      "Content-Type": "application/json",
    },
  });
  expect(JSON.parse(String(fetcher.mock.calls[1][1]?.body))).toEqual({
    expected_revision: 0,
    ends_on: null,
  });
});

test("combina búsqueda y filtros, pagina y limpia", async () => {
  const fetcher = server((path) => {
    const number = new URL(path, "http://localhost").searchParams.get("page");
    return reply(
      page(
        [lot],
        number === "2"
          ? { count: 51, previous: "?page=1" }
          : { count: 51, next: "?page=2" },
      ),
    );
  });
  const user = userEvent.setup();
  render(<LicenseLots />);
  await screen.findByRole("button", { name: "Ver lote Suite académica" });
  await user.type(screen.getByLabelText("Buscar lotes"), "Proveedor");
  await user.selectOptions(
    screen.getByLabelText("Filtrar modalidad"),
    "DEVICE_SEAT",
  );
  await user.selectOptions(screen.getByLabelText("Filtrar estado"), "EXPIRED");
  await user.click(screen.getByRole("button", { name: "Aplicar" }));
  await waitFor(() =>
    expect(fetcher.mock.calls.at(-1)?.[0]).toContain(
      "search=Proveedor&license_model=DEVICE_SEAT&temporal_status=EXPIRED&page=1",
    ),
  );
  await screen.findByRole("button", { name: "Ver lote Suite académica" });
  await user.click(screen.getByRole("button", { name: "Siguiente" }));
  await screen.findByText("Página 2");
  expect(fetcher.mock.calls.at(-1)?.[0]).toContain("page=2");
  await user.click(screen.getByRole("button", { name: "Limpiar" }));
  await waitFor(() =>
    expect(fetcher.mock.calls.at(-1)?.[0]).toBe("/api/license-lots/?page=1"),
  );
});

test("distingue estados y representa contenido HTML como texto", async () => {
  const product = '<img src=x onerror="alert(1)">';
  server(() =>
    reply(
      page([
        { ...lot, product_name: product, temporal_status: "EXPIRED" },
        {
          ...lot,
          id: 2,
          product_name: "Futuro",
          temporal_status: "NOT_STARTED",
        },
        { ...lot, id: 3, product_name: "Actual" },
      ]),
    ),
  );
  render(<LicenseLots />);
  expect(await screen.findByText(product)).toBeTruthy();
  expect(document.querySelector("img")).toBeNull();
  expect(screen.getByText("Vencido", { selector: "span" })).toBeTruthy();
  expect(screen.getByText("Por iniciar", { selector: "span" })).toBeTruthy();
  expect(screen.getByText("Vigente", { selector: "span" })).toBeTruthy();
  expect(screen.getByText(/no representan puestos utilizables/)).toBeTruthy();
});

test("carga alta, edición y auditoría desde la pantalla integrada", async () => {
  let current = { ...lot };
  const writes: RequestInit[] = [];
  server((path, options) => {
    if (options.method === "POST") {
      writes.push(options);
      return reply(current, 201);
    }
    if (options.method === "PATCH") {
      writes.push(options);
      current = {
        ...current,
        in_use_quantity: 3,
        remaining_quantity: 7,
        revision: 1,
      };
      return reply(current);
    }
    if (path.includes("history/")) return reply(page([event(current)]));
    if (path === "/api/license-lots/1/") return reply(current);
    return reply(page([]));
  });
  const user = userEvent.setup();
  render(<LicenseLots />);
  await screen.findByText(/No hay lotes que mostrar/);
  await user.click(screen.getByRole("button", { name: "＋ Registrar lote" }));
  await fillForm(user);
  await user.click(screen.getByRole("button", { name: "Registrar lote" }));
  await user.click(await screen.findByRole("button", { name: "Editar lote" }));
  await user.clear(screen.getByLabelText("Cantidad en uso"));
  await user.type(screen.getByLabelText("Cantidad en uso"), "3");
  await user.click(screen.getByRole("button", { name: "Guardar cambios" }));
  expect(await screen.findByText("Remanentes: 7")).toBeTruthy();
  expect(screen.getByText("Edición del lote · Revisión 1")).toBeTruthy();
  expect(screen.getByText("Gestor registrado")).toBeTruthy();
  expect(screen.getByText("Antes")).toBeTruthy();
  expect(screen.getByText("Después")).toBeTruthy();
  expect(writes.map((value) => value.method)).toEqual(["POST", "PATCH"]);
});

test("un conflicto recarga los datos actuales sin reenviar la edición", async () => {
  let current = { ...lot };
  const fetcher = server((path, options) => {
    if (options.method === "PATCH") {
      current = {
        ...lot,
        in_use_quantity: 8,
        remaining_quantity: 2,
        revision: 1,
      };
      return reply({ code: "stale_revision", detail: "El lote cambió." }, 409);
    }
    return reply(path.includes("history/") ? page([event(current)]) : current);
  });
  const user = userEvent.setup();
  render(<LicenseLotDetail lotId={1} onBack={vi.fn()} />);
  await user.click(await screen.findByRole("button", { name: "Editar lote" }));
  await user.clear(screen.getByLabelText("Cantidad en uso"));
  await user.type(screen.getByLabelText("Cantidad en uso"), "3");
  await user.click(screen.getByRole("button", { name: "Guardar cambios" }));
  expect(await screen.findByText("Remanentes: 2")).toBeTruthy();
  expect(screen.getByRole("alert").textContent).toContain(
    "No se reenviaron tus cambios",
  );
  expect(screen.queryByRole("button", { name: "Guardar cambios" })).toBeNull();
  expect(
    fetcher.mock.calls.filter(([, options]) => options?.method === "PATCH"),
  ).toHaveLength(1);
  await user.click(screen.getByRole("button", { name: "Editar lote" }));
  expect(
    (screen.getByLabelText("Cantidad en uso") as HTMLInputElement).value,
  ).toBe("8");
});

test("historial paginado y aviso de vencimiento conservan remanentes", async () => {
  const expired = {
    ...lot,
    temporal_status: "EXPIRED" as const,
    ends_on: "2026-01-01",
  };
  const fetcher = server((path) =>
    reply(
      path.includes("history/")
        ? page(
            [event(expired)],
            path.endsWith("page=1")
              ? { count: 51, next: "?page=2" }
              : { count: 51, previous: "?page=1" },
          )
        : expired,
    ),
  );
  const user = userEvent.setup();
  render(<LicenseLotDetail lotId={1} onBack={vi.fn()} />);
  expect(await screen.findByText("Remanentes: 6")).toBeTruthy();
  expect(screen.getByText(/Lote vencido: los remanentes/)).toBeTruthy();
  await user.click(
    within(
      screen.getByRole("navigation", { name: "Páginas del historial" }),
    ).getByRole("button", { name: "Siguiente" }),
  );
  await screen.findByText("Página 2");
  expect(
    fetcher.mock.calls.some(([path]) => path.endsWith("history/?page=2")),
  ).toBe(true);
});

test("distingue error de red de listado vacío y permite consultar otra vez", async () => {
  const fetcher = vi
    .fn()
    .mockRejectedValueOnce(new TypeError("offline"))
    .mockImplementation(() => reply(page([])));
  vi.stubGlobal("fetch", fetcher);
  const user = userEvent.setup();
  render(<LicenseLots />);
  expect((await screen.findByRole("alert")).textContent).toContain(
    "No se pudo conectar",
  );
  expect(screen.queryByText(/No hay lotes que mostrar/)).toBeNull();
  await user.click(
    screen.getByRole("button", { name: "Volver a consultar lotes" }),
  );
  expect(await screen.findByText(/No hay lotes que mostrar/)).toBeTruthy();
});

test("403 desmonta la vista privada de licencias", async () => {
  server((path) => {
    if (path === "/api/auth/me/") return reply({ id: 1, username: "gestor", permissions: ["inventory.manage"], must_change_password: false });
    if (path.startsWith("/api/assets/")) return reply(page([]));
    if (path === "/api/options/")
      return reply({
        categories: [],
        conditions: [],
        assignments: [],
        locations: [],
      });
    if (path === "/api/custodians/") return reply([]);
    return reply({ code: "permission_denied", detail: "Sin acceso" }, 403);
  });
  const user = userEvent.setup();
  render(<App />);
  await user.click(await screen.findByRole("button", { name: /Licencias/ }));
  expect(await screen.findByRole("button", { name: "Ingresar" })).toBeTruthy();
  expect(screen.queryByText("Lotes de licencias")).toBeNull();
});

test("cerrar sesión limpia la pantalla privada y vuelve a login", async () => {
  server((path) => {
    if (path === "/api/auth/me/") return reply({ id: 1, username: "gestor", permissions: ["inventory.manage"], must_change_password: false });
    if (path === "/api/auth/logout/")
      return reply({ detail: "Sesión cerrada" });
    if (path.startsWith("/api/assets/")) return reply(page([]));
    if (path === "/api/options/")
      return reply({
        categories: [],
        conditions: [],
        assignments: [],
        locations: [],
      });
    if (path === "/api/custodians/") return reply([]);
    return reply(page([lot]));
  });
  const user = userEvent.setup();
  render(<App />);
  await user.click(await screen.findByRole("button", { name: /Licencias/ }));
  await screen.findByText("Suite académica");
  await user.click(screen.getByRole("button", { name: /Cerrar sesión/ }));
  expect(await screen.findByRole("button", { name: "Ingresar" })).toBeTruthy();
  expect(screen.queryByText("Suite académica")).toBeNull();
});
