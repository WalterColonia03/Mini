/* Additional browser checks for identity: distinct browser contexts, 3 roles,
   uniform rejection, cross-context lockout and direct authorization. */
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const crypto = require('node:crypto');
const assert = require('node:assert/strict');
const { chromium } = require(path.join(os.homedir(), '.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright-core'));

const root = path.resolve(__dirname, '../../..');
const data = path.join(root, 'auditoria_por_etapas/resultados/datos/01-H-20261115');
const out = path.join(root, 'auditoria_por_etapas/resultados/evidencias/01-H-20261115');
const creds = JSON.parse(fs.readFileSync(path.join(data, '.credentials.json'), 'utf8'));
const key = fs.readFileSync(path.join(data, '.django-key'), 'utf8').trim();
const base = 'http://127.0.0.1:8794';
const result = { started_at_utc: new Date().toISOString(), checks: [], screenshots: [], page_errors: [] };
function check(id, ok, details = {}) {
  result.checks.push({ id, ok, ...details });
  assert.equal(ok, true, id);
}
async function submit(page, email, password) {
  await page.locator('[name=email]').fill(email);
  await page.locator('[name=password]').fill(password);
  const [response] = await Promise.all([
    page.waitForResponse(r => r.url().startsWith(base + '/') && r.request().method() === 'POST'),
    page.locator('button[type=submit]').click(),
  ]);
  await page.waitForLoadState('domcontentloaded');
  return response.status();
}
async function context(browser) {
  const ctx = await browser.newContext({ locale: 'es-PE', viewport: { width: 1366, height: 768 } });
  ctx.on('page', p => p.on('pageerror', e => result.page_errors.push(e.message)));
  return ctx;
}
async function main() {
  const browser = await chromium.launch({ executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe', headless: true });
  result.chrome_version = browser.version();
  try {
    const checkCtx = await context(browser);
    const proofPage = await checkCtx.newPage();
    const nonce = crypto.randomBytes(24).toString('hex');
    const proof = await proofPage.request.get(base + '/', { headers: { 'X-Audit01h-Challenge': nonce } });
    check('R01_SERvidor_AISLADO', proof.headers()['x-audit01h-proof'] === crypto.createHmac('sha256', key).update(nonce).digest('hex'), { status: proof.status() });
    const rVisitor = await proofPage.goto(base + '/empleados/');
    check('R02_VISITANTE_REDIRIGIDO', rVisitor.status() === 200 && new URL(proofPage.url()).pathname === '/' && new URL(proofPage.url()).searchParams.get('next') === '/empleados/', { final_path: new URL(proofPage.url()).pathname });
    await checkCtx.close();

    for (const [name, label] of [['admin', 'Administrador'], ['warehouse', 'Almacenero'], ['seller', 'Vendedor']]) {
      const ctx = await context(browser);
      const page = await ctx.newPage();
      await page.goto(base + '/');
      const response = await submit(page, '  ' + creds[name].email.toUpperCase() + '  ', creds[name].password);
      await page.waitForURL(base + '/inicio/');
      const role = (await page.locator('.role-pill').textContent()).trim();
      const persisted = await page.reload();
      check('R03_' + name.toUpperCase() + '_INGRESA_Y_RECARGA', response === 302 && role === label && persisted.status() === 200, { role, post_status: response, reload_status: persisted.status() });
      const route = await page.goto(base + '/empleados/');
      const body = await page.locator('body').innerText();
      const expected = name === 'admin' ? 200 : 403;
      check('R04_' + name.toUpperCase() + '_PERMISO_DIRECTO', route.status() === expected && (name === 'admin' || !body.includes('Admin 01H')), { status: route.status(), expected });
      const screenshot = 'navegador/01-H-rol-' + name + '.png';
      if (name !== 'admin') {
        await page.screenshot({ path: path.join(out, screenshot), fullPage: true });
        result.screenshots.push(screenshot);
      }
      await ctx.close();
    }

    const texts = [];
    for (const [id, email, password] of [
      ['existente', creds.admin.email, 'Incorrecta-01H!'],
      ['inexistente', 'sin-cuenta-01h@ejemplo.invalid', 'Incorrecta-01H!'],
      ['inactiva', creds.inactive.email, creds.inactive.password],
    ]) {
      const ctx = await context(browser);
      const page = await ctx.newPage();
      await page.goto(base + '/');
      const status = await submit(page, email, password);
      const message = (await page.locator('[data-testid=login-error]').innerText()).trim();
      const emptyPassword = (await page.locator('[name=password]').inputValue()) === '';
      const authenticatedCookie = (await ctx.cookies()).some(c => c.name === 'audit01h_sessionid');
      check('R05_' + id.toUpperCase() + '_RECHAZO', status === 200 && emptyPassword && !authenticatedCookie && message.includes('Correo o contraseña incorrectos'), { status, emptyPassword, authenticatedCookie, message });
      texts.push(message);
      await ctx.close();
    }
    check('R06_TEXTO_RECHAZO_UNIFORME', texts.every(t => t === texts[0]), { equal: texts.every(t => t === texts[0]) });

    const first = await context(browser);
    const a = await first.newPage();
    await a.goto(base + '/');
    // The uniform-error check has already added exactly one failure for admin.
    for (let attempt = 2; attempt <= 5; attempt++) {
      const status = await submit(a, creds.admin.email.toUpperCase(), 'Incorrecta-01H!');
      const text = (await a.locator('[data-testid=login-error]').innerText()).trim();
      check('R07_FALLO_' + attempt, status === 200 && (attempt < 5 ? text.includes('Correo o contraseña incorrectos') : text.includes('15 minuto(s)')), { status, bloqueado: text.includes('minuto(s)') });
    }
    const second = await context(browser);
    const b = await second.newPage();
    await b.goto(base + '/');
    const lockedStatus = await submit(b, ' ' + creds.admin.email.toUpperCase() + ' ', creds.admin.password);
    const locked = (await b.locator('[data-testid=login-error]').innerText()).trim();
    const session = (await second.cookies()).some(c => c.name === 'audit01h_sessionid');
    check('R08_BLOQUEO_OTRO_CONTEXTO_CLAVE_VALIDA', lockedStatus === 200 && locked.includes('15 minuto(s)') && !session, { status: lockedStatus, message: locked, authenticatedCookie: session });
    await first.close();
    await second.close();
    check('R09_SIN_ERROR_JS', result.page_errors.length === 0, { count: result.page_errors.length });
  } finally {
    await browser.close();
    result.finished_at_utc = new Date().toISOString();
    fs.writeFileSync(path.join(out, 'chrome-roles.json'), JSON.stringify(result, null, 2) + '\n');
  }
  process.stdout.write(JSON.stringify({ checks: result.checks.length, failures: result.checks.filter(x => !x.ok).length, screenshots: result.screenshots.length }) + '\n');
}
main().catch(e => { process.stderr.write(String(e) + '\n'); process.exitCode = 1; });
