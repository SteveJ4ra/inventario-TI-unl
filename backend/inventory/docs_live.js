(function () {
  "use strict";
  const status = document.getElementById("live-status");
  const rows = document.getElementById("live-assets");
  const button = document.getElementById("live-refresh");
  const previous = document.getElementById("live-previous");
  const next = document.getElementById("live-next");
  const pageLabel = document.getElementById("live-page");
  if (!status || !rows || !button || !previous || !next || !pageLabel) return;
  let pending = false;
  let page = 1;

  async function refresh() {
    if (pending) return;
    pending = true;
    const controller = new AbortController();
    const timeout = window.setTimeout(function () { controller.abort(); }, 10000);
    try {
      const response = await fetch("/api/v1/assets/?page=" + page, {
        credentials: "same-origin", cache: "no-store", signal: controller.signal,
      });
      if (response.status === 401 || response.status === 403) {
        rows.replaceChildren();
        previous.disabled = true;
        next.disabled = true;
        status.textContent = "Inicia sesión con una cuenta de gestor para consultar activos.";
        return;
      }
      if (!response.ok) throw new Error("HTTP " + response.status);
      const body = await response.json();
      if (!body.success || !body.data || !Array.isArray(body.data.results)) throw new Error("Respuesta inválida");
      const fragment = document.createDocumentFragment();
      for (const asset of body.data.results) {
        const row = document.createElement("tr");
        for (const key of ["code", "name", "condition", "lifecycle_status", "assignment", "location"]) {
          const cell = document.createElement("td");
          cell.textContent = asset[key] == null ? "—" : String(asset[key]);
          row.appendChild(cell);
        }
        fragment.appendChild(row);
      }
      rows.replaceChildren(fragment);
      previous.disabled = !body.data.previous;
      next.disabled = !body.data.next;
      pageLabel.textContent = "Página " + page;
      status.textContent = "Actualizado a las " + new Date().toLocaleTimeString("es-EC") +
        ". Total: " + body.data.count + ".";
    } catch (_) {
      status.textContent = "No se pudo actualizar. Comprueba la conexión e inténtalo de nuevo.";
    } finally {
      window.clearTimeout(timeout);
      pending = false;
    }
  }
  button.addEventListener("click", refresh);
  previous.addEventListener("click", function () { if (!pending && page > 1) { page--; refresh(); } });
  next.addEventListener("click", function () { if (!pending && !next.disabled) { page++; refresh(); } });
  document.addEventListener("visibilitychange", function () { if (!document.hidden) refresh(); });
  window.setInterval(function () { if (!document.hidden) refresh(); }, 5000);
  refresh();
}());
