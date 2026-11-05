import { expect, test, vi } from "vitest";
import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import App from "../App";
import { ApiError, request } from "../api";
import { IncidentPanel } from "../components/IncidentPanel";
import type { HistoryEntry, Incident } from "../types";
import { asset, options, person } from "./fixtures";

vi.mock("../api", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../api")>()),
  request: vi.fn(),
}));

const actor = { id: 1, username: "gestor" };
const assigned = {
  ...asset, assignment: "asignado", current_custodian: person, revision: 4,
};
const report: Incident = {
  id: 7, asset_id: assigned.id, type: "damage", description: "Bisagra suelta",
  status: "open", reported_by: actor, reported_at: "2026-11-04T13:00:00Z",
  resolution_note: "", resolved_by: null, resolved_at: null,
};

function mockWorkspace(conflict = false) {
  let revision = assigned.revision;
  let incidents: Incident[] = [];
  const history: HistoryEntry[] = [];
  const addToHistory = (incident: Incident) => {
    history.unshift({
      event_type: "incident", event_id: revision, actor,
      occurred_at: incident.resolved_at ?? incident.reported_at,
      resulting_revision: revision,
      data: { projection_id: incident.id, after: { event: incident } },
    });
  };
  const api = vi.mocked(request);
  api.mockReset();
  api.mockImplementation(async (path, opts) => {
    if (path === "/auth/me/") return actor;
    if (path.startsWith("/assets/?")) return { count: 1, results: [assigned] };
    if (path === "/options/") return options;
    if (path === "/custodians/") return [person];
    if (path === "/assets/1/") return { ...assigned, revision };
    if (path === "/assets/1/history/") return [...history];
    if (path === "/assets/1/incidents/") {
      if (!opts?.body) return incidents;
      revision += 1;
      if (conflict) throw new ApiError(409, "stale_revision", "Recarga la ficha.");
      incidents = [report];
      addToHistory(report);
      return report;
    }
    if (path === "/incidents/7/resolve/" && opts?.body) {
      revision += 1;
      const resolved: Incident = {
        ...report, status: "resolved", resolution_note: String(opts.body.resolution_note),
        resolved_by: actor, resolved_at: "2026-11-04T14:00:00Z",
      };
      incidents = [resolved];
      addToHistory(resolved);
      return resolved;
    }
    throw new Error("Ruta inesperada: " + path);
  });
  return api;
}

test("registra y resuelve una novedad en la ficha asignada y conserva ambos eventos", async () => {
  const api = mockWorkspace();
  const user = userEvent.setup();
  render(<App />);
  await user.click(await screen.findByRole("button", { name: "Ver ficha de TI-000001" }));
  await user.type(await screen.findByLabelText("Descripción de la novedad"), "Bisagra suelta");
  await user.click(screen.getByRole("button", { name: "Registrar novedad" }));
  expect(await screen.findByText("1 novedad pendiente")).toBeTruthy();
  expect(api).toHaveBeenCalledWith("/assets/1/incidents/", {
    body: { type: "damage", description: "Bisagra suelta", expected_revision: 4 },
  });
  const pending = within(screen.getByRole("region", { name: "Daños y observaciones" }));
  await user.type(pending.getByLabelText("Nota de resolución"), "Se revisó el equipo");
  await user.click(pending.getByRole("button", { name: "Resolver novedad" }));
  expect(await screen.findByText("Sin novedades pendientes.")).toBeTruthy();
  expect(api).toHaveBeenCalledWith("/incidents/7/resolve/", {
    body: { resolution_note: "Se revisó el equipo", expected_revision: 5 },
  });
  expect(screen.getByText("Registro de novedad · Daño #7")).toBeTruthy();
  expect(screen.getByText("Resolución de novedad · Daño #7")).toBeTruthy();
  expect(screen.getByText("Se revisó el equipo", { exact: false })).toBeTruthy();
  expect(screen.getByText("Docente de prueba")).toBeTruthy();
  expect(screen.getByText("Operativo")).toBeTruthy();
});

test("rechaza una nota en blanco y muestra errores de la API", async () => {
  const onWrite = vi.fn().mockRejectedValue(new ApiError(400, "invalid", "Nota inválida."));
  const user = userEvent.setup();
  render(<IncidentPanel asset={assigned} incidents={[report]} onWrite={onWrite} />);
  const note = screen.getByLabelText("Nota de resolución");
  await user.type(note, "   ");
  await user.click(screen.getByRole("button", { name: "Resolver novedad" }));
  expect((await screen.findByRole("alert")).textContent).toContain("Escribe una nota de resolución.");
  expect(onWrite).not.toHaveBeenCalled();
  await user.clear(note);
  await user.type(note, "Nota");
  await user.click(screen.getByRole("button", { name: "Resolver novedad" }));
  await waitFor(() => expect(screen.getByRole("alert").textContent).toContain("Nota inválida."));
});

test("un conflicto recarga la ficha sin reenviar la novedad", async () => {
  const api = mockWorkspace(true);
  const user = userEvent.setup();
  render(<App />);
  await user.click(await screen.findByRole("button", { name: "Ver ficha de TI-000001" }));
  await user.type(await screen.findByLabelText("Descripción de la novedad"), "Bisagra suelta");
  await user.click(screen.getByRole("button", { name: "Registrar novedad" }));
  expect(await screen.findByText("Recarga la ficha.")).toBeTruthy();
  await waitFor(() => expect(api.mock.calls.filter(([path]) => path === "/assets/1/")).toHaveLength(2));
  expect(api.mock.calls.filter(([path, opts]) => path === "/assets/1/incidents/" && opts?.body)).toHaveLength(1);
});
