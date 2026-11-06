import { afterEach, expect, test, vi } from "vitest";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
const script = readFileSync(resolve(process.cwd(), "../backend/inventory/docs_live.js"), "utf8");

afterEach(() => { vi.useRealTimers(); document.body.replaceChildren(); });

test("la página API actualiza cambios de otros gestores y limpia datos al perder acceso", async () => {
  vi.useFakeTimers();
  document.body.innerHTML = '<button id="live-refresh"></button><button id="live-previous"></button><button id="live-next"></button><span id="live-page"></span><p id="live-status"></p><table><tbody id="live-assets"></tbody></table>';
  const row = { code: "TI-000001", name: "<img src=x>", condition: "operativo", lifecycle_status: "localizado", assignment: "disponible", location: "Bodega" };
  const fetchMock = vi.fn()
    .mockResolvedValueOnce({ ok: true, status: 200, json: async () => ({ success: true, data: { count: 1, results: [row] } }) })
    .mockResolvedValueOnce({ ok: true, status: 200, json: async () => ({ success: true, data: { count: 1, results: [{ ...row, assignment: "asignado", location: "Aula" }] } }) })
    .mockResolvedValueOnce({ ok: false, status: 403 });
  new Function("document", "window", "fetch", script)(document, window, fetchMock);
  await vi.advanceTimersByTimeAsync(0);
  expect(document.querySelector("#live-assets")?.textContent).toContain("disponible");
  expect(document.querySelector("#live-assets img")).toBeNull();
  await vi.advanceTimersByTimeAsync(5000);
  expect(document.querySelector("#live-assets")?.textContent).toContain("asignado");
  expect(document.querySelector("#live-assets")?.textContent).toContain("Aula");
  await vi.advanceTimersByTimeAsync(5000);
  expect(document.querySelector("#live-assets")?.textContent).toBe("");
  expect(document.querySelector("#live-status")?.textContent).toContain("Inicia sesión");
});

test("la página API consulta la página seleccionada y permite regresar", async () => {
  vi.useFakeTimers();
  document.body.innerHTML = '<button id="live-refresh"></button><button id="live-previous"></button><button id="live-next"></button><span id="live-page"></span><p id="live-status"></p><table><tbody id="live-assets"></tbody></table>';
  const fetchMock = vi.fn()
    .mockResolvedValueOnce({ ok: true, status: 200, json: async () => ({ success: true, data: { count: 51, results: [], next: "next", previous: null } }) })
    .mockResolvedValueOnce({ ok: true, status: 200, json: async () => ({ success: true, data: { count: 51, results: [], next: null, previous: "previous" } }) });
  new Function("document", "window", "fetch", script)(document, window, fetchMock);
  await vi.advanceTimersByTimeAsync(0);
  document.getElementById("live-next").click();
  await vi.advanceTimersByTimeAsync(0);
  expect(fetchMock.mock.calls[1][0]).toBe("/api/v1/assets/?page=2");
  expect(document.getElementById("live-page")?.textContent).toBe("Página 2");
  expect(document.getElementById("live-previous").disabled).toBe(false);
});

test("una consulta bloqueada se cancela y permite actualizar después", async () => {
  vi.useFakeTimers();
  document.body.innerHTML = '<button id="live-refresh"></button><button id="live-previous"></button><button id="live-next"></button><span id="live-page"></span><p id="live-status"></p><table><tbody id="live-assets"></tbody></table>';
  const fetchMock = vi.fn()
    .mockImplementationOnce((_, options) => new Promise((resolve, reject) => {
      options.signal.addEventListener("abort", () => reject(new Error("aborted")));
    }))
    .mockResolvedValue({ ok: true, status: 200, json: async () => ({ success: true, data: { count: 0, results: [], next: null, previous: null } }) });
  new Function("document", "window", "fetch", script)(document, window, fetchMock);
  await vi.advanceTimersByTimeAsync(15000);
  expect(fetchMock.mock.calls[0][1].signal.aborted).toBe(true);
  expect(document.getElementById("live-status").textContent).toContain("Actualizado");
});
