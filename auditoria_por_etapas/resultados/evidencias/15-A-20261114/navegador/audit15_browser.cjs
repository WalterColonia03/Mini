const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { chromium } = require(
  'C:/Users/walte/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright-core'
);

const PORT = process.env.AUDIT15_PORT;
const BASE_URL = `http://127.0.0.1:${PORT}`;
const CREDS_FILE = process.env.AUDIT15_CREDS;
const IDS_FILE = process.env.AUDIT15_IDS;
const OUT_DIR = process.env.AUDIT15_OUT;
const CHROME_PATH = 'C:/Program Files/Google/Chrome/Application/chrome.exe';

const creds = JSON.parse(fs.readFileSync(CREDS_FILE, 'utf8'));
const ids = JSON.parse(fs.readFileSync(IDS_FILE, 'utf8'));

function attachGuards(page, state) {
  page.on('pageerror', (err) => state.pageErrors.push(err.message));
  page.on('console', (msg) => {
    if (msg.type() === 'error') {
      const txt = msg.text();
      if (!txt.includes('Failed to load resource: the server responded with a status of 403') &&
          !txt.includes('Failed to load resource: the server responded with a status of 404')) {
        state.consoleErrors.push(txt);
      }
    }
  });
  page.on('requestfailed', (req) => {
    state.failedReqs.push(`${req.method()} ${req.url()} -> ${req.failure()?.errorText}`);
  });
  page.on('response', (res) => {
    if (res.status() >= 500) {
      state.serverErrors.push(`${res.status()} ${res.url()}`);
    }
  });
}

async function loginUI(page, account, expectPathPrefix = '/inicio/') {
  await page.goto(`${BASE_URL}/`, { waitUntil: 'networkidle' });
  await page.fill('input[name="email"]', account.email);
  await page.fill('input[name="password"]', account.password);
  await Promise.all([
    page.waitForNavigation({ waitUntil: 'networkidle' }),
    page.click('button[type="submit"]'),
  ]);
  if (expectPathPrefix) {
    assert(
      new URL(page.url()).pathname.startsWith(expectPathPrefix),
      `Expected path ${expectPathPrefix}, got ${page.url()}`
    );
  }
}

async function inspectStorageAndDomCleanliness(page) {
  return page.evaluate(() => {
    const lsKeys = Object.keys(localStorage);
    const ssKeys = Object.keys(sessionStorage);
    const jsCookie = document.cookie;
    const html = document.documentElement.innerHTML;
    const docOverflow = document.documentElement.scrollWidth > window.innerWidth;
    const tracebackHit = /Traceback \(most recent call last\)|django\.core\.exceptions|POSTGRES_PASSWORD|DJANGO_SECRET_KEY/i.test(html);
    return {
      lsKeys,
      ssKeys,
      jsCookie,
      docOverflow,
      tracebackHit,
    };
  });
}

(async () => {
  const report = {
    started_utc: new Date().toISOString(),
    browser_executable: CHROME_PATH,
    viewport: { width: 1366, height: 768 },
    checks: [],
    pageErrors: [],
    consoleErrors: [],
    failedReqs: [],
    serverErrors: [],
    observations: {},
  };

  async function runCheck(id, fn) {
    const t0 = Date.now();
    try {
      const details = (await fn()) || {};
      report.checks.push({ id, ok: true, ms: Date.now() - t0, ...details });
    } catch (err) {
      report.checks.push({ id, ok: false, ms: Date.now() - t0, error: String(err.stack || err) });
    }
  }

  const browser = await chromium.launch({
    executablePath: CHROME_PATH,
    headless: true,
    args: ['--no-sandbox', '--disable-gpu'],
  });

  try {
    // CHK-NAV-01: Anonymous redirect, login form attributes, storage/cookie flags
    await runCheck('CHK-NAV-01-anonimo-login-cookies-almacenamiento', async () => {
      const ctx = await browser.newContext({ viewport: { width: 1366, height: 768 } });
      const page = await ctx.newPage();
      attachGuards(page, report);
      const res = await page.goto(`${BASE_URL}/inicio/`, { waitUntil: 'networkidle' });
      const u = new URL(page.url());
      assert.equal(res.status(), 200);
      assert.equal(u.pathname, '/');
      assert.equal(u.searchParams.get('next'), '/inicio/');
      const cacheHdr = res.headers()['cache-control'] || '';
      assert(cacheHdr.includes('no-store'), `Expected no-store on login, got: ${cacheHdr}`);
      const pwType = await page.getAttribute('input[name="password"]', 'type');
      assert.equal(pwType, 'password');
      const csrfInputCount = await page.locator('input[name="csrfmiddlewaretoken"]').count();
      assert(csrfInputCount >= 1);
      const clean = await inspectStorageAndDomCleanliness(page);
      assert.equal(clean.lsKeys.length, 0);
      assert.equal(clean.ssKeys.length, 0);
      assert.equal(clean.jsCookie, '', 'Expected HttpOnly CSRF/session cookies hidden from document.cookie');
      assert.equal(clean.tracebackHit, false);
      assert.equal(clean.docOverflow, false);
      await ctx.close();
      return { cacheControl: cacheHdr, storageEmpty: true, jsCookieHidden: true };
    });

    // CHK-NAV-02: RN-18 5 failed logins -> 15 min block rejecting valid password too
    await runCheck('CHK-NAV-02-bloqueo-rn18-5-fallos-en-chrome', async () => {
      const ctx = await browser.newContext({ viewport: { width: 1366, height: 768 } });
      const page = await ctx.newPage();
      attachGuards(page, report);
      await page.goto(`${BASE_URL}/`, { waitUntil: 'networkidle' });
      for (let i = 1; i <= 5; i++) {
        await page.fill('input[name="email"]', creds.lockprobe.email);
        await page.fill('input[name="password"]', `WrongPass15!#${i}`);
        await Promise.all([
          page.waitForNavigation({ waitUntil: 'networkidle' }),
          page.click('button[type="submit"]'),
        ]);
        const alertText = (await page.locator('[role="alert"], .errorlist').first().innerText()).trim();
        if (i < 5) {
          assert(alertText.includes('Correo o contraseña incorrectos'), `Unexpected alert on try ${i}: ${alertText}`);
        } else {
          assert(alertText.includes('15 minuto(s)'), `Expected 15-min lockout on 5th try, got: ${alertText}`);
        }
      }
      // Clear password field naturally (empty) then type correct password -> still locked!
      await page.fill('input[name="email"]', creds.lockprobe.email);
      await page.fill('input[name="password"]', creds.lockprobe.password);
      await Promise.all([
        page.waitForNavigation({ waitUntil: 'networkidle' }),
        page.click('button[type="submit"]'),
      ]);
      const lockedText = (await page.locator('[role="alert"], .errorlist').first().innerText()).trim();
      assert(lockedText.includes('15 minuto(s)'), `Expected lockout with valid password too, got: ${lockedText}`);
      assert.equal(new URL(page.url()).pathname, '/');
      await page.screenshot({ path: path.join(OUT_DIR, '01-login-bloqueo-15min.png'), fullPage: false });
      await ctx.close();
      return { lockoutText: lockedText };
    });

    // CHK-NAV-03: Three role menus vs direct URL 403/header checks + DEC-12 observation + missing no-store
    await runCheck('CHK-NAV-03-roles-menus-403-y-cabeceras', async () => {
      // 3a. ADMIN
      const ctxAdm = await browser.newContext({ viewport: { width: 1366, height: 768 } });
      const pAdm = await ctxAdm.newPage();
      attachGuards(pAdm, report);
      await loginUI(pAdm, creds.admin, '/inicio/');
      const admCookies = await ctxAdm.cookies();
      const sessCookie = admCookies.find((c) => c.name === 'sessionid');
      const csrfCookie = admCookies.find((c) => c.name === 'csrftoken');
      assert(sessCookie && sessCookie.httpOnly === true && sessCookie.sameSite === 'Lax');
      assert(csrfCookie && csrfCookie.httpOnly === true && csrfCookie.sameSite === 'Lax');
      const admClean = await inspectStorageAndDomCleanliness(pAdm);
      assert.equal(admClean.jsCookie, '');
      assert.equal(admClean.tracebackHit, false);

      const admMenu = await pAdm.evaluate(() =>
        [...document.querySelectorAll('nav a[href]')].map((a) => new URL(a.href).pathname)
      );
      assert(admMenu.includes('/empleados/') && admMenu.includes('/productos/') && admMenu.includes('/ventas/historial/'));
      assert(!admMenu.includes('/ventas/') && !admMenu.includes('/inventario/carga-inicial/'));

      // Check ADMIN direct URL denial 403 on seller/warehouse-exclusive URLs
      for (const deniedUrl of ['/ventas/', '/caja/abrir/', '/inventario/carga-inicial/', '/inventario/entrada/']) {
        const r403 = await pAdm.goto(`${BASE_URL}${deniedUrl}`, { waitUntil: 'networkidle' });
        assert.equal(r403.status(), 403, `Expected 403 for ADMIN at ${deniedUrl}`);
        const msg403 = await pAdm.locator('[data-testid="permission-denied"]').innerText();
        assert(msg403.includes('No tienes permiso para esta operación'));
        if (deniedUrl === '/ventas/') {
          await pAdm.screenshot({ path: path.join(OUT_DIR, '02-admin-403-ruta-vendedor.png'), fullPage: false });
        }
      }

      // Check Cache-Control gap on /productos/nuevo/ (missing @never_cache) vs /productos/ (has no-store)
      const rProdList = await pAdm.goto(`${BASE_URL}/productos/`, { waitUntil: 'networkidle' });
      const ccProdList = rProdList.headers()['cache-control'] || '';
      assert(ccProdList.includes('no-store'));
      const rProdNew = await pAdm.goto(`${BASE_URL}/productos/nuevo/`, { waitUntil: 'networkidle' });
      const ccProdNew = rProdNew.headers()['cache-control'] || '';
      const xfoProdNew = rProdNew.headers()['x-frame-options'] || '';
      assert.equal(xfoProdNew, 'DENY');

      // Check /empleados/ now links to intermediate confirmation page before deactivate
      await pAdm.goto(`${BASE_URL}/empleados/`, { waitUntil: 'networkidle' });
      const empHtml = await pAdm.content();
      report.observations.doc02_04_has_state_confirm = empHtml.includes('/estado/confirmar/');
      await ctxAdm.close();

      // 3b. ALMACENERO
      const ctxWh = await browser.newContext({ viewport: { width: 1366, height: 768 } });
      const pWh = await ctxWh.newPage();
      attachGuards(pWh, report);
      await loginUI(pWh, creds.warehouse, '/inicio/');
      const whMenu = await pWh.evaluate(() =>
        [...document.querySelectorAll('nav a[href]')].map((a) => new URL(a.href).pathname)
      );
      assert(whMenu.includes('/inventario/stock/') && whMenu.includes('/inventario/carga-inicial/'));
      assert(!whMenu.includes('/empleados/') && !whMenu.includes('/ventas/'));

      // Read-only catalog and suppliers for ALMACENERO
      await pWh.goto(`${BASE_URL}/productos/`, { waitUntil: 'networkidle' });
      const whProdText = await pWh.content();
      assert(!whProdText.includes('/productos/nuevo/') && !whProdText.includes('/editar/'));
      await pWh.goto(`${BASE_URL}/inventario/proveedores/`, { waitUntil: 'networkidle' });
      const whSupText = await pWh.content();
      assert(!whSupText.includes('/inventario/proveedores/nuevo/') && !whSupText.includes('/estado/'));

      for (const deniedUrl of ['/empleados/', '/productos/nuevo/', '/productos/categorias/', '/inventario/ajustes/nuevo/', '/caja/turnos/', '/ventas/historial/']) {
        const r403 = await pWh.goto(`${BASE_URL}${deniedUrl}`, { waitUntil: 'networkidle' });
        assert.equal(r403.status(), 403, `Expected 403 for ALMACENERO at ${deniedUrl}`);
      }
      await ctxWh.close();

      return {
        sessionCookieFlags: { httpOnly: sessCookie.httpOnly, sameSite: sessCookie.sameSite },
        csrfCookieFlags: { httpOnly: csrfCookie.httpOnly, sameSite: csrfCookie.sameSite },
        adminMenuCount: admMenu.length,
        warehouseMenuCount: whMenu.length,
        productListCacheControl: ccProdList,
        productNewMissingNoStoreHeader: !ccProdNew.includes('no-store'),
        xFrameOptions: xfoProdNew,
      };
    });

    // CHK-NAV-04 & 05: VENDEDOR UI shift open + active draft + DEC-12 check + missing 300s lock + logout confirm & post-logout redirect
    await runCheck('CHK-NAV-04-05-vendedor-borrador-logout-y-ausencia-bloqueo300s', async () => {
      const ctxSel = await browser.newContext({ viewport: { width: 1366, height: 768 } });
      const pSel = await ctxSel.newPage();
      attachGuards(pSel, report);
      await loginUI(pSel, creds.seller1, '/inicio/');

      const selMenu = await pSel.evaluate(() =>
        [...document.querySelectorAll('nav a[href]')].map((a) => new URL(a.href).pathname)
      );
      assert(
        selMenu.includes('/caja/abrir/') &&
          selMenu.includes('/ventas/') &&
          selMenu.includes('/caja/turnos/') &&
          selMenu.includes('/ventas/historial/') &&
          selMenu.includes('/ventas/historial/turno/')
      );

      // Direct 403 checks on ADMIN/ALMACENERO routes
      for (const deniedUrl of ['/empleados/', '/productos/', '/inventario/stock/', '/inventario/carga-inicial/']) {
        const r403 = await pSel.goto(`${BASE_URL}${deniedUrl}`, { waitUntil: 'networkidle' });
        assert.equal(r403.status(), 403, `Expected 403 for VENDEDOR at ${deniedUrl}`);
      }

      // Verify DEC-12 vs code: VENDEDOR gets 200 on /caja/turnos/ and /ventas/historial/ (own-only scope, seller2 hidden)
      const rShHist = await pSel.goto(`${BASE_URL}/caja/turnos/?vendedor=${ids.seller2_id}`, { waitUntil: 'networkidle' });
      const rSalesHist = await pSel.goto(`${BASE_URL}/ventas/historial/?vendedor=${ids.seller2_id}`, { waitUntil: 'networkidle' });
      const selHistHtml = await pSel.content();
      assert.equal(rShHist.status(), 200);
      assert.equal(rSalesHist.status(), 200);
      assert.equal(await pSel.locator('table.sales-history-table').count(), 0, 'Cross-seller sale table leaked');
      assert(!selHistHtml.includes(`/ventas/constancia/${ids.seller2_sale_id}/`), 'Cross-seller sale leaked in filter');
      assert(selHistHtml.includes('No se encontraron ventas'), 'Expected empty result notice on cross-seller filter');
      const rOwnReceipt = await pSel.goto(`${BASE_URL}/ventas/constancia/${ids.seller2_sale_id}/`, { waitUntil: 'networkidle' });
      assert.equal(rOwnReceipt.status(), 404, 'Seller1 could view Seller2 receipt');

      // Open cash shift via UI (real CSRF form POST)
      await pSel.goto(`${BASE_URL}/caja/abrir/`, { waitUntil: 'networkidle' });
      await pSel.fill('input[name="opening_amount"]', '50.00');
      await Promise.all([
        pSel.waitForNavigation({ waitUntil: 'networkidle' }),
        pSel.click('main form button[type="submit"]'),
      ]);
      assert(new URL(pSel.url()).pathname.startsWith('/caja/turnos/'));

      // Go to /ventas/, search product & add 1 unit to create active draft
      await pSel.goto(`${BASE_URL}/ventas/`, { waitUntil: 'networkidle' });
      const draftScripts = await pSel.evaluate(() => [...document.scripts].map((s) => s.src || '[inline]'));
      const navJs = await (await pSel.goto(`${BASE_URL}/static/identity/navigation.js`)).text();
      await pSel.goto(`${BASE_URL}/ventas/?query=${encodeURIComponent(ids.product_barcode)}`, { waitUntil: 'networkidle' });
      await Promise.all([
        pSel.waitForNavigation({ waitUntil: 'networkidle' }),
        pSel.click('form.line-add-form button[type="submit"]'),
      ]);
      const draftText = await pSel.locator('main').innerText();
      assert(draftText.includes('Venta en preparación') && draftText.includes('Cobrar venta') && draftText.includes('Descartar venta'));

      // Go to /salir/ and verify warning about active draft
      await pSel.goto(`${BASE_URL}/salir/`, { waitUntil: 'networkidle' });
      const logoutText = await pSel.locator('main').innerText();
      assert(logoutText.includes('venta en preparación') && logoutText.includes('se descartará'));
      await pSel.screenshot({ path: path.join(OUT_DIR, '03-logout-advertencia-borrador.png'), fullPage: false });

      // Confirm logout -> redirects to /, then /ventas/ redirects back to /?next=/ventas/
      await Promise.all([
        pSel.waitForNavigation({ waitUntil: 'networkidle' }),
        pSel.click('main form button[type="submit"]'),
      ]);
      assert.equal(new URL(pSel.url()).pathname, '/');
      await pSel.goto(`${BASE_URL}/ventas/`, { waitUntil: 'networkidle' });
      assert.equal(new URL(pSel.url()).pathname, '/');

      await ctxSel.close();
      return {
        sellerSidebarHasOwnHistories: true,
        sellerHistRoutes200WithOwnIsolation: true,
        crossSellerReceipt404: true,
        draftScripts,
        navigationJsHasInactivityLock: navJs.includes('300') || navJs.toLowerCase().includes('inactiv'),
        logoutDiscardsDraftAndRevokesSession: true,
      };
    });

    // CHK-NAV-06: /admin/ exposure, RN-18 bypass & session bridge to /inicio/, plus friendly 404
    await runCheck('CHK-NAV-06-admin-bypass-rn18-y-404-amigable', async () => {
      const ctxAdmSite = await browser.newContext({ viewport: { width: 1366, height: 768 } });
      const p = await ctxAdmSite.newPage();
      attachGuards(p, report);

      // Lock staffprobe on commercial /
      await p.goto(`${BASE_URL}/`, { waitUntil: 'networkidle' });
      for (let i = 1; i <= 5; i++) {
        await p.fill('input[name="email"]', creds.staffprobe.email);
        await p.fill('input[name="password"]', `BadStaff15!#${i}`);
        await Promise.all([
          p.waitForNavigation({ waitUntil: 'networkidle' }),
          p.click('button[type="submit"]'),
        ]);
      }
      const lockMsg = (await p.locator('[role="alert"], .errorlist').first().innerText()).trim();
      assert(lockMsg.includes('15 minuto(s)'));

      // Bypass commercial lock via /admin/login/!
      await p.goto(`${BASE_URL}/admin/login/`, { waitUntil: 'networkidle' });
      await p.fill('input[name="username"]', creds.staffprobe.email);
      await p.fill('input[name="password"]', creds.staffprobe.password);
      await Promise.all([
        p.waitForNavigation({ waitUntil: 'networkidle' }),
        p.click('input[type="submit"]'),
      ]);
      assert.equal(new URL(p.url()).pathname, '/admin/');
      await p.screenshot({ path: path.join(OUT_DIR, '04-admin-bypass-en-chrome.png'), fullPage: false });

      // Session bridge: navigate directly to commercial /inicio/ without logging in commercially
      const rBridge = await p.goto(`${BASE_URL}/inicio/`, { waitUntil: 'networkidle' });
      assert.equal(rBridge.status(), 200);
      assert.equal(new URL(p.url()).pathname, '/inicio/');

      // Friendly 404 without debug info
      const r404 = await p.goto(`${BASE_URL}/ruta-inexistente-auditoria-15/`, { waitUntil: 'networkidle' });
      assert.equal(r404.status(), 404);
      const clean404 = await inspectStorageAndDomCleanliness(p);
      assert.equal(clean404.tracebackHit, false);

      await ctxAdmSite.close();
      return {
        lockedOnCommercialLogin: true,
        bypassedViaDjangoAdminLogin: true,
        sessionBridgedToDashboard: true,
        friendly404WithoutTraceback: true,
      };
    });

    // CHK-NAV-07: Mid-session deactivation by ADMIN immediately evicts seller2 active Chrome context
    await runCheck('CHK-NAV-07-desactivacion-revoca-otra-sesion-en-chrome', async () => {
      const ctxS2 = await browser.newContext({ viewport: { width: 1366, height: 768 } });
      const pS2 = await ctxS2.newPage();
      attachGuards(pS2, report);
      await loginUI(pS2, creds.seller2, '/inicio/');

      const ctxAdm = await browser.newContext({ viewport: { width: 1366, height: 768 } });
      const pAdm = await ctxAdm.newPage();
      attachGuards(pAdm, report);
      await loginUI(pAdm, creds.admin, '/inicio/');
      await pAdm.goto(`${BASE_URL}/empleados/`, { waitUntil: 'networkidle' });
      const confirmBtn = pAdm.locator(`form[action="/empleados/${ids.seller2_id}/estado/confirmar/"] button[type="submit"]`);
      assert.equal(await confirmBtn.count(), 1);
      await Promise.all([
        pAdm.waitForNavigation({ waitUntil: 'networkidle' }),
        confirmBtn.click(),
      ]);
      assert.equal(new URL(pAdm.url()).pathname, `/empleados/${ids.seller2_id}/estado/confirmar/`);
      const deactForm = pAdm.locator(`form[action="/empleados/${ids.seller2_id}/estado/"] button[type="submit"]`);
      assert.equal(await deactForm.count(), 1);
      await Promise.all([
        pAdm.waitForNavigation({ waitUntil: 'networkidle' }),
        deactForm.click(),
      ]);
      assert.equal(new URL(pAdm.url()).pathname, '/empleados/');

      // Now seller2 context tries to load /ventas/ -> immediately redirected to /?next=/ventas/
      await pS2.goto(`${BASE_URL}/ventas/`, { waitUntil: 'networkidle' });
      const afterUrl = new URL(pS2.url());
      assert.equal(afterUrl.pathname, '/');
      assert.equal(afterUrl.searchParams.get('next'), '/ventas/');

      await ctxS2.close();
      await ctxAdm.close();
      return { evictedImmediatelyToLogin: true };
    });
  } finally {
    await browser.close();
  }

  report.passed = report.checks.filter((c) => c.ok).length;
  report.total = report.checks.length;
  report.ok =
    report.passed === report.total &&
    report.pageErrors.length === 0 &&
    report.consoleErrors.length === 0 &&
    report.failedReqs.length === 0 &&
    report.serverErrors.length === 0;
  report.finished_utc = new Date().toISOString();

  fs.writeFileSync(path.join(OUT_DIR, 'browser-report.json'), JSON.stringify(report, null, 2) + '\n', 'utf8');
  console.log(JSON.stringify({ ok: report.ok, passed: report.passed, total: report.total }));
  process.exit(report.ok ? 0 : 1);
})();
