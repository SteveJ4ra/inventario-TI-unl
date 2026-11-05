import { afterEach, expect, test, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import App from "../App";
import { asset, movement, options, person } from "./fixtures";
const response = (data: unknown, status = 200) => new Response(JSON.stringify(data), { status });
afterEach(() => vi.unstubAllGlobals());
function server(operator = false) {
  const writes: { path: string; method?: string; body: Record<string, unknown> }[] = [];
  const fetch = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const path = String(input);
    if (path === "/api/auth/me/") return response({ id: 1, username: "fixture",
      permissions: [operator ? "faculties.manage" : "inventory.manage"], must_change_password: false });
    if (path === "/api/auth/csrf/") return response({ csrfToken: "test-edit-csrf" });
    if (init?.method === "PATCH" || init?.method === "POST") {
      const body = JSON.parse(String(init.body)); writes.push({ path, method: init.method, body });
      if (path === "/api/custodians/1/") return response({ ...person, ...body });
      if (path === "/api/assets/1/") return response({ ...asset, ...body, revision: 1 });
      if (path === "/api/operator/faculties/") return response({ id: 3, ...body, active: true }, 201);
      if (path === "/api/operator/faculties/3/") return response({ id: 3, name: "Facultad ficticia", ...body });
      return response({});
    }
    if (path.startsWith("/api/assets/?")) return response({ count: 1, results: [asset], next: null, previous: null });
    if (path === "/api/options/") return response(options);
    if (path === "/api/custodians/") return response([person]);
    if (path === "/api/assets/1/") return response(asset);
    if (path === "/api/assets/1/movements/") return response([movement]);
    if (path === "/api/assets/1/incidents/") return response([]);
    if (path === "/api/assets/1/history/") return response([
      { event_type: "asset_change", event_id: 4, occurred_at: movement.occurred_at, actor: movement.actor,
        resulting_revision: 2, data: { before: { name: "Anterior" }, after: { name: "Corregido" }, reason: "Verificación histórica" } },
      { event_type: "movement", event_id: movement.id, occurred_at: movement.occurred_at, actor: movement.actor,
        resulting_revision: 1, data: movement },
    ]);
    if (path === "/api/operator/faculties/") return response([{ id: 3, name: "Facultad ficticia", active: false }]);
    throw new Error("Unexpected " + path);
  });
  vi.stubGlobal("fetch", fetch); return { fetch, writes };
}
test("edición de activo muestra diferencias y solo envía PATCH al confirmar", async () => {
  const api = server(), user = userEvent.setup(); render(<App />);
  await user.click(await screen.findByRole("button", { name: "Ver ficha de TI-000001" }));
  await user.click(await screen.findByRole("button", { name: "Editar ficha" }));
  const name = screen.getByLabelText("Nombre de activo");
  await user.clear(name); await user.type(name, "Etiqueta corregida");
  await user.type(screen.getByLabelText("Motivo de edición"), "Inventario verificado");
  await user.click(screen.getByRole("button", { name: "Revisar cambios" }));
  expect(api.writes).toHaveLength(0);
  expect(screen.getByText(/Etiqueta corregida/)).toBeDefined();
  expect(screen.queryByLabelText("Facultad responsable")).toBeNull();
  await user.click(screen.getByRole("button", { name: "Confirmar cambios" }));
  await waitFor(() => expect(api.writes).toHaveLength(1));
  expect(api.writes[0]).toMatchObject({ method: "PATCH", body: { expected_revision: 0, name: "Etiqueta corregida", reason: "Inventario verificado" } });
  expect(api.writes[0].body).not.toHaveProperty("condition");
});
test("historial combinado conserva movimientos y presenta ediciones", async () => {
  server(); const user = userEvent.setup(); render(<App />);
  await user.click(await screen.findByRole("button", { name: "Ver ficha de TI-000001" }));
  await screen.findByText("Verificación histórica");
  expect(screen.getByText("Docente de prueba")).toBeDefined();
});
test("Operador administra facultades inactivas sin consultas de inventario", async () => {
  const api = server(true), user = userEvent.setup(); render(<App />);
  await screen.findByRole("heading", { name: "Administrar facultades" });
  expect(api.fetch.mock.calls.some(([path]) => String(path).startsWith("/api/assets"))).toBe(false);
  await user.click(await screen.findByRole("button", { name: "Editar Facultad ficticia" }));
  await user.click(screen.getByLabelText("Facultad activa"));
  await user.click(screen.getByRole("button", { name: "Revisar cambios" }));
  await user.click(screen.getByRole("button", { name: "Confirmar cambios" }));
  expect(api.writes[0]).toMatchObject({ method: "PATCH", body: { active: true } });
});

test("revisión obsoleta conserva cambios y no reintenta ni confirma éxito", async () => {
  const api = server(), base = api.fetch.getMockImplementation()!, user = userEvent.setup();
  api.fetch.mockImplementation(async (input, init) => {
    if (String(input) === "/api/assets/1/" && init?.method === "PATCH") {
      api.writes.push({ path: String(input), method: init.method, body: JSON.parse(String(init.body)) });
      return response({ code: "stale_revision", detail: "La ficha cambió. Recárgala antes de repetir." }, 409);
    }
    return base(input, init);
  });
  render(<App />);
  await user.click(await screen.findByRole("button", { name: "Ver ficha de TI-000001" }));
  await user.click(await screen.findByRole("button", { name: "Editar ficha" }));
  const name = screen.getByLabelText("Nombre de activo"); await user.clear(name); await user.type(name, "Pendiente");
  await user.type(screen.getByLabelText("Motivo de edición"), "Revisión manual");
  await user.click(screen.getByRole("button", { name: "Revisar cambios" }));
  await user.click(screen.getByRole("button", { name: "Confirmar cambios" }));
  expect((await screen.findByRole("alert")).textContent).toContain("Recárgala");
  expect(api.writes).toHaveLength(1);
  expect(screen.queryByText("Ficha actualizada.")).toBeNull();
  await user.click(screen.getByRole("button", { name: "Volver a editar" }));
  expect((screen.getByLabelText("Nombre de activo") as HTMLInputElement).value).toBe("Pendiente");
});
test("respuesta de error del catálogo conserva el formulario del Operador", async () => {
  const api = server(true), base = api.fetch.getMockImplementation()!, user = userEvent.setup();
  api.fetch.mockImplementation(async (input, init) => String(input) === "/api/operator/faculties/" && init?.method === "POST"
    ? response({ code: "duplicate_faculty", detail: "Ya existe esa facultad." }, 409) : base(input, init));
  render(<App />); await screen.findByRole("heading", { name: "Administrar facultades" });
  await user.type(screen.getByLabelText("Nombre de nueva facultad"), "Facultad duplicada");
  await user.click(screen.getByRole("button", { name: "Crear facultad" }));
  expect((await screen.findByRole("alert")).textContent).toContain("Ya existe");
  expect((screen.getByLabelText("Nombre de nueva facultad") as HTMLInputElement).value).toBe("Facultad duplicada");
  expect(screen.getByText(/falta integrar la protección real/)).toBeDefined();
});

test("edición de custodio confirma snapshot esperado y motivo sin revisión de activo", async () => {
  const api = server(), user = userEvent.setup(); render(<App />);
  await user.click(await screen.findByRole("button", { name: "Editar custodios" }));
  await user.click(await screen.findByRole("button", { name: "Editar Docente de prueba" }));
  const name = screen.getByLabelText("Nombre del custodio"); await user.clear(name); await user.type(name, "Docente corregido");
  await user.type(screen.getByLabelText("Motivo de edición"), "Perfil verificado");
  await user.click(screen.getByRole("button", { name: "Revisar cambios" }));
  expect(api.writes).toHaveLength(0);
  await user.click(screen.getByRole("button", { name: "Confirmar cambios" }));
  await waitFor(() => expect(api.writes).toHaveLength(1));
  expect(api.writes[0]).toMatchObject({ method: "PATCH", path: "/api/custodians/1/", body: {
    full_name: "Docente corregido", reason: "Perfil verificado",
    expected_profile: { full_name: person.full_name, email: person.email, department: person.department },
  } });
  expect(api.writes[0].body).not.toHaveProperty("expected_revision");
});
test("perfil obsoleto conserva formulario de custodio sin éxito ficticio", async () => {
  const api = server(), base = api.fetch.getMockImplementation()!, user = userEvent.setup();
  api.fetch.mockImplementation(async (input, init) => String(input) === "/api/custodians/1/" && init?.method === "PATCH"
    ? response({ code: "stale_profile", detail: "El perfil cambió. Consúltalo antes de repetir." }, 409) : base(input, init));
  render(<App />); await user.click(await screen.findByRole("button", { name: "Editar custodios" }));
  await user.click(await screen.findByRole("button", { name: "Editar Docente de prueba" }));
  const email = screen.getByLabelText("Correo del custodio"); await user.clear(email); await user.type(email, "nuevo@example.org");
  await user.type(screen.getByLabelText("Motivo de edición"), "Correo verificado");
  await user.click(screen.getByRole("button", { name: "Revisar cambios" }));
  await user.click(screen.getByRole("button", { name: "Confirmar cambios" }));
  expect((await screen.findByRole("alert")).textContent).toContain("El perfil cambió");
  await user.click(screen.getByRole("button", { name: "Volver a editar" }));
  expect((screen.getByLabelText("Correo del custodio") as HTMLInputElement).value).toBe("nuevo@example.org");
});

test("cuenta con ambos permisos puede administrar y volver sin conceder roles", async () => {
  const api = server(), base = api.fetch.getMockImplementation()!, user = userEvent.setup();
  api.fetch.mockImplementation(async (input, init) => String(input) === "/api/auth/me/"
    ? response({ id: 1, username: "dual", permissions: ["inventory.manage", "faculties.manage"], must_change_password: false })
    : base(input, init));
  render(<App />);
  await user.click(await screen.findByRole("button", { name: "Administrar facultades" }));
  await screen.findByRole("heading", { name: "Administrar facultades" });
  await user.click(screen.getByRole("button", { name: "Volver al inventario" }));
  expect(screen.getByRole("button", { name: /Registrar activo/ })).toBeDefined();
});
