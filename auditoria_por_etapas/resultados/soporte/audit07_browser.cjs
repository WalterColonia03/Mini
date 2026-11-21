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

const out = process.env.AUDIT07_OUT;
const run = process.env.AUDIT07_RUN_DIR;
const base = "http://127.0.0.1:" + process.env.AUDIT07_PORT;
const accounts = JSON.parse(fs.readFileSync(path.join(run, ".credentials.json"), "utf8"));
const fixture = JSON.parse(fs.readFileSync(path.join(out, "fixture.json"), "utf8"));

const report = {
  checks: [],
  layout_metrics: {},
  page_errors: [],
  screenshots: [],
  input: "Chrome 1366x900 Stage 07 audit (stock_overview, product_expirations, dashboard parity, POS contrast, writeoff sync)",
};

function check(id, actual, expected) {
  assert.deepEqual(actual, expected, id);
  report.checks.push(id);
}

function state() {
  return JSON.parse(
    execFileSync(process.env.AUDIT07_PYTHON, [path.join(__dirname, "audit07_run.py"), "snapshot"], {
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

async function runAudit(browser) {
  const initialOrm = state();

  // 1. Cryptographic proof & anonymous redirects
  const probeCtx = await browser.newContext({ locale: "es-PE", viewport: { width: 1366, height: 900 } });
  const probe = await probeCtx.newPage();
  const nonce = crypto.randomBytes(32).toString("hex");
  const probeRes = await probe.request.get(base, { headers: { "X-Audit07-Challenge": nonce } });
  const expectedProof = crypto
    .createHmac("sha256", fs.readFileSync(path.join(run, ".django-key")))
    .update(nonce)
    .digest("hex");
  check("aislamiento_proof", probeRes.headers()["x-audit07-proof"], expectedProof);
  check("aislamiento_run", probeRes.headers()["x-audit07-run"], path.basename(run));

  for (const [tag, url] of [
    ["stock_overview", "/inventario/stock/"],
    ["expirations", "/productos/vencimientos/"],
    ["dashboard", "/inicio/"],
  ]) {
    const r = await probe.request.get(base + url, { maxRedirects: 0 });
    check(`anonimo_${tag}_302`, r.status(), 302);
    check(`anonimo_${tag}_next`, r.headers()["location"], `/?next=${url}`);
  }
  await probeCtx.close();

  // 2. VENDEDOR role boundaries & POS contrast
  const sellerSession = await loginContext(browser, "seller");
  const seller = sellerSession.page;
  for (const href of ["/inventario/stock/", "/productos/vencimientos/", "/productos/"]) {
    check(`vendedor_sin_nav_${href}`, await seller.locator(`#sidebar-navigation a[href="${href}"]`).count(), 0);
    const resp = await seller.request.get(base + href, { maxRedirects: 0 });
    check(`vendedor_${href}_403`, resp.status(), 403);
  }
  check("vendedor_inicio_sin_resumen_general", await seller.locator("#summary-title").count(), 0);

  await seller.goto(base + "/ventas/");
  await seller.locator("[name=query]").fill("Leche Mezcla");
  await seller.getByRole("button", { name: "Buscar", exact: true }).click();
  const lechePosRow = seller.locator(".sales-search-panel tbody tr", { hasText: fixture.products.exp_mix.name });
  check("pos_muestra_vendible_10_y_no_fisico_17", (await lechePosRow.innerText()).includes("10"), true);
  check("pos_no_muestra_fisico_17", (await lechePosRow.innerText()).includes("17"), false);

  for (const blocked of ["Conserva Solo", "Galletas Categoria", "Jugo Producto"]) {
    await seller.locator("[name=query]").fill(blocked);
    await seller.getByRole("button", { name: "Buscar", exact: true }).click();
    const posTxt = await seller.locator(".sales-search-panel").innerText();
    check(`pos_excluye_${blocked}`, posTxt.includes("No se encontraron productos con existencias vendibles."), true);
  }
  await sellerSession.ctx.close();

  // 3. ALMACENERO dashboard -> stock_overview -> product_expirations -> writeoff
  const whSession = await loginContext(browser, "warehouse");
  const wh = whSession.page;

  const whDashSummary = await wh.locator("section.panel").innerText();
  check("wh_inicio_muestra_resumen_sin_ventas", whDashSummary.includes("Resumen general") && !whDashSummary.includes("Ventas de hoy"), true);
  check("wh_inicio_low_stock_3", await wh.locator("dl.summary-list > div").filter({ hasText: "Productos con stock bajo" }).locator("dd").innerText(), "3");
  check("wh_inicio_expiring_7", await wh.locator("dl.summary-list > div").filter({ hasText: "Lotes por vencer" }).locator("dd").innerText(), "7");
  check("wh_inicio_expired_4", await wh.locator("dl.summary-list > div").filter({ hasText: "Lotes vencidos con stock" }).locator("dd").innerText(), "4");
  await shot(wh, "01-dashboard-almacenero.png");

  await wh.getByRole("link", { name: "Ver inventario y alertas", exact: true }).first().click();
  await wh.waitForURL(base + "/inventario/stock/");

  const stockMetrics = await wh.evaluate(() => {
    const docScrollWidth = document.documentElement.scrollWidth;
    const windowInnerWidth = window.innerWidth;
    const wrap = document.querySelector(".table-wrap");
    const panels = Array.from(document.querySelectorAll(".stock-alert-panel")).map((p) => {
      const r = p.getBoundingClientRect();
      return { right: Math.round(r.right), fits: r.right <= windowInnerWidth + 1, clientW: p.clientWidth, scrollW: p.scrollWidth };
    });
    const statusCells = Array.from(document.querySelectorAll(".stock-overview-table td:nth-child(6)")).map((td) => ({
      text: td.textContent.trim(),
      overflowWrap: getComputedStyle(td).overflowWrap,
    }));
    return {
      docScrollWidth,
      windowInnerWidth,
      docOk: docScrollWidth <= windowInnerWidth,
      wrapOk: wrap.scrollWidth <= wrap.clientWidth,
      wrapScrollW: wrap.scrollWidth,
      wrapClientW: wrap.clientWidth,
      panelsAllFit: panels.every((x) => x.fits),
      panels,
      statusNormalWrap: statusCells.every((c) => c.overflowWrap === "normal"),
    };
  });
  report.layout_metrics.stock_overview = stockMetrics;
  check("stock_overview_sin_overflow_doc_ni_paneles", [stockMetrics.docOk, stockMetrics.wrapOk, stockMetrics.panelsAllFit, stockMetrics.statusNormalWrap], [true, true, true, true]);

  const stockMain = await wh.locator("main").innerText();
  check("stock_banner_lote_normalizado_mayus", stockMain.includes("Lote MIX-VENCE-HOY") && !stockMain.includes("mix-vence-hoy"), true);
  check("stock_banner_incluye_etiqueta_inactivo", stockMain.includes("Jugo Producto Deshabilitado (Inactivo)"), true);
  check("stock_banner_incluye_etiqueta_cat_off", stockMain.includes("Galletas Categoria Suspendida (Categoría desactivada)"), true);

  const lowStockPanelText = await wh.locator(".stock-alert-panel").filter({ hasText: "Stock bajo el mínimo" }).innerText();
  check("stock_bajo_excluye_cat_off_e_incluye_3", !lowStockPanelText.includes("Galletas Categoria Suspendida") && lowStockPanelText.includes("(3 productos)") && lowStockPanelText.includes("Leche Mezcla Vencimientos 1L"), true);

  const catOffRowHtml = await wh.locator(".stock-overview-table tbody tr", { hasText: "Galletas Categoria Suspendida" }).innerHTML();
  check("stock_fila_cat_off_sin_resaltado_rojo", !catOffRowHtml.includes("#c0392b") && catOffRowHtml.includes("Categoría desactivada"), true);

  check("wh_stock_footer_acciones", [
    await wh.locator("main").getByRole("link", { name: "+ Registrar existencias iniciales", exact: true }).count(),
    await wh.locator("main").getByRole("link", { name: "+ Entrada de mercadería", exact: true }).count(),
    await wh.locator("main").getByRole("link", { name: "Registrar merma", exact: true }).count(),
    await wh.locator("main").getByRole("link", { name: "Ajuste físico", exact: true }).count(),
  ], [1, 1, 1, 0]);
  await shot(wh, "02-stock-overview-almacenero.png");

  // Navigate to Vencimientos de lotes
  await wh.locator('#sidebar-navigation a[href="/productos/vencimientos/"]').click();
  await wh.waitForURL(base + "/productos/vencimientos/");

  const expMetrics = await wh.evaluate(() => {
    const docScrollWidth = document.documentElement.scrollWidth;
    const windowInnerWidth = window.innerWidth;
    const wrap = document.querySelector(".table-responsive");
    const wrapRect = wrap.getBoundingClientRect();
    const ths = Array.from(document.querySelectorAll(".expirations-table th")).map((th) => {
      const r = th.getBoundingClientRect();
      return { text: th.textContent.trim(), right: Math.round(r.right), clipped: r.right > wrapRect.right + 1 };
    });
    const rowsOrder = Array.from(document.querySelectorAll(".expirations-table tbody tr td.exp-col-lot")).map((td) => td.textContent.trim());
    return {
      docScrollWidth,
      windowInnerWidth,
      docOk: docScrollWidth <= windowInnerWidth,
      tableWrapScrollWidth: wrap.scrollWidth,
      tableWrapClientWidth: wrap.clientWidth,
      wrapOk: wrap.scrollWidth <= wrap.clientWidth,
      thCount: ths.length,
      allHeadersVisible: ths.every((t) => !t.clipped),
      ths,
      rowsOrder,
    };
  });
  report.layout_metrics.expirations = expMetrics;
  check("expirations_8_columnas_sin_overflow_ni_recorte", [expMetrics.docOk, expMetrics.wrapOk, expMetrics.thCount, expMetrics.allHeadersVisible], [true, true, 8, true]);

  const idxZ = expMetrics.rowsOrder.indexOf("MIX-TIE-Z-FIRST");
  const idxA = expMetrics.rowsOrder.indexOf("MIX-TIE-A-SECOND");
  check("expirations_orden_tie_determinista", idxZ >= 0 && idxA > idxZ, true);
  check("expirations_excluye_lote_cero_y_dia31", !expMetrics.rowsOrder.includes("MIX-ZERO-EXP") && !expMetrics.rowsOrder.includes("D31-OUT"), true);

  const expMainText = await wh.locator("main").innerText();
  check("expirations_resumen_4_vencidos_7_proximos", expMainText.includes("Total en pantalla: 11 lotes (4 vencidos bloqueados para venta · 7 próximos dentro de 30 días)"), true);
  check("expirations_textos_exactos", expMainText.includes("Vence hoy") && expMainText.includes("Venció hace 2 días") && expMainText.includes("Bloqueado para venta") && expMainText.includes("Producto inactivo") && expMainText.includes("Categoría desactivada"), true);
  await shot(wh, "03-vencimientos-default-30d.png");

  // Filter variations in browser
  await wh.locator("#expiration-days").fill("7");
  await wh.getByRole("button", { name: "Filtrar", exact: true }).click();
  await wh.waitForURL(base + "/productos/vencimientos/?dias=7");
  check("expirations_filtro_7_excluye_d30", await wh.locator(".expirations-table tbody tr").count(), 10);

  await wh.goto(base + "/productos/vencimientos/?dias=1");
  check("expirations_filtro_1_incluye_manana", await wh.locator(".expirations-table tbody tr").count(), 6);

  await wh.goto(base + "/productos/vencimientos/?dias=31");
  check("expirations_filtro_31_incluye_d31", await wh.locator(".expirations-table tbody tr").count(), 12);

  await wh.goto(base + "/productos/vencimientos/?dias=0");
  check("expirations_dias_0_fallback_30_con_alerta", (await wh.locator(".flash-stack .alert-error").innerText()).includes("entre 1 y 3650") && await wh.locator(".expirations-table tbody tr").count() === 11, true);
  await shot(wh, "04-vencimientos-error-filtro.png");

  await wh.goto(base + "/productos/vencimientos/?dias=abc");
  check("expirations_dias_abc_fallback_30_con_alerta", (await wh.locator(".flash-stack .alert-error").innerText()).includes("número entero válido") && await wh.locator(".expirations-table tbody tr").count() === 11, true);

  // Direct action: "Dar de baja" from ONLY-VENC-HOY row -> write off 8 expired units
  await wh.goto(base + "/productos/vencimientos/");
  const conserveRow = wh.locator(".expirations-table tbody tr", { hasText: "ONLY-VENC-HOY" });
  await conserveRow.getByRole("link", { name: "Dar de baja", exact: true }).click();
  await wh.waitForURL(/\/inventario\/bajas\/nueva\/\?lote=.+/);
  await wh.locator("[name=quantity]").fill("8");
  await wh.locator("[name=reason]").selectOption("VENCIMIENTO");
  await wh.getByRole("button", { name: "Confirmar baja", exact: true }).click();
  await wh.waitForURL(base + "/inventario/bajas/nueva/");

  // Verify synchronization across expirations, stock_overview, dashboard
  await wh.goto(base + "/productos/vencimientos/");
  check("post_baja_expirations_baja_a_3_vencidos", (await wh.locator("main").innerText()).includes("Total en pantalla: 10 lotes (3 vencidos bloqueados para venta · 7 próximos dentro de 30 días)"), true);
  await wh.goto(base + "/inventario/stock/");
  const afterStockText = await wh.locator("main").innerText();
  check("post_baja_stock_sin_only_venc_hoy_y_vencidos_3", !afterStockText.includes("ONLY-VENC-HOY") && afterStockText.includes("Lotes VENCIDOS con unidades registradas (3)"), true);

  // 4. ADMIN dashboard & stock_overview & product_list contrast + POST 405 + logout
  const adminSession = await loginContext(browser, "admin");
  const admin = adminSession.page;
  check("admin_inicio_metricas_ventas_y_stock", [
    await admin.locator("dl.summary-list > div").filter({ hasText: "Ventas de hoy" }).locator("dd").innerText(),
    await admin.locator("dl.summary-list > div").filter({ hasText: "Total vendido hoy" }).locator("dd").innerText(),
    await admin.locator("dl.summary-list > div").filter({ hasText: "Descuentos otorgados hoy" }).locator("dd").innerText(),
    await admin.locator("dl.summary-list > div").filter({ hasText: "Turnos de caja abiertos" }).locator("dd").innerText(),
    await admin.locator("dl.summary-list > div").filter({ hasText: "Productos con stock bajo" }).locator("dd").innerText(),
    await admin.locator("dl.summary-list > div").filter({ hasText: "Lotes por vencer" }).locator("dd").innerText(),
    await admin.locator("dl.summary-list > div").filter({ hasText: "Lotes vencidos con stock" }).locator("dd").innerText(),
  ], ["1", "S/ 3,50", "S/ 0,50", "1", "3", "7", "3"]);
  await shot(admin, "05-dashboard-admin.png");

  await admin.goto(base + "/inventario/stock/");
  check("admin_stock_footer_acciones", [
    await admin.locator("main").getByRole("link", { name: "Ajuste físico", exact: true }).count(),
    await admin.locator("main").getByRole("link", { name: "Registrar merma", exact: true }).count(),
    await admin.locator("main").getByRole("link", { name: "+ Registrar existencias iniciales", exact: true }).count(),
  ], [1, 1, 0]);
  await shot(admin, "06-stock-overview-admin.png");

  await admin.goto(base + "/productos/");
  const catMixRow = await admin.locator(".catalog-products tbody tr", { hasText: fixture.products.exp_mix.name }).innerText();
  const catExpiredRow = await admin.locator(".catalog-products tbody tr", { hasText: fixture.products.all_expired.name }).innerText();
  check("catalogo_contraste_mix_y_vencida", catMixRow.includes("10") && catMixRow.includes("Stock bajo") && catExpiredRow.includes("Sin stock vigente"), true);

  // POST 405 on read-only endpoints + @never_cache headers + logout + back
  await admin.goto(base + "/salir/");
  const adminCookies = await adminSession.ctx.cookies();
  const adminCsrf = adminCookies.find((c) => c.name === "audit07_csrftoken").value;
  for (const url of ["/inventario/stock/", "/productos/vencimientos/"]) {
    const postRes = await admin.request.post(base + url, { form: { csrfmiddlewaretoken: adminCsrf }, maxRedirects: 0 });
    check(`admin_post_${url}_405`, postRes.status(), 405);
    const getRes = await admin.request.get(base + url, { maxRedirects: 0 });
    check(`never_cache_${url}`, (getRes.headers()["cache-control"] || "").includes("no-store"), true);
  }

  // Logout via WH and test Back button
  await wh.locator("a.sidebar-logout").click();
  await wh.waitForURL(base + "/salir/");
  await wh.getByRole("button", { name: "Cerrar sesión", exact: true }).click();
  await wh.waitForURL(base + "/");
  await wh.goBack();
  await wh.waitForLoadState("networkidle");
  check("logout_back_bloqueado", wh.url().startsWith(base + "/?next=") || wh.url() === base + "/" || wh.url().includes("/salir/"), true);
  for (const url of ["/inventario/stock/", "/productos/vencimientos/"]) {
    await wh.goto(base + url);
    check(`post_logout_${url}_redirige_login`, wh.url(), `${base}/?next=${url}`);
  }

  // Confirm DB unchanged except intentional writeoff on p_all_expired
  const finalOrm = state();
  check("solo_1_writeoff_registrado", finalOrm.writeoffs.length - initialOrm.writeoffs.length, 1);
  check("cero_page_errors", report.page_errors.length, 0);

  await whSession.ctx.close();
  await adminSession.ctx.close();
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
