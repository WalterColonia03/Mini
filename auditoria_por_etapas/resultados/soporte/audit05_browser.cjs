const fs = require("node:fs");
const path = require("node:path");
const os = require("node:os");
const crypto = require("node:crypto");
const assert = require("node:assert/strict");
const { execFileSync } = require("node:child_process");
const { chromium } = require(
  path.join(
    os.homedir(),
    ".cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright-core"
  )
);

const out = process.env.AUDIT05_OUT;
const run = process.env.AUDIT05_RUN_DIR;
const base = "http://127.0.0.1:" + process.env.AUDIT05_PORT;
const accounts = JSON.parse(fs.readFileSync(path.join(run, ".credentials.json"), "utf8"));
const fixture = JSON.parse(fs.readFileSync(path.join(out, "fixture.json"), "utf8"));

const report = {
  checks: [],
  page_errors: [],
  screenshots: [],
  transport: [],
  input: "Chrome 1366x900 Stage 05 audit (HU-INV-01a, catalog links, lot queries across roles)",
};

function check(id, actual, expected) {
  assert.deepEqual(actual, expected, id);
  report.checks.push(id);
}

function state() {
  return JSON.parse(
    execFileSync(process.env.AUDIT05_PYTHON, [path.join(__dirname, "audit05_run.py"), "snapshot"], {
      encoding: "utf8",
    })
  );
}

async function loginContext(browser, role) {
  const ctx = await browser.newContext({ locale: "es-PE", viewport: { width: 1366, height: 900 } });
  const page = await ctx.newPage();
  page.on("pageerror", (err) => report.page_errors.push({ role, message: err.message }));
  await page.goto(base);
  await page.locator("[name=email]").fill(accounts[role].email);
  await page.locator("[name=password]").fill(accounts[role].password);
  await page.locator('button[type="submit"]').click();
  await page.waitForURL(base + "/inicio/");
  return { ctx, page };
}

async function shot(page, filename) {
  const target = path.join(out, filename);
  await page.screenshot({ path: target, fullPage: true });
  report.screenshots.push(filename);
}

async function droppedPost(page, afterCommit) {
  let forwardedStatus = null;
  let routeFailure = null;
  const failed = page.waitForEvent(
    "requestfailed",
    (req) => req.method() === "POST" && req.url() === base + "/inventario/carga-inicial/"
  );
  await page.route("**/inventario/carga-inicial/", async (route) => {
    if (route.request().method() !== "POST") return route.continue();
    try {
      if (afterCommit) {
        const res = await route.fetch({ maxRedirects: 0 });
        forwardedStatus = res.status();
      }
      await route.abort("connectionreset");
    } catch (err) {
      routeFailure = err.message;
      await route.abort().catch(() => {});
    }
  });
  await page
    .getByRole("button", { name: "Confirmar existencias", exact: true })
    .click({ noWaitAfter: true })
    .catch((err) => {
      if (!err.message.includes("ERR_CONNECTION_RESET")) throw err;
    });
  const req = await failed;
  await page.waitForLoadState("domcontentloaded").catch(() => {});
  await page.unroute("**/inventario/carga-inicial/");
  check(`intercepcion_sin_error_${afterCommit}`, routeFailure, null);
  check(`fallo_conexion_detectado_${afterCommit}`, req.failure().errorText.includes("ERR_CONNECTION_RESET"), true);
  check(`estado_servidor_intercepcion_${afterCommit}`, forwardedStatus, afterCommit ? 302 : null);
  report.transport.push({ afterCommit, forwardedStatus, browserFailure: req.failure().errorText });
}

function addDaysIso(isoDate, days) {
  const [y, m, d] = isoDate.split("-").map(Number);
  const dt = new Date(Date.UTC(y, m - 1, d + days));
  return dt.toISOString().slice(0, 10);
}

async function fillLots(page, productId, supplierId, rows) {
  await page.locator("[name=product]").selectOption(productId);
  await page.locator("[name=supplier]").selectOption(supplierId);
  for (let i = 0; i < 4; i++) {
    const row = rows[i] || { number: "", quantity: "", unit_cost: "", expiration_date: "" };
    for (const [k, v] of Object.entries(row)) {
      await page.locator(`[name="lots-${i}-${k}"]`).fill(String(v));
    }
  }
}

async function runAudit(browser) {
  const initialOrm = state();

  // 1. Cryptographic environment isolation + anonymous redirects
  const probeCtx = await browser.newContext({ locale: "es-PE", viewport: { width: 1366, height: 900 } });
  const probe = await probeCtx.newPage();
  const nonce = crypto.randomBytes(32).toString("hex");
  const probeRes = await probe.request.get(base, { headers: { "X-Audit05-Challenge": nonce } });
  const expectedProof = crypto
    .createHmac("sha256", fs.readFileSync(path.join(run, ".django-key")))
    .update(nonce)
    .digest("hex");
  check("aislamiento_proof", probeRes.headers()["x-audit05-proof"], expectedProof);
  check("aislamiento_run", probeRes.headers()["x-audit05-run"], path.basename(run));

  const subLoadId = fixture.products.sub.load_id;
  const subId = fixture.products.sub.id;
  for (const [tag, url] of [
    ["carga_inicial", "/inventario/carga-inicial/"],
    ["constancia_canonica", `/inventario/cargas/${subLoadId}/`],
    ["constancia_alias", `/inventario/carga-inicial/${subLoadId}/creada/`],
    ["stock_overview", "/inventario/stock/"],
    ["movimientos", `/inventario/productos/${subId}/movimientos/`],
  ]) {
    const r = await probe.request.get(base + url, { maxRedirects: 0 });
    check(`anonimo_${tag}_302`, r.status(), 302);
    check(`anonimo_${tag}_next`, r.headers()["location"], `/?next=${url}`);
  }
  await probeCtx.close();

  // 2. VENDEDOR role boundary + opens shift + verifies un-loaded & today-expiring products unavailable before initial load
  const sellerSession = await loginContext(browser, "seller");
  const seller = sellerSession.page;
  for (const href of ["/inventario/carga-inicial/", "/inventario/stock/", "/productos/", "/productos/vencimientos/"]) {
    check(`vendedor_sin_nav_${href}`, await seller.locator(`#sidebar-navigation a[href="${href}"]`).count(), 0);
  }
  for (const [tag, url] of [
    ["carga_inicial", "/inventario/carga-inicial/"],
    ["constancia_canonica", `/inventario/cargas/${subLoadId}/`],
    ["constancia_alias", `/inventario/carga-inicial/${subLoadId}/creada/`],
    ["stock_overview", "/inventario/stock/"],
    ["movimientos", `/inventario/productos/${subId}/movimientos/`],
    ["catalogo", "/productos/"],
    ["vencimientos", "/productos/vencimientos/"],
  ]) {
    const resp = await seller.request.get(base + url, { maxRedirects: 0 });
    check(`vendedor_${tag}_403`, resp.status(), 403);
  }
  const sellerCookies = await sellerSession.ctx.cookies();
  const sellerCsrf = sellerCookies.find((c) => c.name === "audit05_csrftoken").value;
  const sellerPost = await seller.request.post(base + "/inventario/carga-inicial/", {
    form: {
      csrfmiddlewaretoken: sellerCsrf,
      product: fixture.products.elig1.id,
      "lots-TOTAL_FORMS": "4",
      "lots-INITIAL_FORMS": "0",
      "lots-MIN_NUM_FORMS": "1",
      "lots-MAX_NUM_FORMS": "1000",
      "lots-0-number": "S-NOPE",
      "lots-0-quantity": "2",
      "lots-0-unit_cost": "1.00",
      "lots-0-expiration_date": fixture.future_45,
    },
    maxRedirects: 0,
  });
  check("vendedor_post_carga_403", sellerPost.status(), 403);
  check("vendedor_denegado_sin_cambios", state(), initialOrm);

  // Seller opens the configured CAJA-01 and searches POS BEFORE elig1 initial load
  await seller.getByTestId("cash-open-link").click();
  await seller.waitForURL(base + "/caja/abrir/");
  await seller.locator("[name=opening_amount]").fill("100.00");
  await seller.getByRole("button", { name: "Abrir turno", exact: true }).click();
  await seller.waitForURL(/\/caja\/turnos\/.+\/abierto\//);

  await seller.goto(base + "/ventas/");
  await seller.locator("[name=query]").fill("Jugo Natural");
  await seller.getByRole("button", { name: "Buscar", exact: true }).click();
  check("pos_antes_carga_excluye_elig1", (await seller.locator(".sales-search-panel").innerText()).includes("No se encontraron productos con existencias vendibles."), true);

  await seller.locator("[name=query]").fill("Yogurt Vence");
  await seller.getByRole("button", { name: "Buscar", exact: true }).click();
  check("pos_excluye_lote_vence_hoy", (await seller.locator(".sales-search-panel").innerText()).includes("No se encontraron productos con existencias vendibles."), true);

  // 3. ADMIN navigation, read access, write denial, and initial stock visibility
  const adminSession = await loginContext(browser, "admin");
  const admin = adminSession.page;
  check("admin_sin_nav_carga_inicial", await admin.locator('#sidebar-navigation a[href="/inventario/carga-inicial/"]').count(), 0);
  check("admin_con_nav_stock", await admin.locator('#sidebar-navigation a[href="/inventario/stock/"]').count(), 1);
  check("admin_con_nav_vencimientos", await admin.locator('#sidebar-navigation a[href="/productos/vencimientos/"]').count(), 1);

  const adminGetInit = await admin.request.get(base + "/inventario/carga-inicial/", { maxRedirects: 0 });
  check("admin_get_carga_inicial_403", adminGetInit.status(), 403);
  const adminCookies = await adminSession.ctx.cookies();
  const adminCsrf = adminCookies.find((c) => c.name === "audit05_csrftoken").value;
  const beforeAdminPost = state();
  const adminPostInit = await admin.request.post(base + "/inventario/carga-inicial/", {
    form: { csrfmiddlewaretoken: adminCsrf, product: fixture.products.elig1.id },
    maxRedirects: 0,
  });
  check("admin_post_carga_inicial_403", adminPostInit.status(), 403);
  check("admin_denegado_sin_cambios", state(), beforeAdminPost);

  // ADMIN inspects sub constancia via canonical URL and sees both initial & subsequent lots WITHOUT action buttons
  const adminSubResp = await admin.goto(base + `/inventario/cargas/${subLoadId}/`);
  check("admin_ver_constancia_200", adminSubResp.status(), 200);
  check("admin_ver_constancia_never_cache", (adminSubResp.headers()["cache-control"] || "").includes("no-store"), true);
  const adminSubText = await admin.locator('[data-testid="inventory-load-created"]').innerText();
  check("admin_ve_responsable_carga_y_subsecuente", adminSubText.includes("Lucia Almacen05") && adminSubText.includes("Pedro Almacen05"), true);
  check("admin_sin_boton_cargar_otro", await admin.getByRole("link", { name: "Cargar otro producto", exact: true }).count(), 0);

  // 4. ALMACENERO navigation & initial form inspection
  const whSession = await loginContext(browser, "warehouse");
  const wh = whSession.page;
  check("wh_nav_carga_inicial", await wh.locator('#sidebar-navigation a[href="/inventario/carga-inicial/"]').count(), 1);
  check("wh_nav_stock", await wh.locator('#sidebar-navigation a[href="/inventario/stock/"]').count(), 1);
  check("wh_nav_vencimientos", await wh.locator('#sidebar-navigation a[href="/productos/vencimientos/"]').count(), 1);

  const initNavPromise = wh.waitForResponse((r) => r.url().endsWith("/inventario/carga-inicial/") && r.request().method() === "GET");
  await wh.getByTestId("inventory-load-link").click();
  await wh.waitForURL(base + "/inventario/carga-inicial/");
  const initNavResp = await initNavPromise;
  check("wh_carga_inicial_200", initNavResp.status(), 200);
  check("wh_carga_inicial_never_cache", (initNavResp.headers()["cache-control"] || "").includes("no-store"), true);

  // Check product dropdown eligibility
  check("select_incluye_elig1", await wh.locator(`[name=product] option[value="${fixture.products.elig1.id}"]`).count(), 1);
  check("select_incluye_elig2", await wh.locator(`[name=product] option[value="${fixture.products.elig2.id}"]`).count(), 1);
  check("select_excluye_sub", await wh.locator(`[name=product] option[value="${subId}"]`).count(), 0);
  check("select_excluye_today_exp", await wh.locator(`[name=product] option[value="${fixture.products.today_exp.id}"]`).count(), 0);
  check("select_excluye_inactive", await wh.locator(`[name=product] option[value="${fixture.products.inactive.id}"]`).count(), 0);
  check("select_excluye_cat_off", await wh.locator(`[name=product] option[value="${fixture.products.cat_off.id}"]`).count(), 0);

  // Empty POST {} with CSRF must fail loudly (200 + errors)
  const whCookies = await whSession.ctx.cookies();
  const whCsrf = whCookies.find((c) => c.name === "audit05_csrftoken").value;
  const emptyPostRes = await wh.request.post(base + "/inventario/carga-inicial/", {
    form: { csrfmiddlewaretoken: whCsrf },
    maxRedirects: 0,
  });
  check("post_vacio_status_200", emptyPostRes.status(), 200);
  check("post_vacio_con_errores", (await emptyPostRes.text()).includes('role="alert"'), true);

  // Eastern Arabic numerals submitted directly to POST must fail ASCII check cleanly
  const arabicPostRes = await wh.request.post(base + "/inventario/carga-inicial/", {
    form: {
      csrfmiddlewaretoken: whCsrf,
      product: fixture.products.elig1.id,
      "lots-TOTAL_FORMS": "1",
      "lots-INITIAL_FORMS": "0",
      "lots-MIN_NUM_FORMS": "1",
      "lots-MAX_NUM_FORMS": "1000",
      "lots-0-number": "L-ARAB",
      "lots-0-quantity": "٥",
      "lots-0-unit_cost": "٢.٥٠",
      "lots-0-expiration_date": fixture.future_45,
    },
    maxRedirects: 0,
  });
  const arabicBody = await arabicPostRes.text();
  check("post_digitos_arabes_200", arabicPostRes.status(), 200);
  check("post_digitos_arabes_rechazado", arabicBody.includes("ASCII") || arabicBody.includes("válido"), true);

  // DEC-05-LOTE-ESPACIOS: internal spaces collapse + case-fold make " ab  12 " duplicate "AB 12", while "AB12" remains distinct
  const beforeDec05Orm = state();
  await fillLots(wh, fixture.products.elig1.id, fixture.suppliers.active.id, [
    { number: " ab  12 ", quantity: "2", unit_cost: "1.5000", expiration_date: fixture.future_45 },
    { number: "AB 12", quantity: "3", unit_cost: "2.0000", expiration_date: fixture.future_90 },
  ]);
  await wh.getByRole("button", { name: "Confirmar existencias", exact: true }).click();
  await wh.waitForLoadState("domcontentloaded");
  check("dec05_espacios_colapsan_como_duplicado", (await wh.locator('[role="alert"]').allInnerTexts()).join(" | ").includes("está repetido"), true);
  check("dec05_duplicado_no_muta_bd", state(), beforeDec05Orm);

  await fillLots(wh, fixture.products.elig1.id, fixture.suppliers.active.id, [
    { number: " ab  12 ", quantity: "0", unit_cost: "1.5000", expiration_date: fixture.future_45 },
    { number: "AB12", quantity: "3", unit_cost: "2.0000", expiration_date: fixture.future_90 },
  ]);
  await wh.getByRole("button", { name: "Confirmar existencias", exact: true }).click();
  await wh.waitForLoadState("domcontentloaded");
  const dec05DistinctAlerts = (await wh.locator('[role="alert"]').allInnerTexts()).join(" | ");
  check("dec05_ab_12_y_ab12_no_colisionan", !dec05DistinctAlerts.includes("está repetido") && dec05DistinctAlerts.includes("mayor o igual a 1"), true);
  check("dec05_rechazo_sin_mutacion", state(), beforeDec05Orm);

  // Multi-error first submit: duplicate lot numbers + qty 0 + today expiration + qty 1000000 + cost 5 decimals + +21 years expiration
  const over20y = addDaysIso(fixture.today, 366 * 21);
  const beforeInvalidOrm = state();
  await fillLots(wh, fixture.products.elig1.id, fixture.suppliers.active.id, [
    { number: "L-DUP", quantity: "0", unit_cost: "0", expiration_date: fixture.today },
    { number: "  l-dup  ", quantity: "1000000", unit_cost: "1.23456", expiration_date: over20y },
  ]);
  await wh.getByRole("button", { name: "Confirmar existencias", exact: true }).click();
  await wh.waitForLoadState("domcontentloaded");
  check("errores_no_mutan_bd", state(), beforeInvalidOrm);
  check("errores_conserva_producto_seleccionado", await wh.locator("[name=product]").inputValue(), fixture.products.elig1.id);
  const allAlertsText = (await wh.locator('[role="alert"]').allInnerTexts()).join(" | ");
  check("error_lote_duplicado_en_primer_envio", allAlertsText.includes("está repetido"), true);
  check("error_cantidad_minima_en_primer_envio", allAlertsText.includes("mayor o igual a 1"), true);
  check("error_cantidad_maxima_en_primer_envio", allAlertsText.includes("999999"), true);
  check("error_vencimiento_hoy_lima", allAlertsText.includes("posterior a hoy en Lima"), true);
  check("error_vencimiento_20_anos", allAlertsText.includes("20 años"), true);
  check("error_costo_4_decimales", allAlertsText.includes("4 dígitos decimales"), true);
  check("error_costo_minimo_en_primer_envio", allAlertsText.includes("0.0001") || allAlertsText.includes("0,0001"), true);
  await shot(wh, "01-form-errores.png");

  // 5. Cross-role stale category suspension during open tab + rollback + reactivation
  await fillLots(wh, fixture.products.elig1.id, fixture.suppliers.active.id, [
    { number: " lote-01 ", quantity: "7", unit_cost: "2.1000", expiration_date: fixture.future_90 },
    { number: "", quantity: "", unit_cost: "", expiration_date: "" },
    { number: "LOTE-02", quantity: "3", unit_cost: "4.2500", expiration_date: fixture.soon_15 },
    { number: "LOTE-03", quantity: "6", unit_cost: "3.0000", expiration_date: fixture.future_45 },
  ]);

  // ADMIN suspends Bebidas Audit05 via UI while WH holds form open
  await admin.goto(base + "/productos/categorias/");
  await admin.locator("tbody tr", { hasText: fixture.categories.drinks.name }).getByRole("button", { name: "Desactivar", exact: true }).click();
  await admin.waitForURL(/\/productos\/categorias\/.+\/estado\/confirmar\//);
  await admin.getByRole("button", { name: "Confirmar desactivación", exact: true }).click();
  await admin.waitForURL(base + "/productos/categorias/");

  const afterAdminSuspendOrm = state();
  await wh.getByRole("button", { name: "Confirmar existencias", exact: true }).click();
  check("categoria_suspendida_rechaza_sin_escrituras", state(), afterAdminSuspendOrm);
  check("categoria_suspendida_cargas_y_lotes_intactos", { loads: afterAdminSuspendOrm.loads, lots: afterAdminSuspendOrm.lots }, { loads: beforeInvalidOrm.loads, lots: beforeInvalidOrm.lots });
  check("categoria_suspendida_error_visible", (await wh.locator('[role="alert"]').allInnerTexts()).length > 0, true);

  // ADMIN reactivates Bebidas Audit05, WH reloads and sees elig1 again
  await admin.locator("tbody tr", { hasText: fixture.categories.drinks.name }).getByRole("button", { name: "Activar", exact: true }).click();
  await admin.waitForURL(/\/productos\/categorias\/.+\/estado\/confirmar\//);
  await admin.getByRole("button", { name: "Confirmar activación", exact: true }).click();
  await admin.waitForURL(base + "/productos/categorias/");

  await wh.goto(base + "/inventario/carga-inicial/");
  check("categoria_reactivada_elig1_disponible", await wh.locator(`[name=product] option[value="${fixture.products.elig1.id}"]`).count(), 1);

  // 6. Confirm Multi-Lot Initial Load on elig1 (including blank middle row 1, weighted cost HALF_UP)
  await fillLots(wh, fixture.products.elig1.id, fixture.suppliers.active.id, [
    { number: " lote-01 ", quantity: "7", unit_cost: "2.1000", expiration_date: fixture.future_90 },
    { number: "", quantity: "", unit_cost: "", expiration_date: "" },
    { number: "LOTE-02", quantity: "3", unit_cost: "4.2500", expiration_date: fixture.soon_15 },
    { number: "LOTE-03", quantity: "6", unit_cost: "3.0000", expiration_date: fixture.future_45 },
  ]);
  await wh.getByRole("button", { name: "Confirmar existencias", exact: true }).click();
  await wh.waitForURL(/\/inventario\/cargas\//);
  const elig1ConstanciaUrl = wh.url();
  const afterElig1 = state();
  const elig1ProductState = afterElig1.products.find((p) => p.id === fixture.products.elig1.id);
  check("elig1_costo_promedio_orm_4dec", elig1ProductState.average_cost, "2.8406");
  const elig1Lots = afterElig1.lots.filter((l) => l.product_id === fixture.products.elig1.id);
  check("elig1_3_lotes_sin_fila_vacia", elig1Lots.length, 3);
  check("elig1_costo_promedio_inicial_ui_2dec", await wh.locator("dl > div").filter({ hasText: "Costo promedio inicial" }).locator("dd").innerText(), "S/ 2,84");
  check("elig1_costo_promedio_actual_ui_2dec", await wh.locator("dl > div").filter({ hasText: "Costo promedio actual" }).locator("dd").innerText(), "S/ 2,84");
  check("elig1_existencias_16_und", await wh.locator("dl > div").filter({ hasText: "Existencias físicas actuales" }).locator("dd").innerText(), "16 UND");
  check("elig1_constancia_sin_overflow", await wh.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth), true);
  await shot(wh, "02-constancia-inicial.png");

  // Single initial load rule: elig1 disappears from select
  await wh.goto(base + "/inventario/carga-inicial/");
  check("una_sola_carga_elig1_excluido", await wh.locator(`[name=product] option[value="${fixture.products.elig1.id}"]`).count(), 0);

  // 7. elig2: network abort BEFORE commit, lost 302 AFTER commit, replay rejection, recovery via UI, 64-char lot + 160-char supplier wrap + HALF_UP + RN-06 min=10
  const lot64 = "L".repeat(64);
  await fillLots(wh, fixture.products.elig2.id, fixture.suppliers.long.id, [
    { number: lot64, quantity: "5", unit_cost: "1.2344", expiration_date: fixture.tomorrow },
    { number: "LOT-SHORT-2", quantity: "5", unit_cost: "1.2345", expiration_date: fixture.future_45 },
  ]);
  await droppedPost(wh, false);
  check("abort_antes_commit_sin_escrituras", state(), afterElig1);

  await wh.goto(base + "/inventario/carga-inicial/");
  check("elig2_sigue_elegible_tras_abort_previo", await wh.locator(`[name=product] option[value="${fixture.products.elig2.id}"]`).count(), 1);
  await fillLots(wh, fixture.products.elig2.id, fixture.suppliers.long.id, [
    { number: lot64, quantity: "5", unit_cost: "1.2344", expiration_date: fixture.tomorrow },
    { number: "LOT-SHORT-2", quantity: "5", unit_cost: "1.2345", expiration_date: fixture.future_45 },
  ]);
  const elig2Payload = await wh.locator('form[data-testid="inventory-load-form"]').evaluate((f) => Object.fromEntries(new FormData(f)));
  await droppedPost(wh, true);

  const afterElig2 = state();
  check("elig2_crea_exactamente_1_carga_pese_302_perdido", afterElig2.loads.length, afterElig1.loads.length + 1);
  check("elig2_promedio_half_up_4dec", afterElig2.products.find((p) => p.id === fixture.products.elig2.id).average_cost, "1.2345");

  // Replay identical payload must reject cleanly without duplicating
  const replayRes = await wh.request.post(base + "/inventario/carga-inicial/", { form: elig2Payload, maxRedirects: 0 });
  check("reenvio_tras_302_perdido_200", replayRes.status(), 200);
  check("reenvio_informa_ya_registrada", (await replayRes.text()).includes("ya tiene una carga inicial registrada"), true);
  check("reenvio_no_duplica_datos", state(), afterElig2);

  // Recover via UI: Stock overview -> Ver carga
  await wh.goto(base + "/inventario/stock/");
  await wh.locator("tbody tr", { hasText: fixture.products.elig2.name }).getByRole("link", { name: "Ver carga", exact: true }).click();
  await wh.waitForURL(/\/inventario\/cargas\//);
  check("elig2_costo_promedio_inicial_s_1_23", await wh.locator("dl > div").filter({ hasText: "Costo promedio inicial" }).locator("dd").innerText(), "S/ 1,23");
  check("elig2_costo_promedio_actual_s_1_23", await wh.locator("dl > div").filter({ hasText: "Costo promedio actual" }).locator("dd").innerText(), "S/ 1,23");
  await wh.reload();
  check("elig2_constancia_reload_idempotente", state(), afterElig2);

  const wrapChecksElig2 = await wh.evaluate(() => {
    const docOk = document.documentElement.scrollWidth <= window.innerWidth;
    const thWrapValues = Array.from(document.querySelectorAll(".load-detail-panel th")).map(
      (th) => getComputedStyle(th).overflowWrap
    );
    const shortCell = Array.from(document.querySelectorAll(".load-detail-panel td.load-col-lot")).find(
      (td) => td.textContent.trim() === "LOT-SHORT-2"
    );
    let shortHeightOk = false;
    if (shortCell) {
      const range = document.createRange();
      range.selectNodeContents(shortCell);
      shortHeightOk = range.getClientRects().length === 1;
    }
    return { docOk, thNormal: thWrapValues.every((v) => v === "normal"), shortHeightOk };
  });
  check("elig2_wrap_headers_y_lote_corto_sin_rotura", wrapChecksElig2, { docOk: true, thNormal: true, shortHeightOk: true });
  await shot(wh, "03-constancia-extremos-wrap.png");

  // 8. Alias constancia URL on p_sub showing 6-col initial snapshot table + Recepciones con constancia propia list (14-H1)
  const subAliasResp = await wh.goto(base + `/inventario/carga-inicial/${subLoadId}/creada/`);
  check("wh_alias_constancia_sub_200", subAliasResp.status(), 200);
  const subHeadersOk = await wh.evaluate(() => {
    const docOk = document.documentElement.scrollWidth <= window.innerWidth;
    const ths = Array.from(document.querySelectorAll(".load-detail-panel th"));
    return docOk && ths.length === 6 && ths.every((th) => getComputedStyle(th).overflowWrap === "normal");
  });
  check("wh_sub_6col_snapshot_y_headers_normales", subHeadersOk, true);
  const subPanelText = await wh.locator('[data-testid="inventory-load-created"]').innerText();
  check("wh_sub_lista_recepciones_propias", subPanelText.includes("Recepciones con constancia propia") && subPanelText.includes("Pedro Almacen05"), true);
  check("wh_sub_link_recepcion_propia", await wh.locator('[data-testid="inventory-load-created"] ul a[href^="/inventario/recepciones/"]').count(), 1);
  await shot(wh, "04-constancia-con-posteriores.png");

  // 9. Stock Overview (RN-06 stock=10 == min=10), Product List, Expirations, and Kardex Movements
  await wh.goto(base + "/inventario/stock/");
  const stockElig2Row = await wh.locator("tbody tr", { hasText: fixture.products.elig2.name }).innerText();
  const stockTodayRow = await wh.locator("tbody tr", { hasText: fixture.products.today_exp.name }).innerText();
  const stockElig1Row = await wh.locator("tbody tr", { hasText: fixture.products.elig1.name }).innerText();
  check("stock_elig2_bajo_en_igualdad_rn06", stockElig2Row.includes("Stock bajo"), true);
  check("stock_today_sin_vendible", stockTodayRow.includes("Sin stock vendible"), true);
  check("stock_elig1_ok", stockElig1Row.includes("OK"), true);
  check("stock_banner_vencidos_incluye_today", (await wh.locator(".panel-danger").innerText()).includes("L-VENCE-HOY"), true);
  check("stock_banner_bajo_incluye_elig2", (await wh.locator(".stock-alert-panel").filter({hasText: "Stock vigente en el mínimo"}).innerText()).includes(fixture.products.elig2.name), true);
  const stockFit = await wh.evaluate(() => {
    const docOk = document.documentElement.scrollWidth <= window.innerWidth;
    const wrap = document.querySelector(".table-wrap");
    const wrapRect = wrap.getBoundingClientRect();
    const wrapOk = wrap.scrollWidth <= wrap.clientWidth;
    const thsNormal = Array.from(document.querySelectorAll(".stock-overview-table th")).every(
      (th) => getComputedStyle(th).overflowWrap === "normal"
    );
    const buttonsInside = Array.from(document.querySelectorAll(".stock-actions a")).every((a) => {
      const r = a.getBoundingClientRect();
      return r.right <= wrapRect.right + 1 && r.left >= wrapRect.left - 1;
    });
    return { docOk, wrapOk, thsNormal, buttonsInside };
  });
  check("stock_overview_sin_recorte_acciones_desktop", stockFit, {
    docOk: true,
    wrapOk: true,
    thsNormal: true,
    buttonsInside: true,
  });
  await shot(wh, "05-stock-overview.png");

  await wh.goto(base + "/productos/");
  const listElig2Row = await wh.locator("tbody tr", { hasText: fixture.products.elig2.name }).innerText();
  const listTodayRow = await wh.locator("tbody tr", { hasText: fixture.products.today_exp.name }).innerText();
  check("product_list_concuerda_stock_bajo", listElig2Row.includes("Stock bajo") && listElig2Row.includes("Disponible"), true);
  check("product_list_today_sin_stock_vigente", listTodayRow.includes("Sin stock vigente"), true);
  await shot(wh, "06-product-list.png");

  await wh.goto(base + "/productos/vencimientos/");
  const expText = await wh.locator("table").innerText();
  check("vencimientos_lote_hoy_vencido", expText.includes("L-VENCE-HOY") && expText.includes("Vencido"), true);
  check("vencimientos_lotes_futuros_proximos", expText.includes("LOTE-02") && expText.includes("Próximo"), true);
  await shot(wh, "07-product-expirations.png");

  await wh.goto(base + `/inventario/productos/${subId}/movimientos/`);
  const movSubText = await wh.locator("table.movements-table").innerText();
  check("kardex_sub_dos_responsables_y_proveedor", movSubText.includes("Lucia Almacen05") && movSubText.includes("Pedro Almacen05") && movSubText.includes("Distribuidora Norte Audit05 SAC"), true);
  check("kardex_sub_saldos_reconstruidos", [
    await wh.getByTestId("opening-balance").innerText(),
    await wh.getByTestId("closing-balance").innerText(),
    await wh.getByTestId("filtered-count").innerText(),
  ], ["0", "20", "2"]);
  await shot(wh, "08-product-movements.png");

  // 10. Downstream VENDEDOR POS FEFO sale on elig1 (buys 5 -> depletes LOTE-02=3 soon_15 + 2 from LOTE-03 future_45)
  await seller.goto(base + "/ventas/");
  await seller.locator("[name=query]").fill("Yogurt Vence");
  await seller.getByRole("button", { name: "Buscar", exact: true }).click();
  check("pos_sigue_excluyendo_vencido", (await seller.locator(".sales-search-panel").innerText()).includes("No se encontraron productos con existencias vendibles."), true);

  await seller.locator("[name=query]").fill("Jugo Natural");
  await seller.getByRole("button", { name: "Buscar", exact: true }).click();
  const jugRow = seller.locator(".sales-search-panel tbody tr", { hasText: fixture.products.elig1.name });
  check("pos_muestra_elig1_16_disponibles", (await jugRow.innerText()).includes("16"), true);
  await jugRow.locator('input[name="quantity"]').fill("5");
  await jugRow.getByRole("button", { name: "Agregar", exact: true }).click();
  await seller.getByRole("link", { name: "Cobrar venta →", exact: true }).click();
  await seller.waitForURL(base + "/ventas/cobrar/");
  await seller.locator("[name=cash_received]").fill("50.00");
  await seller.getByRole("button", { name: "Confirmar cobro", exact: true }).click();
  await seller.waitForURL(/\/ventas\/constancia\/.+\//);
  check("venta_constancia_total_37_50", (await seller.locator("#constancia-interna").innerText()).includes("S/ 37,50"), true);
  await shot(seller, "09-venta-pos-fefo.png");

  const afterSale = state();
  const l02 = afterSale.lots.find((l) => l.product_id === fixture.products.elig1.id && l.number_normalized === "LOTE-02");
  const l03 = afterSale.lots.find((l) => l.product_id === fixture.products.elig1.id && l.number_normalized === "LOTE-03");
  const l01 = afterSale.lots.find((l) => l.product_id === fixture.products.elig1.id && l.number_normalized === "LOTE-01");
  check("fefo_agota_lote02_primero", l02.available_quantity, 0);
  check("fefo_descuenta_2_de_lote03", l03.available_quantity, 4);
  check("fefo_conserva_lote01_intacto", l01.available_quantity, 7);
  check("venta_guarda_snapshot_costo_promedio", afterSale.sale_lines[afterSale.sale_lines.length - 1].unit_cost, "2.8406");

  // ALMACENERO observes post-sale Kardex (-5) and constancia preserving average_cost & original_initial_quantity
  await wh.goto(base + `/inventario/productos/${fixture.products.elig1.id}/movimientos/`);
  const elig1MovText = await wh.locator("main").innerText();
  check("kardex_elig1_postventa_muestra_11_y_menos_5", elig1MovText.toLowerCase().includes("11 unid.") && elig1MovText.includes("-5"), true);
  check("kardex_elig1_cierre_11", await wh.getByTestId("closing-balance").innerText(), "11");
  await wh.goto(elig1ConstanciaUrl);
  const lote02Cells = await wh.locator(".load-detail-panel tbody tr", { hasText: "LOTE-02" }).locator("td").allInnerTexts();
  check("constancia_postventa_conserva_costo_y_originales", [
    await wh.locator("dl > div").filter({ hasText: "Costo promedio inicial" }).locator("dd").innerText(),
    await wh.locator("dl > div").filter({ hasText: "Costo promedio actual" }).locator("dd").innerText(),
    await wh.locator("dl > div").filter({ hasText: "Existencias físicas actuales" }).locator("dd").innerText(),
    lote02Cells[1]?.trim(),
    lote02Cells[2]?.trim(),
  ], ["S/ 2,84", "S/ 2,84", "11 UND", "3 UND", "0 UND"]);

  // 11. Logout + Back button + @never_cache across all 5 Stage 05 routes
  await wh.locator("a.sidebar-logout").click();
  await wh.waitForURL(base + "/salir/");
  await wh.getByRole("button", { name: "Cerrar sesión", exact: true }).click();
  await wh.waitForURL(base + "/");
  await wh.goBack();
  await wh.waitForLoadState("networkidle");
  check("logout_back_no_sirve_constancia", wh.url().startsWith(base + "/?next=") || wh.url() === base + "/", true);

  for (const [tag, url] of [
    ["carga_inicial", "/inventario/carga-inicial/"],
    ["constancia_canonica", `/inventario/cargas/${subLoadId}/`],
    ["constancia_alias", `/inventario/carga-inicial/${subLoadId}/creada/`],
    ["stock_overview", "/inventario/stock/"],
    ["movimientos", `/inventario/productos/${subId}/movimientos/`],
  ]) {
    await wh.goto(base + url);
    check(`post_logout_${tag}_redirige_login`, wh.url(), `${base}/?next=${url}`);
  }

  check("cero_page_errors", report.page_errors.length, 0);

  await sellerSession.ctx.close();
  await adminSession.ctx.close();
  await whSession.ctx.close();
}

(async () => {
  const browser = await chromium.launch({
    executablePath: "C:/Program Files/Google/Chrome/Application/chrome.exe",
    headless: true,
  });
  try {
    report.chrome = browser.version();
    await runAudit(browser);
  } catch (error) {
    report.error = error.message;
    process.exitCode = 1;
  } finally {
    fs.writeFileSync(path.join(out, "browser.json"), JSON.stringify(report, null, 2), "utf8");
    await browser.close();
  }
})();
