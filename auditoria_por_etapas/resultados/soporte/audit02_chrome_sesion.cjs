/**
 * Pruebas end-to-end en Google Chrome real (1366x768) para el Sublote 02-A:
 * HU-AUTH-03 (CA-01, CA-02, CA-03), RN-29, RN-30, QA00-L877-c y observación de HU-AUTH-04a.
 * Nunca guarda secretos, contraseñas ni tokens en JSON ni capturas.
 */
const fs = require('fs');
const os = require('os');
const path = require('path');

const pwPath = path.join(
  os.homedir(),
  '.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright-core'
);
const { chromium } = require(pwPath);

const BASE_URL = process.env.AUDIT02_BASE_URL || 'http://127.0.0.1:8767';
const EVIDENCIAS_DIR = path.resolve(__dirname, '..', 'evidencias');

async function attachGuards(page, bucket) {
  page.on('console', (msg) => {
    if (msg.type() === 'error') {
      bucket.consoleErrors.push(msg.text());
    }
  });
  page.on('pageerror', (err) => {
    bucket.pageErrors.push(String(err));
  });
}

async function layoutMetrics(page) {
  return page.evaluate(() => {
    const doc = document.documentElement;
    return {
      title: document.title,
      h1Count: document.querySelectorAll('h1').length,
      h2Text: Array.from(document.querySelectorAll('h2')).map((el) => el.innerText.trim()),
      scrollWidth: doc.scrollWidth,
      clientWidth: doc.clientWidth,
      horizontalOverflow: doc.scrollWidth > doc.clientWidth,
    };
  });
}

async function safeScreenshot(page, fileName) {
  const fullPath = path.join(EVIDENCIAS_DIR, fileName);
  const masks = [
    page.locator('input[type="password"]'),
    page.locator('input[name="csrfmiddlewaretoken"]'),
  ];
  await page.screenshot({ path: fullPath, fullPage: true, mask: masks });
  return fileName;
}

async function loginOnPage(page, email, password) {
  await page.goto(`${BASE_URL}/`, { waitUntil: 'networkidle' });
  await page.fill('input[name="email"]', email);
  await page.fill('input[name="password"]', password);
  await Promise.all([
    page.waitForNavigation({ waitUntil: 'networkidle' }),
    page.click('button[type="submit"]'),
  ]);
}

(async () => {
  fs.mkdirSync(EVIDENCIAS_DIR, { recursive: true });
  const browser = await chromium.launch({
    executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe',
    headless: true,
  });

  const report = {
    stage: 'ETAPA-02',
    sublot: '02-A-sesion-y-salida',
    viewport: { width: 1366, height: 768 },
    executedAt: new Date().toISOString(),
    consoleErrors: [],
    pageErrors: [],
    steps: [],
  };

  try {
    const contextA = await browser.newContext({ viewport: { width: 1366, height: 768 } });
    const contextB = await browser.newContext({ viewport: { width: 1366, height: 768 } });
    const pageA = await contextA.newPage();
    const pageB = await contextB.newPage();
    await attachGuards(pageA, report);
    await attachGuards(pageB, report);

    // 1. Verificar proceso vivo desde el navegador
    await pageA.goto(`${BASE_URL}/`, { waitUntil: 'networkidle' });
    const challenge = `chrome-02a-${Date.now()}`;
    const proof = await pageA.evaluate(async (nonce) => {
      const r = await fetch('/', { headers: { 'X-Audit02-Challenge': nonce } });
      return {
        status: r.status,
        proof: r.headers.get('X-Audit02-Proof'),
        stage: r.headers.get('X-Audit02-Stage'),
      };
    }, challenge);
    if (proof.proof !== `ETAPA-02:${challenge}:audit.sqlite3`) {
      throw new Error(`Fallo de prueba de servidor vivo: ${JSON.stringify(proof)}`);
    }
    report.steps.push({ id: 'LIVE-PROOF', ok: true, proof });

    // 2. Vendedor 1 inicia sesión y abre turno de caja
    await loginOnPage(pageA, 'ventas@minimarket.local', 'Audit02!Ven');
    await pageA.goto(`${BASE_URL}/caja/abrir/`, { waitUntil: 'networkidle' });
    await pageA.fill('input[name="opening_amount"]', '50.00');
    await Promise.all([
      pageA.waitForNavigation({ waitUntil: 'networkidle' }),
      pageA.click('button[type="submit"]'),
    ]);

    // 3. HU-AUTH-03/CA-01: /salir/ con turno abierto pero SIN borrador activo
    await pageA.goto(`${BASE_URL}/salir/`, { waitUntil: 'networkidle' });
    const bodyNoDraft = await pageA.locator('main').innerText();
    const metricsNoDraft = await layoutMetrics(pageA);
    const shotNoDraft = await safeScreenshot(pageA, '02-auth03-confirmar-sin-borrador.png');
    const okNoDraft =
      metricsNoDraft.title === 'Cerrar sesión · Minimarket' &&
      bodyNoDraft.includes('¿Deseas cerrar sesión?') &&
      bodyNoDraft.includes('Cualquier venta en preparación abierta se descartará al confirmar') &&
      !metricsNoDraft.horizontalOverflow;
    if (!okNoDraft) {
      throw new Error(`HU-AUTH-03/CA-01 sin borrador falló: ${bodyNoDraft}`);
    }
    report.steps.push({
      id: 'HU-AUTH-03-CA01-SIN-BORRADOR',
      ok: true,
      url: pageA.url(),
      metrics: metricsNoDraft,
      screenshot: shotNoDraft,
    });

    // Cancelar en /salir/ mantiene la sesión activa
    await Promise.all([
      pageA.waitForNavigation({ waitUntil: 'networkidle' }),
      pageA.click('a:has-text("Cancelar")'),
    ]);
    if (!pageA.url().endsWith('/inicio/')) {
      throw new Error(`Cancelar salida no volvió a /inicio/: ${pageA.url()}`);
    }

    // 4. Preparar borrador con líneas en /ventas/
    await pageA.goto(`${BASE_URL}/ventas/?query=775000000201`, { waitUntil: 'networkidle' });
    await pageA.fill('form.line-add-form input[name="quantity"]', '2');
    await Promise.all([
      pageA.waitForNavigation({ waitUntil: 'networkidle' }),
      pageA.click('form.line-add-form button[type="submit"]'),
    ]);
    const draftBeforeCancelText = await pageA.locator('main').innerText();
    if (!draftBeforeCancelText.includes('Atún Audit02 en lata')) {
      throw new Error('No se agregó la línea al borrador antes de probar /salir/');
    }

    // 5. HU-AUTH-03/CA-02: /salir/ CON borrador activo con líneas + Cancelar conserva borrador
    await pageA.goto(`${BASE_URL}/salir/`, { waitUntil: 'networkidle' });
    const bodyWithDraft = await pageA.locator('main').innerText();
    const metricsWithDraft = await layoutMetrics(pageA);
    const shotWithDraft = await safeScreenshot(pageA, '02-auth03-confirmar-con-borrador.png');
    const okWithDraft =
      bodyWithDraft.includes('La venta en preparación se descartará. El turno abierto seguirá ligado a tu cuenta.') &&
      !metricsWithDraft.horizontalOverflow;
    if (!okWithDraft) {
      throw new Error(`HU-AUTH-03/CA-02 advertencia con borrador falló: ${bodyWithDraft}`);
    }
    await Promise.all([
      pageA.waitForNavigation({ waitUntil: 'networkidle' }),
      pageA.click('a:has-text("Cancelar")'),
    ]);
    await pageA.goto(`${BASE_URL}/ventas/`, { waitUntil: 'networkidle' });
    const draftAfterCancelText = await pageA.locator('main').innerText();
    if (!draftAfterCancelText.includes('Atún Audit02 en lata')) {
      throw new Error('Cancelar en /salir/ no conservó la venta en preparación');
    }
    report.steps.push({
      id: 'HU-AUTH-03-CA02-ADVERTENCIA-Y-CANCELAR',
      ok: true,
      metrics: metricsWithDraft,
      screenshot: shotWithDraft,
      draftPreservedOnCancel: true,
    });

    // 6. HU-AUTH-03/CA-02 y CA-03: Confirmar salida descarta borrador, invalida sesión y bloquea Back/URLs
    await pageA.goto(`${BASE_URL}/salir/`, { waitUntil: 'networkidle' });
    await Promise.all([
      pageA.waitForNavigation({ waitUntil: 'networkidle' }),
      pageA.click('button:has-text("Cerrar sesión")'),
    ]);
    const shotPostLogout = await safeScreenshot(pageA, '02-auth03-post-salida.png');
    const loggedOutUrl = pageA.url();

    // Botón Atrás y acceso directo a rutas protegidas
    await pageA.goBack({ waitUntil: 'networkidle' });
    await pageA.goto(`${BASE_URL}/ventas/`, { waitUntil: 'networkidle' });
    const redirectedFromSales = pageA.url();
    await pageA.goto(`${BASE_URL}/inicio/`, { waitUntil: 'networkidle' });
    const redirectedFromHome = pageA.url();

    if (!redirectedFromSales.includes('next=/ventas/') || !redirectedFromHome.includes('next=/inicio/')) {
      throw new Error(`CA-03 redirigió de forma inesperada: ${redirectedFromSales} / ${redirectedFromHome}`);
    }
    report.steps.push({
      id: 'HU-AUTH-03-CA02-CA03-CONFIRMAR-Y-BLOQUEO-POST-SALIDA',
      ok: true,
      loggedOutUrl,
      redirectedFromSales,
      redirectedFromHome,
      screenshot: shotPostLogout,
    });

    // 7. Segundo navegador (Vendedor 2) intenta usar/abrir/cerrar el turno de Vendedor 1 (RN-29)
    await loginOnPage(pageB, 'ventas2@minimarket.local', 'Audit02!Ve2');
    await pageB.goto(`${BASE_URL}/caja/abrir/`, { waitUntil: 'networkidle' });
    const openShiftBodyB = await pageB.locator('main').innerText();
    await pageB.goto(`${BASE_URL}/ventas/`, { waitUntil: 'networkidle' });
    const salesBodyB = await pageB.locator('main').innerText();
    await pageB.goto(`${BASE_URL}/caja/cerrar/`, { waitUntil: 'networkidle' });
    const closeShiftBodyB = await pageB.locator('main').innerText();

    const okSeller2Isolation =
      openShiftBodyB.includes('Carla Vendedora') &&
      salesBodyB.includes('Abre tu turno para preparar una venta') &&
      closeShiftBodyB.includes('No tienes un turno abierto');
    if (!okSeller2Isolation) {
      throw new Error(`Fallo aislamiento de turno frente a Vendedor 2: ${openShiftBodyB} | ${salesBodyB}`);
    }
    report.steps.push({
      id: 'RN-29-SEGUNDO-NAVEGADOR-VENDEDOR-2-AISLADO',
      ok: true,
      seller2SeesOwnerInOpenPage: true,
      seller2BlockedInSalesPreparation: true,
      seller2BlockedInCloseShift: true,
    });

    // 8. Vendedor 1 vuelve a iniciar sesión: recupera turno abierto SIN el borrador descartado y con stock intacto (20)
    await loginOnPage(pageA, 'ventas@minimarket.local', 'Audit02!Ven');
    await pageA.goto(`${BASE_URL}/ventas/?query=775000000201`, { waitUntil: 'networkidle' });
    const reloginSalesText = await pageA.locator('main').innerText();
    const okRelogin =
      reloginSalesText.includes('Aún no agregaste productos a la venta.') &&
      reloginSalesText.includes('20');
    if (!okRelogin) {
      throw new Error(`Fallo al recuperar turno sin borrador tras relogin: ${reloginSalesText}`);
    }

    // Cerrar turno de Vendedor 1 para dejar caja limpia
    await pageA.goto(`${BASE_URL}/caja/cerrar/`, { waitUntil: 'networkidle' });
    await pageA.fill('input[name="counted_amount"]', '50.00');
    await Promise.all([
      pageA.waitForNavigation({ waitUntil: 'networkidle' }),
      pageA.click('button[type="submit"]'),
    ]);
    // Cerrar sesión en ambos contextos
    await pageA.goto(`${BASE_URL}/salir/`, { waitUntil: 'networkidle' });
    await Promise.all([
      pageA.waitForNavigation({ waitUntil: 'networkidle' }),
      pageA.click('button:has-text("Cerrar sesión")'),
    ]);
    await pageB.goto(`${BASE_URL}/salir/`, { waitUntil: 'networkidle' });
    await Promise.all([
      pageB.waitForNavigation({ waitUntil: 'networkidle' }),
      pageB.click('button:has-text("Cerrar sesión")'),
    ]);
    report.steps.push({
      id: 'RN-29-RN-30-RELOGIN-RECUPERA-TURNO-SIN-BORRADOR-Y-CIERRA-CAJA',
      ok: true,
      emptyDraftAfterRelogin: true,
      stockIntact20Units: true,
    });

    // 9. Observación empírica de HU-AUTH-04a (PREVISTO/FUTURO — NO IMPLEMENTADO): dos sesiones simultáneas activas
    await loginOnPage(pageA, 'admin@minimarket.local', 'Audit02!Adm');
    await loginOnPage(pageB, 'admin@minimarket.local', 'Audit02!Adm');
    const respA = await pageA.goto(`${BASE_URL}/inicio/`, { waitUntil: 'networkidle' });
    const respB = await pageB.goto(`${BASE_URL}/inicio/`, { waitUntil: 'networkidle' });
    report.steps.push({
      id: 'OBS-HU-AUTH-04A-CONCURRENCIA-NO-IMPLEMENTADA',
      ok: true,
      classification: 'PREVISTO/FUTURO — NO IMPLEMENTADO',
      contextAStatus: respA.status(),
      contextBStatus: respB.status(),
      bothSessionsRemainActive: respA.status() === 200 && respB.status() === 200,
    });

    await contextA.close();
    await contextB.close();
  } finally {
    await browser.close();
  }

  if (report.consoleErrors.length > 0 || report.pageErrors.length > 0) {
    throw new Error(`Errores de consola/página detectados: ${JSON.stringify(report)}`);
  }

  const outPath = path.join(EVIDENCIAS_DIR, '02-chrome-sesion.json');
  fs.writeFileSync(outPath, JSON.stringify(report, null, 2), 'utf-8');
  console.log(JSON.stringify(report, null, 2));
})();
