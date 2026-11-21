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
  observations: {},
  layout_metrics: {},
  computed_styles: {},
  page_errors: [],
  console_errors: [],
  server_5xx: [],
  screenshots: [],
  input: "Chrome Stage 09 Revalidation 2026-11-14 (1366x768 & 390x844; HU-CAJA-01..07; DEC-11-TOPE, DEC-12-PERMISOS, CT-COHERENCIA-UI)",
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

async function loginContext(browser, role, viewport = { width: 1366, height: 768 }) {
  const ctx = await browser.newContext({ locale: "es-PE", viewport });
  const page = await ctx.newPage();
  page.on("pageerror", (err) => report.page_errors.push({ role, message: err.message }));
  page.on("console", (msg) => {
    if (msg.type() === "error") report.console_errors.push({ role, text: msg.text() });
  });
  page.on("response", (res) => {
    if (res.status() >= 500) report.server_5xx.push({ role, url: res.url(), status: res.status() });
  });
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
  const probeCtx = await browser.newContext({ locale: "es-PE", viewport: { width: 1366, height: 768 } });
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

  // 2. ALMACENERO denied on all /caja/ routes (GET + POST) & zero nav links
  const whSession = await loginContext(browser, "warehouse");
  const wh = whSession.page;
  for (const href of ["/caja/abrir/", "/caja/cerrar/", "/caja/turnos/"]) {
    check(`almacenero_sin_nav_${href}`, await wh.locator(`#sidebar-navigation a[href="${href}"]`).count(), 0);
    const resp = await wh.request.get(base + href, { maxRedirects: 0 });
    check(`almacenero_${href}_403`, resp.status(), 403);
  }
  check("almacenero_opened_403", (await wh.request.get(base + `/caja/turnos/${dummyUuid}/abierto/`, { maxRedirects: 0 })).status(), 403);
  check("almacenero_closed_403", (await wh.request.get(base + `/caja/turnos/${dummyUuid}/cerrado/`, { maxRedirects: 0 })).status(), 403);
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

  // 3. VENDEDOR 1 invalid openings (DEC-11-TOPE-EFECTIVO-FORM), sidebar observation, valid keyboard open
  const s1Session = await loginContext(browser, "seller1");
  const s1 = s1Session.page;
  const s1Sidebar = {
    open: await s1.locator('#sidebar-navigation a[href="/caja/abrir/"]').count(),
    close: await s1.locator('#sidebar-navigation a[href="/caja/cerrar/"]').count(),
    history: await s1.locator('#sidebar-navigation a[href="/caja/turnos/"]').count(),
    salesShift: await s1.locator('#sidebar-navigation a[href="/ventas/historial/turno/"]').count(),
    salesAll: await s1.locator('#sidebar-navigation a[href="/ventas/historial/"]').count(),
  };
  report.observations.vendedor_sidebar_links = s1Sidebar;
  check("vendedor1_sidebar_all_links", [s1Sidebar.open, s1Sidebar.close, s1Sidebar.history, s1Sidebar.salesShift, s1Sidebar.salesAll], [1, 1, 1, 1, 1]);

  await s1.locator('[data-testid="cash-open-link"]').click();
  await s1.waitForURL(base + "/caja/abrir/");

  // Empty submit -> visible required error
  await s1.getByRole("button", { name: "Abrir turno", exact: true }).click();
  check("apertura_vacia_muestra_error", (await s1.locator(".error-list").innerText()).includes("obligatorio"), true);

  // Invalid negative, >2 decimals, '+' prefix, exponent, above 9,999,999.99 limit
  for (const bad of ["-0.01", "1.005", "+10.00", "1e2", "10000000.00"]) {
    const postRes = await s1.request.post(base + "/caja/abrir/", {
      form: { opening_amount: bad, csrfmiddlewaretoken: await csrfFromContext(s1Session.ctx) },
      maxRedirects: 0,
    });
    check(`apertura_invalida_post_${bad}`, postRes.status() === 200 && (await postRes.text()).includes("error-list"), true);
  }
  await s1.locator("[name=opening_amount]").fill("-0.01");
  await Promise.all([
    s1.waitForLoadState("load"),
    s1.locator("[name=opening_amount]").press("Enter"),
  ]);
  check("apertura_ui_negativo_muestra_error", (await s1.locator(".error-list").count()) > 0 && s1.url().endsWith("/caja/abrir/"), true);

  await s1.locator("[name=opening_amount]").fill("10000000.00");
  await Promise.all([
    s1.waitForLoadState("load"),
    s1.getByRole("button", { name: "Abrir turno", exact: true }).click(),
  ]);
  check("apertura_ui_sobre_tope_muestra_error_servidor", (await s1.locator(".error-list").count()) > 0 && s1.url().endsWith("/caja/abrir/"), true);
  await shot(s1, "01-apertura-error-validacion.png");

  await s1.locator("[name=opening_amount]").fill("0.00");
  await s1.locator("main").evaluate(() => true);
  const openLayout1366 = await s1.evaluate(() => ({
    docScrollWidth: document.documentElement.scrollWidth,
    innerWidth: window.innerWidth,
    docOk: document.documentElement.scrollWidth <= window.innerWidth,
  }));
  report.layout_metrics.cash_open_desktop_1366x768 = openLayout1366;
  check("apertura_sin_desborde_1366x768", openLayout1366.docOk, true);

  // Valid keyboard submit
  await s1.locator("[name=opening_amount]").fill("100.00");
  await s1.locator("[name=opening_amount]").press("Enter");
  await s1.waitForURL(/\/caja\/turnos\/[0-9a-f-]+\/abierto\//);
  const shift1Id = s1.url().match(/\/turnos\/([0-9a-f-]+)\/abierto\//)[1];

  const openedText = await s1.locator("main").innerText();
  report.observations.opened_text_sample = openedText;
  check(
    "apertura_ok_detalle",
    openedText.includes("CAJA-01 está abierta") &&
      openedText.includes(fixture.accounts.seller1.display_name) &&
      (openedText.includes("100.00") || openedText.includes("100,00")) &&
      openedText.includes("Abierto"),
    true
  );
  check("apertura_ok_enlace_preparar_venta", await s1.locator('main a[href="/ventas/"]').count(), 1);
  await shot(s1, "02-turno-abierto-confirmacion.png");

  // Logout preserves open shift
  await s1.locator("a.sidebar-logout").click();
  await s1.waitForURL(base + "/salir/");
  check("logout_indica_turno_conservado", (await s1.locator("main").innerText()).includes("turno abierto seguirá ligado a tu cuenta"), true);
  await s1.getByRole("button", { name: "Cerrar sesión", exact: true }).click();
  await s1.waitForURL(base + "/");

  // 4. VENDEDOR 2 blocked by single-register open shift + cross-role denials
  const s2Session = await loginContext(browser, "seller2");
  const s2 = s2Session.page;
  await s2.goto(base + "/caja/abrir/");
  const blockedOpenText = await s2.locator('[data-testid="cash-already-open"]').innerText();
  check(
    "vendedor2_ve_caja_ocupada_con_nombre_s1",
    blockedOpenText.includes("La caja ya está en uso") && blockedOpenText.includes(fixture.accounts.seller1.display_name),
    true
  );
  check("vendedor2_sin_form_apertura", await s2.locator('[data-testid="cash-open-form"]').count(), 0);
  await shot(s2, "03-bloqueo-otro-vendedor.png");

  await s2.goto(base + "/caja/cerrar/");
  check("vendedor2_sin_turno_abierto_mensaje", (await s2.locator("main").innerText()).includes("No tienes un turno abierto"), true);
  const s2Csrf = await csrfFromContext(s2Session.ctx);
  const s2DirectClose = await s2.request.post(base + "/caja/cerrar/", {
    form: { counted_amount: "50.00", csrfmiddlewaretoken: s2Csrf },
    maxRedirects: 0,
  });
  check(
    "vendedor2_post_cerrar_sin_turno_muestra_alerta",
    s2DirectClose.status() === 200 && (await s2DirectClose.text()).includes("No tienes un turno de caja abierto para cerrar."),
    true
  );
  check("vendedor2_abierto_s1_404", (await s2.request.get(base + `/caja/turnos/${shift1Id}/abierto/`, { maxRedirects: 0 })).status(), 404);

  // 5. ADMIN dashboard metric + history + 403 on operational cash routes
  const adminSession = await loginContext(browser, "admin");
  const admin = adminSession.page;
  check(
    "admin_dashboard_turnos_abiertos_1",
    await admin.locator("dl.summary-list > div").filter({ hasText: "Turnos de caja abiertos" }).locator("dd").innerText(),
    "1"
  );
  check("admin_sin_link_nueva_venta", await admin.locator('a[href="/ventas/"]').count(), 0);
  for (const deniedUrl of ["/caja/abrir/", "/caja/cerrar/", `/caja/turnos/${shift1Id}/abierto/`]) {
    check(`admin_denied_${deniedUrl}_403`, (await admin.request.get(base + deniedUrl, { maxRedirects: 0 })).status(), 403);
  }
  await admin.locator('#sidebar-navigation a[href="/caja/turnos/"]').click();
  await admin.waitForURL(base + "/caja/turnos/");
  check(
    "admin_historial_muestra_turno_abierto_s1",
    (await admin.locator(".cash-history-table tbody").innerText()).includes(fixture.accounts.seller1.display_name) &&
      (await admin.locator(".cash-history-table tbody").innerText()).includes("Abierto"),
    true
  );

  // 6. VENDEDOR 1 relogs -> empty /ventas/ does not block close -> draft line blocks -> remove line unblocks -> sale (no discount!) -> parallel tabs
  const s1bSession = await loginContext(browser, "seller1");
  const s1b = s1bSession.page;
  await s1b.goto(base + "/caja/abrir/");
  check("relogin_muestra_ya_abriste", (await s1b.locator('[data-testid="cash-already-open"]').innerText()).includes("Ya abriste CAJA-01"), true);

  // Empty /ventas/ does not create blocking draft
  await s1b.goto(base + "/ventas/");
  await s1b.goto(base + "/caja/cerrar/");
  check("ventas_vacio_no_bloquea_cierre", await s1b.locator("form .alert-info").count(), 0);

  // Add product -> /caja/cerrar/ warns and blocks POST
  await s1b.goto(base + "/ventas/");
  await s1b.locator("[name=query]").fill("Arroz Extra");
  await s1b.getByRole("button", { name: "Buscar", exact: true }).click();
  await s1b.locator(".sales-search-panel tbody tr").first().locator("[name=quantity]").fill("1");
  await s1b.locator(".sales-search-panel tbody tr").first().getByRole("button", { name: "Agregar", exact: true }).click();
  await s1b.locator('main a[href="/ventas/cobrar/"]').waitFor({ state: "visible" });

  await s1b.goto(base + "/caja/cerrar/");
  check("cierre_advierte_borrador_activo", (await s1b.locator("form .alert-info").innerText()).includes("Tienes una venta en preparación activa"), true);
  await s1b.locator("[name=counted_amount]").fill("100.00");
  await s1b.getByRole("button", { name: "Cerrar turno", exact: true }).click();
  await s1b.locator("main .alert-error").waitFor({ state: "visible" });
  check(
    "cierre_bloqueado_con_enlace_a_ventas",
    (await s1b.locator("main .alert-error").innerText()).includes("Hay una venta en preparación con productos") &&
      (await s1b.locator('main .alert-error a[href="/ventas/"]').count()) === 1,
    true
  );
  await shot(s1b, "04-cierre-bloqueado-por-borrador.png");

  // Removing last line via "Quitar" also unblocks close
  await s1b.locator('main .alert-error a[href="/ventas/"]').click();
  await s1b.waitForURL(base + "/ventas/");
  await s1b.getByRole("button", { name: "Quitar", exact: true }).click();
  await s1b.getByText("Aún no agregaste productos a la venta.").waitFor({ state: "visible" });
  await s1b.goto(base + "/caja/cerrar/");
  check("post_quitar_ultima_linea_sin_alerta_borrador", await s1b.locator("form .alert-info").count(), 0);

  // Add 2 Arroz Extra (5.50 * 2 = 11.00) -> checkout WITHOUT discount -> cash 20.00 -> change 9.00
  await s1b.goto(base + "/ventas/");
  await s1b.locator("[name=query]").fill("Arroz Extra");
  await s1b.getByRole("button", { name: "Buscar", exact: true }).click();
  await s1b.locator(".sales-search-panel tbody tr").first().locator("[name=quantity]").fill("2");
  await s1b.locator(".sales-search-panel tbody tr").first().getByRole("button", { name: "Agregar", exact: true }).click();
  await s1b.locator('main a[href="/ventas/cobrar/"]').waitFor({ state: "visible" });
  await s1b.locator('main a[href="/ventas/cobrar/"]').click();
  await s1b.waitForURL(base + "/ventas/cobrar/");
  check("checkout_sin_campo_descuento", await s1b.locator("[name=discount_amount]").count(), 0);
  await s1b.locator("[name=cash_received]").fill("20.00");
  await s1b.getByRole("button", { name: /Confirmar cobro/i }).click();
  await s1b.waitForURL(/\/ventas\/constancia\/[0-9a-f-]+\//);
  const receiptText = await s1b.locator("main").innerText();
  check("constancia_venta_11_soles", receiptText.includes("11,00") || receiptText.includes("11.00"), true);

  // Navigate to "Ventas del turno" via receipt CTA
  await s1b.locator('main a[href="/ventas/historial/turno/"]').click();
  await s1b.waitForURL(base + "/ventas/historial/turno/");
  const shiftSalesText = await s1b.locator("main").innerText();
  check("ventas_del_turno_muestra_11", shiftSalesText.includes("11,00") || shiftSalesText.includes("11.00"), true);

  // Parallel tabs setup: tab1 (/caja/cerrar/), tab2 (/caja/cerrar/), tabSales (/ventas/)
  const tab2 = await s1bSession.ctx.newPage();
  const tabSales = await s1bSession.ctx.newPage();
  for (const [label, pg] of [["seller1-tab2", tab2], ["seller1-tabSales", tabSales]]) {
    pg.on("pageerror", (err) => report.page_errors.push({ role: label, message: err.message }));
    pg.on("console", (msg) => {
      if (msg.type() === "error") report.console_errors.push({ role: label, text: msg.text() });
    });
    pg.on("response", (res) => {
      if (res.status() >= 500) report.server_5xx.push({ role: label, url: res.url(), status: res.status() });
    });
  }

  await s1b.goto(base + "/caja/cerrar/");
  await tab2.goto(base + "/caja/cerrar/");
  await tabSales.goto(base + "/ventas/");
  await tabSales.locator("[name=query]").fill("Arroz Extra");
  await tabSales.getByRole("button", { name: "Buscar", exact: true }).click();

  // Check close screen BEFORE closing: shows Caja, Apertura, Monto inicial 100.00 (blind count: omits 11.00 sales / 111.00 expected)
  const preCloseText = await s1b.locator("main").innerText();
  report.observations.pre_close_text = preCloseText;
  check(
    "cierre_preview_arqueo_ciego_muestra_inicial_y_oculta_esperado",
    (preCloseText.includes("100,00") || preCloseText.includes("100.00")) &&
      !preCloseText.includes("111,00") &&
      !preCloseText.includes("111.00"),
    true
  );

  // Tab1 closes with 106.00 (expected 111.00 -> Faltante S/ -5,00 or -5.00)
  await s1b.locator("[name=counted_amount]").fill("106.00");
  await s1b.getByRole("button", { name: "Cerrar turno", exact: true }).click();
  await s1b.waitForURL(base + `/caja/turnos/${shift1Id}/cerrado/`);

  const actaText = await s1b.locator("main").innerText();
  report.observations.acta_faltante_text = actaText;
  check(
    "acta_faltante_valores_exactos",
    (actaText.includes("100,00") || actaText.includes("100.00")) &&
      (actaText.includes("111,00") || actaText.includes("111.00")) &&
      (actaText.includes("106,00") || actaText.includes("106.00")) &&
      (actaText.includes("Faltante S/ -5,00") || actaText.includes("Faltante S/ -5.00")),
    true
  );

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

  // @media print check
  await s1b.emulateMedia({ media: "print" });
  const printHidden = await s1b.evaluate(() => ({
    sidebar: getComputedStyle(document.querySelector(".app-sidebar")).display,
    actions: getComputedStyle(document.querySelector(".form-actions.no-print")).display,
  }));
  await s1b.emulateMedia({ media: "screen" });
  check("acta_print_media_oculta_chrome", printHidden, { sidebar: "none", actions: "none" });
  await shot(s1b, "05-acta-cierre-faltante.png");

  // Tab2 parallel close race -> visible error alert, no second CashShiftClose
  await tab2.locator("[name=counted_amount]").fill("111.00");
  await tab2.getByRole("button", { name: "Cerrar turno", exact: true }).click();
  await tab2.locator("main .alert-error").waitFor({ state: "visible" });
  check(
    "doble_cierre_pestana_paralela_muestra_error",
    (await tab2.locator("main .alert-error").innerText()).includes("No tienes un turno de caja abierto para cerrar."),
    true
  );
  await shot(tab2, "06-doble-cierre-pestana-paralela.png");

  // TabSales parallel sale attempt after close -> rejected cleanly
  await tabSales.locator(".sales-search-panel tbody tr").first().getByRole("button", { name: "Agregar", exact: true }).click();
  await tabSales.locator("main .alert-error").waitFor({ state: "visible" });
  check(
    "venta_en_pestana_paralela_tras_cierre_rechazada",
    (await tabSales.locator("main .alert-error").innerText()).includes("Necesitas un turno de caja abierto"),
    true
  );

  // Revisiting /abierto/ after close
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

  // Seller 1 opens own /caja/turnos/ -> sees 1 shift, NO seller dropdown
  await s1b.goto(base + "/caja/turnos/");
  check("vendedor1_historial_propio_1_fila", await s1b.locator(".cash-history-table tbody tr").count(), 1);
  check("vendedor1_historial_sin_selector_vendedor", await s1b.locator('[name="vendedor"]').count(), 0);
  await s1bSession.ctx.close();

  // 7. VENDEDOR 2 (long display_name) opens & closes Exacto (0.00) and Sobrante (50 -> 65.50)
  await s2.goto(base + "/caja/abrir/");
  await s2.locator("[name=opening_amount]").fill("0.00");
  await s2.getByRole("button", { name: "Abrir turno", exact: true }).click();
  await s2.waitForURL(/\/caja\/turnos\/[0-9a-f-]+\/abierto\//);
  const shift2Id = s2.url().match(/\/turnos\/([0-9a-f-]+)\/abierto\//)[1];
  await s2.goto(base + "/caja/cerrar/");
  await s2.locator("[name=counted_amount]").fill("0.00");
  await s2.getByRole("button", { name: "Cerrar turno", exact: true }).click();
  await s2.waitForURL(/\/caja\/turnos\/[0-9a-f-]+\/cerrado\//);
  const exactText = await s2.locator("main").innerText();
  check("acta_exacto_s0", exactText.includes("Exacto S/ 0,00") || exactText.includes("Exacto S/ 0.00"), true);

  await s2.goto(base + "/caja/abrir/");
  await s2.locator("[name=opening_amount]").fill("50.00");
  await s2.getByRole("button", { name: "Abrir turno", exact: true }).click();
  await s2.waitForURL(/\/caja\/turnos\/[0-9a-f-]+\/abierto\//);
  await s2.goto(base + "/caja/cerrar/");
  await s2.locator("[name=counted_amount]").fill("65.50");
  await s2.getByRole("button", { name: "Cerrar turno", exact: true }).click();
  await s2.waitForURL(/\/caja\/turnos\/[0-9a-f-]+\/cerrado\//);
  const sobranteText = await s2.locator("main").innerText();
  check("acta_sobrante_15_50", sobranteText.includes("Sobrante S/ 15,50") || sobranteText.includes("Sobrante S/ 15.50"), true);

  // VENDEDOR 2 history sees only own 2 shifts & cannot bypass via ?vendedor=<s1> or view s1 /cerrado/
  await s2.goto(base + "/caja/turnos/");
  check("vendedor2_historial_solo_sus_2_turnos", await s2.locator(".cash-history-table tbody tr").count(), 2);
  check("vendedor2_historial_sin_s1", !(await s2.locator(".cash-history-table tbody").innerText()).includes(fixture.accounts.seller1.display_name), true);
  await s2.goto(base + `/caja/turnos/?vendedor=${fixture.accounts.seller1.id}`);
  check("vendedor2_filtro_vendedor_ignorado", await s2.locator(".cash-history-table tbody tr").count(), 2);
  check("vendedor2_cerrado_s1_404", (await s2.request.get(base + `/caja/turnos/${shift1Id}/cerrado/`, { maxRedirects: 0 })).status(), 404);
  await s2Session.ctx.close();

  // 8. ADMIN sees all 3 shifts, 0 open shifts, desktop + mobile 390x844 metrics, filters, /cerrado/ H1 observation
  await admin.goto(base + "/inicio/");
  check(
    "admin_dashboard_turnos_abiertos_0",
    await admin.locator("dl.summary-list > div").filter({ hasText: "Turnos de caja abiertos" }).locator("dd").innerText(),
    "0"
  );
  await admin.goto(base + "/caja/turnos/");
  const histMetricsDesktop = await admin.evaluate(() => {
    const docScrollWidth = document.documentElement.scrollWidth;
    const windowInnerWidth = window.innerWidth;
    const wrap = document.querySelector(".table-responsive");
    const longSellerCell = document.querySelector(".cash-history-table tbody tr td:nth-child(2)");
    const firstCajaCell = document.querySelector(".cash-history-table tbody tr td:nth-child(1)");
    const ths = Array.from(document.querySelectorAll(".cash-history-table th")).map((th) => ({
      text: th.textContent.trim(),
      clipped: th.getBoundingClientRect().right > wrap.getBoundingClientRect().right + 1,
    }));
    const filterBtn = document.querySelector(".history-filter-panel button[type=submit]");
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
      filterBtnBg: filterBtn ? getComputedStyle(filterBtn).backgroundColor : null,
      tableHeaderBg: getComputedStyle(document.querySelector(".cash-history-table thead")).backgroundColor,
    };
  });
  report.layout_metrics.cash_shift_history_desktop = histMetricsDesktop;
  check(
    "historial_11_columnas_sin_overflow_desktop",
    [histMetricsDesktop.docOk, histMetricsDesktop.allHeadersVisible, histMetricsDesktop.thCount, histMetricsDesktop.sellerOverflowWrap, histMetricsDesktop.cajaWhiteSpace],
    [true, true, 11, "anywhere", "nowrap"]
  );
  check("admin_historial_3_turnos_estados", await admin.locator(".cash-history-table tbody tr").count(), 3);
  const histBody = await admin.locator(".cash-history-table tbody").innerText();
  check(
    "admin_historial_contiene_3_tipos_diferencia",
    histBody.includes("Sobrante") && histBody.includes("Exacto") && histBody.includes("Faltante"),
    true
  );
  await shot(admin, "08-historial-turnos-admin-desktop.png");

  // ADMIN seller filter UI check
  await admin.locator('[name="vendedor"]').selectOption(fixture.accounts.seller1.id);
  await Promise.all([
    admin.waitForURL(/vendedor=/),
    admin.getByRole("button", { name: "Filtrar", exact: true }).click(),
  ]);
  check("admin_filtro_vendedor1_1_fila", await admin.locator(".cash-history-table tbody tr").count(), 1);
  await admin.getByRole("link", { name: "Limpiar", exact: true }).click();
  await admin.waitForURL(base + "/caja/turnos/");

  // ADMIN invalid filter in UI (inverted dates)
  await admin.locator('[name="fecha_desde"]').fill("2026-12-10");
  await admin.locator('[name="fecha_hasta"]').fill("2026-12-01");
  await Promise.all([
    admin.waitForURL(/fecha_desde=2026-12-10/),
    admin.getByRole("button", { name: "Filtrar", exact: true }).click(),
  ]);
  check("admin_filtro_invertido_alerta_sin_filas", (await admin.locator(".alert-error").count()) > 0 && (await admin.locator(".alert-warning").count()) > 0 && (await admin.locator(".cash-history-table").count()) === 0, true);
  await admin.goto(base + "/caja/turnos/");

  // ADMIN opens VENDEDOR 1 closed acta and checks topbar H1 (captures literal text if 'Cerrar turno')
  await admin.locator(".cash-history-table tbody tr", { hasText: fixture.accounts.seller1.display_name }).getByRole("link", { name: "Ver acta", exact: true }).click();
  await admin.waitForURL(base + `/caja/turnos/${shift1Id}/cerrado/`);
  const admClosedText = await admin.locator("main").innerText();
  const admClosedH1 = (await admin.locator("header.app-topbar h1").innerText()).trim();
  report.observations.admin_closed_topbar_h1 = admClosedH1;
  check("admin_closed_topbar_h1_acta", admClosedH1, "Acta de cierre");
  check("admin_ve_acta_cerrada_s1", admClosedText.includes("Faltante S/ -5,00") || admClosedText.includes("Faltante S/ -5.00"), true);

  // @never_cache header & 405 checks
  const adminCsrf = await csrfFromContext(adminSession.ctx);
  for (const url of ["/caja/turnos/", `/caja/turnos/${shift1Id}/cerrado/`]) {
    const getRes = await admin.request.get(base + url, { maxRedirects: 0 });
    check(`never_cache_${url}`, (getRes.headers()["cache-control"] || "").toLowerCase().includes("no-store"), true);
    const postRes = await admin.request.post(base + url, { form: { csrfmiddlewaretoken: adminCsrf }, maxRedirects: 0 });
    check(`readonly_post_${url}_405`, postRes.status(), 405);
  }

  // Mobile 390x844 checks as ADMIN on /caja/turnos/ and /cerrado/
  await admin.setViewportSize({ width: 390, height: 844 });
  await admin.goto(base + "/caja/turnos/");
  const mobileHistoryMetrics = await admin.evaluate(() => ({
    docScrollWidth: document.documentElement.scrollWidth,
    innerWidth: window.innerWidth,
    docOk: document.documentElement.scrollWidth <= window.innerWidth,
    wrapScrollWidth: document.querySelector(".table-responsive")?.scrollWidth ?? null,
    wrapClientWidth: document.querySelector(".table-responsive")?.clientWidth ?? null,
  }));
  report.layout_metrics.cash_shift_history_mobile_390 = mobileHistoryMetrics;
  await shot(admin, "09-historial-turnos-admin-390px.png");

  await admin.goto(base + `/caja/turnos/${shift2Id}/cerrado/`);
  const mobileClosedMetrics = await admin.evaluate(() => ({
    docScrollWidth: document.documentElement.scrollWidth,
    innerWidth: window.innerWidth,
    docOk: document.documentElement.scrollWidth <= window.innerWidth,
  }));
  report.layout_metrics.cash_closed_mobile_390 = mobileClosedMetrics;
  await shot(admin, "10-acta-cerrada-admin-390px.png");

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
  check("cero_console_errors", report.console_errors.length, 0);
  check("cero_server_5xx", report.server_5xx.length, 0);
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
