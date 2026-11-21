'use strict';

const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const crypto = require('node:crypto');
const assert = require('node:assert/strict');
const { execFileSync } = require('node:child_process');

const { chromium } = require(
  path.join(os.homedir(), '.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright-core')
);

const runDir = process.env.AUDIT03_REVAL_RUN_DIR;
const outDir = process.env.AUDIT03_REVAL_OUT_DIR;
const pyBin = process.env.AUDIT03_REVAL_PYTHON;
const runScript = path.join(__dirname, 'audit03_reval_run.py');
const baseUrl = 'http://127.0.0.1:' + process.env.AUDIT03_REVAL_PORT;
const creds = JSON.parse(fs.readFileSync(path.join(runDir, '.credentials.json'), 'utf8'));

const report = {
  chrome_version: null,
  checks: [],
  observations: {},
  screenshots: [],
  cache_headers: {},
  responsive: {},
};

function record(id, actual, expected, detail = null) {
  assert.deepEqual(actual, expected, `${id} (actual=${JSON.stringify(actual)}, expected=${JSON.stringify(expected)})`);
  report.checks.push({ id, ok: true, detail });
}

function pyCmd(mode, ...args) {
  const raw = execFileSync(pyBin, [runScript, mode, ...args], { encoding: 'utf8' });
  return JSON.parse(raw);
}

async function loginCtx(browser, alias, viewport = { width: 1366, height: 900 }) {
  const ctx = await browser.newContext({ viewport, locale: 'es-PE' });
  const page = await ctx.newPage();
  await page.goto(baseUrl + '/');
  await page.locator('[name=email]').fill(creds[alias].email);
  await page.locator('[name=password]').fill(creds[alias].password);
  await Promise.all([
    page.waitForURL(url => !url.pathname.endsWith('/') || url.pathname === '/inicio/'),
    page.locator('button[type=submit]').click(),
  ]);
  await page.waitForSelector('h2');
  return { ctx, page };
}

async function getCsrf(ctx) {
  const cookies = await ctx.cookies();
  const c = cookies.find(x => x.name === 'audit03_reval_csrftoken');
  return c ? c.value : '';
}

async function snapShot(page, name) {
  const file = path.join(outDir, name + '.png');
  await page.screenshot({ path: file, fullPage: true });
  report.screenshots.push(name + '.png');
}

(async () => {
  const browser = await chromium.launch({
    executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe',
    headless: true,
  });
  report.chrome_version = browser.version();

  try {
    // 0. HMAC isolation challenge
    {
      const probe = await browser.newContext();
      const page = await probe.newPage();
      const nonce = crypto.randomBytes(32).toString('hex');
      const res = await page.request.get(baseUrl + '/', { headers: { 'X-Audit03-Challenge': nonce } });
      const expectedProof = crypto.createHmac('sha256', fs.readFileSync(path.join(runDir, '.django-key'))).update(nonce).digest('hex');
      record('00_hmac_isolated_server', res.headers()['x-audit03-proof'], expectedProof);
      await probe.close();
    }

    // 1. Login roles & check sidebar / dashboard visibility + empty catalog states
    const { ctx: adminCtx, page: adminPage } = await loginCtx(browser, 'admin');
    const adminBody = await adminPage.locator('body').innerText();
    record('01_admin_dashboard_has_links', {
      registrar: adminBody.includes('Registrar producto'),
      catalogo: adminBody.includes('Ver catálogo de productos'),
      categorias: adminBody.includes('Categorías'),
    }, { registrar: true, catalogo: true, categorias: true });

    // Empty category list
    await adminPage.getByRole('link', { name: 'Categorías' }).click();
    await adminPage.waitForURL('**/productos/categorias/');
    report.cache_headers['/productos/categorias/'] = (await adminPage.request.get(baseUrl + '/productos/categorias/')).headers()['cache-control'] || '';
    record('02_cat_empty_list', (await adminPage.locator('main').innerText()).includes('No hay categorías registradas.'), true);
    await snapShot(adminPage, '01-cat-empty');

    // Check FUTURO buttons absent
    const catListHtml = await adminPage.locator('main').innerHTML();
    record('03_cat_no_edit_or_delete_ui', {
      has_edit: /Editar|Renombrar/i.test(catListHtml),
      has_delete: /Eliminar/i.test(catListHtml),
    }, { has_edit: false, has_delete: false });

    // Empty product list (ADMIN sidebar uses "Productos")
    const prodNavLink = adminPage.locator('.sidebar-nav a[href$="/productos/"]');
    report.observations.admin_sidebar_catalog_link_text = (await prodNavLink.innerText()).trim();
    await prodNavLink.click();
    await adminPage.waitForURL('**/productos/');
    report.cache_headers['/productos/'] = (await adminPage.request.get(baseUrl + '/productos/')).headers()['cache-control'] || '';
    record('04_prod_empty_list', (await adminPage.locator('main').innerText()).includes('No hay productos registrados.'), true);
    await snapShot(adminPage, '02-prod-empty');

    // 2. Category create (HU-CAT-02): empty, whitespace, create canned & non-canned, tampered is_active, duplicate
    await adminPage.goto(baseUrl + '/productos/categorias/nueva/');
    report.cache_headers['/productos/categorias/nueva/'] = (await adminPage.request.get(baseUrl + '/productos/categorias/nueva/')).headers()['cache-control'] || '';

    // Submit empty
    await adminPage.getByRole('button', { name: 'Guardar' }).click();
    record('05_cat_empty_error', (await adminPage.locator('main').innerText()).includes('El nombre es obligatorio'), true);
    // Focus / aria-invalid check
    record('06_cat_error_aria_and_id', {
      ariaInvalid: await adminPage.locator('[name=name]').getAttribute('aria-invalid'),
      errVisible: await adminPage.locator('#id_name_error').isVisible(),
    }, { ariaInvalid: 'true', errVisible: true });

    // Submit whitespace only
    await adminPage.locator('[name=name]').fill('   \t\u00a0  ');
    await adminPage.getByRole('button', { name: 'Guardar' }).click();
    record('07_cat_whitespace_only_error', (await adminPage.locator('main').innerText()).includes('El nombre es obligatorio'), true);

    // Create Productos enlatados + Lácteos y derivados (with redundant spaces & tampered is_active=false)
    await adminPage.locator('[name=name]').fill('  Productos   enlatados ');
    await adminPage.getByRole('button', { name: 'Guardar' }).click();
    await adminPage.waitForURL('**/productos/categorias/');

    const catCsrf = await getCsrf(adminCtx);
    const catPostRes = await adminPage.request.post(baseUrl + '/productos/categorias/nueva/', {
      form: { csrfmiddlewaretoken: catCsrf, name: '  Lácteos   y\tderivados  ', is_active: 'false' },
    });
    record('08_cat_create_tampered_inactive_ignored_http', catPostRes.status(), 200); // follows redirect to list 200 or check DB
    await adminPage.reload();
    const catText = await adminPage.locator('main').innerText();
    record('09_cat_list_shows_collapsed_active', catText.includes('Lácteos y derivados') && catText.includes('Productos enlatados'), true);

    // Duplicate casefold + extra whitespace
    await adminPage.goto(baseUrl + '/productos/categorias/nueva/');
    await adminPage.locator('[name=name]').fill('  LÁCTEOS\tY  DERIVADOS  ');
    await adminPage.getByRole('button', { name: 'Guardar' }).click();
    record('10_cat_duplicate_rejected', (await adminPage.locator('main').innerText()).includes('La categoría ya existe'), true);

    // Non-existent HU-CAT-03 / HU-CAT-04 routes -> 404
    const snap1 = pyCmd('snapshot');
    const lacteosId = snap1.categories.find(c => c.name_normalized === 'lácteos y derivados').id;
    record('11_cat_future_routes_absent', {
      edit404: (await adminPage.request.get(`${baseUrl}/productos/categorias/${lacteosId}/editar/`)).status(),
      del404: (await adminPage.request.get(`${baseUrl}/productos/categorias/${lacteosId}/eliminar/`)).status(),
    }, { edit404: 404, del404: 404 });

    // PROP-E00-HU-02 J-CA1..J-CA3 category confirmation, cancel, stale 409, reactivate
    await adminPage.goto(baseUrl + '/productos/categorias/');
    const lactRow = adminPage.locator('tbody tr', { hasText: 'Lácteos y derivados' });
    await lactRow.getByRole('button', { name: 'Desactivar' }).click();
    await adminPage.waitForURL('**/estado/confirmar/**');
    const confirmUrl = adminPage.url();
    report.cache_headers['/productos/categorias/<id>/estado/confirmar/'] = (await adminPage.request.get(confirmUrl)).headers()['cache-control'] || '';
    const confirmText = await adminPage.locator('main').innerText();
    record('12_jca1_confirm_screen_content', {
      name: confirmText.includes('Lácteos y derivados'),
      state: confirmText.includes('Activa'),
      impact: /productos/i.test(confirmText) && /existencias/i.test(confirmText),
    }, { name: true, state: true, impact: true });
    await snapShot(adminPage, '03-cat-confirm');

    // Cancel without mutation
    await adminPage.getByRole('link', { name: 'Cancelar' }).click();
    await adminPage.waitForURL('**/productos/categorias/');
    record('13_jca1_cancel_preserves_state', pyCmd('snapshot').categories.find(c => c.id === lacteosId).is_active, true);

    // Concurrent ADMIN B stale version test (J-CA3)
    const { ctx: admin2Ctx, page: admin2Page } = await loginCtx(browser, 'admin2');
    await admin2Page.goto(baseUrl + '/productos/categorias/');
    await admin2Page.locator('tbody tr', { hasText: 'Lácteos y derivados' }).getByRole('button', { name: 'Desactivar' }).click();
    await admin2Page.waitForURL('**/estado/confirmar/**');

    // Admin1 opens confirm page at v0, then confirms -> v1 (inactive)
    await adminPage.locator('tbody tr', { hasText: 'Lácteos y derivados' }).getByRole('button', { name: 'Desactivar' }).click();
    await adminPage.waitForURL('**/estado/confirmar/**');
    await adminPage.getByRole('button', { name: 'Confirmar desactivación' }).click();
    await adminPage.waitForURL('**/productos/categorias/');
    // Admin1 reactivates -> v2 (active again)
    await adminPage.locator('tbody tr', { hasText: 'Lácteos y derivados' }).getByRole('button', { name: 'Activar' }).click();
    await adminPage.waitForURL('**/estado/confirmar/**');
    await adminPage.getByRole('button', { name: 'Confirmar activación' }).click();
    await adminPage.waitForURL('**/productos/categorias/');

    // Admin2 tries submitting stale confirm form from v0 even though category returned to active!
    const admin2ConfirmTxtPromise = admin2Page.waitForResponse(r => r.url().includes('/estado/'));
    await admin2Page.getByRole('button', { name: 'Confirmar desactivación' }).click();
    const admin2ResStatus = (await admin2ConfirmTxtPromise).status();
    record('14_jca3_stale_version_rejected_after_roundtrip', {
      status409: admin2ResStatus,
      staleMsg: (await admin2Page.locator('main').innerText()).includes('La categoría cambió desde que abrió esta pantalla'),
      stillActive: pyCmd('snapshot').categories.find(c => c.id === lacteosId).is_active,
      stateVersion: pyCmd('snapshot').categories.find(c => c.id === lacteosId).state_version,
    }, { status409: 409, staleMsg: true, stillActive: true, stateVersion: 2 });
    await admin2Ctx.close();

    // 3. Product Registration (HU-PROD-02 & HU-PROD-03) + UI observations
    await adminPage.goto(baseUrl + '/productos/nuevo/');
    report.cache_headers['/productos/nuevo/'] = (await adminPage.request.get(baseUrl + '/productos/nuevo/')).headers()['cache-control'] || '';
    const formOptions = await adminPage.locator('[name=category] option').allInnerTexts();
    const unitOptions = await adminPage.locator('[name=unit] option').allInnerTexts();
    report.observations.product_form_unit_options = unitOptions;
    record('15_prod_form_allows_non_canned_active_categories', {
      hasEnlatados: formOptions.includes('Productos enlatados'),
      hasLacteos: formOptions.includes('Lácteos y derivados'),
      unitFixedUnd: unitOptions.length === 1 && unitOptions[0].includes('UND'),
      hasExpControl: (await adminPage.locator('main').innerText()).includes('Control de vencimiento'),
    }, { hasEnlatados: true, hasLacteos: true, unitFixedUnd: true, hasExpControl: true });
    await snapShot(adminPage, '04-prod-form');

    // UI audit check: Bootstrap vs custom classes, sidebar/error markup on product_form vs product_edit
    const prodFormHtml = await adminPage.locator('main').innerHTML();
    await adminPage.getByRole('button', { name: 'Registrar producto' }).click({ noWaitAfter: true });
    await adminPage.waitForSelector('.field-error .error-list');
    const prodFormErrHtml = await adminPage.locator('main').innerHTML();
    report.observations.product_form_css_and_error_markup = {
      uses_form_panel: prodFormHtml.includes('class="panel form-panel"'),
      dom_id_name_error_exists: await adminPage.evaluate(() => Boolean(document.getElementById('id_name_error'))),
      has_field_error_id_wrapper_in_html: prodFormErrHtml.includes('_error"'),
      name_aria_invalid_on_err: await adminPage.locator('[name=name]').getAttribute('aria-invalid'),
      name_aria_describedby_on_err: await adminPage.locator('[name=name]').getAttribute('aria-describedby'),
    };

    // Wait briefly for initial state before filling valid fields, and track http responses on adminPage
    report.observations.http_trace_tail = [];
    adminPage.on('response', r => {
      if (r.url().startsWith(baseUrl)) {
        report.observations.http_trace_tail.push(`${r.request().method()} ${new URL(r.url()).pathname} -> ${r.status()}`);
        if (report.observations.http_trace_tail.length > 25) report.observations.http_trace_tail.shift();
      }
    });

    // Register non-canned product "Yogur natural 200 g" in Lácteos y derivados with omitted minimum_stock (-> 10)
    await adminPage.locator('[name=name]').fill('  Yogur   natural 200 g  ');
    await adminPage.locator('[name=barcode_type]').selectOption('INTERNAL');
    await adminPage.locator('[name=barcode]').fill('INT-YOGUR-200');
    await adminPage.locator('[name=category]').selectOption(lacteosId);
    await adminPage.locator('[name=sale_price]').fill('2.50');
    await adminPage.locator('[name=minimum_stock]').fill('');
    await adminPage.getByRole('button', { name: 'Registrar producto' }).click({ noWaitAfter: true });
    await adminPage.waitForURL('**/productos/*/registrado/');
    const createdUrl = adminPage.url();
    report.cache_headers['/productos/<id>/registrado/'] = (await adminPage.request.get(createdUrl)).headers()['cache-control'] || '';
    const createdId = createdUrl.match(/\/productos\/([0-9a-f-]+)\/registrado\//)[1];
    const createdText = await adminPage.locator('main').innerText();
    record('16_prod_non_canned_created_zero_stock_not_sellable', {
      heading: createdText.includes('Yogur natural 200 g'),
      noSell: createdText.includes('No disponible para venta: sin stock vigente'),
      cat: createdText.includes('Lácteos y derivados'),
      zeroStock: createdText.includes('0 UND'),
    }, { heading: true, noSell: true, cat: true, zeroStock: true });
    // Alias route /creado/
    const aliasRes = await adminPage.request.get(`${baseUrl}/productos/${createdId}/creado/`);
    record('17_prod_created_alias_200', aliasRes.status(), 200);
    await snapShot(adminPage, '05-prod-created');

    // Register GTIN product with leading zero (04006381333931) via form, then test HU-PROD-03 scanner modal!
    await adminPage.goto(baseUrl + '/productos/nuevo/');
    await adminPage.locator('[name=name]').fill('Atún clásico 170 g');
    await adminPage.locator('[name=barcode_type]').selectOption('GTIN');
    await adminPage.locator('[name=barcode]').fill('04006381333931');
    await adminPage.locator('[name=category]').selectOption({ label: 'Productos enlatados' });
    await adminPage.locator('[name=sale_price]').fill('6.50');
    await adminPage.locator('[name=minimum_stock]').fill('10');
    await adminPage.getByRole('button', { name: 'Registrar producto' }).click({ noWaitAfter: true });
    await adminPage.waitForURL('**/productos/*/registrado/');

    // Now test Scanner Modal (HU-PROD-03) on /productos/nuevo/
    await adminPage.goto(baseUrl + '/productos/nuevo/');
    await adminPage.getByRole('button', { name: 'Escanear código' }).click();
    await adminPage.waitForSelector('#barcode-capture-dialog[open]');
    const scanInput = adminPage.locator('#barcode-capture-input');
    const useBtn = adminPage.locator('#barcode-capture-apply');

    // Test oversized >64 chars inside scanner dialog via synthetic paste event
    await scanInput.evaluate((el) => {
      const dt = new DataTransfer();
      dt.setData('text/plain', '9'.repeat(65));
      el.dispatchEvent(new ClipboardEvent('paste', { clipboardData: dt, bubbles: true, cancelable: true }));
    });
    const over64Msg = (await adminPage.locator('#barcode-capture-error').innerText()).trim();
    report.observations.scanner_over64_error = over64Msg;
    record('17b_scanner_over64_blocked', over64Msg.includes('supera los 64 caracteres') && (await useBtn.isDisabled()), true);
    await adminPage.locator('#barcode-capture-cancel').click();
    await adminPage.getByRole('button', { name: 'Escanear código' }).click();
    await adminPage.waitForSelector('#barcode-capture-dialog[open]');

    // Read duplicate GTIN (13-digit equivalence 4006381333931 to stored 04006381333931!)
    await adminPage.locator('[name=barcode_type]').selectOption('GTIN');
    await scanInput.fill('4006381333931');
    await adminPage.waitForFunction(() => document.getElementById('barcode-capture-status').textContent.includes('ya está registrado'));
    record('18_scanner_duplicate_gtin_blocked', {
      statusMsg: (await adminPage.locator('#barcode-capture-status').innerText()).trim(),
      useDisabled: await useBtn.isDisabled(),
    }, { statusMsg: 'El código de barras ya está registrado', useDisabled: true });
    await snapShot(adminPage, '06-scanner-duplicate');

    // H-03Z-01: Ctrl+A overwrite inside Código leído with INTERNAL leading-zero code 000123
    await adminPage.locator('[name=barcode_type]').selectOption('INTERNAL');
    await scanInput.click();
    await adminPage.keyboard.press('Control+A');
    await adminPage.keyboard.type('000123');
    await adminPage.waitForFunction(() => !document.getElementById('barcode-capture-apply').disabled);
    const scannerAvailText = await adminPage.locator('#barcode-capture-status').innerText();
    report.observations.scanner_available_status = scannerAvailText;
    record('19_scanner_new_internal_allowed', { enabled: !(await useBtn.isDisabled()), hasText: scannerAvailText.length > 0 }, { enabled: true, hasText: true });
    await scanInput.press('Enter');
    const stillOpenOnEnter = await adminPage.locator('#barcode-capture-dialog').evaluate(el => el.open);
    record('19b_scanner_enter_does_not_submit_form', stillOpenOnEnter && adminPage.url().endsWith('/productos/nuevo/'), true);

    await useBtn.click();
    record('20_scanner_use_copies_without_submit', {
      fieldVal: await adminPage.locator('[name=barcode]').inputValue(),
      stillOnForm: adminPage.url().endsWith('/productos/nuevo/'),
    }, { fieldVal: '000123', stillOnForm: true });

    // Also test network failure fallback inside modal
    await adminPage.route('**/productos/codigos/comprobar/**', route => route.abort('failed'));
    await adminPage.getByRole('button', { name: 'Escanear código' }).click();
    await scanInput.click();
    await adminPage.keyboard.press('Control+A');
    await adminPage.keyboard.type('999888');
    await adminPage.waitForFunction(() => document.getElementById('barcode-capture-status').textContent.includes('No se pudo comprobar'));
    record('21_scanner_network_fallback', {
      statusMsg: (await adminPage.locator('#barcode-capture-status').innerText()).trim(),
      useDisabled: await useBtn.isDisabled(),
    }, { statusMsg: 'No se pudo comprobar el código. Se validará al guardar.', useDisabled: false });
    await adminPage.locator('#barcode-capture-cancel').click();
    await adminPage.unroute('**/productos/codigos/comprobar/**');

    // Save 000123 explicitly
    await adminPage.locator('[name=name]').fill('Producto lector cero inicial');
    await adminPage.locator('[name=barcode_type]').selectOption('INTERNAL');
    await adminPage.locator('[name=barcode]').fill('000123');
    await adminPage.locator('[name=category]').selectOption(lacteosId);
    await adminPage.locator('[name=sale_price]').fill('5.00');
    await adminPage.locator('[name=minimum_stock]').fill('0');
    await adminPage.getByRole('button', { name: 'Registrar producto' }).click({ noWaitAfter: true });
    await adminPage.waitForURL('**/productos/*/registrado/');
    record('22_internal_leading_zeros_and_min0_persisted', (() => {
      const p = pyCmd('snapshot').products.find(x => x.barcode === '000123');
      return { barcode: p.barcode, minimum_stock: p.minimum_stock, barcode_type: p.barcode_type };
    })(), { barcode: '000123', minimum_stock: 0, barcode_type: 'INTERNAL' });

    // Check product_barcode_check query-param edge cases
    record('23_barcode_check_empty_param_status', {
      emptyProductId: (await adminPage.request.get(baseUrl + '/productos/codigos/comprobar/', { params: { barcode: 'NEW123', product_id: '' } })).status(),
      emptyBarcodeType: (await adminPage.request.get(baseUrl + '/productos/codigos/comprobar/', { params: { barcode: 'NEW123', barcode_type: '' } })).status(),
    }, { emptyProductId: 400, emptyBarcodeType: 400 });

    // Extreme values, underscore barcode rejection & accents on product_create UI + raw +10 HTTP check
    report.observations.extreme_errors = {};
    for (const [label, bc, priceVal, minVal] of [
      ['barcode_underscore', 'EXT_BAD_UND', '5.00', '10'],
      ['price_zero', 'EXT-PRICE-ZERO', '0.00', '10'],
      ['price_3dec', 'EXT-PRICE-3DEC', '2.501', '10'],
      ['price_over_max', 'EXT-PRICE-OVER', '10000000.00', '10'],
      ['min_over_max', 'EXT-MIN-OVER', '5.00', '1000000'],
      ['min_negative', 'EXT-MIN-NEG', '5.00', '-1'],
      ['min_decimal', 'EXT-MIN-DEC', '5.00', '1.5'],
    ]) {
      await adminPage.goto(baseUrl + '/productos/nuevo/');
      await adminPage.locator('[name=name]').fill('Extremo ' + label);
      await adminPage.locator('[name=barcode_type]').selectOption('INTERNAL');
      await adminPage.locator('[name=barcode]').fill(bc);
      await adminPage.locator('[name=category]').selectOption(lacteosId);
      await adminPage.locator('[name=sale_price]').fill(priceVal);
      await adminPage.locator('[name=minimum_stock]').fill(minVal);
      await adminPage.getByRole('button', { name: 'Registrar producto' }).click({ noWaitAfter: true });
      await adminPage.waitForSelector('.field-error .error-list');
      const errTxt = (await adminPage.locator('.field-error .error-list').allInnerTexts()).join(' | ');
      report.observations.extreme_errors[label] = errTxt;
      record('24_extreme_' + label, !adminPage.url().includes('/registrado/') && errTxt.length > 0, true);
    }
    const rawPlusRes = await adminPage.request.post(baseUrl + '/productos/nuevo/', {
      form: {
        csrfmiddlewaretoken: await getCsrf(adminCtx),
        name: 'Extremo plus10',
        barcode_type: 'INTERNAL',
        barcode: 'EXT-PLUS10',
        category: lacteosId,
        sale_price: '+10',
        minimum_stock: '10',
      },
    });
    const rawPlusBody = await rawPlusRes.text();
    const afterExtremeSnap = pyCmd('snapshot');
    record('24_extreme_none_persisted_and_plus10_rejected', {
      plusRejected: rawPlusBody.includes('error') && !rawPlusRes.url().includes('/registrado/'),
      anyExtremeCreated: afterExtremeSnap.products.some(p => p.barcode.startsWith('EXT-')),
    }, { plusRejected: true, anyExtremeCreated: false });

    // 4. Prepare stock & sales history via backend service helper, then audit Search, Alerts, Edit & Deactivation
    const fx = pyCmd('prepare-stock');
    const probes = pyCmd('probes', fx.leche_id, fx.suspendida_id);
    report.observations.cross_module_probes = probes;

    // Catalog view & search as ADMIN & ALMACENERO
    await adminPage.goto(baseUrl + '/productos/');
    await snapShot(adminPage, '07-prod-list-stock');
    const getRowText = async (p, name) => await p.locator('tbody tr', { hasText: name }).innerText();
    record('25_catalog_alerts_and_statuses', {
      atunLowSellable5Not28: (await getRowText(adminPage, 'Atún clásico 170 g')).includes('5') && (await getRowText(adminPage, 'Atún clásico 170 g')).includes('Stock bajo'),
      sobreNoAlert11: !/Stock bajo|Sin stock vigente/.test(await getRowText(adminPage, 'Sobre normal')),
      yogurZeroAlert: (await getRowText(adminPage, 'Yogur natural 200 g')).includes('Sin stock vigente') && (await getRowText(adminPage, 'Yogur natural 200 g')).includes('Stock bajo'),
      inactProdNoStockBajo: (await getRowText(adminPage, 'Producto suspendido')).includes('Inactivo') && !(await getRowText(adminPage, 'Producto suspendido')).includes('Stock bajo'),
      catOffProdNoStockBajo: (await getRowText(adminPage, 'Producto categoría suspendida')).includes('Categoría desactivada') && !(await getRowText(adminPage, 'Producto categoría suspendida')).includes('Stock bajo'),
    }, {
      atunLowSellable5Not28: true,
      sobreNoAlert11: true,
      yogurZeroAlert: true,
      inactProdNoStockBajo: true,
      catOffProdNoStockBajo: true,
    });

    // Search GTIN equivalence (04006381333931 stored: 13-digit 4006381333931 and 14-digit 04006381333931 match; 15-digit does not), NFD accents, and clear
    for (const q of ['4006381333931', '04006381333931', 'Atu\u0301n']) {
      await adminPage.locator('[name=q]').fill(q);
      await adminPage.getByRole('button', { name: 'Buscar' }).click();
      record('26_search_match_' + q.replace(/\u0301/, '_accent'), await adminPage.locator('tbody tr').count(), 1);
    }
    await adminPage.locator('[name=q]').fill('004006381333931');
    await adminPage.getByRole('button', { name: 'Buscar' }).click();
    record('26b_search_15digit_not_gtin_matched', await adminPage.locator('tbody tr').count(), 0);
    await adminPage.locator('[name=q]').fill('Atun');
    await adminPage.getByRole('button', { name: 'Buscar' }).click();
    record('27_search_accent_not_stripped', await adminPage.locator('tbody tr').count(), 0);
    await adminPage.locator('a[aria-label="Limpiar búsqueda"]').click();
    record('28_search_clear_restores_all', (await adminPage.locator('tbody tr').count()) >= 6, true);

    // ALMACENERO view parity (no Acciones column) + VENDEDOR denied /productos/
    const { ctx: almCtx, page: almPage } = await loginCtx(browser, 'warehouse');
    await almPage.goto(baseUrl + '/productos/');
    const almHeaders = await almPage.locator('thead th').allInnerTexts();
    record('29_warehouse_catalog_no_actions', {
      hasAcciones: almHeaders.includes('Acciones'),
      hasRows: (await almPage.locator('tbody tr').count()) >= 6,
      editLinkCount: await almPage.getByRole('link', { name: 'Editar' }).count(),
    }, { hasAcciones: false, hasRows: true, editLinkCount: 0 });
    await almCtx.close();

    // 5. Product Edit (HU-PROD-04) + Cache-Control + Stale Edit + Draft price update + History preservation
    const editUrl = `${baseUrl}/productos/${fx.leche_id}/editar/`;
    report.cache_headers['/productos/<id>/editar/'] = (await adminPage.request.get(editUrl)).headers()['cache-control'] || '';
    await adminPage.goto(editUrl);
    report.observations.product_edit_rendered_sale_price = await adminPage.locator('[name=sale_price]').inputValue();
    report.observations.product_edit_sale_price_type = await adminPage.locator('[name=sale_price]').getAttribute('type');
    await snapShot(adminPage, '08-prod-edit');

    // Open second admin tab for stale edit conflict test
    const { ctx: tab2Ctx, page: tab2Page } = await loginCtx(browser, 'admin2');
    await tab2Page.goto(editUrl);

    // Tab 1 edits price 10.00 -> 11.50, name -> Leche entera 1L, barcode -> INT-LECHE-NUEVO, min -> 12, category -> Abarrotes
    await adminPage.locator('[name=name]').fill('Leche entera 1L');
    await adminPage.locator('[name=barcode]').fill('INT-LECHE-NUEVO');
    await adminPage.locator('[name=category]').selectOption(fx.abarrotes_id);
    await adminPage.locator('[name=sale_price]').fill('11.50');
    await adminPage.locator('[name=minimum_stock]').fill('12');
    await adminPage.getByRole('button', { name: 'Guardar cambios' }).click();
    await adminPage.waitForURL('**/productos/');

    // Tab 2 tries stale submit with different values -> rejected without mutation
    await tab2Page.locator('[name=sale_price]').fill('99.99');
    await tab2Page.getByRole('button', { name: 'Guardar cambios' }).click();
    const staleEditTxt = await tab2Page.locator('main').innerText();
    report.observations.stale_edit_msg = staleEditTxt;
    record('30_stale_edit_rejected_in_browser', {
      msg: staleEditTxt.includes('El producto cambió desde que abrió esta pantalla'),
      reviewBtn: staleEditTxt.includes('Revisar ficha actual'),
      currentPrice: pyCmd('snapshot').products.find(p => p.id === fx.leche_id).sale_price,
    }, { msg: true, reviewBtn: true, currentPrice: '11.50' });
    await tab2Ctx.close();

    // Historical Sale 1 receipt preserves old name/barcode/price!
    await adminPage.goto(`${baseUrl}/ventas/constancia/${fx.sale1_id}/`);
    const recTxt = await adminPage.locator('#constancia-interna').innerText();
    record('31_old_receipt_preserves_snapshots', {
      oldName: recTxt.includes('Leche prueba'),
      oldCode: recTxt.includes('INT-LECHE-1'),
      oldPrice: recTxt.includes('10,00') || recTxt.includes('10.00'),
    }, { oldName: true, oldCode: true, oldPrice: true });

    // Kardex stays linked to same product ID with updated title + old lot intact
    await adminPage.goto(`${baseUrl}/inventario/productos/${fx.leche_id}/movimientos/`);
    const movTxt = await adminPage.locator('main').innerText();
    record('32_kardex_remains_linked_after_edit', movTxt.includes('Leche entera 1L') && movTxt.includes('L-A1'), true);

    // VENDEDOR: Check active draft GET preserves 10.00 until review POST!
    const { ctx: selCtx, page: selPage } = await loginCtx(browser, 'seller');
    await selPage.goto(baseUrl + '/ventas/');
    const draftTxtBefore = await selPage.locator('.sales-summary-panel').innerText();
    report.observations.seller_draft_before_checkout_post = draftTxtBefore;
    record('33_draft_get_shows_old_price_without_silent_mutation', draftTxtBefore.includes('10,00') || draftTxtBefore.includes('10.00'), true);
    // Denied direct URL /productos/ for VENDEDOR
    record('34_seller_denied_catalog_routes', {
      list403: (await selPage.request.get(baseUrl + '/productos/')).status(),
      cats403: (await selPage.request.get(baseUrl + '/productos/categorias/')).status(),
      new403: (await selPage.request.get(baseUrl + '/productos/nuevo/')).status(),
      check403: (await selPage.request.get(baseUrl + '/productos/codigos/comprobar/', { params: { barcode: 'X' } })).status(),
    }, { list403: 403, cats403: 403, new403: 403, check403: 403 });

    // Go to checkout and submit with old subtotal 10.00 -> must reject & refresh unit_price to 11.50!
    await selPage.goto(baseUrl + '/ventas/cobrar/');
    await selPage.locator('[name=cash_received]').fill('20.00');
    await selPage.getByRole('button', { name: 'Confirmar cobro' }).click();
    const checkoutStaleTxt = await selPage.locator('main').innerText();
    report.observations.checkout_stale_price_msg = checkoutStaleTxt;
    record('35_checkout_blocks_stale_price_once', checkoutStaleTxt.includes('10.00') && checkoutStaleTxt.includes('11.50'), true);

    // 6. Product Deactivation impact on active draft + POS search + inventory + reactivation
    await adminPage.goto(baseUrl + '/productos/');
    const lecheRow = adminPage.locator('tbody tr', { hasText: 'Leche entera 1L' });
    await lecheRow.getByRole('button', { name: 'Deshabilitar' }).click();
    await adminPage.waitForURL('**/productos/');

    // Also inspect seller draft GET banner when product is disabled
    await selPage.goto(baseUrl + '/ventas/?query=Leche+entera');
    report.observations.seller_draft_when_product_inactive = await selPage.locator('.sales-summary-panel').innerText();
    record('36_inactive_product_excluded_from_pos_search', await selPage.locator('.sales-search-panel tbody tr').count(), 0);
    await selPage.goto(baseUrl + '/ventas/cobrar/');
    await selPage.locator('[name=cash_received]').fill('20.00');
    await selPage.getByRole('button', { name: 'Confirmar cobro' }).click();
    const checkoutInactiveTxt = await selPage.locator('main').innerText();
    report.observations.checkout_inactive_msg = checkoutInactiveTxt;
    record('37_checkout_blocks_inactive_product_in_draft', checkoutInactiveTxt.includes('no está disponible') || checkoutInactiveTxt.includes('deshabilitado') || checkoutInactiveTxt.includes('inactivo'), true);

    // Seller can still remove line via Quitar, or let's leave and reactivate product to verify reactivation -> checkout works!
    // First test omitting is_active on product_toggle_availability (observes whether it toggles without explicit target)
    const toggleUrl = `${baseUrl}/productos/${fx.leche_id}/disponibilidad/`;
    const adminCsrf = await getCsrf(adminCtx);
    await adminPage.request.post(toggleUrl, { form: { csrfmiddlewaretoken: adminCsrf } });
    const lecheAfterOmit = pyCmd('snapshot').products.find(p => p.id === fx.leche_id);
    report.observations.product_toggle_omitted_is_active_toggles = lecheAfterOmit.is_active;
    record('37b_missing_target_preserves_inactive', lecheAfterOmit.is_active, false);
    await adminPage.goto(baseUrl + '/productos/');
    await adminPage.locator('form[action="' + new URL(toggleUrl).pathname + '"] button').click();

    // Now confirm checkout succeeds cleanly after reactivation at 11.50!
    await selPage.goto(baseUrl + '/ventas/cobrar/');
    await selPage.locator('[name=cash_received]').fill('20.00');
    await selPage.getByRole('button', { name: 'Confirmar cobro' }).click();
    await selPage.waitForURL('**/ventas/constancia/*/');
    record('38_reactivated_product_checkout_succeeds_new_price', (await selPage.locator('#constancia-interna').innerText()).includes('11,50') || (await selPage.locator('#constancia-interna').innerText()).includes('11.50'), true);
    await selCtx.close();

    // 7. Check remaining Cache-Control headers & /admin/ & anonymous perimeter
    for (const [label, u] of [
      ['/productos/categorias/<id>/estado/', `${baseUrl}/productos/categorias/${lacteosId}/estado/`],
      ['/productos/<id>/disponibilidad/', toggleUrl],
    ]) {
      const r = await adminPage.request.post(u, {
        maxRedirects: 0,
        form: { csrfmiddlewaretoken: adminCsrf, is_active: 'true', state_version: '2', confirm: 'yes' },
      });
      report.cache_headers[label] = `${r.status()} -> ${r.headers()['cache-control'] || ''}`;
    }
    // Check POST /productos/categorias/nueva/ & POST /productos/nuevo/ & /productos/<id>/editar/ redirect Cache-Control (direct 302) vs GET
    report.cache_headers['/productos/vencimientos/'] = (await adminPage.request.get(baseUrl + '/productos/vencimientos/')).headers()['cache-control'] || '';
    report.cache_headers['/productos/codigos/comprobar/'] = (await adminPage.request.get(baseUrl + '/productos/codigos/comprobar/', { params: { barcode: '000123' } })).headers()['cache-control'] || '';
    const anonCtx = await browser.newContext();
    record('38b_anonymous_redirect_to_login', {
      prodList302: (await anonCtx.request.get(baseUrl + '/productos/', { maxRedirects: 0 })).status(),
      cats302: (await anonCtx.request.get(baseUrl + '/productos/categorias/', { maxRedirects: 0 })).status(),
      check401or302: (await anonCtx.request.get(baseUrl + '/productos/codigos/comprobar/', { maxRedirects: 0 })).status(),
    }, { prodList302: 302, cats302: 302, check401or302: 302 });
    await anonCtx.close();

    // The commercial build removed the Django admin, including for staff (08, DOC-01-06).
    const { ctx: staffCtx, page: staffPage } = await loginCtx(browser, 'staff_noperm');
    const loginStatus = (await staffPage.goto(baseUrl + '/admin/login/')).status();
    const categoryStatus = (await staffPage.goto(baseUrl + '/admin/catalog/category/')).status();
    record('39_retired_staff_portal_and_category_route', [loginStatus, categoryStatus], [404, 404]);
    await staffCtx.close();

    // 8. Responsive check at 390x844 mobile on catalog views
    const { ctx: mobCtx, page: mobPage } = await loginCtx(browser, 'admin', { width: 390, height: 844 });
    for (const [slug, urlPath] of [
      ['cat_list', '/productos/categorias/'],
      ['prod_list', '/productos/'],
      ['prod_form', '/productos/nuevo/'],
      ['prod_edit', `/productos/${fx.leche_id}/editar/`],
    ]) {
      await mobPage.goto(baseUrl + urlPath);
      const metrics = await mobPage.evaluate(() => ({
        scrollWidth: document.documentElement.scrollWidth,
        innerWidth: window.innerWidth,
      }));
      report.responsive[slug] = metrics;
      record('40_mobile_no_doc_overflow_' + slug, metrics.scrollWidth <= metrics.innerWidth, true);
    }
    await snapShot(mobPage, '09-mobile-prod-list');
    await mobCtx.close();

    await adminCtx.close();
  } catch (err) {
    report.error = String(err && err.stack ? err.stack : err);
    process.exitCode = 1;
  } finally {
    fs.writeFileSync(path.join(outDir, 'browser-report.json'), JSON.stringify(report, null, 2), 'utf8');
    await browser.close();
  }
})();
