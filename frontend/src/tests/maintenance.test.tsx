import { expect, test, vi } from "vitest";
import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import App from "../App";
import { ApiError, request } from "../api";
import { MaintenancePanel } from "../components/MaintenancePanel";
import type { HistoryEntry, Maintenance } from "../types";
import { asset, movement, options, person } from "./fixtures";

vi.mock("../api", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../api")>()),
  request: vi.fn(),
}));

const started: Maintenance = {
  id: 8, asset_id: asset.id, status: "in_progress", description: "Revisión preventiva",
  previous_location: "Laboratorio", workshop_location: "Taller",
  receiving_location: "", result: "", revision: 1,
};
const historical: HistoryEntry = {
  event_type: "movement", event_id: movement.id, data: movement,
  actor: movement.actor, occurred_at: movement.occurred_at, resulting_revision: 0,
};

test("la ficha inicia, bloquea entrega y cierra con una ubicación editada y confirmada", async () => {
  let current = { ...asset };
  let maintenance = started;
  const history: HistoryEntry[] = [historical];
  const addEntry = () => history.unshift({
    event_type: "maintenance", event_id: maintenance.revision,
    actor: asset.created_by, occurred_at: asset.created_at,
    resulting_revision: maintenance.revision,
    data: { projection_id: maintenance.id, after: { event: maintenance } },
  });
  const api = vi.mocked(request);
  api.mockReset();
  api.mockImplementation(async (path, opts) => {
    if (path === "/auth/me/") return { ...asset.created_by, permissions: ["inventory.manage"], must_change_password: false };
    if (path.startsWith("/assets/?")) return { count: 1, results: [current] };
    if (path === "/options/") return options;
    if (path === "/custodians/") return [person];
    if (path === "/assets/1/") return current;
    if (path === "/assets/1/history/") return [...history];
    if (path === "/assets/1/incidents/") return [];
    if (path === "/maintenance/8/") return maintenance;
    if (path === "/assets/1/maintenance/" && opts?.body) {
      current = { ...current, active_maintenance_id: 8, location: "Taller", revision: 1 };
      addEntry();
      return maintenance;
    }
    if (path === "/maintenance/8/close/" && opts?.body) {
      maintenance = {
        ...maintenance, status: "completed", result: String(opts.body.result),
        receiving_location: String(opts.body.receiving_location), revision: 2,
      };
      current = {
        ...current, active_maintenance_id: null, location: maintenance.receiving_location,
        revision: 2,
      };
      addEntry();
      return maintenance;
    }
    throw new Error("Ruta inesperada: " + path);
  });
  const user = userEvent.setup();
  render(<App />);
  await user.click(await screen.findByRole("button", { name: "Ver ficha de TI-000001" }));
  await user.type(await screen.findByLabelText("Descripción del mantenimiento"), "Revisión preventiva");
  await user.type(screen.getByLabelText("Ubicación del taller"), "Taller");
  await user.click(screen.getByRole("button", { name: "Iniciar mantenimiento" }));
  expect(await screen.findByText("Mantenimiento en curso")).toBeTruthy();
  expect(api).toHaveBeenCalledWith("/assets/1/maintenance/", {
    body: { description: "Revisión preventiva", workshop_location: "Taller", expected_revision: 0 },
  });
  expect(screen.queryByRole("button", { name: "Entregar" })).toBeNull();
  expect(screen.getByRole("button", { name: "Cambiar condición" })).toBeTruthy();
  const panel = within(screen.getByRole("region", { name: "Mantenimiento" }));
  const location = panel.getByRole<HTMLInputElement>("combobox", { name: "Ubicación de recepción" });
  expect(location.value).toBe("Laboratorio");
  const datalist = document.getElementById(location.getAttribute("list")!);
  expect(datalist?.querySelector('option[value="Aula"]')).toBeTruthy();
  await user.clear(location);
  await user.type(location, "Bodega");
  await user.type(panel.getByLabelText("Resultado"), "Revisado");
  await user.click(panel.getByRole("button", { name: "Cerrar mantenimiento" }));
  expect(api.mock.calls.some(([path]) => path === "/maintenance/8/close/")).toBe(false);
  await user.click(panel.getByRole("checkbox", { name: /Confirmo la ubicación/ }));
  await user.click(panel.getByRole("button", { name: "Cerrar mantenimiento" }));
  expect(await screen.findByText("Cierre de mantenimiento #8")).toBeTruthy();
  expect(screen.getByText("Inicio de mantenimiento #8")).toBeTruthy();
  expect(screen.getByText("Resultado: Revisado · Recepción: Bodega")).toBeTruthy();
  expect(api).toHaveBeenCalledWith("/maintenance/8/close/", {
    body: { result: "Revisado", receiving_location: "Bodega", location_confirmed: true, expected_revision: 1 },
  });
  expect(screen.getByRole("button", { name: "Entregar" })).toBeTruthy();
  expect(screen.getByText("Operativo")).toBeTruthy();
});

test("no ofrece inicio para activos asignados y muestra los errores de cierre", async () => {
  const onWrite = vi.fn().mockRejectedValue(new ApiError(400, "invalid", "Ubicación inválida."));
  const user = userEvent.setup();
  const { rerender } = render(<MaintenancePanel
    asset={{ ...asset, assignment: "asignado", current_custodian: person }}
    active={null} locations={[]} history={[]} onWrite={onWrite}
  />);
  expect(screen.queryByRole("button", { name: "Iniciar mantenimiento" })).toBeNull();
  rerender(<MaintenancePanel
    asset={{ ...asset, active_maintenance_id: 8 }} active={started}
    locations={[]} history={[]} onWrite={onWrite}
  />);
  await user.type(screen.getByLabelText("Resultado"), "Revisado");
  await user.click(screen.getByRole("checkbox", { name: /Confirmo la ubicación/ }));
  await user.click(screen.getByRole("button", { name: "Cerrar mantenimiento" }));
  expect((await screen.findByRole("alert")).textContent).toContain("Ubicación inválida.");
});
