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

const out = process.env.AUDIT10_OUT;
const run = process.env.AUDIT10_RUN_DIR;
const base = "http://127.0.0.1:" + process.env.AUDIT10_PORT;
const accounts = JSON.parse(fs.readFileSync(path.join(run, ".credentials.json"), "utf8"));
const fixture = JSON.parse(fs.readFileSync(path.join(out, "fixture.json"), "utf8"));

const report = {
  checks: [],
  layout_metrics: {},
  inactivity_evidence: {},
  page_errors: [],
  screenshots: [],
  input: "Chrome 1366x900 & 1366x768 Stage 10 audit (sales draft, roles, stock/price cross-role, two tabs, discard, logout, screen lock check)",
};

function check(id, actual, expected) {
  assert.deepEqual(actual, expected, id);
  report.checks.push(id);
}

function state() {
  return JSON.parse(
    execFileSync(process.env.AUDIT10_PYTHON, [path.join(__dirname, "audit10_run.py"), "snapshot"], {
      encoding: "utf8",
    })
  );
}

async function getCsrf(ctx) {
  const cookies = await ctx.cookies();
  const cookie = cookies.find((c) => c.name === "audit10_csrftoken");
  assert.ok(cookie && cookie.value, "audit10_csrftoken missing");
  return cookie.value;
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

async function clickAndNav(page, locator) {
  await Promise.all([page.waitForNavigation({ waitUntil: "load" }), locator.click()]);
}

async function measureSalesLayout(page) {
  return page.evaluate(() => {
    const docScrollWidth = document.documentElement.scrollWidth;
    const windowInnerWidth = window.innerWidth;
    const searchPanel = document.querySelector(".sales-search-panel");
    const summaryPanel = document.querySelector(".sales-summary-panel");
    const tableWrap = document.querySelector(".sales-search-panel .table-wrap");
    const ths = tableWrap
      ? Array.from(tableWrap.querySelectorAll("th")).map((th) => {
          const r = th.getBoundingClientRect();
          const wr = tableWrap.getBoundingClientRect();
          return {
            text: th.textContent.trim(),
            left: Math.round(r.left),
            right: Math.round(r.right),
            clipped: r.right > wr.right + 1 || r.right > windowInnerWidth + 1,
          };
        })
      : [];
    const sr = searchPanel ? searchPanel.getBoundingClientRect() : null;
    const dr = summaryPanel ? summaryPanel.getBoundingClientRect() : null;
    return {
      viewport: { width: windowInnerWidth, height: window.innerHeight },
      docScrollWidth,
      windowInnerWidth,
      docOk: docScrollWidth <= windowInnerWidth,
      wrapOk: tableWrap ? tableWrap.scrollWidth <= tableWrap.clientWidth : true,
      wrapScrollW: tableWrap ? tableWrap.scrollWidth : null,
      wrapClientW: tableWrap ? tableWrap.clientWidth : null,
      searchPanelFits: sr ? sr.right <= windowInnerWidth + 1 && searchPanel.scrollWidth <= searchPanel.clientWidth + 1 : true,
      summaryPanelFits: dr ? dr.right <= windowInnerWidth + 1 && summaryPanel.scrollWidth <= summaryPanel.clientWidth + 1 : true,
      summaryScrollW: summaryPanel ? summaryPanel.scrollWidth : null,
      summaryClientW: summaryPanel ? summaryPanel.clientWidth : null,
      ths,
      allHeadersVisible: ths.every((t) => !t.clipped),
    };
  });
}

async function runAudit(browser) {
  const initialOrm = state();

  // 1. Cryptographic proof & anonymous redirects across all Stage 10 routes
  const probeCtx = await browser.newContext({ locale: "es-PE", viewport: { width: 1366, height: 900 } });
  const probe = await probeCtx.newPage();
  const nonce = crypto.randomBytes(32).toString("hex");
  const probeRes = await probe.request.get(base, { headers: { "X-Audit10-Challenge": nonce } });
  const expectedProof = crypto
    .createHmac("sha256", fs.readFileSync(path.join(run, ".django-key")))
    .update(nonce)
    .digest("hex");
  check("aislamiento_proof", probeRes.headers()["x-audit10-proof"], expectedProof);
  check("aislamiento_run", probeRes.headers()["x-audit10-run"], path.basename(run));

  const dummyId = "00000000-0000-4000-8000-000000000001";
  for (const url of ["/ventas/", "/ventas/cobrar/"]) {
    const r = await probe.request.get(base + url, { maxRedirects: 0 });
    check(`anon_get_${url}_302`, r.status(), 302);
    check(`anon_get_${url}_next`, r.headers()["location"], `/?next=${url}`);
  }
  const rNoCsrf = await probe.request.post(base + "/ventas/", { maxRedirects: 0 });
  check("anon_post_sin_csrf_403", rNoCsrf.status(), 403);
  const anonCsrf = await getCsrf(probeCtx);
  for (const url of [
    "/ventas/",
    `/ventas/lineas/${dummyId}/`,
    `/ventas/lineas/${dummyId}/quitar/`,
    "/ventas/descartar/",
  ]) {
    const r = await probe.request.post(base + url, {
      form: { csrfmiddlewaretoken: anonCsrf, quantity: "1" },
      maxRedirects: 0,
    });
    check(`anon_post_${url}_302`, r.status(), 302);
    check(`anon_post_${url}_next`, r.headers()["location"], `/?next=${url}`);
  }
  await probeCtx.close();

  // 2. ADMIN & ALMACENERO: zero POS links in nav + 403 on all draft/checkout routes (GET + CSRF POST)
  const adminSession = await loginContext(browser, "admin");
  const whSession = await loginContext(browser, "warehouse");
  for (const [role, session] of [
    ["admin", adminSession],
    ["warehouse", whSession],
  ]) {
    const { ctx, page } = session;
    for (const href of ["/ventas/", "/ventas/cobrar/", "/ventas/historial/turno/"]) {
      check(`${role}_sin_nav_${href}`, await page.locator(`#sidebar-navigation a[href="${href}"]`).count(), 0);
    }
    const csrf = await getCsrf(ctx);
    for (const url of ["/ventas/", "/ventas/cobrar/"]) {
      const rGet = await page.request.get(base + url, { maxRedirects: 0 });
      check(`${role}_get_${url}_403`, rGet.status(), 403);
    }
    for (const url of [
      "/ventas/",
      `/ventas/lineas/${dummyId}/`,
      `/ventas/lineas/${dummyId}/quitar/`,
      "/ventas/descartar/",
      "/ventas/cobrar/",
    ]) {
      const rPost = await page.request.post(base + url, {
        form: { csrfmiddlewaretoken: csrf, product_id: fixture.products.gtin.id, quantity: "1" },
        maxRedirects: 0,
      });
      check(`${role}_post_${url}_403`, rPost.status(), 403);
    }
  }
  check("no_draft_created_by_denied_roles", state().drafts.length, 0);

  // 3. VENDEDOR 2 without open shift: sidebar navigation, hidden query bar (HU-VEN-04 gap), POST shows visible alert-error
  const s2Session = await loginContext(browser, "seller2");
  const s2 = s2Session.page;
  await s2.locator('#sidebar-navigation a[href="/ventas/"]').click();
  await s2.waitForURL(base + "/ventas/");
  const s2Text = await s2.locator("main").innerText();
  check("s2_requiere_turno_ui", [
    s2Text.includes("Requiere turno abierto"),
    s2Text.includes("Abre tu turno para preparar una venta"),
    (await s2.locator('a[href="/caja/abrir/"]').count()) >= 1,
    await s2.locator('input[name="query"]').count(),
  ], [true, true, true, 0]);
  await shot(s2, "01-vendedor-sin-turno.png");

  // Direct query while no shift still hides lookup (HU-VEN-04 gap)
  await s2.goto(`${base}/ventas/?query=${fixture.products.gtin.barcode}`);
  check("s2_query_con_param_oculto_sin_turno", await s2.locator(".sales-search-panel").count(), 0);

  // Direct POST without open shift shows visible .alert-error
  const s2Csrf = await getCsrf(s2Session.ctx);
  await s2.goto(base + "/ventas/");
  const s2Post = await s2.request.post(base + "/ventas/", {
    form: {
      csrfmiddlewaretoken: s2Csrf,
      product_id: fixture.products.gtin.id,
      quantity: "1",
    },
    maxRedirects: 0,
  });
  check("s2_post_sin_turno_200_con_alerta", [
    s2Post.status(),
    (await s2Post.text()).includes("alert-error"),
    (await s2Post.text()).includes("Necesitas un turno de caja abierto a tu nombre para preparar una venta."),
  ], [200, true, true]);
  check("s2_sin_draft_creado", state().drafts.length, 0);
  await s2Session.ctx.close();

  // 4. VENDEDOR (open shift) -> verify screen-lock absence (HU-VEN-01a/RN-22) & navigation
  const sellerSession = await loginContext(browser, "seller");
  const seller = sellerSession.page;
  await seller.locator('#sidebar-navigation a[href="/ventas/"]').click();
  await seller.waitForURL(base + "/ventas/");

  const inactivityCheck = await seller.evaluate(() => {
    const scripts = Array.from(document.querySelectorAll("script")).map((s) => ({
      src: s.getAttribute("src"),
      inlineLen: s.textContent.trim().length,
      text: s.textContent,
    }));
    const bodyText = document.body.innerText.toLowerCase();
    const hasLockTerms =
      bodyText.includes("bloquear pantalla") ||
      bodyText.includes("pantalla bloqueada") ||
      bodyText.includes("reingresar mi contraseña") ||
      bodyText.includes("inactividad");
    const hasTimerInScripts = scripts.some((s) => /setTimeout|setInterval|inactiv|idle|lock/i.test(s.text));
    return { scripts: scripts.map(({ src, inlineLen }) => ({ src, inlineLen })), hasLockTerms, hasTimerInScripts };
  });
  const sellerCookies = await sellerSession.ctx.cookies();
  const sessCookie = sellerCookies.find((c) => c.name === "audit10_sessionid");
  report.inactivity_evidence = {
    dom: inactivityCheck,
    session_cookie_expires: sessCookie ? sessCookie.expires : null,
    session_only_browser_close: sessCookie ? sessCookie.expires === -1 : null,
  };
  check("hu_ven_01a_sin_bloqueo_pantalla_dom_ni_timer", [inactivityCheck.hasLockTerms, inactivityCheck.hasTimerInScripts], [false, false]);

  // Empty state check
  const emptyMain = await seller.locator("main").innerText();
  check("pos_estado_inicial", [
    emptyMain.includes("Turno abierto"),
    emptyMain.includes("Escribe un nombre o código de barras para buscar."),
    emptyMain.includes("Aún no agregaste productos a la venta."),
  ], [true, true, true]);

  // 5. Searches: accents+spaces, multi-GTIN, internal leading zero, missing barcode, excluded controls, errors
  await seller.locator('[name="query"]').fill("  ATÚN   EN   LATA  ");
  await clickAndNav(seller, seller.getByRole("button", { name: "Buscar", exact: true }));
  const gtinRow = seller.locator(".sales-search-panel tbody tr", { hasText: fixture.products.gtin.name });
  const gtinCells = await gtinRow.locator("td").allInnerTexts();
  check("busqueda_acentos_espacios_gtin", [
    await seller.locator(".sales-search-panel tbody tr").count(),
    gtinCells[0].trim(),
    gtinCells[1].trim(),
    gtinCells[2].trim(),
    gtinCells[3].trim(),
  ], [1, fixture.products.gtin.name, "0775000000014", "6", "S/ 5,90"]);

  for (const code of ["775000000014", "00775000000014"]) {
    await seller.locator('[name="query"]').fill(code);
    await clickAndNav(seller, seller.getByRole("button", { name: "Buscar", exact: true }));
    const cells = await seller.locator(".sales-search-panel tbody tr").first().locator("td").allInnerTexts();
    check(`busqueda_gtin_variante_${code}`, [
      await seller.locator(".sales-search-panel tbody tr").count(),
      cells[0].trim(),
      cells[2].trim(),
    ], [1, fixture.products.gtin.name, "6"]);
  }

  // Internal leading zeroes exact match vs stripped
  await seller.locator('[name="query"]').fill("00A10-99");
  await clickAndNav(seller, seller.getByRole("button", { name: "Buscar", exact: true }));
  check("busqueda_codigo_interno_ceros", await seller.locator(".sales-search-panel tbody tr").count(), 1);

  await seller.locator('[name="query"]').fill("A10-99");
  await clickAndNav(seller, seller.getByRole("button", { name: "Buscar", exact: true }));
  check("busqueda_codigo_interno_sin_ceros_no_coincide", (await seller.locator(".sales-search-panel").innerText()).includes("No se encontraron productos con existencias vendibles."), true);

  // Missing barcode + HU-VEN-04 gap ("Producto no encontrado" absent)
  await seller.locator('[name="query"]').fill("9999999999999");
  await clickAndNav(seller, seller.getByRole("button", { name: "Buscar", exact: true }));
  const missingTxt = await seller.locator(".sales-search-panel").innerText();
  check("busqueda_inexistente_y_brecha_hu_ven_04", [
    missingTxt.includes("No se encontraron productos con existencias vendibles."),
    missingTxt.includes("Producto no encontrado"),
  ], [true, false]);

  // Excluded controls: expired today, zero stock, inactive product, suspended category
  for (const blocked of ["Leche Solo Hoy A10", "Arroz Cero Stock A10", "Fideos Inactivo A10", "Jugo Categoria Suspendida A10"]) {
    await seller.locator('[name="query"]').fill(blocked);
    await clickAndNav(seller, seller.getByRole("button", { name: "Buscar", exact: true }));
    const txt = await seller.locator(".sales-search-panel").innerText();
    check(`busqueda_excluye_${blocked}`, txt.includes("No se encontraron productos con existencias vendibles."), true);
  }

  // Search form invalid queries (>160 chars & NUL)
  await seller.goto(`${base}/ventas/?query=${"X".repeat(161)}`);
  check("busqueda_over160_alerta_error", [
    await seller.locator(".sales-search-panel .alert-error").count(),
    await seller.locator(".sales-search-panel table").count(),
  ], [1, 0]);

  await seller.goto(`${base}/ventas/?query=atun%00`);
  check("busqueda_nul_alerta_error", [
    await seller.locator(".sales-search-panel .alert-error").count(),
    await seller.locator(".sales-search-panel table").count(),
  ], [1, 0]);

  // 6. Long 160-char name + 64-char barcode layout verification at 1366x900 & 1366x768
  await seller.locator('[name="query"]').fill("ProductoSuperLargo");
  await clickAndNav(seller, seller.getByRole("button", { name: "Buscar", exact: true }));
  await clickAndNav(
    seller,
    seller.locator(".sales-search-panel tbody tr", { hasText: "ProductoSuperLargo" }).getByRole("button", { name: "Agregar", exact: true })
  );

  const metrics900 = await measureSalesLayout(seller);
  report.layout_metrics.pos_long_1366x900 = metrics900;
  check("layout_pos_largo_1366x900_sin_overflow", [
    metrics900.docOk,
    metrics900.wrapOk,
    metrics900.searchPanelFits,
    metrics900.summaryPanelFits,
    metrics900.allHeadersVisible,
    metrics900.ths.length,
  ], [true, true, true, true, true, 5]);
  await shot(seller, "02-pos-largo-1366x900.png");

  await seller.setViewportSize({ width: 1366, height: 768 });
  const metrics768 = await measureSalesLayout(seller);
  report.layout_metrics.pos_long_1366x768 = metrics768;
  check("layout_pos_largo_1366x768_sin_overflow", [
    metrics768.docOk,
    metrics768.wrapOk,
    metrics768.searchPanelFits,
    metrics768.summaryPanelFits,
    metrics768.allHeadersVisible,
  ], [true, true, true, true, true]);
  await shot(seller, "03-pos-largo-1366x768.png");
  await seller.setViewportSize({ width: 1366, height: 900 });

  // Remove p_long from draft
  await clickAndNav(
    seller,
    seller.locator(".draft-line", { hasText: "ProductoSuperLargo" }).getByRole("button", { name: "Quitar", exact: true })
  );
  check("draft_vacio_tras_quitar_ultima_linea_largo", (await seller.locator(".sales-summary-panel").innerText()).includes("Aún no agregaste productos a la venta."), true);

  // 7. Add & group p_gtin (1 + 2 = 3), stock limit (7 > 6), strict ASCII/bounds, exact IGV totals
  await seller.locator('[name="query"]').fill("ATÚN");
  await clickAndNav(seller, seller.getByRole("button", { name: "Buscar", exact: true }));
  await clickAndNav(
    seller,
    seller.locator(".sales-search-panel tbody tr", { hasText: fixture.products.gtin.name }).getByRole("button", { name: "Agregar", exact: true })
  );

  // Add 2 more of same product -> consolidated line qty=3
  const gtinAddInput = seller.locator(".sales-search-panel tbody tr", { hasText: fixture.products.gtin.name }).locator('input[name="quantity"]');
  await gtinAddInput.fill("2");
  await clickAndNav(
    seller,
    seller.locator(".sales-search-panel tbody tr", { hasText: fixture.products.gtin.name }).getByRole("button", { name: "Agregar", exact: true })
  );

  const gtinDraftLine = seller.locator(".draft-line", { hasText: fixture.products.gtin.name });
  const totalsAfter3 = await seller.locator(".sale-totals dd").allInnerTexts();
  check("agrupa_linea_gtin_3_e_igv_exacto", [
    await seller.locator(".draft-line").count(),
    (await gtinDraftLine.locator(".draft-line-total").innerText()).replace(/\s+/g, " ").trim(),
    totalsAfter3.map((t) => t.trim()),
  ], [1, "3 und. S/ 17,70", ["S/ 15,00", "S/ 2,70", "S/ 17,70"]]);

  // Attempt add +4 (3 + 4 = 7 > 6) via UI
  await seller.locator(".sales-search-panel tbody tr", { hasText: fixture.products.gtin.name }).locator('input[name="quantity"]').fill("4");
  await clickAndNav(
    seller,
    seller.locator(".sales-search-panel tbody tr", { hasText: fixture.products.gtin.name }).getByRole("button", { name: "Agregar", exact: true })
  );
  check("rechaza_agregar_sobre_vendible", [
    (await seller.locator(".sales-search-panel .alert-error").innerText()).includes("La cantidad supera las existencias vendibles disponibles."),
    await gtinDraftLine.locator('input[name="quantity"]').inputValue(),
  ], [true, "3"]);

  // HTML5 constraint check in real UI input + altered CSRF POST requests for invalid quantities
  await gtinAddInput.fill("0");
  check("html5_min_1_valido_false", await gtinAddInput.evaluate((el) => el.validity.valid), false);
  await gtinAddInput.fill("1000000");
  check("html5_max_999999_valido_false", await gtinAddInput.evaluate((el) => el.validity.valid), false);
  await gtinAddInput.fill("1");

  const sCsrf = await getCsrf(sellerSession.ctx);
  const emptyPostRes = await seller.request.post(base + "/ventas/", {
    form: { csrfmiddlewaretoken: sCsrf },
    maxRedirects: 0,
  });
  check("post_vacio_200_con_alert_error", [
    emptyPostRes.status(),
    (await emptyPostRes.text()).includes("alert-error"),
  ], [200, true]);

  const gtinAction = await gtinDraftLine.locator("form.draft-line-actions").getAttribute("action");
  for (const badQty of ["٥", "+2", "0", "-1", "1.5", "1e2", "1000000"]) {
    const rAdd = await seller.request.post(base + "/ventas/", {
      form: { csrfmiddlewaretoken: sCsrf, product_id: fixture.products.gtin.id, quantity: badQty },
      maxRedirects: 0,
    });
    const rAddHtml = await rAdd.text();
    check(`post_add_invalido_${badQty}`, [rAdd.status(), rAddHtml.includes("alert-error")], [200, true]);

    const rUpd = await seller.request.post(base + gtinAction, {
      form: { csrfmiddlewaretoken: sCsrf, quantity: badQty },
      maxRedirects: 1,
    });
    const rUpdHtml = await rUpd.text();
    check(`post_upd_invalido_${badQty}`, [rUpd.status(), rUpdHtml.includes("alert-error")], [200, true]);
  }
  await seller.reload();
  check("cantidad_gtin_intacta_en_3_tras_rechazos", await gtinDraftLine.locator('input[name="quantity"]').inputValue(), "3");

  // 8. Query with '&' survives redirect via urlencode + cross-role interactions
  await seller.locator('[name="query"]').fill("Café & Pan");
  await clickAndNav(seller, seller.getByRole("button", { name: "Buscar", exact: true }));
  await clickAndNav(
    seller,
    seller.locator(".sales-search-panel tbody tr", { hasText: fixture.products.amp.name }).getByRole("button", { name: "Agregar", exact: true })
  );
  check("redirect_preserva_ampersand_en_query", [
    seller.url().includes("query=Caf%C3%A9+%26+Pan") || seller.url().includes("query=Caf%C3%A9%20%26%20Pan"),
    await seller.locator(".sales-search-panel tbody tr", { hasText: fixture.products.amp.name }).count(),
  ], [true, 1]);

  // Verify totals: 3*5.90 + 1*10.00 = 27.70 -> Base = HALF_UP(27.70 / 1.18, 2) = 23.47, IGV = 4.23
  check(
    "totales_mixtos_27_70_igv_half_up",
    (await seller.locator(".sale-totals dd").allInnerTexts()).map((t) => t.trim()),
    ["S/ 23,47", "S/ 4,23", "S/ 27,70"]
  );

  // 8a. ADMIN edits p_amp sale_price: 10.00 -> 12.50 in browser
  const admin = adminSession.page;
  await admin.goto(`${base}/productos/${fixture.products.amp.id}/editar/`);
  await admin.locator('[name="sale_price"]').fill("12.50");
  await clickAndNav(admin, admin.getByRole("button", { name: "Guardar cambios", exact: true }));
  check("admin_edito_precio_redirige_catalogo", admin.url(), base + "/productos/");

  // Observe seller GET /ventas/ before touching line (documents stale-price UI observation)
  await seller.goto(base + "/ventas/");
  const ampLineTextBeforeTouch = await seller.locator(".draft-line", { hasText: fixture.products.amp.name }).innerText();
  check("borrador_conserva_precio_previo_hasta_operar", ampLineTextBeforeTouch.includes("S/ 10,00 por unidad"), true);

  // Seller updates p_amp quantity 1 -> 2 in browser: receives price-change warning flash and refreshes to S/ 12,50
  const ampDraftLine = seller.locator(".draft-line", { hasText: fixture.products.amp.name });
  await ampDraftLine.locator('input[name="quantity"]').fill("2");
  await clickAndNav(seller, ampDraftLine.getByRole("button", { name: "Actualizar", exact: true }));
  const priceFlash = await seller.locator(".flash-stack").innerText();
  check("alerta_cambio_precio_en_actualizacion", [
    priceFlash.includes("El precio unitario de «Café & Pan Especial A10» se actualizó de S/ 10.00 a S/ 12.50."),
    (await seller.locator(".draft-line", { hasText: fixture.products.amp.name }).innerText()).includes("S/ 12,50 por unidad"),
    (await seller.locator(".sale-totals .total-row dd").innerText()).trim(),
  ], [true, true, "S/ 42,70"]);

  // 8b. ALMACENERO performs writeoff of 2 units on p_amp lot -> sellable drops 8 -> 6
  const wh = whSession.page;
  await wh.goto(`${base}/inventario/bajas/nueva/?lote=${fixture.products.amp.lot_id}`);
  await wh.locator('[name="quantity"]').fill("2");
  await wh.locator('[name="reason"]').selectOption("DAÑO");
  await wh.locator('[name="notes"]').fill("Merma auditoria etapa 10");
  await clickAndNav(wh, wh.getByRole("button", { name: "Confirmar baja", exact: true }));
  check("wh_baja_redirige_ok", wh.url(), base + "/inventario/bajas/nueva/");

  // Seller tries to update p_amp to 7 (> 6) -> fails; then updates to 6 -> succeeds
  await ampDraftLine.locator('input[name="quantity"]').fill("7");
  await clickAndNav(seller, ampDraftLine.getByRole("button", { name: "Actualizar", exact: true }));
  check("post_baja_almacenero_rechaza_7", [
    (await seller.locator(".flash-stack .alert-error").innerText()).includes("La cantidad supera las existencias vendibles disponibles."),
    await ampDraftLine.locator('input[name="quantity"]').inputValue(),
  ], [true, "2"]);

  await ampDraftLine.locator('input[name="quantity"]').fill("6");
  await clickAndNav(seller, ampDraftLine.getByRole("button", { name: "Actualizar", exact: true }));
  check("post_baja_almacenero_acepta_6", await ampDraftLine.locator('input[name="quantity"]').inputValue(), "6");
  await shot(seller, "04-cross-role-precio-y-stock.png");

  // 8c. ADMIN disables p_amp -> excluded from search & update fails cleanly -> ADMIN re-enables p_amp
  await admin.goto(base + "/productos/");
  await clickAndNav(
    admin,
    admin.locator(".catalog-products tbody tr", { hasText: fixture.products.amp.name }).getByRole("button", { name: "Deshabilitar", exact: true })
  );

  await seller.locator('[name="query"]').fill("Café & Pan");
  await clickAndNav(seller, seller.getByRole("button", { name: "Buscar", exact: true }));
  check("producto_deshabilitado_excluido_busqueda", (await seller.locator(".sales-search-panel").innerText()).includes("No se encontraron productos con existencias vendibles."), true);

  await ampDraftLine.locator('input[name="quantity"]').fill("5");
  await clickAndNav(seller, ampDraftLine.getByRole("button", { name: "Actualizar", exact: true }));
  check("producto_deshabilitado_bloquea_update_borrador", [
    (await seller.locator(".flash-stack .alert-error").innerText()).includes("El producto seleccionado no está disponible para la venta."),
    await ampDraftLine.locator('input[name="quantity"]').inputValue(),
  ], [true, "6"]);

  await clickAndNav(
    admin,
    admin.locator(".catalog-products tbody tr", { hasText: fixture.products.amp.name }).getByRole("button", { name: "Habilitar", exact: true })
  );

  // 8d. ADMIN deactivates category toggle -> confirm page warns about 1 active draft -> seller update blocked -> ADMIN reactivates
  await admin.goto(base + "/productos/categorias/");
  await clickAndNav(
    admin,
    admin.locator("tbody tr", { hasText: fixture.categories.toggle.name }).getByRole("button", { name: "Desactivar", exact: true })
  );
  check("confirm_categoria_muestra_1_borrador_activo", (await admin.locator("dl.summary-list").innerText()).includes("1"), true);
  await clickAndNav(admin, admin.getByRole("button", { name: "Confirmar desactivación", exact: true }));

  await ampDraftLine.locator('input[name="quantity"]').fill("4");
  await clickAndNav(seller, ampDraftLine.getByRole("button", { name: "Actualizar", exact: true }));
  check("categoria_desactivada_bloquea_update_borrador", (await seller.locator(".flash-stack .alert-error").innerText()).includes("El producto seleccionado no está disponible para la venta."), true);

  await clickAndNav(
    admin,
    admin.locator("tbody tr", { hasText: fixture.categories.toggle.name }).getByRole("button", { name: "Activar", exact: true })
  );
  await clickAndNav(admin, admin.getByRole("button", { name: "Confirmar activación", exact: true }));

  // 9. Two tabs concurrency in Chrome: Tab 2 removes p_amp, stale Tab 1 tries updating p_amp
  const sellerTab2 = await sellerSession.ctx.newPage();
  sellerTab2.on("pageerror", (err) => report.page_errors.push({ role: "sellerTab2", message: err.message }));
  await sellerTab2.goto(base + "/ventas/");
  await seller.goto(base + "/ventas/"); // ensure Tab 1 has p_amp update button rendered fresh

  await clickAndNav(
    sellerTab2,
    sellerTab2.locator(".draft-line", { hasText: fixture.products.amp.name }).getByRole("button", { name: "Quitar", exact: true })
  );
  check("tab2_quita_amp_conserva_gtin", [
    await sellerTab2.locator(".draft-line").count(),
    await sellerTab2.locator(".draft-line", { hasText: fixture.products.gtin.name }).count(),
  ], [1, 1]);

  // Stale Tab 1 submits update on removed p_amp line
  await seller.locator(".draft-line", { hasText: fixture.products.amp.name }).locator('input[name="quantity"]').fill("3");
  await clickAndNav(
    seller,
    seller.locator(".draft-line", { hasText: fixture.products.amp.name }).getByRole("button", { name: "Actualizar", exact: true })
  );
  check("tab1_stale_update_linea_quitada_alerta", [
    (await seller.locator(".flash-stack .alert-error").innerText()).includes("La línea de venta ya no está disponible."),
    await seller.locator(".draft-line").count(),
  ], [true, 1]);

  // 10. RN-30: Cash shift close blocked while draft has lines; Tab 2 removes last line -> draft discarded
  await seller.goto(base + "/caja/cerrar/");
  check("rn30_cash_close_avisa_borrador_activo", (await seller.locator("main").innerText()).includes("Tienes una venta en preparación activa."), true);
  await seller.locator('[name="counted_amount"]').fill("100.00");
  await clickAndNav(seller, seller.getByRole("button", { name: "Cerrar turno", exact: true }));
  check("rn30_cash_close_bloqueado_en_servidor", [
    seller.url(),
    (await seller.locator("main .alert-error").innerText()).includes("venta en preparación"),
  ], [base + "/caja/cerrar/", true]);

  // Tab 2 removes last line (p_gtin) -> auto-discards draft
  await clickAndNav(
    sellerTab2,
    sellerTab2.locator(".draft-line", { hasText: fixture.products.gtin.name }).getByRole("button", { name: "Quitar", exact: true })
  );
  check("quitar_ultima_linea_descarta_borrador", (await sellerTab2.locator(".sales-summary-panel").innerText()).includes("Aún no agregaste productos a la venta."), true);
  await sellerTab2.close();

  // 11. Manual "Descartar venta" button + flash success
  await seller.goto(base + "/ventas/");
  await seller.locator('[name="query"]').fill("ATÚN");
  await clickAndNav(seller, seller.getByRole("button", { name: "Buscar", exact: true }));
  await clickAndNav(
    seller,
    seller.locator(".sales-search-panel tbody tr", { hasText: fixture.products.gtin.name }).getByRole("button", { name: "Agregar", exact: true })
  );

  await clickAndNav(seller, seller.getByRole("button", { name: "Descartar venta", exact: true }));
  check("descarte_manual_exito", [
    (await seller.locator(".flash-stack .alert-success").innerText()).includes("La venta en preparación fue descartada."),
    (await seller.locator(".sales-summary-panel").innerText()).includes("Aún no agregaste productos a la venta."),
  ], [true, true]);
  await shot(seller, "05-descarte-manual.png");

  // 12. Re-add p_gtin (qty=2), test /salir/ cancel (preserves draft) then confirm (discards draft, keeps shift & lots, revokes session & blocks Back)
  await seller.locator('[name="query"]').fill("ATÚN");
  await clickAndNav(seller, seller.getByRole("button", { name: "Buscar", exact: true }));
  await seller.locator(".sales-search-panel tbody tr", { hasText: fixture.products.gtin.name }).locator('input[name="quantity"]').fill("2");
  await clickAndNav(
    seller,
    seller.locator(".sales-search-panel tbody tr", { hasText: fixture.products.gtin.name }).getByRole("button", { name: "Agregar", exact: true })
  );

  await clickAndNav(seller, seller.locator("a.sidebar-logout"));
  check("salir_advierte_descarte_borrador", (await seller.locator("main").innerText()).includes("La venta en preparación se descartará."), true);
  await clickAndNav(seller, seller.getByRole("link", { name: "Cancelar", exact: true }));

  await seller.goto(base + "/ventas/");
  check("cancelar_salir_conserva_borrador", await seller.locator(".draft-line", { hasText: fixture.products.gtin.name }).locator('input[name="quantity"]').inputValue(), "2");

  // Confirm logout
  await clickAndNav(seller, seller.locator("a.sidebar-logout"));
  await clickAndNav(seller, seller.getByRole("button", { name: "Cerrar sesión", exact: true }));
  check("logout_redirige_inicio", seller.url(), base + "/");
  await seller.goBack();
  await seller.waitForLoadState("load");
  check("logout_back_bloqueado", seller.url().startsWith(base + "/?next=") || seller.url() === base + "/" || seller.url().includes("/salir/"), true);

  await seller.goto(base + "/ventas/");
  check("post_logout_ventas_redirige_login", seller.url(), `${base}/?next=/ventas/`);

  // Verify Cache-Control: no-store header across Stage 10 views while authenticated as admin/logout? Wait - check before closing admin?
  // Note: admin GET /ventas/ returned 403, so check @never_cache via probe or reopen seller? Let's quickly verify via admin GET /salir/ no-store or fresh seller login not needed if we inspect final ORM. Let's quickly log in seller? Better yet check during probe/s2? Actually let's log seller back in briefly just to inspect Cache-Control header on /ventas/ or check it before logout? We already logged out seller, let's log seller2 (wait closed) - let's log seller in quick 4 lines to check never_cache header cleanly!
  const verifyCacheSession = await loginContext(browser, "seller");
  const vGet = await verifyCacheSession.page.request.get(base + "/ventas/", { maxRedirects: 0 });
  check("never_cache_ventas_no_store", (vGet.headers()["cache-control"] || "").includes("no-store"), true);
  await verifyCacheSession.ctx.close();

  // 13. Final ORM invariants: 0 sales, only 1 writeoff (p_amp lot 8 -> 6), shift still OPEN at S/ 100.00, all lots otherwise untouched, 0 active drafts
  const finalOrm = state();
  check("cero_ventas_creadas", finalOrm.sales.length - initialOrm.sales.length, 0);
  check("solo_1_writeoff_intencional", finalOrm.writeoffs.length - initialOrm.writeoffs.length, 1);
  check("caja_sin_movimientos_ni_cierres", [
    finalOrm.shifts.length,
    finalOrm.shifts[0].status,
    finalOrm.shifts[0].opening_amount,
    finalOrm.closes.length,
  ], [1, "OPEN", "100.00", 0]);
  check("cero_borradores_activos_y_cero_lineas_tras_salir", [
    finalOrm.drafts.filter((d) => d.status === "ACTIVE").length,
    finalOrm.draft_lines.length,
    finalOrm.drafts.every((d) => d.status === "DISCARDED" && Boolean(d.discarded_at)),
  ], [0, 0, true]);

  const initialLots = Object.fromEntries(initialOrm.lots.map((l) => [l.id, l.available_quantity]));
  const lotDiffs = finalOrm.lots
    .filter((l) => l.available_quantity !== initialLots[l.id])
    .map((l) => ({ id: l.id, before: initialLots[l.id], after: l.available_quantity }));
  check("lotes_solo_cambiado_por_baja_almacenero", lotDiffs, [
    { id: fixture.products.amp.lot_id, before: 8, after: 6 },
  ]);

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
