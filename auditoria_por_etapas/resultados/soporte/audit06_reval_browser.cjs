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

const out = process.env.AUDIT06_OUT;
const run = process.env.AUDIT06_RUN_DIR;
const base = "http://127.0.0.1:" + process.env.AUDIT06_PORT;
const accounts = JSON.parse(fs.readFileSync(path.join(run, ".credentials.json"), "utf8"));
const fixture = JSON.parse(fs.readFileSync(path.join(out, "fixture.json"), "utf8"));

const report = {
  checks: [],
  page_errors: [],
  screenshots: [],
  transport: [],
  layout_metrics: {},
  ui_observations: {},
  input: "Chrome 1366x900 & 390x844 Stage 06 revalidation (DOC-03AB/03AH/03AI/DEC-05, StockReceipt, FEFO, cross-role)",
};

function check(id, actual, expected) {
  assert.deepEqual(actual, expected, id);
  report.checks.push(id);
}

function state() {
  return JSON.parse(
    execFileSync(process.env.AUDIT06_PYTHON, [path.join(__dirname, "audit06_reval_run.py"), "snapshot"], {
      encoding: "utf8",
    })
  );
}

async function loginContext(browser, role, viewport = { width: 1366, height: 900 }) {
  const ctx = await browser.newContext({ locale: "es-PE", viewport });
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
  let forwardedLocation = null;
  let routeFailure = null;
  const failed = page.waitForEvent(
    "requestfailed",
    (req) => req.method() === "POST" && req.url() === base + "/inventario/entrada/"
  );
  await page.route("**/inventario/entrada/", async (route) => {
    if (route.request().method() !== "POST") return route.continue();
    try {
      if (afterCommit) {
        const res = await route.fetch({ maxRedirects: 0 });
        forwardedStatus = res.status();
        forwardedLocation = res.headers()["location"] || null;
      }
      await route.abort("connectionreset");
    } catch (err) {
      routeFailure = err.message;
      await route.abort().catch(() => {});
    }
  });
  await page
    .getByRole("button", { name: "Confirmar entrada", exact: true })
    .click({ noWaitAfter: true })
    .catch((err) => {
      if (!err.message.includes("ERR_CONNECTION_RESET")) throw err;
    });
  const req = await failed;
  await page.waitForLoadState("domcontentloaded").catch(() => {});
  await page.unroute("**/inventario/entrada/");
  check(`intercepcion_sin_error_${afterCommit}`, routeFailure, null);
  check(`fallo_conexion_detectado_${afterCommit}`, req.failure().errorText.includes("ERR_CONNECTION_RESET"), true);
  check(`estado_servidor_intercepcion_${afterCommit}`, forwardedStatus, afterCommit ? 302 : null);
  report.transport.push({ afterCommit, forwardedStatus, forwardedLocation, browserFailure: req.failure().errorText });
  return forwardedLocation;
}

function addDaysIso(isoDate, days) {
  const [y, m, d] = isoDate.split("-").map(Number);
  const dt = new Date(Date.UTC(y, m - 1, d + days));
  return dt.toISOString().slice(0, 10);
}

async function fillEntryLots(page, productId, supplierId, rows) {
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
  const probeRes = await probe.request.get(base, { headers: { "X-Audit06-Challenge": nonce } });
  const expectedProof = crypto
    .createHmac("sha256", fs.readFileSync(path.join(run, ".django-key")))
    .update(nonce)
    .digest("hex");
  check("aislamiento_proof", probeRes.headers()["x-audit06-proof"], expectedProof);
  check("aislamiento_run", probeRes.headers()["x-audit06-run"], path.basename(run));

  const rAnon = await probe.request.get(base + "/inventario/entrada/", { maxRedirects: 0 });
  check("anonimo_entrada_302", rAnon.status(), 302);
  check("anonimo_entrada_next", rAnon.headers()["location"], "/?next=/inventario/entrada/");
  await probeCtx.close();

  // 2. VENDEDOR role boundary + opens CAJA-01 + pre-entry POS sale on p_entry1 (RN-28 baseline)
  const sellerSession = await loginContext(browser, "seller");
  const seller = sellerSession.page;
  check("vendedor_sin_nav_entrada", await seller.locator('#sidebar-navigation a[href="/inventario/entrada/"]').count(), 0);
  check("vendedor_get_entrada_403", (await seller.request.get(base + "/inventario/entrada/", { maxRedirects: 0 })).status(), 403);
  const sellerCsrf = (await sellerSession.ctx.cookies()).find((c) => c.name === "audit06_csrftoken").value;
  const sellerPost = await seller.request.post(base + "/inventario/entrada/", {
    form: {
      csrfmiddlewaretoken: sellerCsrf,
      product: fixture.products.entry1.id,
      "lots-TOTAL_FORMS": "1",
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
  check("vendedor_post_entrada_403", sellerPost.status(), 403);
  check("vendedor_denegado_sin_cambios", state(), initialOrm);

  await seller.getByTestId("cash-open-link").click();
  await seller.waitForURL(base + "/caja/abrir/");
  await seller.locator("[name=opening_amount]").fill("100.00");
  await seller.getByRole("button", { name: "Abrir turno", exact: true }).click();
  await seller.waitForURL(/\/caja\/turnos\/.+\/abierto\//);

  await seller.goto(base + "/ventas/");
  await seller.locator("[name=query]").fill("Jugo Natural");
  await seller.getByRole("button", { name: "Buscar", exact: true }).click();
  const jugPreRow = seller.locator(".sales-search-panel tbody tr", { hasText: fixture.products.entry1.name });
  check("pos_pre_entrada_muestra_10", (await jugPreRow.innerText()).includes("10"), true);
  await jugPreRow.locator('input[name="quantity"]').fill("3");
  await jugPreRow.getByRole("button", { name: "Agregar", exact: true }).click();
  await seller.getByRole("link", { name: "Cobrar venta →", exact: true }).click();
  await seller.waitForURL(base + "/ventas/cobrar/");
  await seller.locator("[name=cash_received]").fill("30.00");
  await seller.getByRole("button", { name: "Confirmar cobro", exact: true }).click();
  await seller.waitForURL(/\/ventas\/constancia\/.+\//);
  const preSaleReceiptUrl = seller.url();
  const preSaleReceiptText = await seller.locator("#constancia-interna").innerText();
  check("venta_previa_total_22_50", preSaleReceiptText.includes("S/ 22,50"), true);
  check("venta_previa_unit_cost_2_6000", state().sale_lines[0].unit_cost, "2.6000");

  // 3. ADMIN role boundary on /inventario/entrada/ (403 GET/POST, no nav link)
  const adminSession = await loginContext(browser, "admin");
  const admin = adminSession.page;
  check("admin_sin_nav_entrada", await admin.locator('#sidebar-navigation a[href="/inventario/entrada/"]').count(), 0);
  check("admin_get_entrada_403", (await admin.request.get(base + "/inventario/entrada/", { maxRedirects: 0 })).status(), 403);
  await admin.goto(base + "/inventario/proveedores/nuevo/");
  const adminCsrf = (await adminSession.ctx.cookies()).find((c) => c.name === "audit06_csrftoken").value;
  const beforeAdminPost = state();
  const adminPost = await admin.request.post(base + "/inventario/entrada/", {
    form: { csrfmiddlewaretoken: adminCsrf, product: fixture.products.entry1.id },
    maxRedirects: 0,
  });
  check("admin_post_entrada_403", adminPost.status(), 403);
  check("admin_denegado_sin_cambios", state(), beforeAdminPost);

  // 4. ALMACENERO navigation + eligibility + FIX06-01 empty POST + heading check
  const whSession = await loginContext(browser, "warehouse");
  const wh = whSession.page;
  check("wh_nav_entrada", await wh.locator('#sidebar-navigation a[href="/inventario/entrada/"]').count(), 1);
  check("wh_card_entrada", await wh.getByTestId("stock-entry-link").count(), 1);

  const entryNavPromise = wh.waitForResponse((r) => r.url().endsWith("/inventario/entrada/") && r.request().method() === "GET");
  await wh.getByTestId("stock-entry-link").click();
  await wh.waitForURL(base + "/inventario/entrada/");
  const entryNavResp = await entryNavPromise;
  check("wh_entrada_200", entryNavResp.status(), 200);
  check("wh_entrada_never_cache", (entryNavResp.headers()["cache-control"] || "").includes("no-store"), true);
  report.ui_observations.stock_entry_topbar_h1 = (await wh.locator("header.app-topbar h1").innerText()).trim();
  report.ui_observations.stock_entry_h2 = (await wh.locator("main h2").innerText()).trim();

  check("select_incluye_entry1", await wh.locator(`[name=product] option[value="${fixture.products.entry1.id}"]`).count(), 1);
  check("select_incluye_exhausted", await wh.locator(`[name=product] option[value="${fixture.products.exhausted.id}"]`).count(), 1);
  check("select_incluye_expired_only", await wh.locator(`[name=product] option[value="${fixture.products.expired_only.id}"]`).count(), 1);
  check("select_excluye_no_load", await wh.locator(`[name=product] option[value="${fixture.products.no_load.id}"]`).count(), 0);
  check("select_excluye_inactive", await wh.locator(`[name=product] option[value="${fixture.products.inactive.id}"]`).count(), 0);
  check("select_excluye_cat_off", await wh.locator(`[name=product] option[value="${fixture.products.cat_off.id}"]`).count(), 0);

  const whCsrf = (await whSession.ctx.cookies()).find((c) => c.name === "audit06_csrftoken").value;
  const emptyHeaderPost = await wh.request.post(base + "/inventario/entrada/", {
    headers: { "X-CSRFToken": whCsrf },
    data: "",
    maxRedirects: 0,
  });
  const emptyHeaderBody = await emptyHeaderPost.text();
  check("fix06_post_vacio_header_csrf_200", emptyHeaderPost.status(), 200);
  check("fix06_post_vacio_header_csrf_con_alertas", emptyHeaderBody.includes("Seleccione un producto.") && emptyHeaderBody.includes('role="alert"'), true);

  // 5. Validation + Sentinel supplier race + key preservation across errors (no partial commit!)
  const initialUuidKey = await wh.locator('[name="idempotency_key"]').inputValue();
  check("uuid_oculto_presente", initialUuidKey.length, 36);

  await fillEntryLots(wh, fixture.products.entry1.id, fixture.suppliers.race.id, [
    { number: "POST-BAD-1", quantity: "0", unit_cost: "1e2", expiration_date: fixture.tomorrow },
    { number: "POST-BAD-2", quantity: "5", unit_cost: "1.23456", expiration_date: fixture.today },
    { number: "POST-BAD-3", quantity: "3", unit_cost: "2.00", expiration_date: addDaysIso(fixture.today, 366 * 21) },
    { number: " post-bad-3 ", quantity: "2", unit_cost: "2.00", expiration_date: fixture.tomorrow },
  ]);

  await admin.goto(base + "/inventario/proveedores/");
  await admin.locator("tbody tr", { hasText: fixture.suppliers.race.name }).getByRole("button", { name: /Desactivar|Inactivar/i }).click();
  await admin.waitForLoadState("networkidle");
  const afterAdminSupToggle = state();

  await wh.getByRole("button", { name: "Confirmar entrada", exact: true }).click();
  await wh.waitForLoadState("domcontentloaded");
  check("errores_no_mutan_bd", state(), afterAdminSupToggle);
  check("errores_conservan_uuid_clave", await wh.locator('[name="idempotency_key"]').inputValue(), initialUuidKey);
  check("errores_conserva_producto_seleccionado", await wh.locator("[name=product]").inputValue(), fixture.products.entry1.id);
  check("errores_conserva_sentinel_inactivo", await wh.locator("[name=supplier]").inputValue(), `__inactive__:${fixture.suppliers.race.id}`);
  const alertsJoined = (await wh.locator('[role="alert"]').allInnerTexts()).join(" | ");
  check("error_proveedor_inactivo_visible", alertsJoined.includes("está inactivo"), true);
  check("error_cantidad_minima", alertsJoined.includes("mayor o igual a 1"), true);
  check("error_notacion_cientifica", alertsJoined.includes("notación científica"), true);
  check("error_vencimiento_hoy_lima", alertsJoined.includes("posterior a hoy en Lima"), true);
  check("error_vencimiento_20_anos", alertsJoined.includes("20 años"), true);
  check("error_lote_duplicado_lote", alertsJoined.includes("está repetido"), true);
  report.ui_observations.stock_entry_has_top_focus_summary = (await wh.locator("#stock-entry-errors").count()) > 0;
  check(
    "form_errores_sin_overflow",
    await wh.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth),
    true
  );
  await shot(wh, "01-entrada-errores-y-sentinel.png");

  // 6. Parallel ADMIN suspends Bebidas Audit06R while WH submits valid entry -> rejects atomically, then reactivates
  await admin.goto(base + "/productos/categorias/");
  await admin.locator("tbody tr", { hasText: fixture.categories.drinks.name }).getByRole("button", { name: "Desactivar", exact: true }).click();
  await admin.waitForURL(/\/productos\/categorias\/.+\/estado\/confirmar\//);
  await admin.getByRole("button", { name: "Confirmar desactivación", exact: true }).click();
  await admin.waitForURL(base + "/productos/categorias/");

  const afterSuspendOrm = state();
  await fillEntryLots(wh, fixture.products.entry1.id, fixture.suppliers.long.id, [
    { number: "POST-EARLY", quantity: "2", unit_cost: "4.0000", expiration_date: fixture.soon_10 },
  ]);
  await wh.getByRole("button", { name: "Confirmar entrada", exact: true }).click();
  check("categoria_suspendida_rechaza_entrada_sin_escrituras", state(), afterSuspendOrm);
  check("categoria_suspendida_alerta", (await wh.locator('[role="alert"]').allInnerTexts()).length > 0, true);

  await admin.locator("tbody tr", { hasText: fixture.categories.drinks.name }).getByRole("button", { name: "Activar", exact: true }).click();
  await admin.waitForURL(/\/productos\/categorias\/.+\/estado\/confirmar\//);
  await admin.getByRole("button", { name: "Confirmar activación", exact: true }).click();
  await admin.waitForURL(base + "/productos/categorias/");

  // 7. Second ALMACENERO registers multi-lot stock entry on p_entry1 -> /inventario/recepciones/<uuid>/ (R-00000001)
  // Remaining: 7 @ 2.6000 = 18.2000; incoming POST-EARLY (2 @ 4.0000 = 8.0000, +10d) + lot64 (1 @ 5.0345 = 5.0345, +60d)
  // Average = (18.2000 + 13.0345)/10 = 3.12345 -> HALF_UP 3.1235 -> UI S/ 3,12
  const wh2Session = await loginContext(browser, "warehouse2");
  const wh2 = wh2Session.page;
  await wh2.getByTestId("stock-entry-link").click();
  await wh2.waitForURL(base + "/inventario/entrada/");

  const lot64 = "E".repeat(64);
  await fillEntryLots(wh2, fixture.products.entry1.id, fixture.suppliers.long.id, [
    { number: " post-early ", quantity: "2", unit_cost: "4.0000", expiration_date: fixture.soon_10 },
    { number: "", quantity: "", unit_cost: "", expiration_date: "" },
    { number: lot64, quantity: "1", unit_cost: "5.0345", expiration_date: fixture.future_60 },
    { number: "", quantity: "", unit_cost: "", expiration_date: "" },
  ]);
  await wh2.getByRole("button", { name: "Confirmar entrada", exact: true }).click();
  await wh2.waitForURL(/\/inventario\/recepciones\/.+\//);
  const receipt1Url = wh2.url();
  const afterEntry1 = state();

  const entry1Prod = afterEntry1.products.find((p) => p.id === fixture.products.entry1.id);
  check("entry1_costo_promedio_half_up_4dec", entry1Prod.average_cost, "3.1235");
  const rec1 = afterEntry1.stock_receipts.find((r) => r.correlative === "R-00000001");
  check("entry1_crea_stock_receipt_r1", Boolean(rec1), true);
  check("entry1_responsables_distintos", rec1.responsible_id !== afterEntry1.loads.find((l) => l.product_id === fixture.products.entry1.id).responsible_id, true);

  const rec1Main = await wh2.locator('[data-testid="stock-receipt"]').innerText();
  check("rec1_titulo_correlativo", (await wh2.locator("main h2").innerText()).trim(), "R-00000001");
  check("rec1_muestra_s_3_12", rec1Main.includes("S/ 3,12"), true);
  check("rec1_muestra_dos_lotes", rec1Main.includes("POST-EARLY") && rec1Main.includes(lot64), true);
  check("rec1_wh_tiene_boton_otra_recepcion", await wh2.getByRole("link", { name: "Registrar otra recepción", exact: true }).count(), 1);
  report.ui_observations.stock_receipt_topbar_h1 = (await wh2.locator("header.app-topbar h1").innerText()).trim();

  const rec1Metrics = await wh2.evaluate(() => {
    const docOk = document.documentElement.scrollWidth <= window.innerWidth;
    const dlItems = document.querySelectorAll('[data-testid="stock-receipt"] dl > div').length;
    const ths = Array.from(document.querySelectorAll('[data-testid="stock-receipt"] th'));
    const thWrapOk = ths.length === 5 && ths.every((th) => getComputedStyle(th).overflowWrap === "normal");
    return { docOk, dlItems, thCount: ths.length, thWrapOk };
  });
  report.layout_metrics.stock_receipt_desktop = rec1Metrics;
  check("rec1_layout_5_cols_6_dl_sin_overflow", rec1Metrics, {
    docOk: true,
    dlItems: 6,
    thCount: 5,
    thWrapOk: true,
  });
  await shot(wh2, "02-entrada-lote64-y-recepcion.png");

  // 8. F-COSTO direct receipt WITHOUT supplier & WITHOUT SOL -> R-00000002 (4.0714 -> S/ 4,07)
  //    Then second delivery of same commercial lot C@8 -> R-00000003 (4.6666 -> S/ 4,67), plus contradictory date rejected
  await wh.goto(base + "/inventario/entrada/");
  await fillEntryLots(wh, fixture.products.fcosto.id, "", [
    { number: " c ", quantity: "10", unit_cost: "6.0000", expiration_date: fixture.future_60 },
  ]);
  await wh.getByRole("button", { name: "Confirmar entrada", exact: true }).click();
  await wh.waitForURL(/\/inventario\/recepciones\/.+\//);
  const rec2Main = await wh.locator("main").innerText();
  check("fcosto_r2_sin_proveedor", rec2Main.includes("R-00000002") && rec2Main.includes("Sin proveedor asignado") && rec2Main.includes("S/ 4,07"), true);
  check("fcosto_r2_sin_texto_sol", !rec2Main.toLowerCase().includes("solicitud aprobada"), true);

  // Second commercial delivery of same lot C (+60d) with supplier -> R-00000003
  await wh2.goto(base + "/inventario/entrada/");
  await fillEntryLots(wh2, fixture.products.fcosto.id, fixture.suppliers.active.id, [
    { number: "C", quantity: "5", unit_cost: "8.0000", expiration_date: fixture.future_60 },
  ]);
  await wh2.getByRole("button", { name: "Confirmar entrada", exact: true }).click();
  await wh2.waitForURL(/\/inventario\/recepciones\/.+\//);
  const rec3Main = await wh2.locator("main").innerText();
  check("fcosto_r3_lote_comercial_repetido_permitido", rec3Main.includes("R-00000003") && rec3Main.includes("S/ 4,67"), true);
  check("fcosto_avg_4_6666", state().products.find((p) => p.id === fixture.products.fcosto.id).average_cost, "4.6666");
  await shot(wh2, "03-fcosto-sin-proveedor-y-repetido.png");

  // Contradictory date for lot C must reject cleanly
  const beforeBadDate = state();
  await wh2.goto(base + "/inventario/entrada/");
  await fillEntryLots(wh2, fixture.products.fcosto.id, fixture.suppliers.active.id, [
    { number: "c", quantity: "2", unit_cost: "8.0000", expiration_date: fixture.future_90 },
  ]);
  await wh2.getByRole("button", { name: "Confirmar entrada", exact: true }).click();
  await wh2.waitForLoadState("domcontentloaded");
  check("lote_c_fecha_contradictoria_rechazada", (await wh2.locator('[role="alert"]').allInnerTexts()).join(" | ").includes("otro vencimiento"), true);
  check("lote_c_fecha_contradictoria_sin_escrituras", state(), beforeBadDate);

  // 9. p_exhausted: ERR_CONNECTION_RESET before commit (0 writes) & after commit (302 lost -> R-00000004), replay, divergent key, recovery via Ver carga
  await wh.goto(base + "/inventario/entrada/");
  await fillEntryLots(wh, fixture.products.exhausted.id, fixture.suppliers.active.id, [
    { number: "EXH-POST-01", quantity: "12", unit_cost: "3.7500", expiration_date: fixture.future_45 },
  ]);
  const beforePreAbort = state();
  await droppedPost(wh, false);
  check("abort_antes_commit_entrada_sin_escrituras", state(), beforePreAbort);

  await wh.goto(base + "/inventario/entrada/");
  await fillEntryLots(wh, fixture.products.exhausted.id, fixture.suppliers.active.id, [
    { number: "EXH-POST-01", quantity: "12", unit_cost: "3.7500", expiration_date: fixture.future_45 },
  ]);
  const exhPayload = await wh.locator('form[data-testid="stock-entry-form"]').evaluate((f) => Object.fromEntries(new FormData(f)));
  const lostRedirectLoc = await droppedPost(wh, true);

  const afterExh = state();
  const exhReceipts = afterExh.stock_receipts.filter((r) => r.product_id === fixture.products.exhausted.id);
  check("exh_crea_1_recepcion_r4_pese_302_perdido", exhReceipts.length, 1);
  check("exh_correlative_r4", exhReceipts[0].correlative, "R-00000004");
  check("exh_costo_promedio_zero_prior_3_7500", afterExh.products.find((p) => p.id === fixture.products.exhausted.id).average_cost, "3.7500");

  // Same-key HTTP replay returns 302 to SAME receipt without duplication
  const replayExh = await wh.request.post(base + "/inventario/entrada/", { form: exhPayload, maxRedirects: 0 });
  check("reenvio_idempotente_302", replayExh.status(), 302);
  check("reenvio_idempotente_mismo_destino", replayExh.headers()["location"], lostRedirectLoc);
  check("reenvio_idempotente_no_duplica", state(), afterExh);

  // Divergent payload with same idempotency_key rejects (200) without mutating
  const divergentPayload = { ...exhPayload, "lots-0-quantity": "13" };
  const divReplay = await wh.request.post(base + "/inventario/entrada/", { form: divergentPayload, maxRedirects: 0 });
  check("reenvio_divergente_200", divReplay.status(), 200);
  check("reenvio_divergente_alerta", (await divReplay.text()).includes("otro contenido o responsable"), true);
  check("reenvio_divergente_sin_escrituras", state(), afterExh);

  // Recovery via UI: /inventario/stock/ -> "Ver carga" -> link R-00000004 under "Recepciones con constancia propia"
  await wh.goto(base + "/inventario/stock/");
  const stockFit = await wh.evaluate(() => {
    const docOk = document.documentElement.scrollWidth <= window.innerWidth;
    const ths = Array.from(document.querySelectorAll(".table-wrap table th"));
    const wrap = document.querySelector(".table-wrap");
    return { docOk, wrapScrollWidth: wrap.scrollWidth, wrapClientWidth: wrap.clientWidth, thCount: ths.length };
  });
  report.layout_metrics.stock_overview = stockFit;
  check("stock_overview_sin_overflow", stockFit.docOk && stockFit.thCount === 7, true);
  await shot(wh, "04-stock-overview-tras-entrada.png");

  await wh.locator("tbody tr", { hasText: fixture.products.exhausted.name }).getByRole("link", { name: "Ver carga", exact: true }).click();
  await wh.waitForURL(/\/inventario\/cargas\//);
  const loadText = await wh.locator("main").innerText();
  check("carga_enlaza_recepciones_propias", loadText.includes("Recepciones con constancia propia") && loadText.includes("R-00000004"), true);
  await wh.getByRole("link", { name: "R-00000004", exact: true }).click();
  await wh.waitForURL(/\/inventario\/recepciones\/.+\//);
  check("recuperacion_ui_llega_a_r4", (await wh.locator("main").innerText()).includes("EXH-POST-01") && (await wh.locator("main").innerText()).includes("12 UND"), true);

  // 10. Post-entry POS FEFO sale V-00000002 on p_entry1 (qty=4 -> exhausts POST-EARLY + 2 from L02-INI-EARLY)
  await seller.goto(base + "/ventas/");
  await seller.locator("[name=query]").fill("Jugo Natural");
  await seller.getByRole("button", { name: "Buscar", exact: true }).click();
  const jugPostRow = seller.locator(".sales-search-panel tbody tr", { hasText: fixture.products.entry1.name });
  check("pos_post_entrada_muestra_10_combinados", (await jugPostRow.innerText()).includes("10"), true);
  await jugPostRow.locator('input[name="quantity"]').fill("4");
  await jugPostRow.getByRole("button", { name: "Agregar", exact: true }).click();
  await seller.getByRole("link", { name: "Cobrar venta →", exact: true }).click();
  await seller.waitForURL(base + "/ventas/cobrar/");
  await seller.locator("[name=cash_received]").fill("50.00");
  await seller.getByRole("button", { name: "Confirmar cobro", exact: true }).click();
  await seller.waitForURL(/\/ventas\/constancia\/.+\//);
  const postSaleReceiptText = await seller.locator("#constancia-interna").innerText();
  check("venta_post_total_30_00", postSaleReceiptText.includes("S/ 30,00"), true);
  check("pos_oculta_costo_compra_al_vendedor", !postSaleReceiptText.includes("3,1235") && !postSaleReceiptText.includes("3.1235"), true);
  await shot(seller, "06-pos-venta-post-entrada.png");

  const afterPostSale = state();
  const pEarly = afterPostSale.lots.find((l) => l.product_id === fixture.products.entry1.id && l.number_normalized === "POST-EARLY");
  const p64 = afterPostSale.lots.find((l) => l.product_id === fixture.products.entry1.id && l.number_normalized === lot64);
  const iniEarly = afterPostSale.lots.find((l) => l.product_id === fixture.products.entry1.id && l.number_normalized === "L02-INI-EARLY");
  const iniLate = afterPostSale.lots.find((l) => l.product_id === fixture.products.entry1.id && l.number_normalized === "L01-INI-LATE");
  check("fefo_mixto_agota_subsequent_post_early", pEarly.available_quantity, 0);
  check("fefo_mixto_descuenta_2_de_initial_early", iniEarly.available_quantity, 1);
  check("fefo_mixto_conserva_post64_y_ini_late", [p64.available_quantity, iniLate.available_quantity], [1, 4]);
  const v1Sale = afterPostSale.sales.find((s) => s.correlative === "V-00000001");
  const v2Sale = afterPostSale.sales.find((s) => s.correlative === "V-00000002");
  const v1Line = afterPostSale.sale_lines.find((sl) => v1Sale && sl.sale_id === v1Sale.id);
  const v2Line = afterPostSale.sale_lines.find((sl) => v2Sale && sl.sale_id === v2Sale.id);
  check("rn28_venta_previa_conserva_2_6000", v1Line && v1Line.unit_cost, "2.6000");
  check("rn28_venta_posterior_captura_3_1235", v2Line && v2Line.unit_cost, "3.1235");
  await seller.goto(preSaleReceiptUrl);
  check("rn28_constancia_previa_inalterada", await seller.locator("#constancia-interna").innerText(), preSaleReceiptText);

  // 11. ADMIN Kardex verification + Product rename proving StockReceipt snapshot immutability + ADMIN read-only receipt check
  await admin.goto(base + `/inventario/productos/${fixture.products.entry1.id}/movimientos/`);
  const kardexText = await admin.locator("table").innerText();
  check(
    "admin_kardex_recepciones_y_actores_completos",
    kardexText.includes("Carga inicial — Lote L02-INI-EARLY") &&
      kardexText.includes("Recepción R-00000001 — Lote POST-EARLY") &&
      kardexText.includes("Ver recepción") &&
      kardexText.includes("Lucia Almacen06R") &&
      kardexText.includes("Pedro Almacen06R") &&
      kardexText.includes("Venta V-00000001") &&
      kardexText.includes("Venta V-00000002") &&
      kardexText.includes("3,1235"),
    true
  );
  check(
    "admin_kardex_sin_overflow",
    await admin.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth),
    true
  );
  await shot(admin, "05-kardex-mixto-y-rn28.png");

  // Rename product in catalog and confirm R-00000001 snapshot stays original + ADMIN sees no Registrar otra recepcion CTA
  await admin.goto(base + `/productos/${fixture.products.entry1.id}/editar/`);
  await admin.locator('[name="name"]').fill("Jugo Renombrado Audit06R");
  await admin.locator('main form button[type="submit"]').click();
  await admin.waitForURL(base + "/productos/");
  await admin.goto(receipt1Url);
  const adminRec1Text = await admin.locator('[data-testid="stock-receipt"]').innerText();
  check("admin_constancia_conserva_snapshot_nombre_original", adminRec1Text.includes("Jugo Natural Naranja 1L") && !adminRec1Text.includes("Jugo Renombrado Audit06R"), true);
  check("admin_constancia_sin_boton_otra_recepcion", await admin.getByRole("link", { name: "Registrar otra recepción", exact: true }).count(), 0);

  // 12. Responsive mobile 390x844 check for ALMACENERO on stock-entry and stock-receipt
  await wh.setViewportSize({ width: 390, height: 844 });
  await wh.goto(base + "/inventario/entrada/");
  const mobileEntryOverflow = await wh.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth);
  check("movil_entrada_390_sin_overflow", mobileEntryOverflow, true);
  await shot(wh, "07-movil-entrada-390x844.png");
  await wh.goto(receipt1Url);
  const mobileRecOverflow = await wh.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth);
  check("movil_recepcion_390_sin_overflow", mobileRecOverflow, true);
  await shot(wh, "08-movil-recepcion-390x844.png");
  await wh.setViewportSize({ width: 1366, height: 900 });

  // 13. Logout + Back button + @never_cache on /inventario/entrada/
  await wh.goto(base + "/inventario/entrada/");
  await wh.locator("a.sidebar-logout").click();
  await wh.waitForURL(base + "/salir/");
  await wh.getByRole("button", { name: "Cerrar sesión", exact: true }).click();
  await wh.waitForURL(base + "/");
  await wh.goBack();
  await wh.waitForLoadState("networkidle");
  check("logout_back_no_sirve_entrada", wh.url().startsWith(base + "/?next=") || wh.url() === base + "/", true);

  await wh.goto(base + "/inventario/entrada/");
  check("post_logout_entrada_redirige_login", wh.url(), `${base}/?next=/inventario/entrada/`);

  check("cero_page_errors", report.page_errors.length, 0);

  await sellerSession.ctx.close();
  await adminSession.ctx.close();
  await whSession.ctx.close();
  await wh2Session.ctx.close();
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
