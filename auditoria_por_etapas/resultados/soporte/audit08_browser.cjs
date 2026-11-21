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

const out = process.env.AUDIT08_OUT;
const run = process.env.AUDIT08_RUN_DIR;
const base = "http://127.0.0.1:" + process.env.AUDIT08_PORT;
const accounts = JSON.parse(fs.readFileSync(path.join(run, ".credentials.json"), "utf8"));
const fixture = JSON.parse(fs.readFileSync(path.join(out, "fixture.json"), "utf8"));

const report = {
  checks: [],
  layout_metrics: {},
  console_errors: [],
  page_errors: [],
  server_5xx: [],
  screenshots: [],
  input: "Chrome 1366x900 Stage 08 audit (writeoffs, physical adjustments, product movements, cross-role POS sync)",
};

function check(id, actual, expected) {
  assert.deepEqual(actual, expected, id);
  report.checks.push(id);
}

function state() {
  return JSON.parse(
    execFileSync(process.env.AUDIT08_PYTHON, [path.join(__dirname, "audit08_run.py"), "snapshot"], {
      encoding: "utf8",
    })
  );
}

async function loginContext(browser, role) {
  const ctx = await browser.newContext({ locale: "es-PE", viewport: { width: 1366, height: 900 } });
  const page = await ctx.newPage();
  page.on("pageerror", (err) => report.page_errors.push({ role, message: err.message }));
  page.on("console", (msg) => {
    if (msg.type() === "error") {
      report.console_errors.push({ role, text: msg.text() });
    }
  });
  page.on("response", (resp) => {
    if (resp.status() >= 500) {
      report.server_5xx.push({ role, url: resp.url(), status: resp.status() });
    }
  });
  await page.goto(base);
  await page.locator("[name=email]").fill(accounts[role].email);
  await page.locator("[name=password]").fill(accounts[role].password);
  await page.locator('button[type="submit"]').click();
  await page.waitForURL(base + "/inicio/");
  return { ctx, page };
}

async function measureOverflow(page, label) {
  const metrics = await page.evaluate(() => {
    const docScrollW = document.documentElement.scrollWidth;
    const winW = window.innerWidth;
    const mainEl = document.querySelector("main");
    const mainRect = mainEl ? mainEl.getBoundingClientRect() : null;
    const alertsFit = Array.from(document.querySelectorAll(".alert")).every((el) => {
      const r = el.getBoundingClientRect();
      return r.right <= winW + 2 && el.scrollWidth <= el.clientWidth + 2;
    });
    const tableContainers = Array.from(document.querySelectorAll(".table-responsive, .table-wrap"));
    const tablesFit = tableContainers.every((el) => el.scrollWidth <= el.clientWidth + 2);
    return {
      docScrollW,
      winW,
      docOk: docScrollW <= winW,
      mainFits: !mainRect || mainRect.right <= winW + 2,
      alertsFit,
      tablesFit,
    };
  });
  report.layout_metrics[label] = metrics;
  check(
    `layout_${label}_sin_overflow`,
    [metrics.docOk, metrics.mainFits, metrics.alertsFit, metrics.tablesFit],
    [true, true, true, true]
  );
}

async function shot(page, filename) {
  const target = path.join(out, filename);
  await page.screenshot({ path: target, fullPage: true });
  report.screenshots.push(filename);
}

async function runAudit(browser) {
  const initialOrm = state();
  check("initial_writeoffs_empty", initialOrm.writeoffs.length, 0);
  check("initial_adjustments_empty", initialOrm.adjustments.length, 0);

  // 1. Cryptographic proof & anonymous redirects
  const probeCtx = await browser.newContext({ locale: "es-PE", viewport: { width: 1366, height: 900 } });
  const probe = await probeCtx.newPage();
  const nonce = crypto.randomBytes(32).toString("hex");
  const probeRes = await probe.request.get(base, { headers: { "X-Audit08-Challenge": nonce } });
  const expectedProof = crypto
    .createHmac("sha256", fs.readFileSync(path.join(run, ".django-key")))
    .update(nonce)
    .digest("hex");
  check("aislamiento_proof", probeRes.headers()["x-audit08-proof"], expectedProof);
  check("aislamiento_run", probeRes.headers()["x-audit08-run"], path.basename(run));

  for (const [tag, url] of [
    ["stock_writeoff", "/inventario/bajas/nueva/"],
    ["physical_adjustment", "/inventario/ajustes/nuevo/"],
    ["product_movements", `/inventario/productos/${fixture.products.mix.id}/movimientos/`],
  ]) {
    const r = await probe.request.get(base + url, { maxRedirects: 0 });
    check(`anonimo_${tag}_302`, r.status(), 302);
    check(`anonimo_${tag}_next`, r.headers()["location"], `/?next=${url}`);
  }
  await probeCtx.close();

  // 2. VENDEDOR denied without mutation
  const sellerCtx0 = await loginContext(browser, "seller");
  const s0 = sellerCtx0.page;
  for (const href of ["/inventario/bajas/nueva/", "/inventario/ajustes/nuevo/"]) {
    check(`vendedor_sin_nav_${href}`, await s0.locator(`#sidebar-navigation a[href="${href}"]`).count(), 0);
    const gr = await s0.request.get(base + href, { maxRedirects: 0 });
    check(`vendedor_get_${href}_403`, gr.status(), 403);
  }
  const mov403 = await s0.request.get(base + `/inventario/productos/${fixture.products.mix.id}/movimientos/`, {
    maxRedirects: 0,
  });
  check("vendedor_movements_403", mov403.status(), 403);

  const s0Cookies = await sellerCtx0.ctx.cookies();
  const s0Csrf = s0Cookies.find((c) => c.name === "audit08_csrftoken")?.value || "";
  for (const [tag, pathUrl, formData] of [
    ["writeoff", `/inventario/bajas/nueva/?lote=${fixture.lots.mix_vig.id}`, { lot_id: fixture.lots.mix_vig.id, quantity: "1", reason: "DAÑO", notes: "x" }],
    ["adjustment", `/inventario/ajustes/nuevo/?lote=${fixture.lots.mix_vig.id}`, { lot_id: fixture.lots.mix_vig.id, delta: "1", reason: "x" }],
  ]) {
    const pr = await s0.request.post(base + pathUrl, {
      form: formData,
      headers: { "X-CSRFToken": s0Csrf, Referer: base + pathUrl },
      maxRedirects: 0,
    });
    check(`vendedor_post_${tag}_403`, pr.status(), 403);
  }
  await sellerCtx0.ctx.close();

  // 3. ALMACENERO: selector, 403 adjustment, unimplemented 404 routes, expired lot rejections, empty POST, DAÑO vs VENCIMIENTO writeoff
  const whCtx = await loginContext(browser, "warehouse");
  const wh = whCtx.page;

  check("wh_403_ajuste_get", (await wh.request.get(base + "/inventario/ajustes/nuevo/", { maxRedirects: 0 })).status(), 403);
  check("wh_404_global_bajas", (await wh.request.get(base + "/inventario/bajas/", { maxRedirects: 0 })).status(), 404);
  check("wh_404_global_ajustes", (await wh.request.get(base + "/inventario/ajustes/", { maxRedirects: 0 })).status(), 404);

  await wh.locator('#sidebar-navigation a[href="/inventario/bajas/nueva/"]').click();
  await wh.waitForURL(base + "/inventario/bajas/nueva/");
  await measureOverflow(wh, "baja_selector_wh");
  await shot(wh, "01-baja-selector-almacenero.png");

  // Empty POST {} via request without & with ?lote= -> HTTP 200 (never 500)
  const whCsrf = (await whCtx.ctx.cookies()).find((c) => c.name === "audit08_csrftoken")?.value || "";
  for (const [lbl, postUrl] of [
    ["sin_lote", "/inventario/bajas/nueva/"],
    ["con_lote", `/inventario/bajas/nueva/?lote=${fixture.lots.mix_exp.id}`],
  ]) {
    const empRes = await wh.request.post(base + postUrl, {
      form: {},
      headers: { "X-CSRFToken": whCsrf, Referer: base + "/inventario/bajas/nueva/" },
    });
    check(`baja_post_vacio_${lbl}_200`, empRes.status(), 200);
    const empTxt = await empRes.text();
    check(`baja_post_vacio_${lbl}_muestra_alerta`, empTxt.includes("alert-danger"), true);
  }

  // Click Dar de baja on expired lot LOT08-VENC
  const expRow = wh.locator("table.inventory-op-table tbody tr", { hasText: fixture.lots.mix_exp.number });
  await expRow.getByRole("link", { name: "Dar de baja" }).click();
  await wh.waitForURL(base + `/inventario/bajas/nueva/?lote=${fixture.lots.mix_exp.id}`);
  await measureOverflow(wh, "baja_form_exp_wh");

  // Rejection 1: reason=DAÑO on expired lot with valid notes -> blocked without mutation
  await wh.locator('[name="quantity"]').fill("2");
  await wh.locator('[name="reason"]').selectOption("DAÑO");
  await wh.locator('[name="notes"]').fill("Envase abollado pero vencido");
  await wh.getByRole("button", { name: "Confirmar baja" }).click();
  await wh.waitForLoadState("networkidle");
  check(
    "baja_rechaza_dano_lote_vencido",
    (await wh.locator("main").innerText()).includes("El lote está vencido; el motivo debe ser «Vencimiento»."),
    true
  );
  await shot(wh, "02-baja-rechazo-vencido.png");

  const ormAfterReject = state();
  check("rechazo_vencido_sin_mutacion", ormAfterReject.writeoffs.length, 0);

  // Rejection 2: exceeding available stock (9 > 8) -> blocked without mutation
  await wh.locator('[name="quantity"]').fill("9");
  await wh.locator('[name="reason"]').selectOption("VENCIMIENTO");
  await wh.locator('[name="notes"]').fill("");
  await wh.getByRole("button", { name: "Confirmar baja" }).click();
  await wh.waitForLoadState("networkidle");
  check(
    "baja_rechaza_supera_stock",
    (await wh.locator("main").innerText()).includes("La cantidad supera las existencias disponibles del lote."),
    true
  );

  // Valid full expiration writeoff (8u VENCIMIENTO) preserving same idempotency_key from failed retry!
  await wh.locator('[name="quantity"]').fill("8");
  await wh.locator('[name="reason"]').selectOption("VENCIMIENTO");
  await wh.locator('[name="notes"]').fill("Retiro por fecha vencida.");
  await wh.getByRole("button", { name: "Confirmar baja" }).click();
  await wh.waitForURL(base + "/inventario/bajas/nueva/");
  const wo1Body = await wh.locator("main").innerText();
  check("baja_vencida_exitosa_B1", wo1Body.includes("Baja B-00000001 registrada correctamente."), true);
  check("baja_vencida_lote_agotado_desaparece_lista", !wo1Body.includes(fixture.lots.mix_exp.number), true);
  await shot(wh, "03-baja-vencimiento-confirmada.png");

  // Also test @never_cache header on writeoff page
  const ncWo = await wh.request.get(base + "/inventario/bajas/nueva/");
  check("baja_never_cache_header", (ncWo.headers()["cache-control"] || "").includes("no-store"), true);

  // Partial write-off on LOT08-VIG (-2u DAÑO)
  const vigRow = wh.locator("table.inventory-op-table tbody tr", { hasText: fixture.lots.mix_vig.number });
  await vigRow.getByRole("link", { name: "Dar de baja" }).click();
  await wh.waitForURL(base + `/inventario/bajas/nueva/?lote=${fixture.lots.mix_vig.id}`);
  await wh.locator('[name="quantity"]').fill("2");
  await wh.locator('[name="reason"]').selectOption("DAÑO");
  await wh.locator('[name="notes"]').fill("Lata golpeada en estanteria.");
  await wh.getByRole("button", { name: "Confirmar baja" }).click();
  await wh.waitForURL(base + "/inventario/bajas/nueva/");
  check(
    "baja_dano_exitosa_B2",
    (await wh.locator("main").innerText()).includes("Baja B-00000002 registrada correctamente."),
    true
  );

  const ormAfterWo = state();
  check("orm_tras_bajas_qty", {
    exp: ormAfterWo.lots.find((l) => l.id === fixture.lots.mix_exp.id).available_quantity,
    vig: ormAfterWo.lots.find((l) => l.id === fixture.lots.mix_vig.id).available_quantity,
    avg: ormAfterWo.products.find((p) => p.id === fixture.products.mix.id).average_cost,
  }, { exp: 0, vig: 10, avg: "4.0000" });

  await whCtx.ctx.close();

  // 4. ADMIN: Physical adjustments (+delta, -delta, rejections, long wrap) + Kardex inspection + isolated barcode check
  const admCtx = await loginContext(browser, "admin");
  const adm = admCtx.page;

  // Empty POST {} to physical adjustment without & with ?lote= -> HTTP 200 (never 500)
  const admCsrf = (await admCtx.ctx.cookies()).find((c) => c.name === "audit08_csrftoken")?.value || "";
  for (const [lbl, postUrl] of [
    ["sin_lote", "/inventario/ajustes/nuevo/"],
    ["con_lote", `/inventario/ajustes/nuevo/?lote=${fixture.lots.mix_vig.id}`],
  ]) {
    const empAdj = await adm.request.post(base + postUrl, {
      form: {},
      headers: { "X-CSRFToken": admCsrf, Referer: base + "/inventario/ajustes/nuevo/" },
    });
    check(`ajuste_post_vacio_${lbl}_200`, empAdj.status(), 200);
    check(`ajuste_post_vacio_${lbl}_alerta`, (await empAdj.text()).includes("alert-danger"), true);
  }

  await adm.locator('#sidebar-navigation a[href="/inventario/ajustes/nuevo/"]').click();
  await adm.waitForURL(base + "/inventario/ajustes/nuevo/");
  await measureOverflow(adm, "ajuste_selector_admin");
  await shot(adm, "04-ajuste-selector-admin.png");

  // Click Ajustar on LOT08-VIG
  const adjVigRow = adm.locator("table.inventory-op-table tbody tr", { hasText: fixture.lots.mix_vig.number });
  await adjVigRow.getByRole("link", { name: "Ajustar" }).click();
  await adm.waitForURL(base + `/inventario/ajustes/nuevo/?lote=${fixture.lots.mix_vig.id}`);

  // Rejection: delta=0
  await adm.locator('[name="delta"]').fill("0");
  await adm.locator('[name="reason"]').fill("Cero");
  await adm.getByRole("button", { name: "Confirmar ajuste" }).click();
  await adm.waitForLoadState("networkidle");
  check("ajuste_rechaza_cero", (await adm.locator("main").innerText()).includes("El ajuste no puede ser cero."), true);

  // Rejection: negative exceeding available stock (-15 > 10)
  await adm.locator('[name="delta"]').fill("-15");
  await adm.locator('[name="reason"]').fill("Faltante exagerado");
  await adm.getByRole("button", { name: "Confirmar ajuste" }).click();
  await adm.waitForLoadState("networkidle");
  check(
    "ajuste_rechaza_negativo_exceso",
    (await adm.locator("main").innerText()).includes("El ajuste negativo supera las existencias disponibles del lote."),
    true
  );
  await shot(adm, "05-ajuste-rechazo-admin.png");

  // Positive adjustment +5 (testing explicit +5 input in HTML number field / text)
  await adm.locator('[name="delta"]').fill("+5");
  await adm.locator('[name="reason"]').fill("Conteo físico halló 5 cajas adicionales.");
  await adm.getByRole("button", { name: "Confirmar ajuste" }).click();
  await adm.waitForURL(base + "/inventario/ajustes/nuevo/");
  check(
    "ajuste_positivo_exitoso",
    (await adm.locator("main").innerText()).includes("Ajuste físico registrado correctamente."),
    true
  );

  // Long product/lot negative adjustment (-3) & visual overflow check
  const adjLongRow = adm.locator("table.inventory-op-table tbody tr", { hasText: fixture.lots.long.number });
  await adjLongRow.getByRole("link", { name: "Ajustar" }).click();
  await adm.waitForURL(base + `/inventario/ajustes/nuevo/?lote=${fixture.lots.long.id}`);
  await measureOverflow(adm, "ajuste_form_texto_largo");
  await shot(adm, "06-ajuste-formulario-texto-largo.png");

  await adm.locator('[name="delta"]').fill("-3");
  await adm.locator('[name="reason"]').fill(
    "FaltanteDetectadoEnConteoFisicoDeAnaquelSinEspaciosMuyExtensoParaValidarEnvolturaEnKardexAudit08."
  );
  await adm.getByRole("button", { name: "Confirmar ajuste" }).click();
  await adm.waitForURL(base + "/inventario/ajustes/nuevo/");

  const ormAfterAdj = state();
  const lotVigAfterAdj = ormAfterAdj.lots.find((l) => l.id === fixture.lots.mix_vig.id);
  const lotLongAfterAdj = ormAfterAdj.lots.find((l) => l.id === fixture.lots.long.id);
  check("ajuste_pos_actualiza_initial_y_available", [lotVigAfterAdj.initial_quantity, lotVigAfterAdj.available_quantity], [17, 15]);
  check("ajuste_neg_mantiene_initial_baja_available", [lotLongAfterAdj.initial_quantity, lotLongAfterAdj.available_quantity], [15, 12]);

  // Verify VENDEDOR POS sees updated sellable=15 on mix and executes checkout
  const sellerCtx1 = await loginContext(browser, "seller");
  const s1 = sellerCtx1.page;
  await s1.goto(base + "/ventas/");
  await s1.locator("[name=query]").fill("Leche Evaporada Audit08");
  await s1.getByRole("button", { name: "Buscar", exact: true }).click();
  const posMixRow = s1.locator(".sales-search-panel tbody tr", { hasText: fixture.products.mix.name });
  check("pos_muestra_stock_actualizado_15", (await posMixRow.innerText()).includes("15"), true);
  await posMixRow.locator('[name="quantity"]').fill("2");
  await posMixRow.getByRole("button", { name: "Agregar", exact: true }).click();
  await s1.waitForLoadState("networkidle");
  await s1.getByRole("link", { name: /Cobrar venta/ }).click();
  await s1.waitForURL(base + "/ventas/cobrar/");
  await s1.locator('[name="cash_received"]').fill("20.00");
  await s1.getByRole("button", { name: "Confirmar cobro" }).click();
  await s1.waitForLoadState("networkidle");
  const posReceiptText = await s1.locator("main").innerText();
  check("pos_venta_confirmada", posReceiptText.includes("V-00000002"), true);
  await sellerCtx1.ctx.close();

  // Navigate to Inventario -> Ver movimientos for p_mix, p_long, p_reused_bc
  await adm.locator('#sidebar-navigation a[href="/inventario/stock/"]').click();
  await adm.waitForURL(base + "/inventario/stock/");
  await adm
    .locator(".stock-overview-table tbody tr", { hasText: fixture.products.mix.name })
    .getByRole("link", { name: "Ver movimientos" })
    .click();
  await adm.waitForURL(base + `/inventario/productos/${fixture.products.mix.id}/movimientos/`);
  await measureOverflow(adm, "kardex_mix_admin");

  const mixKardexText = await adm.locator("main").innerText();
  check("kardex_mix_stock_actualizado_13", mixKardexText.toLowerCase().includes("stock físico actual: 13 unid. · stock vigente: 13 unid."), true);
  check("kardex_mix_contiene_venta_vendedor", mixKardexText.includes("Venta V-00000002") && mixKardexText.includes("Carmen Vendedora08"), true);
  check("kardex_mix_contiene_bajas_con_correlativo_y_punto",
    mixKardexText.includes("Merma (Vencimiento) · B-00000001 — Lote LOT08-VENC. Retiro por fecha vencida.") &&
    mixKardexText.includes("Merma (Daño o rotura) · B-00000002 — Lote LOT08-VIG. Lata golpeada en estanteria."),
    true
  );
  check("kardex_mix_contiene_ajuste_con_punto_y_admin",
    mixKardexText.includes("Ajuste físico — Lote LOT08-VIG. Conteo físico halló 5 cajas adicionales.") &&
    mixKardexText.includes("Admin Audit08"),
    true
  );
  check("kardex_mix_sin_saldo_ni_filtros",
    (await adm.locator("table.movements-table th").count()) === 5 && (await adm.locator("main form").count()) === 0,
    true
  );
  await shot(adm, "07-kardex-mixto-admin.png");

  // Long-text Kardex check
  await adm.goto(base + `/inventario/productos/${fixture.products.long.id}/movimientos/`);
  await measureOverflow(adm, "kardex_texto_largo");
  await shot(adm, "08-kardex-texto-largo.png");

  // Reused barcode Kardex isolation check
  await adm.goto(base + `/inventario/productos/${fixture.products.reused_bc.id}/movimientos/`);
  await measureOverflow(adm, "kardex_reused_bc");
  const reusedTxt = await adm.locator("main").innerText();
  check("kardex_reused_bc_no_filtra_venta_ajena", !reusedTxt.includes(fixture.products.orig_bc.sale_correlative), true);
  await shot(adm, "09-kardex-barcode-reusado-aislado.png");

  await admCtx.ctx.close();

  const finalOrm = state();
  const mixSale2 = finalOrm.sale_lines.find((sl) => sl.sale__correlative === "V-00000002");
  check("orm_sale_line_unit_cost_4", mixSale2.unit_cost, "4.0000");
  check("orm_lot_vig_final_13", finalOrm.lots.find((l) => l.id === fixture.lots.mix_vig.id).available_quantity, 13);
}

(async () => {
  const browser = await chromium.launch({
    headless: true,
    executablePath: "C:/Program Files/Google/Chrome/Application/chrome.exe",
  });
  try {
    await runAudit(browser);
  } finally {
    await browser.close();
  }
  assert.deepEqual(report.console_errors, [], "console_errors");
  assert.deepEqual(report.page_errors, [], "page_errors");
  assert.deepEqual(report.server_5xx, [], "server_5xx");
  fs.writeFileSync(path.join(out, "browser.json"), JSON.stringify(report, null, 2), "utf8");
  console.log(JSON.stringify({ ok: true, checks: report.checks.length, screenshots: report.screenshots.length }));
})();
