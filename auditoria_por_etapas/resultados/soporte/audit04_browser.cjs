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

const out = process.env.AUDIT04_OUT;
const run = process.env.AUDIT04_RUN_DIR;
const base = "http://127.0.0.1:" + process.env.AUDIT04_PORT;
const accounts = JSON.parse(fs.readFileSync(path.join(run, ".credentials.json"), "utf8"));
const fixture = JSON.parse(fs.readFileSync(path.join(out, "fixture.json"), "utf8"));

const report = {
  checks: [],
  page_errors: [],
  screenshots: [],
  input: "Chrome 1366x900 automated Stage 04 audit across ADMIN, ALMACENERO, VENDEDOR, and anonymous contexts",
};

function check(id, actual, expected) {
  assert.deepEqual(actual, expected, id);
  report.checks.push(id);
}

function state() {
  return JSON.parse(
    execFileSync(process.env.AUDIT04_PYTHON, [path.join(__dirname, "audit04_run.py"), "snapshot"], {
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
  // 1. Challenge/Proof isolation
  const probeCtx = await browser.newContext({ locale: "es-PE", viewport: { width: 1366, height: 900 } });
  const probe = await probeCtx.newPage();
  const nonce = crypto.randomBytes(32).toString("hex");
  const probeRes = await probe.request.get(base, { headers: { "X-Audit04-Challenge": nonce } });
  const expectedProof = crypto
    .createHmac("sha256", fs.readFileSync(path.join(run, ".django-key")))
    .update(nonce)
    .digest("hex");
  check("aislamiento_proof", probeRes.headers()["x-audit04-proof"], expectedProof);
  check("aislamiento_run", probeRes.headers()["x-audit04-run"], path.basename(run));

  // 2. Anonymous redirects
  const anonList = await probe.request.get(base + "/inventario/proveedores/", { maxRedirects: 0 });
  check("anonimo_lista_redirect", anonList.status(), 302);
  check("anonimo_lista_location", anonList.headers()["location"], "/?next=/inventario/proveedores/");
  const anonCreate = await probe.request.get(base + "/inventario/proveedores/nuevo/", { maxRedirects: 0 });
  check("anonimo_crear_redirect", anonCreate.status(), 302);
  await probeCtx.close();

  // 3. VENDEDOR access denied & sidebar absence
  const sellerSession = await loginContext(browser, "seller");
  const seller = sellerSession.page;
  check(
    "vendedor_sin_menu_proveedores",
    await seller.locator('#sidebar-navigation a[href="/inventario/proveedores/"]').count(),
    0
  );
  const sellerListResp = await seller.goto(base + "/inventario/proveedores/");
  check("vendedor_lista_403", sellerListResp.status(), 403);
  const sellerCreateResp = await seller.goto(base + "/inventario/proveedores/nuevo/");
  check("vendedor_crear_403", sellerCreateResp.status(), 403);
  const sellerCookies = await sellerSession.ctx.cookies();
  const sellerCsrf = sellerCookies.find((c) => c.name === "audit04_csrftoken").value;
  const sellerPost = await seller.request.post(base + "/inventario/proveedores/nuevo/", {
    form: { csrfmiddlewaretoken: sellerCsrf, name: "Bloqueado", ruc: "20999111222" },
    maxRedirects: 0,
  });
  check("vendedor_crear_post_403", sellerPost.status(), 403);
  check("vendedor_sin_efectos", state().suppliers.length, 0);

  // 4. ADMIN initial empty list, headers, and label/search geometry
  const adminSession = await loginContext(browser, "admin");
  const admin = adminSession.page;
  adminSession.ctx.on("page", (p) => p.on("pageerror", (err) => report.page_errors.push({ role: "admin-tab", message: err.message })));

  check(
    "admin_menu_proveedores_visible",
    await admin.locator('#sidebar-navigation a[href="/inventario/proveedores/"]').count(),
    1
  );
  const navRespPromise = admin.waitForResponse((r) => r.url().endsWith("/inventario/proveedores/") && r.request().method() === "GET");
  await admin.locator('#sidebar-navigation a[href="/inventario/proveedores/"]').click();
  const navResp = await navRespPromise;
  check("admin_lista_200", navResp.status(), 200);
  check("admin_lista_never_cache", (navResp.headers()["cache-control"] || "").includes("no-store"), true);
  check("admin_lista_vacia_mensaje", await admin.locator(".alert-info").innerText(), "No hay proveedores registrados.");

  const labelBox = await admin.locator('label[for="supplier-search"]').boundingBox();
  const groupBox = await admin.locator(".input-group").boundingBox();
  check("admin_label_arriba_input_group", labelBox.y + labelBox.height <= groupBox.y + 1, true);
  const overflowInitial = await admin.evaluate(() => document.documentElement.scrollWidth > window.innerWidth);
  check("admin_lista_vacia_sin_overflow", overflowInitial, false);
  await shot(admin, "04-admin-lista-vacia.png");

  // 5. ADMIN Create Form Validations & Boundaries
  await admin.getByRole("link", { name: "+ Nuevo proveedor", exact: true }).click();
  await admin.waitForURL(base + "/inventario/proveedores/nuevo/");
  const rucHelp = await admin.locator("#id_ruc_helptext").innerText();
  check("form_distingue_formato_vs_sunat", rucHelp.includes("solo valida formato") && rucHelp.includes("SUNAT"), true);

  // Empty submit
  await admin.getByRole("button", { name: "Guardar", exact: true }).click();
  const emptyAlerts = await admin.locator('[role="alert"]').allInnerTexts();
  check("form_post_vacio_errores", emptyAlerts.some((t) => t.includes("nombre")) && emptyAlerts.some((t) => t.includes("RUC")), true);

  // Symbol name, Unicode Arabic-Indic digits RUC, symbol phone
  await admin.locator("[name=name]").fill("---");
  await admin.locator("[name=ruc]").fill("٢٠١٢٣٤٥٦٧٨٩");
  await admin.locator("[name=phone]").fill("((--))");
  await admin.getByRole("button", { name: "Guardar", exact: true }).click();
  const unicodeAlerts = await admin.locator('[role="alert"]').allInnerTexts();
  check("form_rechaza_simbolos_nombre", unicodeAlerts.some((t) => t.includes("letras o números")), true);
  check("form_rechaza_ruc_unicode", unicodeAlerts.some((t) => t.includes("exactamente 11 dígitos numéricos")), true);
  check("form_rechaza_telefono_simbolos", unicodeAlerts.some((t) => t.includes("al menos un dígito")), true);
  await shot(admin, "04-form-errores.png");

  // Valid name + short RUC -> autofocus shifts to #id_ruc
  await admin.locator("[name=name]").fill("Proveedor Autofoco");
  await admin.locator("[name=ruc]").fill("2012345678");
  await admin.locator("[name=phone]").fill("");
  await admin.getByRole("button", { name: "Guardar", exact: true }).click();
  const focusedId = await admin.evaluate(() => (document.activeElement ? document.activeElement.id : null));
  check("form_autofocus_mueve_a_ruc", focusedId, "id_ruc");

  // Create supplier #1 (collapsed spaces, leading-zero RUC, formatted phone)
  await admin.locator("[name=name]").fill("  Comercial   Andes   EIRL ");
  await admin.locator("[name=ruc]").fill("00987654321");
  await admin.locator("[name=phone]").fill(" +51  (01) 444-5555 ");
  await admin.getByRole("button", { name: "Guardar", exact: true }).click();
  await admin.waitForURL(base + "/inventario/proveedores/");
  check("crear_sup1_flash", (await admin.locator(".flash-stack").innerText()).includes("Comercial Andes EIRL"), true);
  const sup1Row = admin.locator("tbody tr", { hasText: "00987654321" });
  check("crear_sup1_normalizado", (await sup1Row.locator("td").nth(0).innerText()).trim(), "Comercial Andes EIRL");
  check("crear_sup1_telefono", (await sup1Row.locator("td").nth(2).innerText()).trim(), "+51 (01) 444-5555");

  // Create supplier #2 (exact 160-char name wrapping check, optional blank phone)
  const name160 = ("Distribuidora Mayorista Regional Sur SAC ".padEnd(156, "A") + " FIN").slice(0, 160);
  check("nombre160_longitud_exacta", name160.length, 160);
  await admin.getByRole("link", { name: "+ Nuevo proveedor", exact: true }).click();
  await admin.locator("[name=name]").fill(name160);
  await admin.locator("[name=ruc]").fill("20123456789");
  await admin.locator("[name=phone]").fill("");
  await admin.getByRole("button", { name: "Guardar", exact: true }).click();
  await admin.waitForURL(base + "/inventario/proveedores/");
  const tableNoOverflow = await admin.evaluate(() => {
    const docOk = document.documentElement.scrollWidth <= window.innerWidth;
    const wrap = document.querySelector(".table-responsive");
    const wrapOk = wrap ? wrap.scrollWidth <= wrap.clientWidth : true;
    return docOk && wrapOk;
  });
  check("tabla_160chars_sin_overflow", tableNoOverflow, true);

  // Duplicate RUC against active supplier
  await admin.getByRole("link", { name: "+ Nuevo proveedor", exact: true }).click();
  await admin.locator("[name=name]").fill("Otro Distinto");
  await admin.locator("[name=ruc]").fill("00987654321");
  await admin.getByRole("button", { name: "Guardar", exact: true }).click();
  check("duplicado_ruc_rechazado_ui", (await admin.locator('[role="alert"]').allInnerTexts()).some((t) => t.includes("El RUC ya está registrado.")), true);
  await admin.getByRole("link", { name: "Cancelar", exact: true }).click();
  await admin.waitForURL(base + "/inventario/proveedores/");

  const afterCreate = state();
  const sup1 = afterCreate.suppliers.find((s) => s.ruc === "00987654321");
  const sup2 = afterCreate.suppliers.find((s) => s.ruc === "20123456789");

  // Check HU-PROV-03 unimplemented
  check("sin_boton_editar", await admin.locator('a:has-text("Editar"), button:has-text("Editar")').count(), 0);
  const edit404 = await admin.request.get(base + `/inventario/proveedores/${sup1.id}/editar/`);
  check("hu_prov_03_editar_404", edit404.status(), 404);

  // 6. ADMIN Search & NUL query protection
  await admin.locator("#supplier-search").fill("andes");
  await admin.getByRole("button", { name: "Buscar", exact: true }).click();
  check("buscar_por_nombre_encuentra_sup1", await admin.locator("tbody tr").count(), 1);
  check("buscar_por_nombre_texto", await admin.locator("tbody tr").first().innerText(), await admin.locator("tbody tr", { hasText: "00987654321" }).innerText());

  await admin.locator("#supplier-search").fill("20123456");
  await admin.getByRole("button", { name: "Buscar", exact: true }).click();
  check("buscar_por_ruc_encuentra_sup2", await admin.locator("tbody tr").count(), 1);
  check("buscar_por_ruc_valor", (await admin.locator("tbody tr td").nth(1).innerText()).trim(), "20123456789");

  await admin.locator('a[aria-label="Limpiar búsqueda"]').click();
  check("limpiar_busqueda_restaura_2", await admin.locator("tbody tr").count(), 2);

  await admin.goto(base + "/inventario/proveedores/?q=%00");
  check("busqueda_nul_error_controlado", await admin.locator("#supplier-search-error").innerText(), "La búsqueda contiene caracteres no válidos.");
  check("busqueda_nul_sin_filas", await admin.locator("tbody tr").count(), 0);
  await admin.locator('a[aria-label="Limpiar búsqueda"]').click();
  check("limpiar_tras_nul_restaura_2", await admin.locator("tbody tr").count(), 2);

  // 7. Two-Tab Stale Toggle Concurrency & State Persistence
  const adminTab2 = await adminSession.ctx.newPage();
  await adminTab2.goto(base + "/inventario/proveedores/");
  await admin.locator("tbody tr", { hasText: "00987654321" }).getByRole("button", { name: "Desactivar", exact: true }).click();
  check("tab1_desactiva_sup1", (await admin.locator(".flash-stack").innerText()).includes("ahora está inactivo"), true);
  check("tab1_sup1_badge_inactivo", (await admin.locator("tbody tr", { hasText: "00987654321" }).innerText()).includes("Inactivo"), true);

  // Tab 2 still displays old "Desactivar" button! Clicking must NOT flip back to Activo!
  await adminTab2.locator("tbody tr", { hasText: "00987654321" }).getByRole("button", { name: "Desactivar", exact: true }).click();
  check("tab2_idempotente_ya_inactivo", (await adminTab2.locator(".flash-stack").innerText()).includes("ya se encontraba inactivo"), true);
  check("tab2_sup1_sigue_inactivo", state().suppliers.find((s) => s.ruc === "00987654321").is_active, false);
  await shot(adminTab2, "04-admin-dos-pestanas-inactivo.png");

  // Duplicate RUC against inactive supplier still rejected
  await admin.getByRole("link", { name: "+ Nuevo proveedor", exact: true }).click();
  await admin.locator("[name=name]").fill("Intento Sobre Inactivo");
  await admin.locator("[name=ruc]").fill("00987654321");
  await admin.getByRole("button", { name: "Guardar", exact: true }).click();
  check("duplicado_ruc_contra_inactivo_rechazado", (await admin.locator('[role="alert"]').allInnerTexts()).some((t) => t.includes("El RUC ya está registrado.")), true);
  await admin.getByRole("link", { name: "Cancelar", exact: true }).click();

  // 8. ALMACENERO Read-Only List & Permission Denials
  const whSession = await loginContext(browser, "warehouse");
  const wh = whSession.page;
  check(
    "almacenero_menu_proveedores_visible",
    await wh.locator('#sidebar-navigation a[href="/inventario/proveedores/"]').count(),
    1
  );
  await wh.locator('#sidebar-navigation a[href="/inventario/proveedores/"]').click();
  await wh.waitForURL(base + "/inventario/proveedores/");
  check("almacenero_ve_2_proveedores", await wh.locator("tbody tr").count(), 2);
  check("almacenero_sin_nuevo", await wh.getByRole("link", { name: "+ Nuevo proveedor", exact: true }).count(), 0);
  check("almacenero_sin_toggle_botones", await wh.locator("tbody button").count(), 0);
  await shot(wh, "04-almacenero-lista-solo-lectura.png");

  await wh.locator("#supplier-search").fill("009876");
  await wh.getByRole("button", { name: "Buscar", exact: true }).click();
  check("almacenero_busca_ruc", await wh.locator("tbody tr").count(), 1);
  check("almacenero_ve_inactivo_y_telefono", (await wh.locator("tbody tr").first().innerText()).includes("Inactivo") && (await wh.locator("tbody tr").first().innerText()).includes("+51 (01) 444-5555"), true);

  const whCreateResp = await wh.goto(base + "/inventario/proveedores/nuevo/");
  check("almacenero_crear_403", whCreateResp.status(), 403);

  const whCookies = await whSession.ctx.cookies();
  const whCsrf = whCookies.find((c) => c.name === "audit04_csrftoken").value;
  const whBefore = state();
  const whTogglePost = await wh.request.post(base + `/inventario/proveedores/${sup2.id}/estado/`, {
    form: { csrfmiddlewaretoken: whCsrf, is_active: "false" },
    maxRedirects: 0,
  });
  check("almacenero_toggle_403", whTogglePost.status(), 403);
  check("almacenero_denegado_sin_cambios", state(), whBefore);

  // Also check VENDEDOR POST toggle 403
  const sellerTogglePost = await seller.request.post(base + `/inventario/proveedores/${sup2.id}/estado/`, {
    form: { csrfmiddlewaretoken: sellerCsrf, is_active: "false" },
    maxRedirects: 0,
  });
  check("vendedor_toggle_403", sellerTogglePost.status(), 403);
  check("vendedor_toggle_sin_cambios", state(), whBefore);

  // 9. Inactive Supplier in Receipts (Initial Load & Subsequent Stock Entry) + Sentinel + History
  const whInit = await whSession.ctx.newPage();
  const whEntry = await whSession.ctx.newPage();
  await whInit.goto(base + "/inventario/carga-inicial/");
  await whEntry.goto(base + "/inventario/entrada/");

  // Active sup2 present; Inactive sup1 absent
  check("init_dropdown_excluye_sup1_inactivo", await whInit.locator(`[name=supplier] option[value="${sup1.id}"]`).count(), 0);
  check("init_dropdown_incluye_sup2_activo", await whInit.locator(`[name=supplier] option[value="${sup2.id}"]`).count(), 1);
  check("entry_dropdown_excluye_sup1_inactivo", await whEntry.locator(`[name=supplier] option[value="${sup1.id}"]`).count(), 0);
  check("entry_dropdown_incluye_sup2_activo", await whEntry.locator(`[name=supplier] option[value="${sup2.id}"]`).count(), 1);

  await whInit.locator("[name=product]").selectOption(fixture.products.initial.id);
  await whInit.locator("[name=supplier]").selectOption(sup2.id);
  await whInit.locator('[name="lots-0-number"]').fill("L-INACT-01");
  await whInit.locator('[name="lots-0-quantity"]').fill("3");
  await whInit.locator('[name="lots-0-unit_cost"]').fill("2.50");
  await whInit.locator('[name="lots-0-expiration_date"]').fill(fixture.future_date);

  await whEntry.locator("[name=product]").selectOption(fixture.products.subsequent.id);
  await whEntry.locator("[name=supplier]").selectOption(sup2.id);
  await whEntry.locator('[name="lots-0-number"]').fill("L-INACT-02");
  await whEntry.locator('[name="lots-0-quantity"]').fill("4");
  await whEntry.locator('[name="lots-0-unit_cost"]').fill("7.20");
  await whEntry.locator('[name="lots-0-expiration_date"]').fill(fixture.future_date);

  // ADMIN deactivates sup2 while both warehouse forms are open with sup2 selected
  await admin.locator("tbody tr", { hasText: "20123456789" }).getByRole("button", { name: "Desactivar", exact: true }).click();
  check("admin_desactiva_sup2", (await admin.locator("tbody tr", { hasText: "20123456789" }).innerText()).includes("Inactivo"), true);

  const beforeBlocked = state();
  await whInit.getByRole("button", { name: "Confirmar existencias", exact: true }).click();
  const initSupplierErr = await whInit.locator(".field-error").filter({ has: whInit.locator("[name=supplier]") }).innerText();
  check("init_error_identifica_sup2_inactivo", initSupplierErr.includes("20123456789") && initSupplierErr.includes("inactivo"), true);
  check("init_remueve_option_cruda", await whInit.locator(`[name=supplier] option[value="${sup2.id}"]`).count(), 0);
  check("init_sentinel_seleccionado", await whInit.locator("[name=supplier]").inputValue(), `__inactive__:${sup2.id}`);
  check("init_rechazo_atomico", state(), beforeBlocked);
  await shot(whInit, "04-almacenero-proveedor-inactivo.png");

  // Blind second click without changing supplier must stay blocked (never silently persist None!)
  await whInit.getByRole("button", { name: "Confirmar existencias", exact: true }).click();
  check("init_segundo_envio_ciego_bloqueado", await whInit.locator("[name=supplier]").inputValue(), `__inactive__:${sup2.id}`);
  check("init_segundo_envio_sin_escrituras", state(), beforeBlocked);

  // Explicit choice "Sin proveedor asignado" succeeds
  await whInit.locator("[name=supplier]").selectOption("");
  await whInit.getByRole("button", { name: "Confirmar existencias", exact: true }).click();
  await whInit.waitForURL(/\/inventario\/cargas\//);
  check(
    "init_opcional_vacio_persiste_null",
    state().lots.find((l) => l.number_normalized === "L-INACT-01").supplier_id,
    null
  );

  // Stock entry blocked when sup2 is inactive + blind second click blocked
  const beforeEntryBlocked = state();
  await whEntry.getByRole("button", { name: "Confirmar entrada", exact: true }).click();
  const entryErr = await whEntry.locator(".field-error").filter({ has: whEntry.locator("[name=supplier]") }).innerText();
  check("entry_error_identifica_sup2_inactivo", entryErr.includes("20123456789") && entryErr.includes("inactivo"), true);
  await whEntry.getByRole("button", { name: "Confirmar entrada", exact: true }).click();
  check("entry_segundo_envio_ciego_bloqueado", state(), beforeEntryBlocked);

  // Reactivate sup2 and complete stock entry
  await admin.locator("tbody tr", { hasText: "20123456789" }).getByRole("button", { name: "Activar", exact: true }).click();
  await whEntry.goto(base + "/inventario/entrada/");
  await whEntry.locator("[name=product]").selectOption(fixture.products.subsequent.id);
  await whEntry.locator("[name=supplier]").selectOption(sup2.id);
  await whEntry.locator('[name="lots-0-number"]').fill("L-SUP-OK2");
  await whEntry.locator('[name="lots-0-quantity"]').fill("4");
  await whEntry.locator('[name="lots-0-unit_cost"]').fill("7.20");
  await whEntry.locator('[name="lots-0-expiration_date"]').fill(fixture.future_date);
  await whEntry.getByRole("button", { name: "Confirmar entrada", exact: true }).click();
  await whEntry.waitForURL(/\/inventario\/cargas\//);
  const loadUrl = whEntry.url();
  check("entry_reactivado_persiste_sup2", state().lots.find((l) => l.number_normalized === "L-SUP-OK2").supplier_id, sup2.id);

  // Deactivate sup2 again and confirm historical reads remain intact across load detail, kardex, and expirations
  await admin.locator("tbody tr", { hasText: "20123456789" }).getByRole("button", { name: "Desactivar", exact: true }).click();
  check("admin_re_desactiva_sup2", state().suppliers.find((s) => s.id === sup2.id).is_active, false);

  for (const [roleLabel, pageObj] of [["almacenero", whEntry], ["admin", admin]]) {
    const loadResp = await pageObj.goto(loadUrl);
    check(`${roleLabel}_carga_historica_200`, loadResp.status(), 200);
    check(`${roleLabel}_carga_muestra_proveedor_inactivo`, (await pageObj.locator('[data-testid="inventory-load-created"]').innerText()).includes(name160), true);

    const movResp = await pageObj.goto(base + `/inventario/productos/${fixture.products.subsequent.id}/movimientos/`);
    check(`${roleLabel}_kardex_200`, movResp.status(), 200);
    check(`${roleLabel}_kardex_muestra_proveedor`, (await pageObj.locator("table").innerText()).includes(name160), true);
    check(
      `${roleLabel}_kardex_sin_overflow`,
      await pageObj.evaluate(() => {
        const wrap = document.querySelector(".table-wrap");
        return !wrap || wrap.scrollWidth <= wrap.clientWidth;
      }),
      true
    );

    const expResp = await pageObj.goto(base + "/productos/vencimientos/");
    check(`${roleLabel}_vencimientos_200`, expResp.status(), 200);
    check(`${roleLabel}_vencimientos_muestra_proveedor`, (await pageObj.locator("table").innerText()).includes(name160), true);
    check(
      `${roleLabel}_vencimientos_sin_overflow`,
      await pageObj.evaluate(() => {
        const wrap = document.querySelector(".table-responsive");
        return !wrap || wrap.scrollWidth <= wrap.clientWidth;
      }),
      true
    );
  }
  await whEntry.goto(loadUrl);
  await shot(whEntry, "04-historico-carga-detalle.png");
  await whEntry.goto(base + `/inventario/productos/${fixture.products.subsequent.id}/movimientos/`);
  await shot(whEntry, "04-historico-kardex-movimientos.png");
  await whEntry.goto(base + "/productos/vencimientos/");
  await shot(whEntry, "04-historico-vencimientos.png");

  if (process.env.AUDIT04_EXTENDED === "1") {
    // 04-B: CSRF enforcement and legacy request semantics, separate from acceptance.
    const beforeSecurity = state();
    const toggleUrl = base + `/inventario/proveedores/${sup1.id}/estado/`;
    const token = (await adminSession.ctx.cookies()).find(c => c.name === "audit04_csrftoken").value;
    for (const [label, url, form] of [
      ["alta", base + "/inventario/proveedores/nuevo/", {name: "No guardar CSRF", ruc: "00123456789"}],
      ["estado", toggleUrl, {is_active: "true"}],
    ]) {
      for (const [variant, extra] of [["ausente", {}], ["invalido", {csrfmiddlewaretoken: "invalid"}]]) {
        const response = await admin.request.post(url, {form: {...form, ...extra}, maxRedirects: 0});
        check(`04B_csrf_${label}_${variant}_403`, response.status(), 403);
        check(`04B_csrf_${label}_${variant}_sin_escritura`, state(), beforeSecurity);
      }
    }
    report.legacy_state_observation = [];
    for (let attempt = 0; attempt < 2; attempt++) {
      const response = await admin.request.post(toggleUrl, {form: {csrfmiddlewaretoken: token}, maxRedirects: 0});
      report.legacy_state_observation.push({attempt: attempt + 1, status: response.status(),
        active: state().suppliers.find(s => s.id === sup1.id).is_active});
    }
    // Two inversions restore the fixture; this records behavior, not approval of idempotency.
    check("04B_legacy_dos_envios_restituyen_estado", state(), beforeSecurity);
    report.mobile = [];
    for (const [role, page, url, filename] of [
      ["admin", admin, base + "/inventario/proveedores/", "04B-mobile-admin.png"],
      ["admin", admin, base + "/inventario/proveedores/nuevo/", "04B-mobile-form.png"],
      ["warehouse", whEntry, base + "/inventario/proveedores/", "04B-mobile-warehouse.png"],
      ["warehouse", whEntry, loadUrl, "04B-mobile-load.png"],
    ]) {
      await page.setViewportSize({width: 390, height: 844});
      const response = await page.goto(url);
      check(`04B_mobile_${filename}_200`, response.status(), 200);
      report.mobile.push({role, path: new URL(url).pathname, ...await page.evaluate(() => ({
        viewport: innerWidth, documentWidth: document.documentElement.scrollWidth,
        tables: Array.from(document.querySelectorAll(".table-responsive,.table-wrap")).map(e => ({
          width: e.clientWidth, scrollWidth: e.scrollWidth, overflowX: getComputedStyle(e).overflowX
        }))
      }))});
      await shot(page, filename);
    }
    await admin.setViewportSize({width: 1366, height: 900});
  }

  // 10. Logout + Back button / no-store cache protection
  await admin.goto(base + "/inventario/proveedores/");
  await admin.locator("a.sidebar-logout").click();
  await admin.waitForURL(base + "/salir/");
  await admin.getByRole("button", { name: "Cerrar sesión", exact: true }).click();
  await admin.waitForURL(base + "/");
  await admin.goBack();
  await admin.waitForLoadState("networkidle");
  const afterBackUrl = admin.url();
  check("logout_back_no_sirve_proveedores", afterBackUrl.startsWith(base + "/?next=") || afterBackUrl === base + "/", true);
  await admin.goto(base + "/inventario/proveedores/");
  check("post_logout_proveedores_redirige_login", admin.url(), base + "/?next=/inventario/proveedores/");

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
