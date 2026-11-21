/* Isolated Stage 10-B real Chrome Playwright audit (read-only over product). */
'use strict';

const fs = require('fs');
const path = require('path');

const pwPath = path.join(
  process.env.USERPROFILE,
  '.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright-core'
);
const { chromium } = require(pwPath);

const BASE = process.env.AUDIT10B_BASE_URL;
const EV_DIR = process.env.AUDIT10B_EVIDENCE_DIR;
const META = JSON.parse(process.env.AUDIT10B_META);
const ADMIN_EMAIL = process.env.AUDIT10B_ADMIN_EMAIL;
const WH_EMAIL = process.env.AUDIT10B_WH_EMAIL;
const SELLER_EMAIL = process.env.AUDIT10B_SELLER_EMAIL;
const SELLER2_EMAIL = process.env.AUDIT10B_SELLER2_EMAIL;
const PASS = process.env.AUDIT10B_PASS;
const NONCE = process.env.AUDIT10B_NONCE;
const EXPECTED_HMAC = process.env.AUDIT10B_EXPECTED_HMAC;

const CHROME_PATH = 'C:/Program Files/Google/Chrome/Application/chrome.exe';

const results = [];
const consoleErrors = [];
const expected403ConsoleErrors = [];
const expected403Labels = new Set();
const pageErrors = [];
const serverErrors = [];
const externalRequests = [];

function record(id, ok, detail = {}) {
  results.push({ id, ok: Boolean(ok), ...detail });
  if (!ok) {
    console.error('FAIL CHECK:', id, JSON.stringify(detail));
  }
}

function normalizeMoneyText(str) {
  return String(str || '').replace(/\s+/g, ' ').trim();
}

function attachListeners(page, label) {
  page.on('console', (msg) => {
    if (msg.type() === 'error') {
      const text = msg.text();
      if (expected403Labels.has(label) && text.includes('status of 403')) {
        expected403ConsoleErrors.push({ page: label, text });
      } else {
        consoleErrors.push({ page: label, text });
      }
    }
  });
  page.on('pageerror', (err) => {
    pageErrors.push({ page: label, error: String(err) });
  });
  page.on('response', (resp) => {
    const url = resp.url();
    if (!url.startsWith(BASE) && !url.startsWith('data:')) {
      externalRequests.push({ page: label, url, status: resp.status() });
    }
    if (resp.status() >= 500) {
      serverErrors.push({ page: label, url, status: resp.status() });
    }
  });
}

async function loginUI(page, email, password) {
  await page.goto(BASE + '/', { waitUntil: 'load' });
  await page.fill('input[name="email"]', email);
  await page.fill('input[name="password"]', password);
  await Promise.all([
    page.waitForNavigation({ waitUntil: 'load' }),
    page.click('button[type="submit"]'),
  ]);
}

async function logoutUI(page) {
  await page.goto(BASE + '/salir/', { waitUntil: 'load' });
  const text = (await page.locator('main').innerText()).replace(/\s+/g, ' ').trim();
  await Promise.all([
    page.waitForNavigation({ waitUntil: 'load' }),
    page.click('main form button[type="submit"], form[action*="salir"] button[type="submit"], main button[type="submit"]'),
  ]);
  return text;
}

(async () => {
  fs.mkdirSync(EV_DIR, { recursive: true });
  const browser = await chromium.launch({
    executablePath: CHROME_PATH,
    headless: true,
    args: ['--no-sandbox', '--disable-dev-shm-usage'],
  });

  try {
    // 0. Server isolation HMAC verification
    const probeCtx = await browser.newContext({ viewport: { width: 1366, height: 900 } });
    const probePage = await probeCtx.newPage();
    attachListeners(probePage, 'hmac');
    await probePage.setExtraHTTPHeaders({ 'X-Audit10B-Challenge': NONCE });
    const homeResp = await probePage.goto(BASE + '/', { waitUntil: 'load' });
    const gotHmac = homeResp.headers()['x-audit10b-proof'];
    const cacheCtrlLogin = homeResp.headers()['cache-control'] || '';
    record('B00_hmac_and_isolation', gotHmac === EXPECTED_HMAC, {
      expected: EXPECTED_HMAC.slice(0, 12),
      got: (gotHmac || '').slice(0, 12),
      cacheCtrlLogin,
    });

    // 1. Anonymous redirect on /ventas/ and /ventas/cobrar/
    const anonSales = await probePage.goto(BASE + '/ventas/', { waitUntil: 'load' });
    record('B01_anon_redirect_sales', new URL(probePage.url()).pathname === '/', {
      status: anonSales.status(),
      finalPath: new URL(probePage.url()).pathname,
    });
    await probeCtx.close();

    // 2. Seller WITHOUT open shift: /ventas/ gate + DOC-02-04/C-04 check on /salir/
    const s2Ctx = await browser.newContext({ viewport: { width: 1366, height: 900 } });
    const s2Page = await s2Ctx.newPage();
    attachListeners(s2Page, 'seller2');
    await loginUI(s2Page, SELLER2_EMAIL, PASS);
    await s2Page.goto(BASE + '/ventas/', { waitUntil: 'load' });
    const s2SalesText = (await s2Page.locator('main').innerText()).replace(/\s+/g, ' ');
    const s2HasSearch = (await s2Page.locator('input[name="query"]').count()) > 0;
    record(
      'B02_seller_no_shift_gate',
      s2SalesText.includes('Abre tu turno para preparar una venta') &&
        s2SalesText.includes('Ir a apertura de caja') &&
        !s2HasSearch,
      { hasSearch: s2HasSearch }
    );
    await s2Page.goto(BASE + '/salir/', { waitUntil: 'load' });
    const s2LogoutText = (await s2Page.locator('main').innerText()).replace(/\s+/g, ' ').trim();
    await s2Page.screenshot({ path: path.join(EV_DIR, '01-logout-seller-no-shift.png'), fullPage: true });
    // Observe literal DOC-02-04/C-04 check on current build
    const doc02SellerNoShiftAccurate =
      s2LogoutText.includes('actualmente no tienes un turno de caja abierto') &&
      !s2LogoutText.toLowerCase().includes('tu turno abierto seguirá ligado');
    record('B03_doc02_04_c04_seller_no_shift_logout', doc02SellerNoShiftAccurate, {
      doc02_c04_cumple: doc02SellerNoShiftAccurate,
      renderedLogoutText: s2LogoutText,
    });
    // Confirm cancel returns safely
    await Promise.all([
      s2Page.waitForNavigation({ waitUntil: 'load' }),
      s2Page.click('a:has-text("Cancelar")'),
    ]);
    record('B04_logout_cancel_keeps_session', new URL(s2Page.url()).pathname !== '/', {
      urlAfterCancel: new URL(s2Page.url()).pathname,
    });
    await logoutUI(s2Page);
    await s2Ctx.close();

    // 3. Admin role perimeter + menu visibility + /salir/ text
    const admCtx = await browser.newContext({ viewport: { width: 1366, height: 900 } });
    const admPage = await admCtx.newPage();
    attachListeners(admPage, 'admin');
    await loginUI(admPage, ADMIN_EMAIL, PASS);
    const admNavText = await admPage.locator('header, nav').allInnerTexts();
    const admHidesPos = !admNavText.join(' ').includes('Preparar venta');
    expected403Labels.add('admin');
    const admSalesResp = await admPage.goto(BASE + '/ventas/', { waitUntil: 'load' });
    const admCheckoutResp = await admPage.goto(BASE + '/ventas/cobrar/', { waitUntil: 'load' });
    expected403Labels.delete('admin');
    await admPage.goto(BASE + '/salir/', { waitUntil: 'load' });
    const admLogoutText = (await admPage.locator('main').innerText()).replace(/\s+/g, ' ').trim();
    record('B05_admin_denied_pos_and_nav_hidden', admHidesPos && admSalesResp.status() === 403 && admCheckoutResp.status() === 403, {
      admHidesPos,
      salesStatus: admSalesResp.status(),
      checkoutStatus: admCheckoutResp.status(),
      admLogoutText,
    });
    await Promise.all([
      admPage.waitForNavigation({ waitUntil: 'load' }),
      admPage.click('main button[type="submit"]'),
    ]);
    await admCtx.close();

    // 4. Almacenero denied POS + write-off receipt redirect check (/inventario/bajas/<uuid>/)
    const whCtx = await browser.newContext({ viewport: { width: 1366, height: 900 } });
    const whPage = await whCtx.newPage();
    attachListeners(whPage, 'almacenero');
    await loginUI(whPage, WH_EMAIL, PASS);
    expected403Labels.add('almacenero');
    const whSalesResp = await whPage.goto(BASE + '/ventas/', { waitUntil: 'load' });
    expected403Labels.delete('almacenero');
    await whPage.goto(BASE + '/inventario/bajas/nueva/', { waitUntil: 'load' });
    // Pick Aceite LOT-ACE-1 write-off link
    const aceRow = whPage.locator('tr', { hasText: 'LOT-ACE-1' });
    await Promise.all([
      whPage.waitForNavigation({ waitUntil: 'load' }),
      aceRow.locator('a:has-text("Dar de baja")').click(),
    ]);
    await whPage.fill('input[name="quantity"]', '2');
    await whPage.selectOption('select[name="reason"]', 'DAÑO');
    await whPage.fill('textarea[name="notes"], input[name="notes"]', 'Rotura prueba 10B');
    await Promise.all([
      whPage.waitForNavigation({ waitUntil: 'load' }),
      whPage.click('button:has-text("Confirmar baja")'),
    ]);
    const writeoffUrl = new URL(whPage.url()).pathname;
    const writeoffRedirectUuidOk = /^\/inventario\/bajas\/[0-9a-f-]+\/$/.test(writeoffUrl);
    await whPage.goto(BASE + '/salir/', { waitUntil: 'load' });
    const whLogoutText = (await whPage.locator('main').innerText()).replace(/\s+/g, ' ').trim();
    record('B06_almacenero_denied_and_writeoff_receipt_redirect', whSalesResp.status() === 403 && writeoffRedirectUuidOk, {
      whSalesStatus: whSalesResp.status(),
      writeoffRedirectUrl: writeoffUrl,
      whLogoutText,
    });
    await Promise.all([
      whPage.waitForNavigation({ waitUntil: 'load' }),
      whPage.click('main button[type="submit"]'),
    ]);
    await whCtx.close();

    // 5. Seller1 opens cash shift, prepares draft, searches, tests limits, expired lots, math, mobile/desktop UI
    const s1Ctx = await browser.newContext({ viewport: { width: 1366, height: 900 } });
    const s1Page = await s1Ctx.newPage();
    attachListeners(s1Page, 'seller1_tab1');
    await loginUI(s1Page, SELLER_EMAIL, PASS);

    await s1Page.goto(BASE + '/caja/abrir/', { waitUntil: 'load' });
    await s1Page.fill('input[name="opening_amount"]', '100.00');
    await Promise.all([
      s1Page.waitForNavigation({ waitUntil: 'load' }),
      s1Page.click('button:has-text("Abrir turno")'),
    ]);

    const s1SalesResp = await s1Page.goto(BASE + '/ventas/', { waitUntil: 'load' });
    const cacheCtrlSales = s1SalesResp.headers()['cache-control'] || '';
    const emptyBody = (await s1Page.locator('main').innerText()).replace(/\s+/g, ' ');
    record(
      'B07_seller_empty_draft_screen',
      emptyBody.includes('Turno abierto') &&
        emptyBody.includes('Aún no agregaste productos a la venta.') &&
        !emptyBody.includes('Cobrar venta') &&
        cacheCtrlSales.includes('no-store'),
      { cacheCtrlSales }
    );

    // Search expired-only product (0 sellable) & non-existent code & special characters
    await s1Page.fill('input[name="query"]', META.zero_barcode);
    await Promise.all([s1Page.waitForNavigation({ waitUntil: 'load' }), s1Page.click('button:has-text("Buscar")')]);
    const zeroMsg = (await s1Page.locator('.empty-table').first().innerText()).trim();

    await s1Page.fill('input[name="query"]', 'NO-EXISTE-999');
    await Promise.all([s1Page.waitForNavigation({ waitUntil: 'load' }), s1Page.click('button:has-text("Buscar")')]);
    const missingMsg = (await s1Page.locator('.empty-table').first().innerText()).trim();

    await s1Page.fill('input[name="query"]', 'Café & Té');
    await Promise.all([s1Page.waitForNavigation({ waitUntil: 'load' }), s1Page.click('button:has-text("Buscar")')]);
    const specialFound = (await s1Page.locator('table').innerText()).includes('Café & Té 100g');

    // Search Tuna (15 valid, 4 expired excluded) & Sardina (3 expires TODAY Lima)
    await s1Page.fill('input[name="query"]', META.tuna_barcode);
    await Promise.all([s1Page.waitForNavigation({ waitUntil: 'load' }), s1Page.click('button:has-text("Buscar")')]);
    const tunaRowText = (await s1Page.locator('tr', { hasText: 'Atún Clásico 170g' }).innerText()).replace(/\s+/g, ' ');
    const expiredExcludedInSearch = tunaRowText.includes(' 15 ') && !tunaRowText.includes(' 19 ');

    // Try quantity 0 (via bypassing HTML min via DOM eval) & insufficient stock 16
    await s1Page.evaluate((pid) => {
      const inp = document.getElementById('quantity-' + pid);
      if (inp) { inp.removeAttribute('min'); inp.removeAttribute('max'); inp.value = '0'; }
    }, META.tuna_id);
    await Promise.all([
      s1Page.waitForNavigation({ waitUntil: 'load' }),
      s1Page.locator('tr', { hasText: 'Atún Clásico 170g' }).locator('button:has-text("Agregar")').click(),
    ]);
    const errQtyZero = (await s1Page.locator('.alert-error').allInnerTexts()).join(' ').trim();

    await s1Page.fill('#quantity-' + META.tuna_id, '16');
    await Promise.all([
      s1Page.waitForNavigation({ waitUntil: 'load' }),
      s1Page.locator('tr', { hasText: 'Atún Clásico 170g' }).locator('button:has-text("Agregar")').click(),
    ]);
    const errOverStock = (await s1Page.locator('.alert-error').allInnerTexts()).join(' ').trim();

    record(
      'B08_search_expired_exclusion_and_add_validation',
      zeroMsg === 'No se encontraron productos con existencias vendibles.' &&
        specialFound &&
        expiredExcludedInSearch &&
        errQtyZero.length > 0 &&
        errOverStock.toLowerCase().includes('existencias vendibles disponibles'),
      { zeroMsg, missingMsg, specialFound, tunaRowText, errQtyZero, errOverStock }
    );

    // Add 2 Tuna, then add 3 more Tuna -> consolidated 5 x 6.50 = 32.50, while search still shows Available 15 (no stock discount!)
    await s1Page.fill('#quantity-' + META.tuna_id, '2');
    await Promise.all([
      s1Page.waitForNavigation({ waitUntil: 'load' }),
      s1Page.locator('tr', { hasText: 'Atún Clásico 170g' }).locator('button:has-text("Agregar")').click(),
    ]);
    await s1Page.fill('input[name="query"]', META.tuna_barcode);
    await Promise.all([s1Page.waitForNavigation({ waitUntil: 'load' }), s1Page.click('button:has-text("Buscar")')]);
    await s1Page.fill('#quantity-' + META.tuna_id, '3');
    await Promise.all([
      s1Page.waitForNavigation({ waitUntil: 'load' }),
      s1Page.locator('tr', { hasText: 'Atún Clásico 170g' }).locator('button:has-text("Agregar")').click(),
    ]);
    await s1Page.fill('input[name="query"]', META.tuna_barcode);
    await Promise.all([s1Page.waitForNavigation({ waitUntil: 'load' }), s1Page.click('button:has-text("Buscar")')]);
    const tunaAvailableAfterAdd = (await s1Page.locator('tr', { hasText: 'Atún Clásico 170g' }).innerText()).replace(/\s+/g, ' ');
    const draftTunaCount = await s1Page.locator('.draft-line', { hasText: 'Atún Clásico 170g' }).count();
    const draftTunaText = (await s1Page.locator('.draft-line', { hasText: 'Atún Clásico 170g' }).innerText()).replace(/\s+/g, ' ');

    // Also add 1 Long-name product + 1 Sardina (expires today) to test multi-line layout & 390x844 mobile viewport!
    await s1Page.fill('input[name="query"]', 'Duraznos');
    await Promise.all([s1Page.waitForNavigation({ waitUntil: 'load' }), s1Page.click('button:has-text("Buscar")')]);
    await Promise.all([
      s1Page.waitForNavigation({ waitUntil: 'load' }),
      s1Page.locator('tr', { hasText: 'Duraznos' }).locator('button:has-text("Agregar")').click(),
    ]);

    // Check 1366x768 laptop viewport
    await s1Page.setViewportSize({ width: 1366, height: 768 });
    const overflow1366 = await s1Page.evaluate(() => ({
      scrollW: document.documentElement.scrollWidth,
      innerW: window.innerWidth,
      overflow: document.documentElement.scrollWidth > window.innerWidth,
    }));
    await s1Page.screenshot({ path: path.join(EV_DIR, '03-draft-desktop-1366x768.png'), fullPage: true });

    // Check 390x844 MOBILE viewport (first time ever in Stage 10!)
    await s1Page.setViewportSize({ width: 390, height: 844 });
    await s1Page.reload({ waitUntil: 'load' });
    const mobileMetrics = await s1Page.evaluate(() => {
      const tbl = document.querySelector('.table-wrap, .table-responsive, table')?.parentElement;
      const nav = document.querySelector('.sidebar-nav, nav');
      const addBtn = document.querySelector('table button[type="submit"]');
      const tblRect = tbl ? tbl.getBoundingClientRect() : null;
      const addRect = addBtn ? addBtn.getBoundingClientRect() : null;
      return {
        scrollW: document.documentElement.scrollWidth,
        innerW: window.innerWidth,
        overflow: document.documentElement.scrollWidth > window.innerWidth,
        tableContainerScrollW: tbl ? tbl.scrollWidth : null,
        tableContainerClientW: tbl ? tbl.clientWidth : null,
        tableInnerHorizontalScroll: tbl ? tbl.scrollWidth > tbl.clientWidth : false,
        agregarButtonClippedAt390: addRect && tblRect ? addRect.right > tblRect.right + 1 : null,
        navScrollW: nav ? nav.scrollWidth : null,
        navClientW: nav ? nav.clientWidth : null,
        navInnerHorizontalScroll: nav ? nav.scrollWidth > nav.clientWidth : false,
        cobrarRect: document.querySelector('a[href*="/ventas/cobrar/"]')?.getBoundingClientRect().toJSON() || null,
        discardRect: document.querySelector('form[action*="/ventas/descartar/"] button')?.getBoundingClientRect().toJSON() || null,
      };
    });
    await s1Page.screenshot({ path: path.join(EV_DIR, '02-draft-mobile-390x844.png'), fullPage: true });

    // Keyboard focus Tab walk on /ventas/ (restore 1366x900)
    await s1Page.setViewportSize({ width: 1366, height: 900 });
    await s1Page.focus('input[name="query"]');
    const focusedTags = [];
    for (let i = 0; i < 14; i++) {
      await s1Page.keyboard.press('Tab');
      const info = await s1Page.evaluate(() => {
        const el = document.activeElement;
        return el ? (el.tagName + ':' + (el.innerText || el.name || el.getAttribute('href') || '').trim().slice(0, 32)) : '';
      });
      focusedTags.push(info);
    }

    record(
      'B09_consolidate_zero_discount_viewports_and_keyboard',
      draftTunaCount === 1 &&
        draftTunaText.includes('5 und.') &&
        tunaAvailableAfterAdd.includes(' 15 ') &&
        !overflow1366.overflow &&
        !mobileMetrics.overflow,
      {
        draftTunaCount,
        draftTunaText,
        overflow1366,
        mobileMetrics,
        focusedSample: focusedTags.slice(0, 10),
      }
    );

    // 6. Test update qty, remove line, and check Aceite stock untouched after earlier writeoff of 2 (was 8 -> now 6)
    const longDraftCard = s1Page.locator('.draft-line', { hasText: 'Duraznos' });
    await Promise.all([s1Page.waitForNavigation({ waitUntil: 'load' }), longDraftCard.locator('button:has-text("Quitar")').click()]);
    const tunaCard = s1Page.locator('.draft-line', { hasText: 'Atún Clásico 170g' });
    await tunaCard.locator('input[name="quantity"]').fill('2');
    await Promise.all([s1Page.waitForNavigation({ waitUntil: 'load' }), tunaCard.locator('button:has-text("Actualizar")').click()]);
    const totals2x650 = normalizeMoneyText(await s1Page.locator('.sale-totals').innerText());

    // 7. Two-tab Chrome test + Admin price changes:
    //    (a) 6.50 -> 8.00: GET /ventas/ keeps frozen price; POST qty update shows price-change alert
    //    (b) 8.00 -> 9.00: Tab 2 opened BEFORE price edit tries stale Confirmar cobro -> rejected cleanly!
    const admEditCtx = await browser.newContext({ viewport: { width: 1366, height: 900 } });
    const admEditPage = await admEditCtx.newPage();
    attachListeners(admEditPage, 'admin_price_edit');
    await loginUI(admEditPage, ADMIN_EMAIL, PASS);
    await admEditPage.goto(BASE + `/productos/${META.tuna_id}/editar/`, { waitUntil: 'load' });
    await admEditPage.fill('input[name="sale_price"]', '8.00');
    await Promise.all([
      admEditPage.waitForNavigation({ waitUntil: 'load' }),
      admEditPage.click('button:has-text("Guardar cambios")'),
    ]);

    // (a) Seller Tab 1 reloads GET /ventas/ -> MUST preserve frozen unit_price S/ 6.50 (C-04!)
    await s1Page.reload({ waitUntil: 'load' });
    const tab1AfterGetReload = normalizeMoneyText(await s1Page.locator('.draft-line', { hasText: 'Atún Clásico 170g' }).innerText());
    await s1Page.screenshot({ path: path.join(EV_DIR, '04-get-frozen-price.png'), fullPage: true });

    // (a) Seller Tab 1 submits POST update qty 2->3 -> updates unit_price to S/ 8.00 and displays price-change warning
    await s1Page.locator('.draft-line', { hasText: 'Atún Clásico 170g' }).locator('input[name="quantity"]').fill('3');
    await Promise.all([
      s1Page.waitForNavigation({ waitUntil: 'load' }),
      s1Page.locator('.draft-line', { hasText: 'Atún Clásico 170g' }).locator('button:has-text("Actualizar")').click(),
    ]);
    const tab1WarnText = (await s1Page.locator('.alert-warning, .alert, main').allInnerTexts()).join(' ').replace(/\s+/g, ' ');

    // (b) Now Tab 2 opens /ventas/cobrar/ (3 x 8.00 = 24.00), THEN Admin changes price 8.00 -> 9.00
    const s1Tab2 = await s1Ctx.newPage();
    attachListeners(s1Tab2, 'seller1_tab2');
    await s1Tab2.goto(BASE + '/ventas/cobrar/', { waitUntil: 'load' });
    const tab2OldCheckoutTotals = normalizeMoneyText(await s1Tab2.locator('.sale-totals').innerText());

    await admEditPage.goto(BASE + `/productos/${META.tuna_id}/editar/`, { waitUntil: 'load' });
    await admEditPage.fill('input[name="sale_price"]', '9.00');
    await Promise.all([
      admEditPage.waitForNavigation({ waitUntil: 'load' }),
      admEditPage.click('button:has-text("Guardar cambios")'),
    ]);

    // Tab 2 (opened BEFORE 8.00->9.00 price change) submits stale Confirmar cobro -> MUST reject cleanly!
    await s1Tab2.fill('input[name="cash_received"]', '25.00');
    await Promise.all([
      s1Tab2.waitForNavigation({ waitUntil: 'load' }),
      s1Tab2.click('button:has-text("Confirmar cobro")'),
    ]);
    const tab2StaleErr = (await s1Tab2.locator('.alert-error').allInnerTexts()).join(' ').trim();
    const tab2AfterStaleUrl = new URL(s1Tab2.url()).pathname;
    await s1Tab2.screenshot({ path: path.join(EV_DIR, '05-stale-checkout-rejected.png'), fullPage: true });
    await s1Tab2.close();

    // Admin deactivates Tuna -> Seller Tab 1 tries Actualizar -> blocked; Admin reactivates -> ready for B11/B13
    await admEditPage.goto(BASE + '/productos/?q=' + META.tuna_barcode, { waitUntil: 'load' });
    await Promise.all([
      admEditPage.waitForNavigation({ waitUntil: 'load' }),
      admEditPage.locator(`form[action="/productos/${META.tuna_id}/disponibilidad/"] button`).click(),
    ]);
    await s1Page.locator('.draft-line', { hasText: 'Atún Clásico 170g' }).locator('input[name="quantity"]').fill('4');
    await Promise.all([
      s1Page.waitForNavigation({ waitUntil: 'load' }),
      s1Page.locator('.draft-line', { hasText: 'Atún Clásico 170g' }).locator('button:has-text("Actualizar")').click(),
    ]);
    const deactErr = (await s1Page.locator('.alert-error').allInnerTexts()).join(' ').trim();
    await Promise.all([
      admEditPage.waitForNavigation({ waitUntil: 'load' }),
      admEditPage.locator(`form[action="/productos/${META.tuna_id}/disponibilidad/"] button`).click(),
    ]);
    await admEditCtx.close();

    record(
      'B10_dec12_price_freeze_stale_checkout_and_deactivation',
      (tab1AfterGetReload.includes('6.50') || tab1AfterGetReload.includes('6,50')) &&
        tab1WarnText.includes('se actualizó de S/ 6.50 a S/ 8.00') &&
        tab2AfterStaleUrl === '/ventas/cobrar/' &&
        tab2StaleErr.includes('cambió de S/ 8.00 a S/ 9.00') &&
        deactErr.toLowerCase().includes('disponible'),
      {
        totals2x650,
        tab2OldCheckoutTotals,
        tab1AfterGetReload,
        tab1HasPriceWarn: tab1WarnText.includes('se actualizó de S/ 6.50 a S/ 8.00'),
        tab2AfterStaleUrl,
        tab2StaleErr,
        deactErr,
      }
    );

    // 8. Cash close blocked while active draft exists (RN-30) -> discard -> verify empty
    await s1Page.goto(BASE + '/caja/cerrar/', { waitUntil: 'load' });
    await s1Page.fill('input[name="counted_amount"]', '100.00');
    await Promise.all([s1Page.waitForNavigation({ waitUntil: 'load' }), s1Page.click('button[type="submit"]')]);
    const closeBlockedErr = (await s1Page.locator('.alert-error').allInnerTexts()).join(' ').trim();
    record('B11_rn30_close_blocked_by_active_draft', closeBlockedErr.toLowerCase().includes('venta en preparación'), {
      closeBlockedErr,
    });

    // 9. Explicit HU-VEN-01a / RN-22 UI check: verify NO idle lock timer/modal/route in client DOM
    await s1Page.goto(BASE + '/ventas/', { waitUntil: 'load' });
    const rawHtmlSales = await s1Page.content();
    const hasIdleUiLock = /inactividad|screen.?lock|bloqueo.*puesto|desbloquear.*sesi/i.test(rawHtmlSales);
    const cookies = await s1Ctx.cookies();
    record('B12_hu_ven_01a_browser_lock_absent', !hasIdleUiLock, {
      hu_ven_01a_cumple: false,
      hasIdleUiLock,
      cookieNames: cookies.map((c) => ({ name: c.name, session: c.session, httpOnly: c.httpOnly })),
    });

    // 10. Logout WITH active draft -> confirm discard -> Back button protection -> relogin recovery of shift without draft -> close shift
    await s1Page.goto(BASE + '/salir/', { waitUntil: 'load' });
    const logoutWithDraftText = (await s1Page.locator('main').innerText()).replace(/\s+/g, ' ').trim();
    await s1Page.screenshot({ path: path.join(EV_DIR, '06-logout-seller-with-draft.png'), fullPage: true });
    await Promise.all([
      s1Page.waitForNavigation({ waitUntil: 'load' }),
      s1Page.click('main button[type="submit"]'),
    ]);
    const pathAfterLogout = new URL(s1Page.url()).pathname;
    await s1Page.goBack({ waitUntil: 'load' });
    const pathAfterBack = new URL(s1Page.url()).pathname;

    // Relogin seller -> shift still open, draft empty -> close shift cleanly
    await loginUI(s1Page, SELLER_EMAIL, PASS);
    await s1Page.goto(BASE + '/ventas/', { waitUntil: 'load' });
    const reloginSalesText = (await s1Page.locator('main').innerText()).replace(/\s+/g, ' ');
    await s1Page.goto(BASE + '/caja/cerrar/', { waitUntil: 'load' });
    await s1Page.fill('input[name="counted_amount"]', '100.00');
    await Promise.all([s1Page.waitForNavigation({ waitUntil: 'load' }), s1Page.click('button[type="submit"]')]);
    const finalClosePath = new URL(s1Page.url()).pathname;
    await s1Ctx.close();

    record(
      'B13_logout_discard_back_relogin_and_clean_close',
      logoutWithDraftText.includes('La venta en preparación se descartará') &&
        pathAfterLogout === '/' &&
        pathAfterBack === '/' &&
        reloginSalesText.includes('Aún no agregaste productos a la venta.') &&
        /^\/caja\/turnos\/[0-9a-f-]+\/cerrado\/$/.test(finalClosePath),
      {
        logoutWithDraftText,
        pathAfterLogout,
        pathAfterBack,
        finalClosePath,
      }
    );

    const summary = {
      timestamp_utc: new Date().toISOString(),
      total_checks: results.length,
      passed_checks: results.filter((r) => r.ok).length,
      failed_checks: results.filter((r) => !r.ok).length,
      console_errors: consoleErrors,
      expected_403_console_errors: expected403ConsoleErrors,
      page_errors: pageErrors,
      server_500_errors: serverErrors,
      external_requests: externalRequests,
      checks: results,
    };
    fs.writeFileSync(path.join(EV_DIR, 'browser-results.json'), JSON.stringify(summary, null, 2) + '\n', 'utf-8');
    console.log(JSON.stringify({
      total_checks: summary.total_checks,
      passed_checks: summary.passed_checks,
      failed_checks: summary.failed_checks,
      console_errors: consoleErrors.length,
      expected_403_console_errors: expected403ConsoleErrors.length,
      page_errors: pageErrors.length,
      server_500_errors: serverErrors.length,
      external_requests: externalRequests.length,
    }, null, 2));

    if (
      summary.failed_checks > 0 ||
      consoleErrors.length > 0 ||
      pageErrors.length > 0 ||
      serverErrors.length > 0 ||
      externalRequests.length > 0
    ) {
      process.exitCode = 1;
    }
  } finally {
    await browser.close();
  }
})();
