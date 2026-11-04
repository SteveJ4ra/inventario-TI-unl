const assert = require("node:assert/strict");
const { chromium } = require(process.env.VALIDATION_004_PLAYWRIGHT);

async function run() {
  const browser = await chromium.launch({
    executablePath: process.env.VALIDATION_004_CHROMIUM,
    headless: true,
  });
  try {
    const page = await browser.newPage({ baseURL: process.env.VALIDATION_004_URL });
    page.setDefaultTimeout(8000);
    const errors = [];
    page.on("pageerror", (error) => errors.push(error.message));
    const button = (name) => page.getByRole("button", { name, exact: true });
    const visible = (text) => page.getByText(text, { exact: true }).waitFor();
    const post = async (path, status, click) => {
      const [response] = await Promise.all([
        page.waitForResponse((r) => r.url().endsWith(path) && r.request().method() === "POST", { timeout: 8000 }),
        click(),
      ]);
      assert.equal(response.status(), status, path);
      return response.json();
    };
    const api = async (path) => {
      const response = await page.request.get(path);
      assert.equal(response.status(), 200, path);
      return response.json();
    };
    await page.goto("/");
    await page.getByLabel("Usuario", { exact: true }).fill("gestor-004");
    await page.getByLabel("Contraseña", { exact: true }).fill(process.env.VALIDATION_004_LOGIN);
    await post("/api/auth/login/", 200, () => button("Ingresar").click());
    const { results: [seed] } = await api("/api/assets/");
    await button(`Ver ficha de ${seed.code}`).click();
    const assetPath = `/api/assets/${seed.id}/`;
    const incidentsPath = `${assetPath}incidents/`;
    const maintenancePath = `${assetPath}maintenance/`;

    await button("Entregar").click();
    await page.locator("select[name=custodian_id]").selectOption({ index: 1 });
    await page.getByLabel("Destino", { exact: true }).fill("Aula");
    const delivery = await post(`${assetPath}deliver/`, 201, () => button("Confirmar entrega").click());
    await button("Rectificar último movimiento").waitFor();
    await page.getByLabel("Descripción de la novedad").fill("Daño de prueba");
    const report = await post(incidentsPath, 201, () => button("Registrar novedad").click());
    await visible("1 novedad pendiente");
    const assigned = await api(assetPath);
    assert.equal(assigned.condition, "operativo");
    assert.equal(assigned.current_custodian.id, delivery.asset.current_custodian.id);
    assert.equal(assigned.rectifiable_movement_id, null);
    assert.equal(await button("Rectificar último movimiento").count(), 0);
    await page.getByLabel("Nota de resolución", { exact: true }).fill("Revisión completada");
    await post(`/api/incidents/${report.id}/resolve/`, 200, () => button("Resolver novedad").click());
    await visible("Sin novedades pendientes.");
    await button("Devolver").click();
    await page.getByLabel("Condición de recepción").selectOption("operativo");
    await page.getByLabel("Lugar de recepción").fill("Laboratorio");
    await post(`${assetPath}return/`, 201, () => button("Confirmar devolución").click());
    console.log("PASS entrega, daño asignado, resolución y devolución real");

    const start = async () => {
      await page.getByLabel("Descripción del mantenimiento").fill("Preventivo");
      await page.getByLabel("Ubicación del taller").fill("Taller");
      const event = await post(maintenancePath, 201, () => button("Iniciar mantenimiento").click());
      await visible("Mantenimiento en curso");
      assert.equal(await button("Entregar").count(), 0);
      return event;
    };
    const first = await start();
    const receiving = page.getByLabel("Ubicación de recepción", { exact: true });
    assert.equal(await receiving.inputValue(), "Laboratorio");
    await receiving.fill("Bodega");
    await page.getByLabel("Resultado", { exact: true }).fill("Revisado");
    const closePath = `/api/maintenance/${first.id}/close/`;
    const closeButton = button("Cerrar mantenimiento");
    await closeButton.click();
    assert.equal(await page.locator("[name=location_confirmed]").evaluate((el) => el.validity.valueMissing), true);
    assert.equal((await api(`/api/maintenance/${first.id}/`)).status, "in_progress");
    await page.getByRole("checkbox", { name: /Confirmo la ubicación/ }).check();
    await post(closePath, 200, () => closeButton.click());
    await visible(`Cierre de mantenimiento #${first.id}`);
    assert.equal((await api(assetPath)).location, "Bodega");
    console.log("PASS mantenimiento preventivo, entrega bloqueada y cierre confirmado");

    const second = await start();
    await page.getByLabel("Tipo de novedad").selectOption("stolen");
    await page.getByLabel("Descripción de la novedad").fill("Robo de prueba");
    const loss = await post(incidentsPath, 201, () => button("Registrar novedad").click());
    await visible("No localizado");
    await visible("Último custodio conocido");
    const missing = await api(assetPath);
    assert.equal(missing.lifecycle_status, "no_localizado");
    assert.equal(missing.current_custodian, null);
    assert.equal(missing.assignment, null);
    assert.equal(missing.last_location, "Taller");
    assert.equal(await button("Devolver").count(), 0);
    const interrupted = await api(`/api/maintenance/${second.id}/`);
    assert.equal(interrupted.status, "interrupted_unlocated");
    assert.equal(interrupted.result, "");
    await page.getByLabel("Condición tras la inspección").selectOption("averiado");
    await page.getByLabel("Ubicación de recuperación").fill("Recepción");
    await page.getByRole("checkbox", { name: "Confirmo que inspeccioné el activo." }).check();
    await post(`${assetPath}recover/`, 201, () => button("Registrar recuperación").click());
    await visible(`Recuperación del activo · Reporte #${loss.id}`);
    await visible(`Reporte de robo #${loss.id}`);
    await visible(`Interrupción de mantenimiento #${second.id}`);
    const recovered = await api(assetPath);
    assert.equal(recovered.code, seed.code);
    assert.equal(recovered.assignment, "disponible");
    assert.equal(recovered.condition, "averiado");
    assert.equal(recovered.current_custodian, null);
    assert.equal(recovered.active_maintenance_id, null);
    const history = await api(`${assetPath}history/`);
    assert.deepEqual(history.map((row) => row.resulting_revision), [10, 9, 8, 7, 6, 5, 4, 3, 2, 1]);
    assert.deepEqual((await api(`${assetPath}movements/`)).map((row) => row.type), ["devolucion", "entrega"]);
    assert.deepEqual(errors, []);
    console.log("PASS robo en taller, recuperación e historial real de diez revisiones");
  } finally {
    await browser.close();
  }
}

run().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
