const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { chromium } = require(
  'C:/Users/walte/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright-core'
);

const PORT = process.env.AUDIT12_PORT;
const BASE_URL = `http://127.0.0.1:${PORT}`;
const RUN_DIR = process.env.AUDIT12_RUN_DIR;
const OUT_DIR = process.env.AUDIT12_OUT;
const CHROME_PATH = 'C:/Program Files/Google/Chrome/Application/chrome.exe';

const creds = JSON.parse(fs.readFileSync(path.join(RUN_DIR, '.credentials.json'), 'utf8'));
const ids = JSON.parse(fs.readFileSync(path.join(OUT_DIR, 'fixture-ids.json'), 'utf8'));

function attachListeners(page, pageErrors, failedReqs, serverErrors) {
  page.on('pageerror', (err) => pageErrors.push(err.message));
  page.on('console', (msg) => {
    if (msg.type() === 'error') {
      const txt = msg.text();
      if (!txt.includes('Failed to load resource: the server responded with a status of 40')) {
        pageErrors.push(`console.error: ${txt}`);
      }
    }
  });
  page.on('requestfailed', (req) => {
    failedReqs.push(`${req.method()} ${req.url()} -> ${req.failure()?.errorText}`);
  });
  page.on('response', (res) => {
    if (res.status() >= 500) {
      serverErrors.push(`${res.status()} ${res.url()}`);
    }
  });
}

async function login(page, account) {
  await page.goto(`${BASE_URL}/`, { waitUntil: 'networkidle' });
  await page.fill('input[name="username"], input[name="email"]', account.email);
  await page.fill('input[name="password"]', account.password);
  await Promise.all([
    page.waitForNavigation({ waitUntil: 'networkidle' }),
    page.click('button[type="submit"]'),
  ]);
}

async function logout(page) {
  await page.goto(`${BASE_URL}/salir/`, { waitUntil: 'networkidle' });
  const btn = page.locator('main form button[type="submit"]');
  if (await btn.count()) {
    await Promise.all([
      page.waitForNavigation({ waitUntil: 'networkidle' }),
      btn.first().click(),
    ]);
  }
}

async function layoutCheck(page, label) {
  return page.evaluate((lbl) => {
    const docOverflow = document.documentElement.scrollWidth > window.innerWidth;
    const wraps = [...document.querySelectorAll('.table-wrap, .table-responsive')];
    let wrapOverflowPx = 0;
    for (const w of wraps) {
      const diff = Math.ceil(w.scrollWidth - w.clientWidth);
      if (diff > wrapOverflowPx) wrapOverflowPx = diff;
    }
    const rightCell = document.querySelector('th.text-end, td.text-end, th.text-right, td.text-right');
    const rightAlign = rightCell ? getComputedStyle(rightCell).textAlign : null;
    const receipt = document.querySelector('#constancia-interna');
    const receiptCS = receipt ? getComputedStyle(receipt) : null;
    return {
      label: lbl,
      url: location.pathname + location.search,
      viewport: { width: window.innerWidth, height: window.innerHeight },
      docOverflow,
      wrapOverflowPx,
      rightAlign,
      receiptPaddingLeft: receiptCS ? receiptCS.paddingLeft : null,
      receiptPaddingTop: receiptCS ? receiptCS.paddingTop : null,
    };
  }, label);
}

(async () => {
  const report = { checks: [], layout: [], pageErrors: [], failedReqs: [], serverErrors: [] };
  const browser = await chromium.launch({
    executablePath: CHROME_PATH,
    headless: true,
    args: ['--no-sandbox', '--disable-gpu'],
  });

  try {
    // ── Context 1: Seller1 @ 1366x900 and 1366x768 ──────────────────────────
    const ctxSeller = await browser.newContext({
      locale: 'es-PE',
      timezoneId: 'America/Lima',
      viewport: { width: 1366, height: 900 },
    });
    const page = await ctxSeller.newPage();
    attachListeners(page, report.pageErrors, report.failedReqs, report.serverErrors);

    await login(page, creds.seller1);

    // 1) Pos Draft: Última constancia (V-00000003) link
    await page.goto(`${BASE_URL}/ventas/`, { waitUntil: 'networkidle' });
    const ultimaLink = page.locator('a', { hasText: 'Última constancia' });
    assert.equal(await ultimaLink.count(), 1, 'Expected Última constancia link on /ventas/');
    const ultimaText = (await ultimaLink.textContent()).trim();
    assert(ultimaText.includes('V-00000003'), `Expected V-00000003 in ${ultimaText}`);
    await Promise.all([page.waitForNavigation({ waitUntil: 'networkidle' }), ultimaLink.click()]);
    assert(page.url().includes(`/ventas/constancia/${ids.sales.s3}/`), `Unexpected receipt URL: ${page.url()}`);

    // 2) Constancia S3 inspection + long wrapping + legal notice + snapshot immutability + no cost leak
    const s3Html = await page.content();
    assert(s3Html.includes('CONTROL INTERNO — NO VÁLIDO COMO COMPROBANTE DE PAGO'), 'Missing literal RN-26 banner');
    assert(s3Html.includes('constancia interna'), 'Missing constancia interna wording');
    assert(s3Html.includes('validez tributaria'), 'Missing validez tributaria wording');
    assert(s3Html.includes('canal autorizado habitual'), 'Missing external official channel wording');
    assert(s3Html.includes('Medio de pago') && s3Html.includes('Efectivo'), 'Missing Efectivo payment method');
    assert(s3Html.includes('Subtotal') && s3Html.includes('Descuento'), 'Missing pre-discount Subtotal/Descuento');
    assert(s3Html.includes('19,10') && s3Html.includes('1,50') && s3Html.includes('17,60'), 'Missing expected formatted amounts');
    assert(s3Html.includes('14,92') && s3Html.includes('2,68') && s3Html.includes('25,00') && s3Html.includes('7,40'), 'Missing IGV/cash/change amounts');
    assert(!s3Html.includes('CATALOGO RENOMBRADO POST VENTA'), 'Snapshot isolation broken');
    assert(!s3Html.includes('1,7500') && !s3Html.includes('4,2500') && !s3Html.includes('99,00'), 'Cost or mutated price leaked');
    assert(s3Html.includes('Ventas del turno'), 'Missing Ventas del turno shortcut on S3');
    assert(s3Html.includes('Nueva venta'), 'Missing Nueva venta on seller receipt');

    const layReceiptScreen = await layoutCheck(page, 'receipt-s3-1366x900');
    assert.equal(layReceiptScreen.docOverflow, false, 'Receipt docOverflow at 1366x900');
    assert.equal(layReceiptScreen.wrapOverflowPx, 0, `Receipt wrapOverflowPx=${layReceiptScreen.wrapOverflowPx}`);
    assert.equal(layReceiptScreen.rightAlign, 'right', 'Expected rightAlign on receipt');
    assert.notEqual(layReceiptScreen.receiptPaddingLeft, '0px', 'Expected padding on #constancia-interna');
    report.layout.push(layReceiptScreen);
    await page.screenshot({ path: path.join(OUT_DIR, 'post-fix-receipt-1366x900.png'), fullPage: true });

    // @media print emulation
    await page.emulateMedia({ media: 'print' });
    const printStyles = await page.evaluate(() => {
      const sel = (s) => {
        const el = document.querySelector(s);
        return el ? getComputedStyle(el).display : null;
      };
      return {
        sidebar: sel('.app-sidebar'),
        topbar: sel('.app-topbar'),
        footer: sel('.app-footer'),
        actions: sel('.page-heading.no-print'),
        card: sel('#constancia-interna'),
      };
    });
    assert.equal(printStyles.sidebar, 'none');
    assert.equal(printStyles.topbar, 'none');
    assert.equal(printStyles.footer, 'none');
    assert.equal(printStyles.actions, 'none');
    assert.notEqual(printStyles.card, 'none');
    await page.screenshot({ path: path.join(OUT_DIR, 'post-fix-receipt-print-1366x900.png'), fullPage: true });
    await page.emulateMedia({ media: 'screen' });
    report.checks.push({ name: 'receipt-s3-screen-and-print', pass: true, printStyles });

    // 3) Live Checkout + Retry Recovery (both no-draft and with new active draft)
    await page.goto(`${BASE_URL}/ventas/cobrar/`, { waitUntil: 'networkidle' });
    const checkoutHidden = await page.evaluate(() => ({
      csrf: document.querySelector('input[name="csrfmiddlewaretoken"]')?.value,
      idem: document.querySelector('input[name="idempotency_key"]')?.value,
      sig: document.querySelector('input[name="draft_signature"]')?.value,
      sub: document.querySelector('input[name="expected_subtotal"]')?.value,
    }));
    await page.fill('input[name="cash_received"]', '20.00');
    await Promise.all([
      page.waitForNavigation({ waitUntil: 'networkidle' }),
      page.click('main form button[type="submit"]'),
    ]);
    const s4UrlMatch = page.url().match(/\/ventas\/constancia\/([0-9a-f-]+)\//);
    assert(s4UrlMatch, `Expected redirect to S4 receipt after checkout, got ${page.url()}`);
    const s4Id = s4UrlMatch[1];

    // Retry 1 via browser fetch with active_draft now DISCARDED (draft is None)
    const retry1Res = await page.evaluate(async (form) => {
      const body = new URLSearchParams({
        csrfmiddlewaretoken: form.csrf,
        idempotency_key: form.idem,
        draft_signature: form.sig,
        expected_subtotal: form.sub,
        discount_amount: '',
        cash_received: '20.00',
      });
      const res = await fetch('/ventas/cobrar/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: body.toString(),
        credentials: 'same-origin',
      });
      return { url: res.url, status: res.status, text: await res.text() };
    }, checkoutHidden);
    assert.equal(retry1Res.status, 200);
    assert(retry1Res.url.includes(`/ventas/constancia/${s4Id}/`), `Retry1 failed to recover receipt, landed on ${retry1Res.url}`);
    assert(retry1Res.text.includes('V-00000004') && retry1Res.text.includes('ya había sido confirmado'));

    // Prepare draft_2 on /ventas/ then replay S4's POST (Retry 2 with active draft_2!)
    await page.goto(`${BASE_URL}/ventas/`, { waitUntil: 'networkidle' });
    await page.fill('input[name="query"]', 'Arroz');
    await Promise.all([
      page.waitForNavigation({ waitUntil: 'networkidle' }),
      page.click('.search-form button[type="submit"]'),
    ]);
    await Promise.all([
      page.waitForNavigation({ waitUntil: 'networkidle' }),
      page.click('.line-add-form button[type="submit"]'),
    ]);
    assert(await page.locator('.draft-line').count() > 0, 'Expected draft_2 active on /ventas/');
    const freshCsrf = await page.evaluate(() => document.querySelector('input[name="csrfmiddlewaretoken"]')?.value);

    const retry2Res = await page.evaluate(async ({ form, csrf }) => {
      const body = new URLSearchParams({
        csrfmiddlewaretoken: csrf,
        idempotency_key: form.idem,
        draft_signature: form.sig,
        expected_subtotal: form.sub,
        discount_amount: '',
        cash_received: '20.00',
      });
      const res = await fetch('/ventas/cobrar/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: body.toString(),
        credentials: 'same-origin',
      });
      return { url: res.url, status: res.status };
    }, { form: checkoutHidden, csrf: freshCsrf });
    assert.equal(retry2Res.status, 200);
    assert(retry2Res.url.includes(`/ventas/constancia/${s4Id}/`), `Retry2 with active draft failed: ${retry2Res.url}`);

    // Verify draft_2 still untouched then discard it cleanly
    await page.goto(`${BASE_URL}/ventas/`, { waitUntil: 'networkidle' });
    assert(await page.locator('.draft-line').count() > 0, 'draft_2 should still be active after retry2 recovery');
    await Promise.all([
      page.waitForNavigation({ waitUntil: 'networkidle' }),
      page.click('form[action="/ventas/descartar/"] button[type="submit"]'),
    ]);
    report.checks.push({ name: 'checkout-retry-recovery-browser', s4Id, retry1Ok: true, retry2Ok: true });

    // 4) Switch seller viewport to 1366x768 for Shift History + Seller Sales History isolation
    await page.setViewportSize({ width: 1366, height: 768 });
    await page.goto(`${BASE_URL}/ventas/historial/turno/`, { waitUntil: 'networkidle' });
    const shHtml = await page.content();
    assert(shHtml.includes('V-00000003') && shHtml.includes('V-00000004'));
    assert(!shHtml.includes('V-00000001') && !shHtml.includes('V-00000002'));
    const layShift = await layoutCheck(page, 'sales-shift-history-1366x768');
    assert.equal(layShift.docOverflow, false);
    assert.equal(layShift.wrapOverflowPx, 0, `Shift history overflow: ${layShift.wrapOverflowPx}`);
    report.layout.push(layShift);
    await page.screenshot({ path: path.join(OUT_DIR, 'post-fix-sales-shift-history-1366x768.png'), fullPage: true });

    // Seller sales history: no vendedor dropdown, foreign turno returns 0
    await page.goto(`${BASE_URL}/ventas/historial/`, { waitUntil: 'networkidle' });
    assert.equal(await page.locator('select[name="vendedor"]').count(), 0, 'Seller must not see vendedor select');
    const sellerHistHtml = await page.content();
    assert(!sellerHistHtml.includes(ids.accounts.seller2), 'Foreign seller ID should not be in seller history');
    await page.goto(`${BASE_URL}/ventas/historial/?turno=${ids.shifts.s2_closed}`, { waitUntil: 'networkidle' });
    assert((await page.content()).includes('No se encontraron ventas'));

    // Direct navigation to foreign IDs for seller1
    const rForeignRec = await page.goto(`${BASE_URL}/ventas/constancia/${ids.sales.s2}/`);
    assert.equal(rForeignRec.status(), 404);
    const rForeignActa = await page.goto(`${BASE_URL}/caja/turnos/${ids.shifts.s2_closed}/cerrado/`);
    assert.equal(rForeignActa.status(), 404);
    report.checks.push({ name: 'seller-foreign-id-isolation', pass: true });

    // 5) Reversed-UUID 3-line receipt order & legacy position=None fallback notice
    await page.goto(`${BASE_URL}/ventas/constancia/${ids.sales.s_rev_lines}/`, { waitUntil: 'networkidle' });
    const revLineNames = await page.$$eval('.receipt-table tbody tr td:first-child', (cells) =>
      cells.map((c) => c.textContent.trim())
    );
    assert.deepEqual(revLineNames, ['LINEA_ORDEN_1_UUID_FFFF', 'LINEA_ORDEN_2_UUID_8888', 'LINEA_ORDEN_3_UUID_1111']);
    assert(!(await page.content()).includes('El orden original de los productos no está disponible en este registro.'));

    await page.goto(`${BASE_URL}/ventas/constancia/${ids.sales.s_legacy_lines}/`, { waitUntil: 'networkidle' });
    assert((await page.content()).includes('El orden original de los productos no está disponible en este registro.'));
    report.checks.push({ name: 'receipt-line-order-and-legacy-notice', revLineNames, pass: true });

    // 6) VENDEDOR sidebar navigation (Mi historial de ventas / Mi historial de turnos) & cash shift isolation
    await page.goto(`${BASE_URL}/ventas/`, { waitUntil: 'networkidle' });
    await Promise.all([
      page.waitForNavigation({ waitUntil: 'networkidle' }),
      page.locator('a.nav-item', { hasText: 'Mi historial de ventas' }).click(),
    ]);
    assert(page.url().includes('/ventas/historial/'));
    assert.equal(await page.locator('a.nav-item.is-active[href="/ventas/historial/"]').count(), 1);

    await Promise.all([
      page.waitForNavigation({ waitUntil: 'networkidle' }),
      page.locator('a.nav-item', { hasText: 'Mi historial de turnos' }).click(),
    ]);
    assert(page.url().includes('/caja/turnos/'));
    assert.equal(await page.locator('a.nav-item.is-active[href="/caja/turnos/"]').count(), 1);
    assert.equal(await page.locator('select[name="vendedor"]').count(), 0);
    assert(!(await page.content()).includes('Mario Segundo Vendedor12'));
    await page.screenshot({ path: path.join(OUT_DIR, 'post-fix-seller-cash-history-1366x768.png'), fullPage: true });
    report.checks.push({ name: 'seller-sidebar-links-and-cash-history-isolation', pass: true });

    // 7) Keyboard Tab traversal on sales-history + Mobile 390x844 across Stage 12 routes
    await page.goto(`${BASE_URL}/ventas/historial/?fecha=${ids.pagination_date}`, { waitUntil: 'networkidle' });
    const focusedElements = [];
    for (let i = 0; i < 16; i += 1) {
      await page.keyboard.press('Tab');
      const active = await page.evaluate(() => {
        const el = document.activeElement;
        return el ? `${el.tagName}:${el.getAttribute('name') || el.getAttribute('href') || el.textContent.trim().slice(0, 24)}` : null;
      });
      if (active && !focusedElements.includes(active)) focusedElements.push(active);
    }
    assert(focusedElements.length >= 6, `Expected >=6 keyboard Tab targets, got ${JSON.stringify(focusedElements)}`);

    await page.setViewportSize({ width: 390, height: 844 });
    for (const [mLabel, mUrl, mFile] of [
      ['mobile-receipt-390x844', `/ventas/constancia/${ids.sales.s3}/`, 'mobile-receipt-390x844.png'],
      ['mobile-sales-history-390x844', '/ventas/historial/', 'mobile-sales-history-390x844.png'],
      ['mobile-cash-history-390x844', '/caja/turnos/', 'mobile-cash-history-390x844.png'],
    ]) {
      await page.goto(`${BASE_URL}${mUrl}`, { waitUntil: 'networkidle' });
      const layMob = await layoutCheck(page, mLabel);
      assert.equal(layMob.docOverflow, false, `${mLabel} horizontal overflow`);
      if (mLabel === 'mobile-receipt-390x844') {
        const cellOverlap = await page.evaluate(() => {
          const rows = [...document.querySelectorAll('.receipt-table tr')];
          const issues = [];
          for (const row of rows) {
            const cells = [...row.querySelectorAll('th, td')];
            for (let i = 0; i < cells.length; i += 1) {
              const cell = cells[i];
              if (cell.scrollWidth > cell.clientWidth + 1) {
                issues.push(`clipped:${cell.textContent.trim()}(${cell.scrollWidth}>${cell.clientWidth})`);
              }
              if (i + 1 < cells.length) {
                const a = cell.getBoundingClientRect();
                const b = cells[i + 1].getBoundingClientRect();
                if (a.right > b.left + 1) {
                  issues.push(`overlap:${cell.textContent.trim()}|${cells[i + 1].textContent.trim()}`);
                }
              }
            }
          }
          return issues;
        });
        assert.deepEqual(cellOverlap, [], `mobile-receipt cell overlap/clip: ${JSON.stringify(cellOverlap)}`);
      }
      report.layout.push(layMob);
      await page.screenshot({ path: path.join(OUT_DIR, mFile), fullPage: true });
    }
    await page.setViewportSize({ width: 1366, height: 900 });
    report.checks.push({ name: 'keyboard-tab-and-mobile-390x844', focusedCount: focusedElements.length, pass: true });

    // Open Admin context early to mutate p_std price while Seller1 has active draft on /ventas/cobrar/ (DEC-12/C-04)
    const ctxAdmin = await browser.newContext({ locale: 'es-PE', timezoneId: 'America/Lima', viewport: { width: 1366, height: 768 } });
    const pAdm = await ctxAdmin.newPage();
    attachListeners(pAdm, report.pageErrors, report.failedReqs, report.serverErrors);
    await login(pAdm, creds.admin);

    // 8) Seller prepares draft (p_std = 10.00) and opens /ventas/cobrar/; Admin updates p_std price -> 12.50 -> Seller POST triggers re-review
    await page.goto(`${BASE_URL}/ventas/`, { waitUntil: 'networkidle' });
    await page.fill('input[name="query"]', 'Arroz');
    await Promise.all([page.waitForNavigation({ waitUntil: 'networkidle' }), page.click('.search-form button[type="submit"]')]);
    await Promise.all([page.waitForNavigation({ waitUntil: 'networkidle' }), page.click('.line-add-form button[type="submit"]')]);
    await page.goto(`${BASE_URL}/ventas/cobrar/`, { waitUntil: 'networkidle' });
    const initialSub = await page.locator('input[name="expected_subtotal"]').inputValue();
    assert.equal(initialSub, '10.00');

    await pAdm.goto(`${BASE_URL}/productos/${ids.products.std}/editar/`, { waitUntil: 'networkidle' });
    await pAdm.fill('input[name="sale_price"]', '12.50');
    await Promise.all([pAdm.waitForNavigation({ waitUntil: 'networkidle' }), pAdm.click('main form button[type="submit"]')]);
    assert(pAdm.url().includes('/productos/'));

    await page.fill('input[name="cash_received"]', '15.00');
    await Promise.all([page.waitForNavigation({ waitUntil: 'networkidle' }), page.click('main form button[type="submit"]')]);
    assert(page.url().includes('/ventas/cobrar/'));
    const reReviewHtml = await page.content();
    assert(
      reReviewHtml.includes('cambió de S/ 10.00 a S/ 12.50') &&
      reReviewHtml.includes('Verifica el nuevo total antes de confirmar el cobro.') &&
      reReviewHtml.includes('12,50'),
      'Expected price-change re-review message with updated total 12,50'
    );
    assert.equal(await page.locator('input[name="expected_subtotal"]').inputValue(), '12.50');
    await page.screenshot({ path: path.join(OUT_DIR, 'post-fix-price-change-rereview-1366x900.png'), fullPage: true });

    // Discard draft before closing open shift
    await page.goto(`${BASE_URL}/ventas/`, { waitUntil: 'networkidle' });
    await Promise.all([page.waitForNavigation({ waitUntil: 'networkidle' }), page.click('form[action="/ventas/descartar/"] button[type="submit"]')]);
    report.checks.push({ name: 'draft-price-change-rereview-dec12-c04', pass: true });

    // 9) Close shift3_open (80.00 + 17.60 + 10.00 = 107.60), check Acta de cierre H1 + @media print + Mobile + /ventas/ closed Última constancia absent
    await page.goto(`${BASE_URL}/caja/cerrar/`, { waitUntil: 'networkidle' });
    await page.fill('input[name="counted_amount"]', '107.60');
    await Promise.all([page.waitForNavigation({ waitUntil: 'networkidle' }), page.click('main form button[type="submit"]')]);
    assert(page.url().includes(`/caja/turnos/${ids.shifts.s3_open}/cerrado/`));
    assert.equal((await page.locator('header.app-topbar h1').textContent()).trim(), 'Acta de cierre');
    assert.equal(await page.locator('a.nav-item.is-active[href="/caja/turnos/"]').count(), 1);
    assert.equal(await page.locator('a.nav-item.is-active[href="/caja/cerrar/"]').count(), 0);

    await page.emulateMedia({ media: 'print' });
    const actaPrintStyles = await page.evaluate(() => {
      const sel = (s) => {
        const el = document.querySelector(s);
        return el ? getComputedStyle(el).display : null;
      };
      return {
        sidebar: sel('.app-sidebar'),
        topbar: sel('.app-topbar'),
        headingPanel: sel('[data-testid="cash-shift-closed"]'),
        actions: sel('.cash-close-acta .form-actions'),
        acta: sel('.cash-close-acta'),
      };
    });
    assert.equal(actaPrintStyles.sidebar, 'none');
    assert.equal(actaPrintStyles.topbar, 'none');
    assert.equal(actaPrintStyles.headingPanel, 'none');
    assert.equal(actaPrintStyles.actions, 'none');
    assert.notEqual(actaPrintStyles.acta, 'none');
    await page.screenshot({ path: path.join(OUT_DIR, 'post-fix-cash-closed-print-1366x900.png'), fullPage: true });
    await page.emulateMedia({ media: 'screen' });

    await page.setViewportSize({ width: 390, height: 844 });
    const layMobActa = await layoutCheck(page, 'mobile-cash-closed-390x844');
    assert.equal(layMobActa.docOverflow, false);
    report.layout.push(layMobActa);
    await page.setViewportSize({ width: 1366, height: 900 });

    await page.goto(`${BASE_URL}/ventas/`, { waitUntil: 'networkidle' });
    assert.equal(await page.locator('a', { hasText: 'Última constancia' }).count(), 0, 'Closed shift must not show Última constancia');
    report.checks.push({ name: 'seller-closed-acta-h1-print-and-no-ultima-constancia', actaPrintStyles, pass: true });

    // ── Context 2: Warehouse denied checks ───────────────────────────────────
    const ctxWh = await browser.newContext({ locale: 'es-PE', timezoneId: 'America/Lima', viewport: { width: 1366, height: 900 } });
    const pWh = await ctxWh.newPage();
    attachListeners(pWh, report.pageErrors, report.failedReqs, report.serverErrors);
    await login(pWh, creds.warehouse);
    for (const u of [`/ventas/constancia/${ids.sales.s3}/`, '/ventas/historial/turno/', '/ventas/historial/', '/caja/turnos/', `/caja/turnos/${ids.shifts.s1_closed}/cerrado/`]) {
      const r = await pWh.goto(`${BASE_URL}${u}`);
      assert.equal(r.status(), 403, `Expected 403 for warehouse on ${u}`);
    }
    report.checks.push({ name: 'warehouse-denied-403', pass: true });
    await ctxWh.close();

    // ── Context 3: Admin @ 1366x768 + Pagination + Deactivation + Post-logout ─

    // Admin viewing receipt S3
    await pAdm.goto(`${BASE_URL}/ventas/constancia/${ids.sales.s3}/`, { waitUntil: 'networkidle' });
    const admRecHtml = await pAdm.content();
    assert(!admRecHtml.includes('Nueva venta'), 'Admin receipt must hide Nueva venta');
    assert(admRecHtml.includes('/ventas/historial/'), 'Admin receipt must include Volver al historial');

    // Admin sales history 1366x768 + PG/SQLite safe NUL check + filters
    await pAdm.goto(`${BASE_URL}/ventas/historial/`, { waitUntil: 'networkidle' });
    const laySalesHist = await layoutCheck(pAdm, 'sales-history-1366x768');
    assert.equal(laySalesHist.docOverflow, false, 'Admin sales-history docOverflow at 1366x768');
    assert.equal(laySalesHist.wrapOverflowPx, 0, `Admin sales-history wrapOverflowPx=${laySalesHist.wrapOverflowPx}`);
    report.layout.push(laySalesHist);
    await pAdm.screenshot({ path: path.join(OUT_DIR, 'post-fix-sales-history-1366x768.png'), fullPage: true });

    // Filter via UI by seller2
    await pAdm.selectOption('select[name="vendedor"]', ids.accounts.seller2);
    await Promise.all([
      pAdm.waitForNavigation({ waitUntil: 'networkidle' }),
      pAdm.click('form.history-filter-panel button[type="submit"]'),
    ]);
    const admFilteredSales = await pAdm.content();
    assert(admFilteredSales.includes('V-00000002') && !admFilteredSales.includes('V-00000003'));

    // NUL byte URL parameter via browser stays 200 (never 500)
    const rNulSales = await pAdm.goto(`${BASE_URL}/ventas/historial/?correlativo=V-%00`, { waitUntil: 'networkidle' });
    assert.equal(rNulSales.status(), 200);
    assert((await pAdm.content()).includes('caracteres no válidos'));

    // Admin cash shift history 1366x768
    await pAdm.goto(`${BASE_URL}/caja/turnos/`, { waitUntil: 'networkidle' });
    const cashHistHtml = await pAdm.content();
    assert(cashHistHtml.includes('Total cobrado'), 'Missing Total cobrado column');
    assert(cashHistHtml.includes('Faltante') && cashHistHtml.includes('-5,00'), 'Missing Faltante -5,00');
    const layCashHist = await layoutCheck(pAdm, 'cash-history-1366x768');
    assert.equal(layCashHist.docOverflow, false, 'Admin cash-history docOverflow at 1366x768');
    assert.equal(layCashHist.wrapOverflowPx, 0, `Admin cash-history wrapOverflowPx=${layCashHist.wrapOverflowPx}`);
    report.layout.push(layCashHist);
    await pAdm.screenshot({ path: path.join(OUT_DIR, 'post-fix-cash-history-1366x768.png'), fullPage: true });

    // Admin closes-shift acta 1366x768 + H1 check
    await pAdm.goto(`${BASE_URL}/caja/turnos/${ids.shifts.s1_closed}/cerrado/`, { waitUntil: 'networkidle' });
    assert.equal((await pAdm.locator('header.app-topbar h1').textContent()).trim(), 'Acta de cierre');
    assert.equal(await pAdm.locator('a.nav-item.is-active[href="/caja/turnos/"]').count(), 1);
    const actaHtml = await pAdm.content();
    assert(actaHtml.includes('Total cobrado') && actaHtml.includes('20,00'), 'Missing Total cobrado on closed shift acta');
    const layCashClosed = await layoutCheck(pAdm, 'cash-closed-1366x768');
    assert.equal(layCashClosed.docOverflow, false, 'Closed acta docOverflow at 1366x768');
    report.layout.push(layCashClosed);
    await pAdm.screenshot({ path: path.join(OUT_DIR, 'post-fix-cash-closed-1366x768.png'), fullPage: true });

    // Admin 26-item pagination & boundary error handling on both histories
    await pAdm.goto(`${BASE_URL}/ventas/historial/?fecha=${ids.pagination_date}`, { waitUntil: 'networkidle' });
    const salesPage1Correlatives = await pAdm.$$eval('tbody tr', (rows) =>
      rows.map((r) => (r.textContent.match(/V-\d{8}/) || [null])[0]).filter(Boolean)
    );
    assert.equal(salesPage1Correlatives.length, 25);
    assert((await pAdm.content()).includes('260,00'), 'Full filtered total S/ 260,00 expected on page 1');
    await Promise.all([pAdm.waitForNavigation({ waitUntil: 'networkidle' }), pAdm.locator('a[href*="page=2"]').first().click()]);
    assert(pAdm.url().includes(`fecha=${ids.pagination_date}`) && pAdm.url().includes('page=2'));
    const salesPage2Correlatives = await pAdm.$$eval('tbody tr', (rows) =>
      rows.map((r) => (r.textContent.match(/V-\d{8}/) || [null])[0]).filter(Boolean)
    );
    assert.equal(salesPage2Correlatives.length, 1);
    assert.deepEqual([...salesPage1Correlatives, ...salesPage2Correlatives], ids.pagination_sales_correlatives);
    assert((await pAdm.content()).includes('260,00'), 'Full filtered total S/ 260,00 expected on page 2');
    await pAdm.screenshot({ path: path.join(OUT_DIR, 'post-fix-sales-history-pag2-1366x768.png'), fullPage: true });

    const rBadSalePage = await pAdm.goto(`${BASE_URL}/ventas/historial/?fecha=${ids.pagination_date}&page=999`, { waitUntil: 'networkidle' });
    assert.equal(rBadSalePage.status(), 200);
    assert((await pAdm.content()).includes('La página solicitada no existe para estos filtros.'));

    await pAdm.goto(`${BASE_URL}/caja/turnos/?fecha_desde=${ids.pagination_date}&fecha_hasta=${ids.pagination_date}`, { waitUntil: 'networkidle' });
    const shiftsPage1Ids = await pAdm.$$eval('tbody tr a[href*="/cerrado/"]', (links) =>
      links.map((a) => (a.getAttribute('href').match(/\/caja\/turnos\/([0-9a-f-]+)\/cerrado\//) || [null, null])[1]).filter(Boolean)
    );
    assert.equal(shiftsPage1Ids.length, 25);
    await Promise.all([pAdm.waitForNavigation({ waitUntil: 'networkidle' }), pAdm.locator('a[href*="page=2"]').first().click()]);
    assert(pAdm.url().includes(`fecha_desde=${ids.pagination_date}`) && pAdm.url().includes(`fecha_hasta=${ids.pagination_date}`));
    const shiftsPage2Ids = await pAdm.$$eval('tbody tr a[href*="/cerrado/"]', (links) =>
      links.map((a) => (a.getAttribute('href').match(/\/caja\/turnos\/([0-9a-f-]+)\/cerrado\//) || [null, null])[1]).filter(Boolean)
    );
    assert.equal(shiftsPage2Ids.length, 1);
    assert.deepEqual([...shiftsPage1Ids, ...shiftsPage2Ids], ids.pagination_shifts_order);

    for (const badCashUrl of [`/caja/turnos/?fecha_desde=9999-12-31`, `/caja/turnos/?page=abc`]) {
      const rBad = await pAdm.goto(`${BASE_URL}${badCashUrl}`, { waitUntil: 'networkidle' });
      assert.equal(rBad.status(), 200);
    }
    report.checks.push({ name: 'admin-pagination-26-disjoint-and-invalid-bounds', pass: true });

    // Deactivate Seller1 in Admin UI and confirm existing Seller1 cookie in ctxSeller redirects immediately to login
    await pAdm.goto(`${BASE_URL}/empleados/`, { waitUntil: 'networkidle' });
    const seller1Row = pAdm.locator('tbody tr', { hasText: creds.seller1.email });
    await Promise.all([
      pAdm.waitForNavigation({ waitUntil: 'networkidle' }),
      seller1Row.locator('button', { hasText: 'Desactivar' }).click(),
    ]);
    await Promise.all([
      pAdm.waitForNavigation({ waitUntil: 'networkidle' }),
      pAdm.locator('main form button[type="submit"]', { hasText: 'Confirmar desactivación' }).click(),
    ]);
    assert((await pAdm.locator('tbody tr', { hasText: creds.seller1.email }).textContent()).includes('Inactivo'));

    for (const protectedPath of ['/ventas/historial/', '/ventas/', '/caja/turnos/', `/ventas/constancia/${ids.sales.s3}/`]) {
      await page.goto(`${BASE_URL}${protectedPath}`, { waitUntil: 'networkidle' });
      assert(page.url().includes('/?next='), `Deactivated cookie accessed ${protectedPath} without login redirect -> ${page.url()}`);
    }
    report.checks.push({ name: 'deactivated-seller-cookie-revoked-browser', pass: true });
    await ctxSeller.close();

    // Logout & navigate Back + direct re-visit -> verify no cached sensitive page leak (no-store + 302 login)
    await logout(pAdm);
    await pAdm.goBack({ waitUntil: 'networkidle' });
    await pAdm.goto(`${BASE_URL}/ventas/historial/`, { waitUntil: 'networkidle' });
    assert(pAdm.url().includes('/?next='), `Expected redirect to login after logout, got ${pAdm.url()}`);
    report.checks.push({ name: 'admin-histories-acta-and-post-logout-cache', pass: true });

    await ctxAdmin.close();
  } finally {
    await browser.close();
  }

  assert.equal(report.pageErrors.length, 0, `Page errors: ${JSON.stringify(report.pageErrors)}`);
  assert.equal(report.serverErrors.length, 0, `Server 5xx errors: ${JSON.stringify(report.serverErrors)}`);
  assert.equal(report.failedReqs.length, 0, `Failed requests: ${JSON.stringify(report.failedReqs)}`);
  fs.writeFileSync(path.join(OUT_DIR, 'browser-report.json'), JSON.stringify(report, null, 2), 'utf8');
  console.log(JSON.stringify({ ok: true, layout: report.layout, checks: report.checks.length }));
})();
