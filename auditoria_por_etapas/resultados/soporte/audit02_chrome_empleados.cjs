/**
 * Pruebas end-to-end en Google Chrome real (1366x768) para el Sublote 02-B:
 * HU-USR-01..05, RN-12, RN-17, RN-18, RN-24, QA00-L869-a/b y QA00-L877-c (403/404).
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
    sublot: '02-B-empleados-y-roles',
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

    // 1. HU-USR-01/CA-03 y QA00-L877-c: Visitante y Vendedor/Almacenero bloqueados en /empleados/
    await pageB.goto(`${BASE_URL}/empleados/`, { waitUntil: 'networkidle' });
    const anonUrl = pageB.url();
    if (!anonUrl.includes('next=/empleados/')) {
      throw new Error(`Visitante no fue redirigido a login desde /empleados/: ${anonUrl}`);
    }

    await loginOnPage(pageB, 'ventas@minimarket.local', 'Audit02!Ven');
    const respSeller403 = await pageB.goto(`${BASE_URL}/empleados/`, { waitUntil: 'networkidle' });
    const metrics403 = await layoutMetrics(pageB);
    const body403 = await pageB.locator('main').innerText();
    const shot403 = await safeScreenshot(pageB, '02-usr01-403-vendedor.png');
    if (
      respSeller403.status() !== 403 ||
      metrics403.title !== 'Acceso no permitido · Minimarket' ||
      !body403.includes('No tienes permiso para realizar esta acción') ||
      metrics403.horizontalOverflow
    ) {
      throw new Error(`403 en /empleados/ para vendedor falló: ${respSeller403.status()} | ${body403}`);
    }
    report.steps.push({
      id: 'HU-USR-01-CA03-403-VENDEDOR',
      ok: true,
      status: respSeller403.status(),
      metrics: metrics403,
      screenshot: shot403,
    });

    // 2. HU-USR-01/CA-01 y CA-02: Lista de empleados y búsqueda por nombre o correo (ADMIN)
    await loginOnPage(pageA, 'admin@minimarket.local', 'Audit02!Adm');
    await pageA.goto(`${BASE_URL}/empleados/`, { waitUntil: 'networkidle' });
    const rowsAll = await pageA.locator('tbody tr').allInnerTexts();
    const metricsList = await layoutMetrics(pageA);
    if (rowsAll.length < 5 || metricsList.horizontalOverflow) {
      throw new Error(`Lista de empleados inesperada: ${rowsAll.length} filas`);
    }

    await pageA.fill('input[name="q"]', 'Carla');
    await Promise.all([
      pageA.waitForNavigation({ waitUntil: 'networkidle' }),
      pageA.click('form[role="search"] button[type="submit"]'),
    ]);
    const rowsFiltered = await pageA.locator('tbody tr').allInnerTexts();
    const shotList = await safeScreenshot(pageA, '02-usr01-lista-y-busqueda.png');
    if (rowsFiltered.length !== 1 || !rowsFiltered[0].includes('Carla Vendedora')) {
      throw new Error(`Filtro por nombre falló: ${JSON.stringify(rowsFiltered)}`);
    }

    await pageA.fill('input[name="q"]', 'inactivo@minimarket.local');
    await Promise.all([
      pageA.waitForNavigation({ waitUntil: 'networkidle' }),
      pageA.click('form[role="search"] button[type="submit"]'),
    ]);
    const rowsByEmail = await pageA.locator('tbody tr').allInnerTexts();
    if (rowsByEmail.length !== 1 || !rowsByEmail[0].includes('Elena Inactiva')) {
      throw new Error(`Filtro por correo falló: ${JSON.stringify(rowsByEmail)}`);
    }
    report.steps.push({
      id: 'HU-USR-01-CA01-CA02-LISTA-Y-BUSQUEDA',
      ok: true,
      totalRowsUnfiltered: rowsAll.length,
      filteredByNameCount: rowsFiltered.length,
      filteredByEmailCount: rowsByEmail.length,
      metrics: metricsList,
      screenshot: shotList,
    });

    // 3. HU-USR-02: Crear empleado + validaciones RN-12 (duplicado) y RN-24 (contraseña)
    await pageA.goto(`${BASE_URL}/empleados/nuevo/`, { waitUntil: 'networkidle' });
    const sellerOptionValue = await pageA
      .locator('select[name="role"] option:has-text("Vendedor")')
      .getAttribute('value');
    const warehouseOptionValue = await pageA
      .locator('select[name="role"] option:has-text("Almacenero")')
      .getAttribute('value');

    await pageA.fill('input[name="display_name"]', 'Intento Duplicado');
    await pageA.fill('input[name="email"]', 'VENTAS@MINIMARKET.LOCAL');
    await pageA.fill('input[name="password"]', 'abcdef1');
    await pageA.selectOption('select[name="role"]', sellerOptionValue);
    await Promise.all([
      pageA.waitForNavigation({ waitUntil: 'networkidle' }),
      pageA.click('button[type="submit"]'),
    ]);
    const bodyWeakPw = await pageA.locator('main').innerText();
    const shotCreateVal = await safeScreenshot(pageA, '02-usr02-crear-validaciones.png');
    if (
      !bodyWeakPw.includes(
        'La contraseña debe tener al menos 7 caracteres e incluir mayúscula, minúscula y número.'
      )
    ) {
      throw new Error(`Validación RN-24 en navegador falló: ${bodyWeakPw}`);
    }

    // Duplicado con contraseña válida de 7 caracteres
    await pageA.fill('input[name="password"]', 'Abcdef1');
    await Promise.all([
      pageA.waitForNavigation({ waitUntil: 'networkidle' }),
      pageA.click('button[type="submit"]'),
    ]);
    const bodyDupEmail = await pageA.locator('main').innerText();
    if (!bodyDupEmail.includes('El correo ya está registrado.')) {
      throw new Error(`Validación RN-12 correo duplicado falló: ${bodyDupEmail}`);
    }

    // Alta válida de Lucía Vendedora con contraseña de 7 caracteres (RN-24 límite exacto)
    await pageA.fill('input[name="display_name"]', 'Lucía Vendedora');
    await pageA.fill('input[name="email"]', 'lucia@minimarket.local');
    await pageA.fill('input[name="password"]', 'Abcdef1');
    await pageA.selectOption('select[name="role"]', sellerOptionValue);
    await Promise.all([
      pageA.waitForNavigation({ waitUntil: 'networkidle' }),
      pageA.click('button[type="submit"]'),
    ]);
    const listAfterCreate = await pageA.locator('main').innerText();
    if (!listAfterCreate.includes('Empleado «Lucía Vendedora» creado correctamente.')) {
      throw new Error(`Alta de empleado no mostró confirmación esperada: ${listAfterCreate}`);
    }

    // Nuevo empleado inicia sesión en el segundo navegador (HU-USR-02/CA-01)
    await pageB.goto(`${BASE_URL}/salir/`, { waitUntil: 'networkidle' });
    await Promise.all([
      pageB.waitForNavigation({ waitUntil: 'networkidle' }),
      pageB.click('button:has-text("Cerrar sesión")'),
    ]);
    await loginOnPage(pageB, 'lucia@minimarket.local', 'Abcdef1');
    const respLuciaSalesBefore = await pageB.goto(`${BASE_URL}/ventas/`, {
      waitUntil: 'networkidle',
    });
    if (respLuciaSalesBefore.status() !== 200) {
      throw new Error(`Lucía recién creada con rol Vendedor no pudo acceder a /ventas/`);
    }
    report.steps.push({
      id: 'HU-USR-02-CA01-CA02-CA03-ALTA-Y-LOGIN-NUEVO-EMPLEADO',
      ok: true,
      screenshot: shotCreateVal,
      newEmployeeLoggedInStatus: respLuciaSalesBefore.status(),
    });

    // 4. HU-USR-03: Editar datos y cambiar rol de Lucía a Almacenero mientras tiene sesión activa en navegador B
    await pageA.goto(`${BASE_URL}/empleados/?q=lucia@minimarket.local`, { waitUntil: 'networkidle' });
    await Promise.all([
      pageA.waitForNavigation({ waitUntil: 'networkidle' }),
      pageA.click('a:has-text("Editar")'),
    ]);
    await pageA.fill('input[name="display_name"]', 'Lucía Almacén');
    await pageA.selectOption('select[name="role"]', warehouseOptionValue);
    const shotEdit = await safeScreenshot(pageA, '02-usr03-editar-empleado.png');
    await Promise.all([
      pageA.waitForNavigation({ waitUntil: 'networkidle' }),
      pageA.click('button[type="submit"]'),
    ]);

    // En navegador B, la sesión existente de Lucía ve reflejado su nuevo rol de inmediato (CA-03)
    const respLuciaSalesAfter = await pageB.goto(`${BASE_URL}/ventas/`, {
      waitUntil: 'networkidle',
    });
    const respLuciaInventoryAfter = await pageB.goto(`${BASE_URL}/inventario/carga-inicial/`, {
      waitUntil: 'networkidle',
    });
    if (respLuciaSalesAfter.status() !== 403 || respLuciaInventoryAfter.status() !== 200) {
      throw new Error(
        `Cambio de rol no surtió efecto inmediato en sesión activa: sales=${respLuciaSalesAfter.status()}, inv=${respLuciaInventoryAfter.status()}`
      );
    }
    report.steps.push({
      id: 'HU-USR-03-CA01-CA03-EDICION-Y-CAMBIO-DE-ROL-EN-SESION-ACTIVA',
      ok: true,
      screenshot: shotEdit,
      oldRoleRouteStatus: respLuciaSalesAfter.status(),
      newRoleRouteStatus: respLuciaInventoryAfter.status(),
    });

    // 5. HU-USR-04 y HU-USR-05: Bloqueo por turno abierto, desactivación con revocación inmediata de sesión y reactivación
    await pageB.goto(`${BASE_URL}/salir/`, { waitUntil: 'networkidle' });
    await Promise.all([
      pageB.waitForNavigation({ waitUntil: 'networkidle' }),
      pageB.click('button:has-text("Cerrar sesión")'),
    ]);
    await loginOnPage(pageB, 'ventas@minimarket.local', 'Audit02!Ven');
    await pageB.goto(`${BASE_URL}/caja/abrir/`, { waitUntil: 'networkidle' });
    await pageB.fill('input[name="opening_amount"]', '30.00');
    await Promise.all([
      pageB.waitForNavigation({ waitUntil: 'networkidle' }),
      pageB.click('button[type="submit"]'),
    ]);

    // Admin intenta desactivar a Carla con turno abierto -> bloqueado
    await pageA.goto(`${BASE_URL}/empleados/?q=ventas@minimarket.local`, { waitUntil: 'networkidle' });
    await Promise.all([
      pageA.waitForNavigation({ waitUntil: 'networkidle' }),
      pageA.click('button:has-text("Desactivar")'),
    ]);
    const bodyBlockedDeact = await pageA.locator('main').innerText();
    if (
      !bodyBlockedDeact.includes(
        'No se puede desactivar a un vendedor con un turno de caja abierto. Cierre el turno primero.'
      )
    ) {
      throw new Error(`Desactivación con turno abierto no mostró el bloqueo esperado: ${bodyBlockedDeact}`);
    }

    // Carla cierra su turno en navegador B pero mantiene su sesión iniciada
    await pageB.goto(`${BASE_URL}/caja/cerrar/`, { waitUntil: 'networkidle' });
    await pageB.fill('input[name="counted_amount"]', '30.00');
    await Promise.all([
      pageB.waitForNavigation({ waitUntil: 'networkidle' }),
      pageB.click('button[type="submit"]'),
    ]);

    // Admin desactiva a Carla -> éxito y revocación inmediata de la sesión de Carla en navegador B
    await pageA.goto(`${BASE_URL}/empleados/?q=ventas@minimarket.local`, { waitUntil: 'networkidle' });
    await Promise.all([
      pageA.waitForNavigation({ waitUntil: 'networkidle' }),
      pageA.click('button:has-text("Desactivar")'),
    ]);
    await pageA.fill('input[name="q"]', 'ventas@minimarket.local');
    await Promise.all([
      pageA.waitForNavigation({ waitUntil: 'networkidle' }),
      pageA.click('form[role="search"] button[type="submit"]'),
    ]);
    const shotDeact = await safeScreenshot(pageA, '02-usr04-05-desactivar-reactivar.png');

    await pageB.goto(`${BASE_URL}/inicio/`, { waitUntil: 'networkidle' });
    const revokedSessionUrl = pageB.url();
    if (!revokedSessionUrl.includes('next=/inicio/')) {
      throw new Error(`Sesión activa de empleada desactivada no fue revocada: ${revokedSessionUrl}`);
    }

    // Intento de login estando inactiva -> rechazado con mensaje uniforme
    await pageB.fill('input[name="email"]', 'ventas@minimarket.local');
    await pageB.fill('input[name="password"]', 'Audit02!Ven');
    await Promise.all([
      pageB.waitForNavigation({ waitUntil: 'networkidle' }),
      pageB.click('button[type="submit"]'),
    ]);
    const inactiveLoginBody = await pageB.locator('main').innerText();
    if (!inactiveLoginBody.includes('Correo o contraseña incorrectos')) {
      throw new Error(`Login de cuenta inactiva no devolvió mensaje uniforme: ${inactiveLoginBody}`);
    }

    // HU-USR-05: Admin reactiva a Carla -> Carla vuelve a iniciar sesión y recupera permisos
    await pageA.goto(`${BASE_URL}/empleados/?q=ventas@minimarket.local`, { waitUntil: 'networkidle' });
    await Promise.all([
      pageA.waitForNavigation({ waitUntil: 'networkidle' }),
      pageA.click('button:has-text("Reactivar")'),
    ]);
    await loginOnPage(pageB, 'ventas@minimarket.local', 'Audit02!Ven');
    const respReactivatedHome = await pageB.goto(`${BASE_URL}/inicio/`, { waitUntil: 'networkidle' });
    if (respReactivatedHome.status() !== 200 || !pageB.url().endsWith('/inicio/')) {
      throw new Error(`Empleada reactivada no pudo recuperar el acceso a /inicio/`);
    }

    // 6. QA00-L877-c: Verificar 404 en UUID inexistente de empleado
    const resp404 = await pageA.goto(
      `${BASE_URL}/empleados/00000000-0000-0000-0000-000000000000/editar/`,
      { waitUntil: 'networkidle' }
    );
    const metrics404 = await layoutMetrics(pageA);
    if (resp404.status() !== 404 || metrics404.title !== 'Página no encontrada · Minimarket') {
      throw new Error(`404 en empleado inexistente falló: ${resp404.status()} | ${metrics404.title}`);
    }

    report.steps.push({
      id: 'HU-USR-04-05-BLOQUEO-TURNO-REVOCACION-SESION-REACTIVACION-Y-404',
      ok: true,
      screenshot: shotDeact,
      revokedSessionUrl,
      reactivatedHomeStatus: respReactivatedHome.status(),
      notFound404Status: resp404.status(),
      notFound404Title: metrics404.title,
    });

    await contextA.close();
    await contextB.close();
  } finally {
    await browser.close();
  }

  if (report.consoleErrors.length > 0 || report.pageErrors.length > 0) {
    throw new Error(`Errores de consola/página detectados: ${JSON.stringify(report)}`);
  }

  const outPath = path.join(EVIDENCIAS_DIR, '02-chrome-empleados.json');
  fs.writeFileSync(outPath, JSON.stringify(report, null, 2), 'utf-8');
  console.log(JSON.stringify(report, null, 2));
})();
