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
  input: "Chrome 1366x900 Stage 06 audit (HU-INV-01b stock_entry, suppliers, lots, HALF_UP, RN-28, FEFO, cross-role)",
};

function check(id, actual, expected) {
  assert.deepEqual(actual, expected, id);
  report.checks.push(id);
}

function state() {
  return JSON.parse(
    execFileSync(process.env.AUDIT06_PYTHON, [path.join(__dirname, "audit06_run.py"), "snapshot"], {
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
    (req) => req.method() === "POST" && req.url() === base + "/inventario/entrada/"
  );
  await page.route("**/inventario/entrada/", async (route) => {
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
  report.transport.push({ afterCommit, forwardedStatus, browserFailure: req.failure().errorText });
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

  // 2. VENDEDOR role boundary + opens CAJA-06 + pre-entry POS sale on p_entry1 (RN-28 baseline)
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

  // VENDEDOR opens CAJA-06 and sells 3 units of p_entry1 BEFORE replenishment (unit_cost == 2.6000)
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

  const afterPreSale = state();
  check("venta_previa_unit_cost_2_6000", afterPreSale.sale_lines[0].unit_cost, "2.6000");

  // 3. ADMIN role boundary on /inventario/entrada/ (403 GET/POST, no nav link)
  const adminSession = await loginContext(browser, "admin");
  const admin = adminSession.page;
  check("admin_sin_nav_entrada", await admin.locator('#sidebar-navigation a[href="/inventario/entrada/"]').count(), 0);
  check("admin_get_entrada_403", (await admin.request.get(base + "/inventario/entrada/", { maxRedirects: 0 })).status(), 403);
  const adminCsrf = (await adminSession.ctx.cookies()).find((c) => c.name === "audit06_csrftoken").value;
  const beforeAdminPost = state();
  const adminPost = await admin.request.post(base + "/inventario/entrada/", {
    form: { csrfmiddlewaretoken: adminCsrf, product: fixture.products.entry1.id },
    maxRedirects: 0,
  });
  check("admin_post_entrada_403", adminPost.status(), 403);
  check("admin_denegado_sin_cambios", state(), beforeAdminPost);

  // 4. ALMACENERO navigation via dashboard & sidebar + eligibility + FIX06-01 empty POST
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

  // Verify StockEntryProductForm dropdown eligibility
  check("select_incluye_entry1", await wh.locator(`[name=product] option[value="${fixture.products.entry1.id}"]`).count(), 1);
  check("select_incluye_exhausted", await wh.locator(`[name=product] option[value="${fixture.products.exhausted.id}"]`).count(), 1);
  check("select_incluye_expired_only", await wh.locator(`[name=product] option[value="${fixture.products.expired_only.id}"]`).count(), 1);
  check("select_excluye_no_load", await wh.locator(`[name=product] option[value="${fixture.products.no_load.id}"]`).count(), 0);
  check("select_excluye_inactive", await wh.locator(`[name=product] option[value="${fixture.products.inactive.id}"]`).count(), 0);
  check("select_excluye_cat_off", await wh.locator(`[name=product] option[value="${fixture.products.cat_off.id}"]`).count(), 0);

  // Empty POST {} with X-CSRFToken header (FIX06-01) -> MUST return 200 with validation alerts
  const whCsrf = (await whSession.ctx.cookies()).find((c) => c.name === "audit06_csrftoken").value;
  const emptyHeaderPost = await wh.request.post(base + "/inventario/entrada/", {
    headers: { "X-CSRFToken": whCsrf },
    data: "",
    maxRedirects: 0,
  });
  const emptyHeaderBody = await emptyHeaderPost.text();
  check("fix06_post_vacio_header_csrf_200", emptyHeaderPost.status(), 200);
  check("fix06_post_vacio_header_csrf_con_alertas", emptyHeaderBody.includes("Seleccione un producto.") && emptyHeaderBody.includes('role="alert"'), true);

  // 5. Validation + Sentinel supplier race across parallel ADMIN tab + no horizontal overflow on errors
  await fillEntryLots(wh, fixture.products.entry1.id, fixture.suppliers.race.id, [
    { number: " l01-ini-late ", quantity: "0", unit_cost: "1e2", expiration_date: fixture.tomorrow },
    { number: "POST-BAD-2", quantity: "5", unit_cost: "1.23456", expiration_date: fixture.today },
    { number: "POST-BAD-1", quantity: "3", unit_cost: "2.00", expiration_date: addDaysIso(fixture.today, 366 * 21) },
    { number: " post-bad-1 ", quantity: "2", unit_cost: "2.00", expiration_date: fixture.tomorrow },
  ]);

  // Parallel ADMIN deactivates suppliers.race while WH holds the form open
  await admin.goto(base + "/inventario/proveedores/");
  await admin.locator("tbody tr", { hasText: fixture.suppliers.race.name }).getByRole("button", { name: /Desactivar|Inactivar/i }).click();
  await admin.waitForLoadState("networkidle");
  const afterAdminSupToggle = state();

  await wh.getByRole("button", { name: "Confirmar entrada", exact: true }).click();
  await wh.waitForLoadState("domcontentloaded");
  check("errores_no_mutan_bd", state(), afterAdminSupToggle);
  check("errores_conserva_producto_seleccionado", await wh.locator("[name=product]").inputValue(), fixture.products.entry1.id);
  const selectedSupVal = await wh.locator("[name=supplier]").inputValue();
  check("errores_conserva_sentinel_inactivo", selectedSupVal, `__inactive__:${fixture.suppliers.race.id}`);
  const alertsJoined = (await wh.locator('[role="alert"]').allInnerTexts()).join(" | ");
  check("error_proveedor_inactivo_visible", alertsJoined.includes("está inactivo"), true);
  check("error_cantidad_minima", alertsJoined.includes("mayor o igual a 1"), true);
  check("error_notacion_cientifica", alertsJoined.includes("notación científica"), true);
  check("error_vencimiento_hoy_lima", alertsJoined.includes("posterior a hoy en Lima"), true);
  check("error_vencimiento_20_anos", alertsJoined.includes("20 años"), true);
  check("error_lote_duplicado_lote", alertsJoined.includes("está repetido"), true);
  check(
    "form_errores_sin_overflow",
    await wh.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth),
    true
  );
  await shot(wh, "01-entrada-errores-y-sentinel.png");

  // Also verify rejecting duplicate against INITIAL lot on valid supplier submission (no partial commit!)
  await fillEntryLots(wh, fixture.products.entry1.id, fixture.suppliers.active.id, [
    { number: "POST-OK-PRE", quantity: "2", unit_cost: "3.0000", expiration_date: fixture.future_45 },
    { number: " l01-ini-late ", quantity: "2", unit_cost: "3.0000", expiration_date: fixture.future_60 },
  ]);
  await wh.getByRole("button", { name: "Confirmar entrada", exact: true }).click();
  await wh.waitForLoadState("domcontentloaded");
  check("lote_repetido_inicial_rechaza_todo", state(), afterAdminSupToggle);
  check("lote_repetido_inicial_mensaje", (await wh.locator('[role="alert"]').allInnerTexts()).join(" | ").includes("ya existe para este producto"), true);

  // 6. Parallel ADMIN suspends Bebidas Audit06 while WH submits valid entry -> rejects atomically, then reactivates
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

  // Reactivate Bebidas Audit06
  await admin.locator("tbody tr", { hasText: fixture.categories.drinks.name }).getByRole("button", { name: "Activar", exact: true }).click();
  await admin.waitForURL(/\/productos\/categorias\/.+\/estado\/confirmar\//);
  await admin.getByRole("button", { name: "Confirmar activación", exact: true }).click();
  await admin.waitForURL(base + "/productos/categorias/");

  // 7. Second ALMACENERO logs in and registers multi-lot stock entry on p_entry1:
  // Prior remaining sellable: 7 @ 2.6000 = 18.2000
  // New lots: POST-EARLY (2 @ 4.0000 = 8.0000, exp +10d) + sparse blank row + 64-char lot (1 @ 5.0345 = 5.0345, exp +60d)
  // Moving average = (18.2000 + 13.0345) / 10 = 3.12345 -> HALF_UP 3.1235 -> visual S/ 3,12
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
  await wh2.waitForURL(/\/inventario\/cargas\//);
  const entry1ConstanciaUrl = wh2.url();
  const afterEntry1 = state();

  const entry1Prod = afterEntry1.products.find((p) => p.id === fixture.products.entry1.id);
  check("entry1_costo_promedio_half_up_4dec", entry1Prod.average_cost, "3.1235");
  const entry1Lots = afterEntry1.lots.filter((l) => l.product_id === fixture.products.entry1.id);
  check("entry1_4_lotes_2ini_2post", entry1Lots.length, 4);
  check(
    "entry1_is_initial_y_responsible_distintos",
    entry1Lots.filter((l) => !l.is_initial).every((l) => l.responsible_id !== entry1Lots.find((x) => x.is_initial).responsible_id),
    true
  );
  check("entry1_constancia_muestra_s_3_12", await wh2.locator("dl > div").filter({ hasText: "Costo promedio" }).locator("dd").innerText(), "S/ 3,12");
  check("entry1_constancia_existencias_10_und", await wh2.locator("dl > div").filter({ hasText: "Existencias físicas" }).locator("dd").innerText(), "10 UND");

  const wrapMetrics = await wh2.evaluate(() => {
    const docOk = document.documentElement.scrollWidth <= window.innerWidth;
    const ths = Array.from(document.querySelectorAll(".load-detail-panel th"));
    const thWrapOk = ths.length === 14 && ths.every((th) => getComputedStyle(th).overflowWrap === "normal");
    const shortCell = Array.from(document.querySelectorAll(".load-detail-panel td.load-col-lot")).find(
      (td) => td.textContent.trim() === "POST-EARLY"
    );
    let shortCellSingleLine = false;
    if (shortCell) {
      const range = document.createRange();
      range.selectNodeContents(shortCell);
      shortCellSingleLine = range.getClientRects().length === 1;
    }
    return { docOk, thCount: ths.length, thWrapOk, shortCellSingleLine };
  });
  report.layout_metrics.constancia_posteriores = wrapMetrics;
  check("entry1_constancia_wrap_14_ths_normales", wrapMetrics, {
    docOk: true,
    thCount: 14,
    thWrapOk: true,
    shortCellSingleLine: true,
  });
  await shot(wh2, "02-entrada-lote64-y-constancia.png");

  // 8. Exhausted product p_exhausted: aborted POST before commit, lost 302 after commit, replay rejects duplicate lot, recovery via stock-overview
  await wh.goto(base + "/inventario/entrada/");
  await fillEntryLots(wh, fixture.products.exhausted.id, fixture.suppliers.active.id, [
    { number: "EXH-POST-01", quantity: "12", unit_cost: "3.7500", expiration_date: fixture.future_45 },
  ]);
  await droppedPost(wh, false);
  check("abort_antes_commit_entrada_sin_escrituras", state(), afterEntry1);

  await wh.goto(base + "/inventario/entrada/");
  await fillEntryLots(wh, fixture.products.exhausted.id, fixture.suppliers.active.id, [
    { number: "EXH-POST-01", quantity: "12", unit_cost: "3.7500", expiration_date: fixture.future_45 },
  ]);
  const exhPayload = await wh.locator('form[data-testid="stock-entry-form"]').evaluate((f) => Object.fromEntries(new FormData(f)));
  await droppedPost(wh, true);

  const afterExh = state();
  check("exh_crea_exactamente_1_lote_pese_302_perdido", afterExh.lots.filter((l) => l.product_id === fixture.products.exhausted.id).length, 2);
  check("exh_costo_promedio_zero_prior_3_7500", afterExh.products.find((p) => p.id === fixture.products.exhausted.id).average_cost, "3.7500");

  // Replay identical payload after lost 302 MUST reject duplicate lot cleanly without mutating DB
  const replayExh = await wh.request.post(base + "/inventario/entrada/", { form: exhPayload, maxRedirects: 0 });
  const replayBody = await replayExh.text();
  check("reenvio_entrada_tras_302_perdido_200", replayExh.status(), 200);
  check("reenvio_entrada_informa_lote_existe", replayBody.includes("ya existe para este producto"), true);
  check("reenvio_entrada_no_duplica", state(), afterExh);

  // Recovery via UI: /inventario/stock/ -> "Ver carga" + visual metrics
  await wh.goto(base + "/inventario/stock/");
  const stockFit = await wh.evaluate(() => {
    const docOk = document.documentElement.scrollWidth <= window.innerWidth;
    const ths = Array.from(document.querySelectorAll(".table-wrap table th"));
    const actionButtons = Array.from(document.querySelectorAll(".table-wrap tbody a.button"));
    const wrap = document.querySelector(".table-wrap");
    const wrapRect = wrap.getBoundingClientRect();
    const outOfBounds = actionButtons
      .map((a) => ({ text: a.textContent.trim(), right: Math.round(a.getBoundingClientRect().right), wrapRight: Math.round(wrapRect.right) }))
      .filter((x) => x.right > x.wrapRight + 1);
    return {
      docOk,
      wrapScrollWidth: wrap.scrollWidth,
      wrapClientWidth: wrap.clientWidth,
      thCount: ths.length,
      btnCount: actionButtons.length,
      buttonsInsideWrap: outOfBounds.length === 0,
      outOfBounds,
    };
  });
  report.layout_metrics.stock_overview = stockFit;
  await shot(wh, "03-stock-overview-tras-entrada.png");
  check("stock_overview_sin_overflow_doc_y_tablas", stockFit.docOk && stockFit.thCount === 7 && stockFit.btnCount > 0, true);

  await wh.locator("tbody tr", { hasText: fixture.products.exhausted.name }).getByRole("link", { name: "Ver carga", exact: true }).click();
  await wh.waitForURL(/\/inventario\/cargas\//);
  check("exh_constancia_recuperada_muestra_12_und", (await wh.locator("main").innerText()).includes("12 UND") && (await wh.locator("main").innerText()).includes("EXH-POST-01"), true);

  // 9. Post-entry POS FEFO sale on p_entry1 (V-00000002): buys 4 -> consumes ALL 2 of POST-EARLY (+10d, subsequent!) + 2 of L02-INI-EARLY (+20d, initial!)
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
  check("venta_post_total_30_00", (await seller.locator("#constancia-interna").innerText()).includes("S/ 30,00"), true);
  await shot(seller, "05-pos-venta-post-entrada.png");

  const afterPostSale = state();
  const pEarly = afterPostSale.lots.find((l) => l.product_id === fixture.products.entry1.id && l.number_normalized === "POST-EARLY");
  const p64 = afterPostSale.lots.find((l) => l.product_id === fixture.products.entry1.id && l.number_normalized === lot64);
  const iniEarly = afterPostSale.lots.find((l) => l.product_id === fixture.products.entry1.id && l.number_normalized === "L02-INI-EARLY");
  const iniLate = afterPostSale.lots.find((l) => l.product_id === fixture.products.entry1.id && l.number_normalized === "L01-INI-LATE");
  check("fefo_mixto_agota_subsequent_post_early", pEarly.available_quantity, 0);
  check("fefo_mixto_descuenta_2_de_initial_early", iniEarly.available_quantity, 1);
  check("fefo_mixto_conserva_post64_y_ini_late", [p64.available_quantity, iniLate.available_quantity], [1, 4]);

  // RN-28: sale 1 keeps unit_cost == 2.6000, sale 2 captures 3.1235, and pre-sale receipt text is bit-identical
  check("rn28_venta_previa_conserva_2_6000", afterPostSale.sale_lines[0].unit_cost, "2.6000");
  check("rn28_venta_posterior_captura_3_1235", afterPostSale.sale_lines[1].unit_cost, "3.1235");
  await seller.goto(preSaleReceiptUrl);
  check("rn28_constancia_previa_inalterada", await seller.locator("#constancia-interna").innerText(), preSaleReceiptText);

  // ADMIN inspects mixed Kardex (Carga inicial, Entrada de mercaderia with long supplier + two warehouse actors, 2 sales)
  await admin.goto(base + `/inventario/productos/${fixture.products.entry1.id}/movimientos/`);
  const kardexText = await admin.locator("table").innerText();
  check(
    "admin_kardex_mixto_completo",
    kardexText.includes("Carga inicial — Lote L02-INI-EARLY") &&
      kardexText.includes("Entrada de mercadería — Lote POST-EARLY") &&
      kardexText.includes("Lucia Almacen06") &&
      kardexText.includes("Pedro Almacen06") &&
      kardexText.includes("Venta V-00000001") &&
      kardexText.includes("Venta V-00000002"),
    true
  );
  check(
    "admin_kardex_sin_overflow",
    await admin.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth),
    true
  );
  await shot(admin, "04-kardex-mixto-y-rn28.png");

  // Constancia as ADMIN keeps no-action-buttons & original quantities
  await admin.goto(entry1ConstanciaUrl);
  check("admin_constancia_sin_boton_entrada_ni_carga", await admin.locator("a", { hasText: /Registrar entrada posterior|Cargar otro producto/ }).count(), 0);

  // 10. Logout + Back button + @never_cache on /inventario/entrada/
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

