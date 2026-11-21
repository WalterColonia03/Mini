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

const out = process.env.AUDIT11_OUT;
const run = process.env.AUDIT11_RUN_DIR;
const base = "http://127.0.0.1:" + process.env.AUDIT11_PORT;
const accounts = JSON.parse(fs.readFileSync(path.join(run, ".credentials.json"), "utf8"));
const fixture = JSON.parse(fs.readFileSync(path.join(out, "fixture.json"), "utf8"));

const report = {
  checks: [],
  layout_metrics: {},
  cache_headers: {},
  page_errors: [],
  screenshots: [],
  input: "Chrome 1366x900 es-PE Stage 11 audit (checkout, discounts, IGV HALF_UP, FEFO, double-submit, inter-role price change, receipt wrap, shift history, cash close, admin/warehouse integration)",
};

function check(id, actual, expected) {
  assert.deepEqual(actual, expected, id);
  report.checks.push(id);
}

function state() {
  return JSON.parse(
    execFileSync(process.env.AUDIT11_PYTHON, [path.join(__dirname, "audit11_run.py"), "snapshot"], {
      encoding: "utf8",
    })
  );
}

async function getCsrf(ctx) {
  const cookies = await ctx.cookies();
  const cookie = cookies.find((c) => c.name === "audit11_csrftoken");
  assert.ok(cookie && cookie.value, "audit11_csrftoken missing");
  return cookie.value;
}

async function loginContext(browser, role, viewport = { width: 1366, height: 900 }) {
  const ctx = await browser.newContext({ locale: "es-PE", viewport });
  const page = await ctx.newPage();
  page.on("pageerror", (err) => report.page_errors.push({ role, message: err.message }));
  await page.goto(base);
  await page.locator("[name=email]").fill(accounts[role].email);
  await page.locator("[name=password]").fill(accounts[role].password);
  await Promise.all([
    page.waitForURL(base + "/inicio/"),
    page.locator('button[type="submit"]').click(),
  ]);
  return { ctx, page };
}

async function shot(page, filename) {
  const target = path.join(out, filename);
  await page.screenshot({ path: target, fullPage: true });
  report.screenshots.push(filename);
}

async function addProductInDraft(page, barcode, quantity) {
  await page.goto(base + "/ventas/?query=" + encodeURIComponent(barcode));
  const row = page.locator("tbody tr").filter({ hasText: barcode }).first();
  await row.locator('input[name="quantity"]').fill(String(quantity));
  await Promise.all([
    page.waitForLoadState("load"),
    row.locator('button[type="submit"]').click(),
  ]);
}

async function measureCheckoutLayout(page) {
  return page.evaluate(() => {
    const docScrollWidth = document.documentElement.scrollWidth;
    const windowInnerWidth = window.innerWidth;
    const aside = document.querySelector(".info-panel");
    const formPanel = document.querySelector(".form-panel");
    const ar = aside ? aside.getBoundingClientRect() : null;
    const fr = formPanel ? formPanel.getBoundingClientRect() : null;
    return {
      docScrollWidth,
      windowInnerWidth,
      docOk: docScrollWidth <= windowInnerWidth,
      asideFits: ar ? ar.right <= windowInnerWidth + 1 && aside.scrollWidth <= aside.clientWidth + 1 : true,
      asideScrollW: aside ? aside.scrollWidth : null,
      asideClientW: aside ? aside.clientWidth : null,
      formFits: fr ? fr.right <= windowInnerWidth + 1 : true,
    };
  });
}

async function measureReceiptLayout(page) {
  return page.evaluate(() => {
    const docScrollWidth = document.documentElement.scrollWidth;
    const windowInnerWidth = window.innerWidth;
    const wrap = document.querySelector("#constancia-interna .table-wrap");
    const ths = wrap
      ? Array.from(wrap.querySelectorAll("th")).map((th) => {
          const r = th.getBoundingClientRect();
          const wr = wrap.getBoundingClientRect();
          return {
            text: th.textContent.trim(),
            clipped: r.right > wr.right + 1 || r.right > windowInnerWidth + 1,
          };
        })
      : [];
    const aligns = Array.from(document.querySelectorAll("#constancia-interna thead th")).map((th) => ({
      text: th.textContent.trim(),
      textAlign: getComputedStyle(th).textAlign,
    }));
    return {
      docScrollWidth,
      windowInnerWidth,
      docOk: docScrollWidth <= windowInnerWidth,
      wrapOk: wrap ? wrap.scrollWidth <= wrap.clientWidth + 1 : true,
      wrapScrollW: wrap ? wrap.scrollWidth : null,
      wrapClientW: wrap ? wrap.clientWidth : null,
      allHeadersVisible: ths.every((t) => !t.clipped),
      aligns,
    };
  });
}

async function runAudit(browser) {
  const initialOrm = state();
  const dummyId = "00000000-0000-4000-8000-000000000001";

  // 1. Cryptographic proof & anonymous HTTP redirects
  const probeCtx = await browser.newContext({ locale: "es-PE", viewport: { width: 1366, height: 900 } });
  const probe = await probeCtx.newPage();
  const nonce = crypto.randomBytes(32).toString("hex");
  const probeRes = await probe.request.get(base, { headers: { "X-Audit11-Challenge": nonce } });
  const expectedProof = crypto
    .createHmac("sha256", fs.readFileSync(path.join(run, ".django-key")))
    .update(nonce)
    .digest("hex");
  check("aislamiento_proof", probeRes.headers()["x-audit11-proof"], expectedProof);
  check("aislamiento_run", probeRes.headers()["x-audit11-run"], path.basename(run));

  for (const url of [
    "/ventas/cobrar/",
    `/ventas/constancia/${dummyId}/`,
    "/ventas/historial/turno/",
    "/ventas/historial/",
  ]) {
    const r = await probe.request.get(base + url, { maxRedirects: 0 });
    check(`anon_get_${url}_302`, r.status(), 302);
    check(`anon_get_${url}_next`, r.headers()["location"], `/?next=${url}`);
  }
  await probeCtx.close();

  // 2. Role sessions
  const sellerSession = await loginContext(browser, "seller");
  const seller2Session = await loginContext(browser, "seller2");
  const adminSession = await loginContext(browser, "admin");
  const whSession = await loginContext(browser, "warehouse");

  // Inactive seller cannot log in
  const inactCtx = await browser.newContext({ locale: "es-PE", viewport: { width: 1366, height: 900 } });
  const inactPage = await inactCtx.newPage();
  await inactPage.goto(base);
  await inactPage.locator("[name=email]").fill(accounts.inactive_seller.email);
  await inactPage.locator("[name=password]").fill(accounts.inactive_seller.password);
  await Promise.all([
    inactPage.waitForLoadState("load"),
    inactPage.locator('button[type="submit"]').click(),
  ]);
  check("inactivo_login_bloqueado", new URL(inactPage.url()).pathname, "/");
  await inactCtx.close();

  // Role gates on Stage 11 URLs
  for (const [roleName, sess, denied] of [
    ["admin", adminSession, ["/ventas/cobrar/", "/ventas/historial/turno/"]],
    ["warehouse", whSession, ["/ventas/cobrar/", `/ventas/constancia/${dummyId}/`, "/ventas/historial/turno/", "/ventas/historial/"]],
  ]) {
    for (const url of denied) {
      const r = await sess.page.request.get(base + url, { maxRedirects: 0 });
      check(`${roleName}_get_${url}_403`, r.status(), 403);
    }
  }
  const s2Cobro = await seller2Session.page.request.get(base + "/ventas/cobrar/", { maxRedirects: 0 });
  check("seller2_sin_turno_cobrar_302", s2Cobro.status(), 302);
  check("seller2_sin_turno_cobrar_dest", s2Cobro.headers()["location"], "/ventas/");

  // 3. Suspended category product must not appear in POS search
  const sPage = sellerSession.page;
  await sPage.goto(base + "/ventas/?query=" + encodeURIComponent(fixture.products.cat_off.name));
  check("producto_categoria_inactiva_oculto", await sPage.locator("tbody tr").count(), 0);

  // 4. Checkout #1 preparation: p_tax qty 3 => subtotal S/ 10,65
  await addProductInDraft(sPage, fixture.products.tax.barcode, 3);
  await sPage.goto(base + "/ventas/cobrar/");
  const ccCheckout = (await sPage.request.get(base + "/ventas/cobrar/")).headers()["cache-control"] || "";
  report.cache_headers.checkout = ccCheckout;
  check("checkout_no_store", ccCheckout.includes("no-store") && ccCheckout.includes("no-cache"), true);

  // Tax warning & initial summary checks
  const checkoutBody = await sPage.locator("main").innerText();
  check("advertencia_tributaria_visible", checkoutBody.includes("constancia interna") && checkoutBody.includes("SUNAT"), true);
  check("resumen_inicial_subtotal", (await sPage.locator("#checkout-subtotal").innerText()).trim(), "S/ 10,65");
  check("resumen_inicial_descuento", (await sPage.locator("#checkout-discount").innerText()).trim(), "S/ 0,00");
  check("resumen_inicial_base", (await sPage.locator("#checkout-base").innerText()).trim(), "S/ 9,03");
  check("resumen_inicial_igv", (await sPage.locator("#checkout-igv").innerText()).trim(), "S/ 1,62");
  check("resumen_inicial_total", (await sPage.locator("#checkout-total").innerText()).trim(), "S/ 10,65");
  check("resumen_inicial_vuelto", (await sPage.locator("#checkout-change").innerText()).trim(), "—");

  // Live JS recalc checks
  await sPage.locator("#id_discount_amount").fill("1.00");
  check("js_recalc_descuento_valido", [
    (await sPage.locator("#checkout-discount").innerText()).trim(),
    (await sPage.locator("#checkout-base").innerText()).trim(),
    (await sPage.locator("#checkout-igv").innerText()).trim(),
    (await sPage.locator("#checkout-total").innerText()).trim(),
  ], ["- S/ 1,00", "S/ 8,18", "S/ 1,47", "S/ 9,65"]);

  await sPage.locator("#id_cash_received").fill("9.65");
  check("js_recalc_vuelto_exacto", (await sPage.locator("#checkout-change").innerText()).trim(), "S/ 0,00");

  await sPage.locator("#id_cash_received").fill("20.00");
  check("js_recalc_vuelto_excedente", (await sPage.locator("#checkout-change").innerText()).trim(), "S/ 10,35");

  await sPage.locator("#id_discount_amount").fill("10.65");
  check("js_recalc_descuento_100pct_invalido", [
    (await sPage.locator("#checkout-discount").innerText()).trim(),
    (await sPage.locator("#checkout-total").innerText()).trim(),
    (await sPage.locator("#checkout-change").innerText()).trim(),
  ], ["—", "—", "—"]);

  // Simulated browser badInput (scientific notation in number field) must render '—'
  await sPage.locator("#id_discount_amount").fill("");
  await sPage.locator("#id_discount_amount").pressSequentially("1e2");
  check("js_recalc_bad_input_disc", (await sPage.locator("#checkout-total").innerText()).trim(), "—");

  // Server rejections without touching stock/sales
  await sPage.goto(base + "/ventas/cobrar/");
  await sPage.locator("#id_discount_amount").fill("10.65");
  await sPage.locator("#id_cash_received").fill("20.00");
  await Promise.all([sPage.waitForLoadState("load"), sPage.locator('button[type="submit"]').click()]);
  check("server_rechaza_descuento_100pct", [
    new URL(sPage.url()).pathname,
    state().sales.length,
    await sPage.locator(".alert-error").count() > 0,
  ], ["/ventas/cobrar/", 0, true]);

  await sPage.locator("#id_discount_amount").fill("1.00");
  await sPage.locator("#id_cash_received").fill("9.64");
  await Promise.all([sPage.waitForLoadState("load"), sPage.locator('button[type="submit"]').click()]);
  check("server_rechaza_efectivo_insuficiente", [
    new URL(sPage.url()).pathname,
    state().sales.length,
    (await sPage.locator("#checkout-total").innerText()).trim(),
    (await sPage.locator("#checkout-discount").innerText()).trim(),
    (await sPage.locator("main").innerText()).includes("insuficiente"),
  ], ["/ventas/cobrar/", 0, "S/ 9,65", "- S/ 1,00", true]);

  // Direct authenticated HTTP POST with Arabic-Indic non-ASCII digits must return 200 form error and 0 sales
  const sellerCsrf = await getCsrf(sellerSession.ctx);
  const idemNonAscii = crypto.randomUUID();
  const hiddenSubtotal = await sPage.locator('input[name="expected_subtotal"]').inputValue();
  const hiddenSig = await sPage.locator('input[name="draft_signature"]').inputValue();
  for (const [label, formFields] of [
    ["non_ascii_disc", { cash_received: "10.00", discount_amount: "١.٠٠" }],
    ["non_ascii_cash", { cash_received: "١٠.٠٠", discount_amount: "" }],
  ]) {
    const r = await sPage.request.post(base + "/ventas/cobrar/", {
      form: {
        csrfmiddlewaretoken: sellerCsrf,
        idempotency_key: idemNonAscii,
        expected_subtotal: hiddenSubtotal,
        draft_signature: hiddenSig,
        ...formFields,
      },
      headers: { Referer: base + "/ventas/cobrar/" },
    });
    const html = await r.text();
    check(`server_rechaza_${label}`, [r.status(), html.includes("ASCII"), state().sales.length], [200, true, 0]);
  }

  // Real Checkout #1 with double-click submit protection + exact cash + discount
  await sPage.goto(base + "/ventas/cobrar/");
  let checkoutPostCount = 0;
  const reqListener = (req) => {
    if (req.method() === "POST" && new URL(req.url()).pathname === "/ventas/cobrar/") {
      checkoutPostCount += 1;
    }
  };
  sPage.on("request", reqListener);
  await sPage.locator("#id_discount_amount").fill("1.00");
  await sPage.locator("#id_cash_received").fill("9.65");
  await Promise.all([
    sPage.waitForURL(/\/ventas\/constancia\/[^/]+\//),
    sPage.locator('button[type="submit"]').dblclick(),
  ]);
  sPage.off("request", reqListener);

  const sale1Url = new URL(sPage.url()).pathname;
  const ccReceipt = (await sPage.request.get(base + sale1Url)).headers()["cache-control"] || "";
  report.cache_headers.receipt = ccReceipt;
  check("receipt_no_store", ccReceipt.includes("no-store") && ccReceipt.includes("no-cache"), true);

  let after1 = state();
  check("doble_clic_envia_1_post_y_crea_1_venta", [checkoutPostCount, after1.sales.length], [1, 1]);
  const sale1 = after1.sales[0];
  check("venta1_importes_exactos", [
    sale1.correlative,
    sale1.discount_amount,
    sale1.total_amount,
    sale1.base_amount,
    sale1.igv_amount,
    sale1.cash_received,
    sale1.change_given,
  ], ["V-00000001", "1.00", "9.65", "8.18", "1.47", "9.65", "0.00"]);
  await shot(sPage, "post-fix-receipt-tax.png");

  // 5. Checkout #2: p_fefo (qty 6 => 27.00) + p_long (140-char name, qty 1 => 12.00) = 39.00, discount 4.00 => 35.00, cash 50.00
  await addProductInDraft(sPage, fixture.products.fefo.barcode, 6);
  await addProductInDraft(sPage, fixture.products.long.barcode, 1);
  await sPage.goto(base + "/ventas/cobrar/");
  const checkoutMetrics = await measureCheckoutLayout(sPage);
  report.layout_metrics.checkout = checkoutMetrics;
  check("layout_checkout_sin_desborde_horizontal", [
    checkoutMetrics.docOk,
    checkoutMetrics.asideFits,
    checkoutMetrics.formFits,
  ], [true, true, true]);
  await sPage.locator("#id_discount_amount").fill("4.00");
  await sPage.locator("#id_cash_received").fill("50.00");
  await shot(sPage, "post-fix-checkout.png");

  await Promise.all([
    sPage.waitForURL(/\/ventas\/constancia\/[^/]+\//),
    sPage.locator('button[type="submit"]').click(),
  ]);
  const sale2Path = new URL(sPage.url()).pathname;
  const receiptMetrics = await measureReceiptLayout(sPage);
  report.layout_metrics.receipt = receiptMetrics;
  check("layout_receipt_sin_desborde_y_alineado", [
    receiptMetrics.docOk,
    receiptMetrics.wrapOk,
    receiptMetrics.allHeadersVisible,
    receiptMetrics.aligns.slice(2).every((a) => a.textAlign === "right"),
  ], [true, true, true, true]);
  await shot(sPage, "post-fix-receipt.png");

  const after2 = state();
  check("venta2_fefo_y_lotes_vencidos_intactos", Object.fromEntries(
    after2.lots
      .filter((l) => l.product_id === fixture.products.fefo.id)
      .map((l) => [l.number, l.available_quantity])
  ), {
    "FEFO-VENC-PAST": 5,
    "FEFO-VENC-HOY": 6,
    "FEFO-ZERO-EXP": 0,
    "FEFO-TIE-B": 0,
    "FEFO-TIE-A": 0,
    "FEFO-FAR": 9,
  });

  // Cross-seller 404 on another seller's receipt
  const s2Receipt = await seller2Session.page.request.get(base + sale2Path, { maxRedirects: 0 });
  check("otro_vendedor_constancia_404", s2Receipt.status(), 404);

  // 5b. Inter-screen stock collision: Seller prepares 15 u. of p_tax (17 available),
  // Warehouse writes off 5 u. -> 12 remain -> checkout must abort atomically without creating a sale.
  await addProductInDraft(sPage, fixture.products.tax.barcode, 15);
  await sPage.goto(base + "/ventas/cobrar/");
  check("stock_antes_merma_subtotal", (await sPage.locator("#checkout-subtotal").innerText()).trim(), "S/ 53,25");

  await whSession.page.goto(base + "/inventario/bajas/nueva/");
  const taxLotRow = whSession.page.locator("tbody tr").filter({ hasText: "TAX-01" }).first();
  await Promise.all([
    whSession.page.waitForURL(/\/inventario\/bajas\/nueva\/\?lote=/),
    taxLotRow.locator("a", { hasText: "Dar de baja" }).click(),
  ]);
  await whSession.page.locator('input[name="quantity"]').fill("5");
  await whSession.page.locator('select[name="reason"]').selectOption("DAÑO");
  await whSession.page.locator('textarea[name="notes"]').fill("Rotura auditoria etapa 11");
  await Promise.all([
    whSession.page.waitForLoadState("load"),
    whSession.page.locator('button[type="submit"]').click(),
  ]);

  await sPage.locator("#id_cash_received").fill("60.00");
  await Promise.all([
    sPage.waitForLoadState("load"),
    sPage.locator('button[type="submit"]').click(),
  ]);
  const stockErrText = await sPage.locator("main").innerText();
  const afterStockAbort = state();
  check("colision_stock_rechaza_atomico", [
    new URL(sPage.url()).pathname,
    afterStockAbort.sales.length,
    afterStockAbort.lots.find((l) => l.number === "TAX-01").available_quantity,
    stockErrText.includes("Stock insuficiente") && stockErrText.includes("Disponible: 12, solicitado: 15"),
  ], ["/ventas/cobrar/", 2, 12, true]);

  await sPage.goto(base + "/ventas/");
  await Promise.all([
    sPage.waitForLoadState("load"),
    sPage.locator('form[action="/ventas/descartar/"] button[type="submit"]').click(),
  ]);

  // 6. Inter-screen price change: Seller views checkout (10.00 * 2 = 20.00), Admin updates p_price to 15.50
  await addProductInDraft(sPage, fixture.products.price.barcode, 2);
  await sPage.goto(base + "/ventas/cobrar/");
  check("precio_antes_cambio", (await sPage.locator("#checkout-subtotal").innerText()).trim(), "S/ 20,00");

  await adminSession.page.goto(base + `/productos/${fixture.products.price.id}/editar/`);
  await adminSession.page.locator('input[name="sale_price"]').fill("15.50");
  await Promise.all([
    adminSession.page.waitForLoadState("load"),
    adminSession.page.locator('button[type="submit"]').click(),
  ]);

  // Seller clicks Confirmar on stale checkout page -> must warn and refresh subtotal to 31.00 without creating a 3rd sale
  await sPage.locator("#id_cash_received").fill("35.00");
  await Promise.all([
    sPage.waitForLoadState("load"),
    sPage.locator('button[type="submit"]').click(),
  ]);
  check("colision_precio_alerta_y_actualiza_sin_cobrar", [
    new URL(sPage.url()).pathname,
    state().sales.length,
    (await sPage.locator("#checkout-subtotal").innerText()).trim(),
    (await sPage.locator("main").innerText()).includes("cambió de S/ 10.00 a S/ 15.50"),
  ], ["/ventas/cobrar/", 2, "S/ 31,00", true]);

  // Now Seller confirms with updated review
  await sPage.locator("#id_cash_received").fill("35.00");
  await Promise.all([
    sPage.waitForURL(/\/ventas\/constancia\/[^/]+\//),
    sPage.locator('button[type="submit"]').click(),
  ]);
  const sale3Url = new URL(sPage.url()).pathname;

  // 7. Seller shift history + Cash shift closure (100.00 opening + 9.65 + 35.00 + 31.00 = 175.65)
  await sPage.goto(base + "/ventas/historial/turno/");
  const ccShiftHist = (await sPage.request.get(base + "/ventas/historial/turno/")).headers()["cache-control"] || "";
  report.cache_headers.shift_history = ccShiftHist;
  const shiftHistText = await sPage.locator("main").innerText();
  check("historial_turno_muestra_3_ventas_y_descuento", [
    ccShiftHist.includes("no-store"),
    shiftHistText.includes("V-00000001"),
    shiftHistText.includes("V-00000002"),
    shiftHistText.includes("V-00000003"),
    shiftHistText.includes("75,65"),
    shiftHistText.includes("5,00"),
  ], [true, true, true, true, true, true]);
  await shot(sPage, "post-fix-shift-history.png");

  await sPage.goto(base + "/caja/cerrar/");
  await sPage.locator('input[name="counted_amount"]').fill("175.65");
  await Promise.all([
    sPage.waitForURL(/\/caja\/turnos\/[^/]+\/cerrado\//),
    sPage.locator('button[type="submit"]').click(),
  ]);
  const closedText = await sPage.locator("main").innerText();
  check("cierre_caja_cuadra_con_ventas_descontadas", [
    closedText.includes("175,65"),
    closedText.includes("0,00"),
  ], [true, true]);
  await shot(sPage, "post-fix-cash-close.png");

  // Logout & browser Back button check (no-store must redirect to login)
  await sPage.goto(base + "/salir/");
  await Promise.all([
    sPage.waitForURL(base + "/"),
    sPage.locator('form[action="/salir/"] button[type="submit"], main button[type="submit"]').first().click(),
  ]);
  await sPage.goBack({ waitUntil: "load" });
  check("back_post_logout_redirige_login", new URL(sPage.url()).pathname, "/");

  // 8. Admin downstream check: dashboard, catalog name change, history, and immutable historical receipt
  const aPage = adminSession.page;
  await aPage.goto(base + "/inicio/");
  const adminDashText = await aPage.locator("main").innerText();
  check("admin_dashboard_refleja_ventas_netas_y_descuentos", [
    adminDashText.includes("75,65"),
    adminDashText.includes("5,00"),
  ], [true, true]);
  await shot(aPage, "post-fix-admin-dashboard.png");

  await aPage.goto(base + `/productos/${fixture.products.price.id}/editar/`);
  await aPage.locator('input[name="name"]').fill("Sardina Nombre Modificado PostVenta 11");
  await aPage.locator('input[name="sale_price"]').fill("22.00");
  await Promise.all([
    aPage.waitForLoadState("load"),
    aPage.locator('button[type="submit"]').click(),
  ]);

  const ccHist = (await aPage.request.get(base + "/ventas/historial/")).headers()["cache-control"] || "";
  report.cache_headers.history = ccHist;
  await aPage.goto(base + "/ventas/historial/");
  check("admin_historial_cache_y_datos", [
    ccHist.includes("no-store"),
    (await aPage.locator("main").innerText()).includes("V-00000003"),
  ], [true, true]);

  await aPage.goto(base + sale3Url);
  const adminReceiptText = await aPage.locator("#constancia-interna").innerText();
  check("admin_constancia_inmutable_y_sin_boton_nueva_venta", [
    adminReceiptText.includes("Sardina Cambio Precio"),
    adminReceiptText.includes("15,50"),
    adminReceiptText.includes("Sardina Nombre Modificado PostVenta 11"),
    await aPage.locator('a', { hasText: "Nueva venta" }).count(),
  ], [true, true, false, 0]);

  // 9. Warehouse downstream check: stock overview and product Kardex
  const wPage = whSession.page;
  await wPage.goto(base + "/inventario/stock/");
  const stockText = await wPage.locator("main").innerText();
  check("almacenero_stock_descontado_visible", [
    stockText.includes(fixture.products.tax.name),
    stockText.includes(fixture.products.fefo.name),
  ], [true, true]);
  await shot(wPage, "post-fix-warehouse-stock.png");

  await wPage.goto(base + `/inventario/productos/${fixture.products.fefo.id}/movimientos/`);
  const kardexText = await wPage.locator("main").innerText();
  check("almacenero_kardex_registra_venta", [
    kardexText.includes("V-00000002"),
    kardexText.includes("-6"),
  ], [true, true]);
  await shot(wPage, "post-fix-kardex.png");

  // 10. Final ORM consistency check
  const finalOrm = state();
  const activeDraftIds = new Set(finalOrm.drafts.filter((d) => d.status === "ACTIVE").map((d) => d.id));
  const activeDraftLines = finalOrm.draft_lines.filter((l) => activeDraftIds.has(l.draft_id)).length;
  check("orm_final_resumen", [
    finalOrm.sales.length - initialOrm.sales.length,
    finalOrm.counter[0].next_value,
    finalOrm.shifts[0].status,
    finalOrm.closes[0].expected_amount,
    finalOrm.closes[0].difference,
    activeDraftIds.size,
    activeDraftLines,
    finalOrm.lots.find((l) => l.number === "TAX-01").available_quantity,
  ], [3, 4, "CLOSED", "175.65", "0.00", 0, 0, 12]);
  check("cero_page_errors", report.page_errors.length, 0);

  await sellerSession.ctx.close();
  await seller2Session.ctx.close();
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
    report.stack = error.stack;
    process.exitCode = 1;
  } finally {
    fs.writeFileSync(path.join(out, "browser.json"), JSON.stringify(report, null, 2), "utf8");
    await browser.close();
  }
})();
