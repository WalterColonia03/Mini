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

const out = process.env.AUDIT09_OUT;
const run = process.env.AUDIT09_RUN_DIR;
const base = "http://127.0.0.1:" + process.env.AUDIT09_PORT;
const accounts = JSON.parse(fs.readFileSync(path.join(run, ".credentials.json"), "utf8"));
const fixture = JSON.parse(fs.readFileSync(path.join(out, "fixture.json"), "utf8"));

const report = {
  checks: [],
  layout_metrics: {},
  computed_styles: {},
  page_errors: [],
  screenshots: [],
  input: "Chrome 1366x900 Stage 09 audit (caja única, apertura, cierre, arqueo, borradores, venta con descuento, pestañas paralelas, historial)",
};

function check(id, actual, expected) {
  assert.deepEqual(actual, expected, id);
  report.checks.push(id);
}

function state() {
  return JSON.parse(
    execFileSync(process.env.AUDIT09_PYTHON, [path.join(__dirname, "audit09_run.py"), "snapshot"], {
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

async function csrfFromContext(ctx) {
  const cookies = await ctx.cookies();
  const c = cookies.find((x) => x.name === "audit09_csrftoken");
  return c ? c.value : "";
}

async function runAudit(browser) {
  const initialOrm = state();
  check("estado_inicial_solo_caja01_sin_turnos", [initialOrm.registers.length, initialOrm.shifts.length], [1, 0]);

  // 1. Cryptographic ProofMiddleware + anonymous redirects across all /caja/ URLs
  const probeCtx = await browser.newContext({ locale: "es-PE", viewport: { width: 1366, height: 900 } });
  const probe = await probeCtx.newPage();
  const nonce = crypto.randomBytes(32).toString("hex");
  const probeRes = await probe.request.get(base, { headers: { "X-Audit09-Challenge": nonce } });
  const expectedProof = crypto
    .createHmac("sha256", fs.readFileSync(path.join(run, ".django-key")))
    .update(nonce)
    .digest("hex");
  check("aislamiento_proof", probeRes.headers()["x-audit09-proof"], expectedProof);
  check("aislamiento_run", probeRes.headers()["x-audit09-run"], path.basename(run));

  const dummyUuid = "00000000-0000-4000-8000-000000000001";
  for (const [tag, url] of [
    ["cash_open", "/caja/abrir/"],
    ["cash_close", "/caja/cerrar/"],
    ["cash_history", "/caja/turnos/"],
    ["cash_opened", `/caja/turnos/${dummyUuid}/abierto/`],
    ["cash_closed", `/caja/turnos/${dummyUuid}/cerrado/`],
  ]) {
    const r = await probe.request.get(base + url, { maxRedirects: 0 });
    check(`anonimo_${tag}_302`, r.status(), 302);
    check(`anonimo_${tag}_next`, r.headers()["location"], `/?next=${url}`);
  }
  await probeCtx.close();

  // 2. ALMACENERO denied on all /caja/ routes and zero nav links
  const whSession = await loginContext(browser, "warehouse");
  const wh = whSession.page;
  for (const href of ["/caja/abrir/", "/caja/cerrar/", "/caja/turnos/"]) {
    check(`almacenero_sin_nav_${href}`, await wh.locator(`#sidebar-navigation a[href="${href}"]`).count(), 0);
    const resp = await wh.request.get(base + href, { maxRedirects: 0 });
    check(`almacenero_${href}_403`, resp.status(), 403);
  }
  await wh.goto(base + "/salir/");
  const whCsrf = await csrfFromContext(whSession.ctx);
  check(
    "almacenero_post_abrir_403",
    (await wh.request.post(base + "/caja/abrir/", { form: { opening_amount: "10.00", csrfmiddlewaretoken: whCsrf }, maxRedirects: 0 })).status(),
    403
  );
  check(
    "almacenero_post_cerrar_403",
    (await wh.request.post(base + "/caja/cerrar/", { form: { counted_amount: "10.00", csrfmiddlewaretoken: whCsrf }, maxRedirects: 0 })).status(),
    403
  );
  await whSession.ctx.close();

  // 3. VENDEDOR 1 invalid opening -> keyboard valid open -> logout preserves shift
  const s1Session = await loginContext(browser, "seller1");
  const s1 = s1Session.page;

  check("vendedor1_sidebar_enlaces_caja", [
    await s1.locator('#sidebar-navigation a[href="/caja/abrir/"]').count(),
    await s1.locator('#sidebar-navigation a[href="/caja/cerrar/"]').count(),
    await s1.locator('#sidebar-navigation a[href="/caja/turnos/"]').count(),
  ], [1, 1, 0]);

  await s1.locator('[data-testid="cash-open-link"]').click();
  await s1.waitForURL(base + "/caja/abrir/");

  // Empty submit -> bound validation error (FIX09-01)
  await s1.getByRole("button", { name: "Abrir turno", exact: true }).click();
  check("apertura_vacia_muestra_error", (await s1.locator(".error-list").innerText()).includes("obligatorio"), true);

  // Invalid negative & >2 decimals
  for (const bad of ["-0.01", "1.005"]) {
    await s1.locator("[name=opening_amount]").fill(bad);
    await s1.locator("[name=opening_amount]").press("Enter");
    check(`apertura_invalida_${bad}`, await s1.locator(".error-list").count() > 0 && s1.url().endsWith("/caja/abrir/"), true);
  }
  await shot(s1, "01-apertura-error-validacion.png");

  // Valid keyboard submit
  await s1.locator("[name=opening_amount]").fill("100.00");
  await s1.locator("[name=opening_amount]").press("Enter");
  await s1.waitForURL(/\/caja\/turnos\/[0-9a-f-]+\/abierto\//);
  const shift1Id = s1.url().match(/\/turnos\/([0-9a-f-]+)\/abierto\//)[1];

  const openedText = await s1.locator("main").innerText();
  check("apertura_ok_detalle", openedText.includes("CAJA-01 está abierta") && openedText.includes(fixture.accounts.seller1.display_name) && openedText.includes("S/ 100,00") && openedText.includes("Abierto"), true);
  check("apertura_ok_enlace_preparar_venta", await s1.locator('main a[href="/ventas/"]').count(), 1);
  await shot(s1, "02-turno-abierto-confirmacion.png");

  // Logout preserves open shift
  await s1.locator("a.sidebar-logout").click();
  await s1.waitForURL(base + "/salir/");
  const logoutMsg = await s1.locator("main").innerText();
  check("logout_indica_turno_conservado", logoutMsg.includes("turno abierto seguirá ligado a tu cuenta"), true);
  await s1.getByRole("button", { name: "Cerrar sesión", exact: true }).click();
  await s1.waitForURL(base + "/");

  // 4. VENDEDOR 2 blocked by single-register open shift + FIX09-02 close error visibility
  const s2Session = await loginContext(browser, "seller2");
  const s2 = s2Session.page;
  await s2.goto(base + "/caja/abrir/");
  const blockedOpenText = await s2.locator('[data-testid="cash-already-open"]').innerText();
  check("vendedor2_ve_caja_ocupada_con_nombre_s1", blockedOpenText.includes("La caja ya está en uso") && blockedOpenText.includes(fixture.accounts.seller1.display_name), true);
  check("vendedor2_sin_form_apertura", await s2.locator('[data-testid="cash-open-form"]').count(), 0);
  await shot(s2, "03-bloqueo-otro-vendedor.png");

  await s2.goto(base + "/caja/cerrar/");
  check("vendedor2_sin_turno_abierto_mensaje", (await s2.locator("main").innerText()).includes("No tienes un turno abierto"), true);
  const s2Csrf = await csrfFromContext(s2Session.ctx);
  const s2DirectClose = await s2.request.post(base + "/caja/cerrar/", {
    form: { counted_amount: "50.00", csrfmiddlewaretoken: s2Csrf },
    maxRedirects: 0,
  });
  check("vendedor2_post_cerrar_sin_turno_muestra_alerta", s2DirectClose.status() === 200 && (await s2DirectClose.text()).includes("No tienes un turno de caja abierto para cerrar."), true);
  // Cross-seller 404
  check("vendedor2_abierto_s1_404", (await s2.request.get(base + `/caja/turnos/${shift1Id}/abierto/`, { maxRedirects: 0 })).status(), 404);

  // 5. ADMIN dashboard metric + history + 403 on operational cash routes
  const adminSession = await loginContext(browser, "admin");
  const admin = adminSession.page;
  check(
    "admin_dashboard_turnos_abiertos_1",
    await admin.locator("dl.summary-list > div").filter({ hasText: "Turnos de caja abiertos" }).locator("dd").innerText(),
    "1"
  );
  for (const deniedUrl of ["/caja/abrir/", "/caja/cerrar/", `/caja/turnos/${shift1Id}/abierto/`]) {
    check(`admin_denied_${deniedUrl}_403`, (await admin.request.get(base + deniedUrl, { maxRedirects: 0 })).status(), 403);
  }
  await admin.locator('#sidebar-navigation a[href="/caja/turnos/"]').click();
  await admin.waitForURL(base + "/caja/turnos/");
  check("admin_historial_muestra_turno_abierto_s1", (await admin.locator(".cash-history-table tbody").innerText()).includes(fixture.accounts.seller1.display_name) && (await admin.locator(".cash-history-table tbody").innerText()).includes("Abierto"), true);

  // 6. VENDEDOR 1 relogs -> draft blocks close -> remove/discard -> discounted sale -> parallel tabs close
  const s1bSession = await loginContext(browser, "seller1");
  const s1b = s1bSession.page;
  await s1b.goto(base + "/caja/abrir/");
  check("relogin_muestra_ya_abriste", (await s1b.locator('[data-testid="cash-already-open"]').innerText()).includes("Ya abriste CAJA-01"), true);

  // Add product to draft
  await s1b.goto(base + "/ventas/");
  await s1b.locator("[name=query]").fill("Arroz Extra");
  await s1b.getByRole("button", { name: "Buscar", exact: true }).click();
  await s1b.locator(".sales-search-panel tbody tr").first().locator("[name=quantity]").fill("2");
  await s1b.locator(".sales-search-panel tbody tr").first().getByRole("button", { name: "Agregar", exact: true }).click();
  await s1b.waitForLoadState("networkidle");

  // Visit /caja/cerrar/ -> shows active draft alert and blocks POST
  await s1b.goto(base + "/caja/cerrar/");
  check("cierre_advierte_borrador_activo", (await s1b.locator("form .alert-info").innerText()).includes("Tienes una venta en preparación activa"), true);
  await s1b.locator("[name=counted_amount]").fill("100.00");
  await s1b.getByRole("button", { name: "Cerrar turno", exact: true }).click();
  check(
    "cierre_bloqueado_con_enlace_a_ventas",
    (await s1b.locator("main .alert-error").innerText()).includes("Hay una venta en preparación con productos") &&
      (await s1b.locator('main .alert-error a[href="/ventas/"]').count()) === 1,
    true
  );
  await shot(s1b, "04-cierre-bloqueado-por-borrador.png");

  // Discard draft and confirm warning disappears
  await s1b.locator('main .alert-error a[href="/ventas/"]').click();
  await s1b.waitForURL(base + "/ventas/");
  await s1b.getByRole("button", { name: /Descartar/i }).click();
  await s1b.waitForLoadState("networkidle");
  await s1b.goto(base + "/caja/cerrar/");
  check("post_descarte_sin_alerta_borrador", await s1b.locator("form .alert-info").count(), 0);

  // Add 2 Arroz Extra (11.00) -> checkout with 1.00 discount -> total 10.00, cash 20.00 -> change 10.00
  await s1b.goto(base + "/ventas/");
  await s1b.locator("[name=query]").fill("Arroz Extra");
  await s1b.getByRole("button", { name: "Buscar", exact: true }).click();
  await s1b.locator(".sales-search-panel tbody tr").first().locator("[name=quantity]").fill("2");
  await s1b.locator(".sales-search-panel tbody tr").first().getByRole("button", { name: "Agregar", exact: true }).click();
  await s1b.waitForLoadState("networkidle");
  await s1b.locator('a[href="/ventas/cobrar/"]').click();
  await s1b.waitForURL(base + "/ventas/cobrar/");
  await s1b.locator("[name=discount_amount]").fill("1.00");
  await s1b.locator("[name=cash_received]").fill("20.00");
  await s1b.getByRole("button", { name: /Confirmar cobro/i }).click();
  await s1b.waitForURL(/\/ventas\/constancia\/[0-9a-f-]+\//);
  check("constancia_venta_10_soles", (await s1b.locator("main").innerText()).includes("10,00"), true);

  // Parallel tabs setup: tab1 (/caja/cerrar/), tab2 (/caja/cerrar/), tabSales (/ventas/)
  const tab2 = await s1bSession.ctx.newPage();
  const tabSales = await s1bSession.ctx.newPage();
  tab2.on("pageerror", (err) => report.page_errors.push({ role: "seller1-tab2", message: err.message }));
  tabSales.on("pageerror", (err) => report.page_errors.push({ role: "seller1-tabSales", message: err.message }));

  await s1b.goto(base + "/caja/cerrar/");
  await tab2.goto(base + "/caja/cerrar/");
  await tabSales.goto(base + "/ventas/");
  await tabSales.locator("[name=query]").fill("Arroz Extra");
  await tabSales.getByRole("button", { name: "Buscar", exact: true }).click();

  // Tab1 closes with 105.00 (expected 100.00 + 10.00 = 110.00 -> Faltante S/ -5,00)
  await s1b.locator("[name=counted_amount]").fill("105.00");
  await s1b.getByRole("button", { name: "Cerrar turno", exact: true }).click();
  await s1b.waitForURL(base + `/caja/turnos/${shift1Id}/cerrado/`);

  const actaText = await s1b.locator("main").innerText();
  check("acta_faltante_valores_exactos", [
    actaText.includes("S/ 100,00"),
    actaText.includes("S/ 110,00"),
    actaText.includes("S/ 105,00"),
    actaText.includes("Faltante S/ -5,00"),
  ], [true, true, true, true]);

  const errorBadgeCss = await s1b.locator("span.status.status-error").evaluate((el) => {
    const st = getComputedStyle(el);
    return { color: st.color, backgroundColor: st.backgroundColor, borderRadius: st.borderRadius };
  });
  const actaPanelPad = await s1b.locator("main section.panel").nth(1).evaluate((el) => {
    const st = getComputedStyle(el);
    return { paddingTop: parseFloat(st.paddingTop), maxWidth: st.maxWidth };
  });
  report.computed_styles.status_error = errorBadgeCss;
  report.computed_styles.acta_panel = actaPanelPad;
  check("acta_panel_con_padding_y_ancho_centrado", [actaPanelPad.paddingTop >= 24, actaPanelPad.maxWidth], [true, "860px"]);
  check("status_error_color_rojo_aplicado", errorBadgeCss.color, "rgb(180, 35, 24)");
  check("status_error_fondo_suave_rojo", errorBadgeCss.backgroundColor !== "rgba(0, 0, 0, 0)", true);

  // Verify @media print hides sidebar/no-print cleanly
  await s1b.emulateMedia({ media: "print" });
  const printHidden = await s1b.evaluate(() => ({
    sidebar: getComputedStyle(document.querySelector(".app-sidebar")).display,
    actions: getComputedStyle(document.querySelector(".form-actions.no-print")).display,
  }));
  await s1b.emulateMedia({ media: "screen" });
  check("acta_print_media_oculta_chrome", printHidden, { sidebar: "none", actions: "none" });
  await shot(s1b, "05-acta-cierre-faltante.png");

  // Tab2 (stale parallel close tab) tries closing same shift -> visible alert-error (FIX09-02)
  await tab2.locator("[name=counted_amount]").fill("110.00");
  await tab2.getByRole("button", { name: "Cerrar turno", exact: true }).click();
  await tab2.waitForLoadState("networkidle");
  check(
    "doble_cierre_pestana_paralela_muestra_error",
    (await tab2.locator("main .alert-error").innerText()).includes("No tienes un turno de caja abierto para cerrar."),
    true
  );
  await shot(tab2, "06-doble-cierre-pestana-paralela.png");

  // TabSales (stale parallel sales tab) tries adding product -> rejected cleanly without open shift
  await tabSales.locator(".sales-search-panel tbody tr").first().getByRole("button", { name: "Agregar", exact: true }).click();
  await tabSales.waitForLoadState("networkidle");
  check(
    "venta_en_pestana_paralela_tras_cierre_rechazada",
    (await tabSales.locator("main .alert-error").innerText()).includes("Necesitas un turno de caja abierto"),
    true
  );

  // Revisiting /abierto/ after close shows closed status, NO "CAJA-01 está abierta" (FIX09-06)
  await s1b.goto(base + `/caja/turnos/${shift1Id}/abierto/`);
  const postCloseOpened = await s1b.locator("main").innerText();
  check("abierto_post_cierre_veraz", [
    !postCloseOpened.includes("CAJA-01 está abierta"),
    postCloseOpened.includes("Turno de CAJA-01 cerrado"),
    postCloseOpened.includes("Cerrado"),
    await s1b.locator(`main a[href="/caja/turnos/${shift1Id}/cerrado/"]`).count() === 1,
    await s1b.locator('main a[href="/ventas/"]').count() === 0,
  ], [true, true, true, true, true]);
  await shot(s1b, "07-registro-apertura-post-cierre.png");
  await s1bSession.ctx.close();

  // 7. VENDEDOR 2 (long display_name) opens & closes Exacto (0.00) and Sobrante (50 -> 65.50)
  await s2.goto(base + "/caja/abrir/");
  await s2.locator("[name=opening_amount]").fill("0.00");
  await s2.getByRole("button", { name: "Abrir turno", exact: true }).click();
  await s2.waitForURL(/\/caja\/turnos\/[0-9a-f-]+\/abierto\//);
  await s2.goto(base + "/caja/cerrar/");
  await s2.locator("[name=counted_amount]").fill("0.00");
  await s2.getByRole("button", { name: "Cerrar turno", exact: true }).click();
  await s2.waitForURL(/\/caja\/turnos\/[0-9a-f-]+\/cerrado\//);
  check("acta_exacto_s0", (await s2.locator("main").innerText()).includes("Exacto S/ 0,00"), true);

  await s2.goto(base + "/caja/abrir/");
  await s2.locator("[name=opening_amount]").fill("50.00");
  await s2.getByRole("button", { name: "Abrir turno", exact: true }).click();
  await s2.waitForURL(/\/caja\/turnos\/[0-9a-f-]+\/abierto\//);
  await s2.goto(base + "/caja/cerrar/");
  await s2.locator("[name=counted_amount]").fill("65.50");
  await s2.getByRole("button", { name: "Cerrar turno", exact: true }).click();
  await s2.waitForURL(/\/caja\/turnos\/[0-9a-f-]+\/cerrado\//);
  check("acta_sobrante_15_50", (await s2.locator("main").innerText()).includes("Sobrante S/ 15,50"), true);

  // VENDEDOR 2 history sees only own 2 shifts
  await s2.goto(base + "/caja/turnos/");
  check("vendedor2_historial_solo_sus_2_turnos", await s2.locator(".cash-history-table tbody tr").count(), 2);
  check("vendedor2_historial_sin_s1", !(await s2.locator(".cash-history-table tbody").innerText()).includes(fixture.accounts.seller1.display_name), true);
  await s2Session.ctx.close();

  // 8. ADMIN sees all 3 shifts, 0 open shifts on dashboard, layout & wrapping metrics, post-logout back blocked
  await admin.goto(base + "/inicio/");
  check(
    "admin_dashboard_turnos_abiertos_0",
    await admin.locator("dl.summary-list > div").filter({ hasText: "Turnos de caja abiertos" }).locator("dd").innerText(),
    "0"
  );
  await admin.goto(base + "/caja/turnos/");
  const histMetrics = await admin.evaluate(() => {
    const docScrollWidth = document.documentElement.scrollWidth;
    const windowInnerWidth = window.innerWidth;
    const wrap = document.querySelector(".table-responsive");
    const longSellerCell = document.querySelector(".cash-history-table tbody tr td:nth-child(2)");
    const firstCajaCell = document.querySelector(".cash-history-table tbody tr td:nth-child(1)");
    const ths = Array.from(document.querySelectorAll(".cash-history-table th")).map((th) => ({
      text: th.textContent.trim(),
      clipped: th.getBoundingClientRect().right > wrap.getBoundingClientRect().right + 1,
    }));
    return {
      docScrollWidth,
      windowInnerWidth,
      docOk: docScrollWidth <= windowInnerWidth,
      wrapScrollWidth: wrap.scrollWidth,
      wrapClientWidth: wrap.clientWidth,
      wrapOk: wrap.scrollWidth <= wrap.clientWidth,
      sellerOverflowWrap: longSellerCell ? getComputedStyle(longSellerCell).overflowWrap : null,
      cajaWhiteSpace: firstCajaCell ? getComputedStyle(firstCajaCell).whiteSpace : null,
      allHeadersVisible: ths.every((t) => !t.clipped),
      thCount: ths.length,
    };
  });
  report.layout_metrics.cash_shift_history = histMetrics;
  check(
    "historial_11_columnas_sin_overflow_con_nombre_largo",
    [histMetrics.docOk, histMetrics.wrapOk, histMetrics.allHeadersVisible, histMetrics.thCount, histMetrics.sellerOverflowWrap, histMetrics.cajaWhiteSpace],
    [true, true, true, 11, "anywhere", "nowrap"]
  );
  check("admin_historial_3_turnos_estados", await admin.locator(".cash-history-table tbody tr").count(), 3);
  const histBody = await admin.locator(".cash-history-table tbody").innerText();
  check(
    "admin_historial_contiene_3_tipos_diferencia",
    histBody.includes("Sobrante") && histBody.includes("Exacto") && histBody.includes("Faltante"),
    true
  );
  await shot(admin, "08-historial-turnos-admin.png");

  // ADMIN opens VENDEDOR 1 closed acta directly from history
  await admin.locator(`.cash-history-table tbody tr`, { hasText: fixture.accounts.seller1.display_name }).getByRole("link", { name: "Ver acta", exact: true }).click();
  await admin.waitForURL(base + `/caja/turnos/${shift1Id}/cerrado/`);
  check("admin_ve_acta_cerrada_s1", (await admin.locator("main").innerText()).includes("Faltante S/ -5,00"), true);

  // @never_cache header & 405 checks
  const adminCsrf = await csrfFromContext(adminSession.ctx);
  for (const url of ["/caja/turnos/", `/caja/turnos/${shift1Id}/cerrado/`]) {
    const getRes = await admin.request.get(base + url, { maxRedirects: 0 });
    check(`never_cache_${url}`, (getRes.headers()["cache-control"] || "").toLowerCase().includes("no-store"), true);
    const postRes = await admin.request.post(base + url, { form: { csrfmiddlewaretoken: adminCsrf }, maxRedirects: 0 });
    check(`readonly_post_${url}_405`, postRes.status(), 405);
  }

  // Logout & back-button blocked
  await admin.locator("a.sidebar-logout").click();
  await admin.waitForURL(base + "/salir/");
  await admin.getByRole("button", { name: "Cerrar sesión", exact: true }).click();
  await admin.waitForURL(base + "/");
  await admin.goBack();
  await admin.waitForLoadState("networkidle");
  check("logout_back_bloqueado", admin.url().startsWith(base + "/?next=") || admin.url() === base + "/" || admin.url().includes("/salir/"), true);
  await admin.goto(base + "/caja/turnos/");
  check("post_logout_historial_redirige_login", admin.url(), `${base}/?next=/caja/turnos/`);
  await adminSession.ctx.close();

  const finalOrm = state();
  check("final_3_turnos_3_cierres_1_venta", [finalOrm.shifts.length, finalOrm.closes.length, finalOrm.sales.length], [3, 3, 1]);
  check("cero_page_errors", report.page_errors.length, 0);
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
