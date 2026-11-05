// Paquete 007: pruebas del flujo web del enlace QR.
import { beforeEach, expect, test, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import App from "../App";
import { ApiError } from "../api";
import { asset, options } from "./fixtures";

const { requestMock } = vi.hoisted(() => ({ requestMock: vi.fn() }));

vi.mock("../api", async (importOriginal) => {
  const actual = await importOriginal<typeof import("../api")>();
  return { ...actual, request: requestMock };
});

const gestor = { id: 1, username: "gestor" };

// Respuestas simuladas del backend 002 + endpoints QR del paquete 007.
function simulateApi({ authenticated = true, missing = false, denied = false } = {}) {
  let hasSession = authenticated;
  requestMock.mockImplementation(async (path: string) => {
    if (path === "/auth/me/") {
      if (!hasSession) throw new ApiError(403, "not_authenticated", "Sin sesión");
      return gestor;
    }
    if (path === "/auth/login/") {
      hasSession = true;
      return gestor;
    }
    if (path.startsWith("/assets/by-code/")) {
      if (denied) throw new ApiError(403, "permission_denied", "Sin acceso");
      if (missing) throw new ApiError(404, "not_found", "No encontrado");
      return asset;
    }
    if (path === "/assets/1/") return asset;
    if (path === "/assets/1/movements/") return [];
    if (path.startsWith("/assets/?")) {
      return { count: 1, next: null, previous: null, results: [asset] };
    }
    if (path === "/options/") return options;
    if (path === "/custodians/") return [];
    throw new Error(`Consulta no simulada: ${path}`);
  });
}

beforeEach(() => {
  requestMock.mockReset();
  window.history.replaceState(null, "", "/assets/code/TI-000001");
});

test("QR sin sesión: solicita login y luego abre la misma ficha", async () => {
  simulateApi({ authenticated: false });
  const user = userEvent.setup();
  render(<App />);

  expect(await screen.findByRole("heading", { name: "Bienvenido al inventario" })).toBeTruthy();
  expect(requestMock).not.toHaveBeenCalledWith(
    "/assets/by-code/TI-000001/",
    expect.anything(),
  );

  await user.type(screen.getByLabelText("Usuario"), "gestor");
  await user.type(screen.getByLabelText("Contraseña"), "clave-de-prueba");
  await user.click(screen.getByRole("button", { name: "Ingresar" }));

  expect(await screen.findByRole("heading", { name: asset.name })).toBeTruthy();
  expect(requestMock).toHaveBeenCalledWith(
    "/assets/by-code/TI-000001/",
    expect.objectContaining({ signal: expect.any(AbortSignal) }),
  );
  expect(window.location.pathname).toBe("/assets/code/TI-000001");
});

test("QR con sesión: resuelve por código TI sin buscar por coincidencia parcial", async () => {
  simulateApi();
  render(<App />);
  expect(await screen.findByRole("heading", { name: asset.name })).toBeTruthy();
  expect(requestMock).toHaveBeenCalledWith(
    "/assets/by-code/TI-000001/",
    expect.anything(),
  );
});

test("QR inexistente: muestra mensaje genérico sin ficha de activo", async () => {
  window.history.replaceState(null, "", "/assets/code/TI-999999");
  simulateApi({ missing: true });
  render(<App />);
  expect(await screen.findByText("No se encontró el activo solicitado.")).toBeTruthy();
  expect(screen.queryByRole("heading", { name: asset.name })).toBeNull();
});

test("QR sin permiso: muestra acceso denegado sin ficha", async () => {
  simulateApi({ denied: true });
  render(<App />);
  expect(await screen.findByText("No tienes permiso para consultar este activo.")).toBeTruthy();
  expect(screen.queryByRole("heading", { name: asset.name })).toBeNull();
});

test("la navegación QR ignora parámetros de retorno externo", async () => {
  window.history.replaceState(
    null,
    "",
    "/assets/code/TI-000001?next=https%3A%2F%2Fejemplo-externo.invalid%2F",
  );
  simulateApi();
  render(<App />);
  expect(await screen.findByRole("heading", { name: asset.name })).toBeTruthy();
  expect(window.location.pathname).toBe("/assets/code/TI-000001");
  expect(window.location.host).not.toBe("ejemplo-externo.invalid");
});
