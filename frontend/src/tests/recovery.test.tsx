import { expect, test, vi } from "vitest";
import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import App from "../App";
import { request } from "../api";
import type { Asset, HistoryEntry, Incident } from "../types";
import { asset, options, person } from "./fixtures";

vi.mock("../api", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../api")>()),
  request: vi.fn(),
}));

test("reporta robo desde la ficha asignada, muestra custodia anterior y recupera con inspección", async () => {
  let current: Asset = { ...asset, assignment: "asignado", current_custodian: person };
  let incidents: Incident[] = [];
  const history: HistoryEntry[] = [];
  const api = vi.mocked(request);
  api.mockReset();
  api.mockImplementation(async (path, opts) => {
    if (path === "/auth/me/") return { ...asset.created_by, permissions: ["inventory.manage"], must_change_password: false };
    if (path.startsWith("/assets/?")) return { count: 1, results: [current] };
    if (path === "/options/") return options;
    if (path === "/custodians/") return [person];
    if (path === "/assets/1/") return current;
    if (path === "/assets/1/history/") return [...history];
    if (path === "/assets/1/incidents/") {
      if (!opts?.body) return incidents;
      const report: Incident = {
        id: 9, asset_id: 1, type: "stolen", description: "No está en su ubicación",
        status: "open", reported_by: asset.created_by, reported_at: asset.created_at,
        resolution_note: "", resolved_by: null, resolved_at: null,
      };
      incidents = [report];
      history.unshift({
        event_type: "incident", event_id: 1, resulting_revision: 1,
        actor: asset.created_by, occurred_at: asset.created_at,
        data: { projection_id: 9, after: { event: {
          ...report, last_location: current.location, last_custodian_snapshot: person,
        } } },
      });
      current = {
        ...current, lifecycle_status: "no_localizado", assignment: null, current_custodian: null,
        revision: 1, last_lifecycle_status: "localizado", last_assignment: "asignado",
        last_condition: current.condition, last_location: current.location, last_custodian: person,
      };
      return report;
    }
    if (path === "/assets/1/recover/" && opts?.body) {
      incidents = [{ ...incidents[0], status: "recovered" }];
      history.unshift({
        event_type: "recovery", event_id: 2, resulting_revision: 2,
        actor: asset.created_by, occurred_at: asset.created_at,
        data: { projection_id: 3, after: { event: {
          incident_id: 9, inspected_condition: "averiado", recovered_location: "Recepción", note: "",
        } } },
      });
      current = { ...asset, condition: "averiado", location: "Recepción", revision: 2 };
      return history[0];
    }
    throw new Error("Ruta inesperada: " + path);
  });
  const user = userEvent.setup();
  render(<App />);
  await user.click(await screen.findByRole("button", { name: "Ver ficha de TI-000001" }));
  await user.selectOptions(await screen.findByLabelText("Tipo de novedad"), "stolen");
  await user.type(screen.getByLabelText("Descripción de la novedad"), "No está en su ubicación");
  await user.click(screen.getByRole("button", { name: "Registrar novedad" }));
  expect(await screen.findByText("No localizado")).toBeTruthy();
  expect(api).toHaveBeenCalledWith("/assets/1/incidents/", {
    body: { expected_revision: 0, type: "stolen", description: "No está en su ubicación" },
  });
  expect(screen.getByText("Último custodio conocido").nextElementSibling?.textContent).toBe(person.full_name);
  expect(screen.queryByText("Custodio actual")).toBeNull();
  for (const name of ["Entregar", "Devolver", "Cambiar condición", "Iniciar mantenimiento", "Resolver novedad"]) {
    expect(screen.queryByRole("button", { name })).toBeNull();
  }
  const panel = within(screen.getByRole("region", { name: "Daños y observaciones" }));
  await user.selectOptions(panel.getByLabelText("Condición tras la inspección"), "averiado");
  await user.type(panel.getByLabelText("Ubicación de recuperación"), "Recepción");
  await user.click(panel.getByRole("button", { name: "Registrar recuperación" }));
  expect(api.mock.calls.some(([path]) => path === "/assets/1/recover/")).toBe(false);
  await user.click(panel.getByRole("checkbox", { name: "Confirmo que inspeccioné el activo." }));
  await user.click(panel.getByRole("button", { name: "Registrar recuperación" }));
  expect(await screen.findByText("Recuperación del activo · Reporte #9")).toBeTruthy();
  expect(screen.getByText("Reporte de robo #9")).toBeTruthy();
  expect(screen.getByText(/Custodia anterior: Docente de prueba/)).toBeTruthy();
  expect(screen.getByText("TI-000001")).toBeTruthy();
  expect(screen.queryByText("No localizado")).toBeNull();
  expect(screen.getByText("Sin mantenimiento en curso.")).toBeTruthy();
  expect(api).toHaveBeenCalledWith("/assets/1/recover/", {
    body: {
      expected_revision: 1, inspection_confirmed: true, inspected_condition: "averiado",
      recovered_location: "Recepción", note: "",
    },
  });
});
