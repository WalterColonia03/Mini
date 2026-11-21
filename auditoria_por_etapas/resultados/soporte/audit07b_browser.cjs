const fs = require("node:fs");
const path = require("node:path");
const assert = require("node:assert/strict");
const { chromium } = require(
  "C:/Users/walte/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright-core"
);

const cfgPath = process.argv[2];
const cfg = JSON.parse(fs.readFileSync(cfgPath, "utf8"));
const base = cfg.baseUrl;
const checks = [];

function record(name, actual, expected) {
  const ok = expected === undefined ? Boolean(actual) : actual === expected;
  checks.push({ name, ok, actual, expected });
  if (!ok) {
    throw new Error(`Check failed [${name}]: actual=${JSON.stringify(actual)} expected=${JSON.stringify(expected)}`);
  }
}

async function loginRole(browser, roleKey, viewport) {
  const context = await browser.newContext({ viewport, locale: "es-PE" });
  const page = await context.newPage();
  const errors = [];
  page.on("pageerror", (e) => errors.push(`pageerror: ${e.message}`));
  page.on("console", (msg) => {
    if (msg.type() === "error") errors.push(`console.error: ${msg.text()}`);
  });
  page.on("response", (resp) => {
    if (resp.status() >= 500) errors.push(`HTTP ${resp.status()} ${resp.url()}`);
  });

  await page.goto(base + "/");
  await page.locator('[name="email"]').fill(cfg.accounts[roleKey].email);
  await page.locator('[name="password"]').fill(cfg.accounts[roleKey].password);
  await Promise.all([
    page.waitForURL((u) => !u.pathname.endsWith("/") || u.pathname === "/inicio/"),
    page.locator('button[type="submit"]').click(),
  ]);
  return { context, page, errors };
}

async function layoutMetrics(page) {
  return await page.evaluate(() => ({
    innerWidth: window.innerWidth,
    docScrollWidth: document.documentElement.scrollWidth,
    bodyScrollWidth: document.body.scrollWidth,
    horizontalOverflowPx: Math.max(0, document.documentElement.scrollWidth - window.innerWidth),
  }));
}

async function runEmptyPhase(browser) {
  const { context, page, errors } = await loginRole(browser, "warehouse", { width: 1366, height: 900 });
  await page.goto(base + "/inicio/");
  const dashText = await page.locator("main").innerText();
  record("empty_dashboard_zero_alerts", dashText.includes("0"), true);

  await page.goto(base + "/inventario/stock/");
  const stockH1 = await page.locator("h1").innerText();
  record("empty_stock_h1", stockH1.trim(), "Stock e inventario");
  const stockBody = await page.locator("main").innerText();
  record("empty_stock_shows_zero_alerts_banner", stockBody.includes("Sin alertas de stock bajo ni de vencimiento."), true);
  record("empty_stock_shows_empty_row", stockBody.includes("No hay productos registrados en el catálogo todavía."), true);
  await page.screenshot({ path: path.join(cfg.screenshotsDir, "empty-stock-desktop.png"), fullPage: true });

  await page.goto(base + "/productos/vencimientos/");
  const expH1 = await page.locator("h1").innerText();
  record("empty_exp_h1", expH1.trim(), "Vencimientos de lotes");
  const expAlert = await page.locator(".alert").first().innerText();
  record(
    "empty_exp_message",
    expAlert.includes("No hay lotes con unidades disponibles que estén vencidos o venzan en los próximos 30 días."),
    true
  );
  await page.screenshot({ path: path.join(cfg.screenshotsDir, "empty-expirations-desktop.png"), fullPage: true });
  record("empty_zero_browser_errors", errors.length, 0);
  await context.close();
}

async function runFullPhase(browser) {
  const collected = {};

  // 1. Anonymous redirects
  const anonCtx = await browser.newContext({ viewport: { width: 1366, height: 900 }, locale: "es-PE" });
  const anonPage = await anonCtx.newPage();
  for (const route of ["/inventario/stock/", "/productos/vencimientos/"]) {
    await anonPage.goto(base + route);
    record(`anon_redirect_${route}`, anonPage.url(), `${base}/?next=${route}`);
  }
  await anonCtx.close();

  // 2. VENDEDOR: 403, absent nav/dashboard KPIs, POS sellable contrast (15 physical vs 8 sellable)
  const seller = await loginRole(browser, "seller", { width: 1366, height: 900 });
  await seller.page.goto(base + "/inicio/");
  const sellerNavHrefs = await seller.page.locator("nav a").evaluateAll((els) => els.map((e) => e.getAttribute("href")));
  record("seller_nav_excludes_stock", sellerNavHrefs.includes("/inventario/stock/"), false);
  record("seller_nav_excludes_expirations", sellerNavHrefs.includes("/productos/vencimientos/"), false);
  record("seller_dashboard_no_resumen_general", (await seller.page.locator("main").innerText()).includes("Resumen general"), false);

  for (const route of ["/inventario/stock/", "/productos/vencimientos/"]) {
    const resp = await seller.page.goto(base + route);
    record(`seller_403_${route}`, resp.status(), 403);
  }
  const expected403Errors = seller.errors.filter((e) => e.includes("403 (Forbidden)"));
  const unexpectedSellerErrors = seller.errors.filter((e) => !e.includes("403 (Forbidden)"));
  record("seller_expected_403_console_count", expected403Errors.length, 2);

  await seller.page.goto(base + "/ventas/");
  await seller.page.locator('[name="query"]').fill("Yogurt Vencimiento Mixto");
  await seller.page.locator('.search-form button[type="submit"]').click();
  const posText = await seller.page.locator(".sales-search-panel").innerText();
  record("pos_shows_yogurt_sellable_8_not_15", posText.includes("8") && !posText.includes("15"), true);

  for (const hiddenName of ["Producto E Vence Hoy", "Gaseosa Suspendida Cat"]) {
    await seller.page.locator('[name="query"]').fill(hiddenName);
    await seller.page.locator('.search-form button[type="submit"]').click();
    const resTxt = await seller.page.locator(".sales-search-panel").innerText();
    record(`pos_excludes_${hiddenName}`, resTxt.includes("No se encontraron productos"), true);
  }
  record("seller_zero_unexpected_browser_errors", unexpectedSellerErrors.length, 0);
  await seller.context.close();

  // 3. ADMIN: category deactivate & reactivate with individually suspended product + UI coherence + parity
  const admin = await loginRole(browser, "admin", { width: 1366, height: 900 });
  await admin.page.goto(base + "/productos/categorias/");
  // Toggle Bebidas OFF then ON via confirmation screen
  const bebRowOff = admin.page.locator("tbody tr", { hasText: "Bebidas" });
  await bebRowOff.locator('button[type="submit"]').click();
  await admin.page.waitForURL((u) => u.pathname.includes("/estado/confirmar/"));
  await admin.page.locator('button[type="submit"]').click();
  await admin.page.waitForURL((u) => u.pathname === "/productos/categorias/");

  const bebRowOn = admin.page.locator("tbody tr", { hasText: "Bebidas" });
  await bebRowOn.locator('button[type="submit"]').click();
  await admin.page.waitForURL((u) => u.pathname.includes("/estado/confirmar/"));
  await admin.page.locator('button[type="submit"]').click();
  await admin.page.waitForURL((u) => u.pathname === "/productos/categorias/");

  await admin.page.goto(base + "/inventario/stock/");
  const adminStockText = await admin.page.locator("main").innerText();
  record("admin_stock_new_heading_13B", adminStockText.includes("Stock vigente en el mínimo o por debajo"), true);
  record("admin_stock_agua_reactivated_alert", adminStockText.includes("Agua Cat Activa"), true);
  const gaseosaRow = admin.page.locator("table.stock-overview-table tbody tr", { hasText: "Gaseosa Suspendida Cat" });
  record("gaseosa_stays_inactivo_after_cat_reactivate", (await gaseosaRow.innerText()).includes("Inactivo"), true);
  const lowSectionText = await admin.page.locator(".stock-alert-panel", { hasText: "Stock vigente en el mínimo o por debajo" }).innerText();
  record("low_section_excludes_gaseosa_susp", !lowSectionText.includes("Gaseosa Suspendida Cat"), true);
  record("low_section_excludes_prod_e", !lowSectionText.includes("Producto E Vence Hoy"), true);
  record("low_section_includes_yogurt_mixto", lowSectionText.includes("Yogurt Vencimiento Mixto"), true);
  record("low_section_includes_sal_min_zero", lowSectionText.includes("Sal Min Cero"), true);
  await admin.page.screenshot({ path: path.join(cfg.screenshotsDir, "stock-admin-desktop.png"), fullPage: true });

  await admin.page.goto(base + "/productos/");
  const catProdERow = admin.page.locator("table.catalog-products tbody tr", { hasText: "Producto E Vence Hoy" });
  record("catalog_H13_02_no_low_badge_prod_e", !(await catProdERow.innerText()).includes("Stock bajo"), true);
  const catGasRow = admin.page.locator("table.catalog-products tbody tr", { hasText: "Gaseosa Suspendida Cat" });
  record("catalog_H13_02_no_low_badge_gaseosa", !(await catGasRow.innerText()).includes("Stock bajo"), true);
  const catMixRow = admin.page.locator("table.catalog-products tbody tr", { hasText: "Yogurt Vencimiento Mixto" });
  record("catalog_yogurt_sellable_8_low", (await catMixRow.innerText()).includes("Stock bajo"), true);
  await admin.page.screenshot({ path: path.join(cfg.screenshotsDir, "catalog-admin-desktop.png"), fullPage: true });

  await admin.page.goto(base + "/inicio/");
  const dashTextBeforeWriteoff = await admin.page.locator("main").innerText();
  collected.adminDashBefore = dashTextBeforeWriteoff;

  // 4. ALMACENERO desktop + filters + DEC-07 check + Dar de baja sync + mobile 390x844 + Back cache
  const wh = await loginRole(browser, "warehouse", { width: 1366, height: 900 });
  await wh.page.goto(base + "/productos/vencimientos/");
  const whExpHeader = await wh.page.locator("h1").innerText();
  record("wh_exp_topbar_h1", whExpHeader.trim(), "Vencimientos de lotes");

  // Filter ?dias=7 via form input: verify DEC-07 status (still mixed single table!)
  await wh.page.locator('input[name="dias"]').fill("7");
  await Promise.all([
    wh.page.waitForURL((u) => u.searchParams.get("dias") === "7"),
    wh.page.locator('form button[type="submit"]').click(),
  ]);
  const dias7Html = await wh.page.content();
  const dias7Rows = await wh.page.locator("table.expirations-table tbody tr").allInnerTexts();
  collected.dias7RowCount = dias7Rows.length;
  collected.dias7Rows = dias7Rows;
  collected.dec07SeparatedInDom = /Próximos a vencer/i.test(dias7Html) && /<h[23][^>]*>\s*Vencidos\s*<\/h[23]>/i.test(dias7Html);
  record("dec07_observed_still_unseparated_mixed_table", collected.dec07SeparatedInDom, false);
  await wh.page.screenshot({ path: path.join(cfg.screenshotsDir, "expirations-wh-dias7-mixed.png"), fullPage: true });

  // Boundary filters: 1, 30, 31, 0, abc
  await wh.page.goto(base + "/productos/vencimientos/?dias=30");
  const rows30 = await wh.page.locator("table.expirations-table tbody tr").allInnerTexts();
  record("dias30_excludes_31d_and_zero_lot", rows30.every((r) => !r.includes("QF-31D") && !r.includes("AR-INIT")), true);

  await wh.page.goto(base + "/productos/vencimientos/?dias=31");
  const rows31 = await wh.page.locator("table.expirations-table tbody tr").allInnerTexts();
  record("dias31_includes_31d", rows31.some((r) => r.includes("QF-31D")), true);

  await wh.page.goto(base + "/productos/vencimientos/?dias=0");
  record("dias0_error_msg", (await wh.page.locator(".alert").first().innerText()).includes("entre 1 y 3650"), true);

  await wh.page.goto(base + "/productos/vencimientos/?dias=abc");
  record("dias_abc_error_msg", (await wh.page.locator(".alert").first().innerText()).includes("número entero válido"), true);

  // Verify PhysicalAdjustment expired lot (AR-ADJ-HOY) shows "—" supplier and "Dar de baja" button
  await wh.page.goto(base + "/productos/vencimientos/?dias=30");
  const adjRow = wh.page.locator("table.expirations-table tbody tr", { hasText: "AR-ADJ-HOY" });
  record("adj_lot_shows_dash_supplier_and_writeoff", (await adjRow.innerText()).includes("—") && (await adjRow.innerText()).includes("Dar de baja"), true);

  // Click Dar de baja on YT-EXP (7 units) -> VENCIMIENTO -> redirect /inventario/bajas/<uuid>/
  const ytExpRow = wh.page.locator("table.expirations-table tbody tr", { hasText: "YT-EXP" });
  await Promise.all([
    wh.page.waitForURL((u) => u.pathname === "/inventario/bajas/nueva/"),
    ytExpRow.locator("a", { hasText: "Dar de baja" }).click(),
  ]);
  await wh.page.locator('[name="quantity"]').fill("7");
  await wh.page.locator('[name="reason"]').selectOption("VENCIMIENTO");
  await wh.page.locator('[name="notes"]').fill("Baja completa audit07b");
  await Promise.all([
    wh.page.waitForURL((u) => /^\/inventario\/bajas\/[0-9a-f-]+\/$/.test(u.pathname)),
    wh.page.locator('button[type="submit"]').click(),
  ]);
  record("writeoff_redirects_to_receipt_14I", /^\/inventario\/bajas\/[0-9a-f-]+\/$/.test(new URL(wh.page.url()).pathname), true);

  // Check cross-view synchronization in WH & ADMIN
  await wh.page.goto(base + "/productos/vencimientos/");
  const rowsAfterWo = await wh.page.locator("table.expirations-table tbody tr").allInnerTexts();
  record("yt_exp_removed_from_expirations_after_full_writeoff", rowsAfterWo.every((r) => !r.includes("YT-EXP")), true);
  await wh.page.goto(base + "/inventario/stock/");
  const whMixRow = wh.page.locator("table.stock-overview-table tbody tr", { hasText: "Yogurt Vencimiento Mixto" });
  const whMixText = await whMixRow.innerText();
  record("wh_stock_yogurt_physical_now_equals_8", whMixText.includes("8") && !whMixText.includes("15"), true);

  await admin.page.goto(base + "/inventario/stock/");
  const adMixRow = admin.page.locator("table.stock-overview-table tbody tr", { hasText: "Yogurt Vencimiento Mixto" });
  record("admin_stock_synced_8", (await adMixRow.innerText()).includes("8") && !(await adMixRow.innerText()).includes("15"), true);

  // Mobile 390x844 check
  const mobileCtx = await browser.newContext({ viewport: { width: 390, height: 844 }, locale: "es-PE" });
  const mPage = await mobileCtx.newPage();
  const mobileErrors = [];
  mPage.on("pageerror", (e) => mobileErrors.push(e.message));
  await mPage.goto(base + "/");
  await mPage.locator('[name="email"]').fill(cfg.accounts.warehouse.email);
  await mPage.locator('[name="password"]').fill(cfg.accounts.warehouse.password);
  await Promise.all([mPage.waitForURL((u) => u.pathname === "/inicio/"), mPage.locator('button[type="submit"]').click()]);

  await mPage.goto(base + "/inventario/stock/");
  const mStockMetrics = await layoutMetrics(mPage);
  record("mobile_stock_no_body_overflow", mStockMetrics.horizontalOverflowPx, 0);
  await mPage.screenshot({ path: path.join(cfg.screenshotsDir, "stock-mobile.png"), fullPage: true });

  await mPage.goto(base + "/productos/vencimientos/");
  const mExpMetrics = await layoutMetrics(mPage);
  record("mobile_exp_no_body_overflow", mExpMetrics.horizontalOverflowPx, 0);
  await mPage.screenshot({ path: path.join(cfg.screenshotsDir, "expirations-mobile.png"), fullPage: true });
  record("mobile_zero_errors", mobileErrors.length, 0);
  await mobileCtx.close();

  // Logout (GET confirm + POST form submit) & Back button / @never_cache check
  const stockResp = await wh.page.goto(base + "/inventario/stock/");
  record("wh_stock_never_cache_header", (stockResp.headers()["cache-control"] || "").includes("no-store"), true);
  const expResp = await wh.page.goto(base + "/productos/vencimientos/");
  record("wh_exp_never_cache_header", (expResp.headers()["cache-control"] || "").includes("no-store"), true);
  await wh.page.goto(base + "/salir/");
  await Promise.all([
    wh.page.waitForURL((u) => u.pathname === "/"),
    wh.page.locator('main form button[type="submit"]').click(),
  ]);
  await wh.page.goBack();
  await wh.page.waitForLoadState("networkidle");
  record("post_logout_protected_stock_redirects", (await wh.page.goto(base + "/inventario/stock/")).url().includes("/?next=/inventario/stock/"), true);
  record("wh_zero_browser_errors", wh.errors.length, 0);
  record("admin_zero_browser_errors", admin.errors.length, 0);

  await wh.context.close();
  await admin.context.close();
  collected.mobileStockMetrics = mStockMetrics;
  collected.mobileExpMetrics = mExpMetrics;
  return collected;
}

(async () => {
  const browser = await chromium.launch({
    executablePath: "C:/Program Files/Google/Chrome/Application/chrome.exe",
    headless: true,
    args: ["--no-sandbox"],
  });
  let details = {};
  try {
    if (cfg.phase === "empty") {
      await runEmptyPhase(browser);
    } else {
      details = await runFullPhase(browser);
    }
  } finally {
    await browser.close();
  }
  fs.writeFileSync(cfg.resultPath, JSON.stringify({ phase: cfg.phase, checks, details }, null, 2), "utf8");
  console.log(`PHASE_${cfg.phase.toUpperCase()}_OK checks=${checks.length}`);
})();
