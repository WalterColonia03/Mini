/* Isolated real-browser checks against the raw WSGI server. */
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const crypto = require('node:crypto');
const assert = require('node:assert/strict');
const { chromium } = require(path.join(os.homedir(), '.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright-core'));
const root = path.resolve(__dirname, '../../..');
const data = path.join(root, 'auditoria_por_etapas/resultados/datos/01-J-20261115');
const out = path.join(root, 'auditoria_por_etapas/resultados/evidencias/01-J-20261115');
const screenshots = path.join(out, 'navegador');
fs.mkdirSync(screenshots, { recursive: true });
const creds = JSON.parse(fs.readFileSync(path.join(data, '.credentials.json'), 'utf8'));
const key = fs.readFileSync(path.join(data, '.django-key'), 'utf8').trim();
const base = 'http://127.0.0.1:8798';
const result = { started_at_utc: new Date().toISOString(), checks: [], screenshots: [], errors: [] };
function check(id, ok, extra = {}) { result.checks.push({ id, ok, ...extra }); assert.equal(ok, true, id); }
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
async function screenshot(page, file) {
  await page.screenshot({ path: path.join(screenshots, file), fullPage: false });
  result.screenshots.push('navegador/' + file);
}
(async () => {
  const browser = await chromium.launch({ executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe', headless: true });
  result.chrome = browser.version();
  try {
    for (const width of [1366, 390, 320]) {
      const ctx = await browser.newContext({ locale: 'es-PE', viewport: { width, height: width === 1366 ? 768 : 844 } });
      const page = await ctx.newPage();
      page.on('pageerror', e => result.errors.push({ width, message: e.message }));
      const nonce = crypto.randomBytes(24).toString('hex');
      const proof = await page.request.get(base + '/', { headers: { 'X-Audit01j-Challenge': nonce } });
      check('UI_' + width + '_SERVIDOR', proof.headers()['x-audit01j-proof'] === crypto.createHmac('sha256', key).update(nonce).digest('hex'));
      const response = await page.goto(base + '/', { waitUntil: 'networkidle' });
      const css = await page.request.get(base + '/static/identity/app.css');
      const js = await page.request.get(base + '/static/identity/navigation.js');
      const view = await page.evaluate(() => ({
        width: innerWidth, scrollWidth: document.documentElement.scrollWidth,
        cssRules: [...document.styleSheets].reduce((sum, sheet) => { try { return sum + sheet.cssRules.length; } catch { return sum; } }, 0),
        borderRadius: getComputedStyle(document.querySelector('.login-card')).borderRadius,
        emailMax: document.querySelector('[name=email]').maxLength,
        emailAutocomplete: document.querySelector('[name=email]').autocomplete,
        passwordAutocomplete: document.querySelector('[name=password]').autocomplete,
      }));
      check('UI_' + width + '_CSS_JS_LAYOUT', response.status() === 200 && css.status() === 200 && js.status() === 200 && (css.headers()['content-type'] || '').includes('text/css') && view.cssRules > 0 && parseFloat(view.borderRadius) > 0 && view.scrollWidth <= view.width, { css: css.status(), js: js.status(), ...view });
      check('UI_' + width + '_ETIQUETAS_AUTOCOMPLETADO', view.emailMax === 254 && view.emailAutocomplete === 'username' && view.passwordAutocomplete === 'current-password' && await page.getByLabel('Correo de trabajo').count() === 1 && await page.getByLabel('Contraseña', { exact: true }).count() === 1);
      await screenshot(page, '01-J-ingreso-' + width + '.png');

      await page.locator('[name=email]').focus();
      await page.keyboard.press('Shift+Tab');
      await page.keyboard.press('Shift+Tab');
      const focus = await page.evaluate(() => {
        const skip = document.querySelector('.skip-link');
        const rect = skip.getBoundingClientRect();
        return { isSkip: document.activeElement === skip, top: rect.top, bottom: rect.bottom, text: skip.textContent.trim() };
      });
      check('UI_' + width + '_SALTO_TECLADO', focus.isSkip && focus.top >= 0 && focus.bottom <= (width === 1366 ? 768 : 844), focus);
      await page.keyboard.press('Enter');
      const target = await page.evaluate(() => ({ hash: location.hash, activeId: document.activeElement.id }));
      check('UI_' + width + '_SALTO_DESTINO', target.hash === '#contenido' && target.activeId === 'contenido', target);

      const emptyStatus = await submit(page, '', '');
      const fields = await page.evaluate(() => {
        const email = document.querySelector('[name=email]');
        const password = document.querySelector('[name=password]');
        return {
          emailInvalid: email.getAttribute('aria-invalid'), passwordInvalid: password.getAttribute('aria-invalid'),
          emailDescription: email.getAttribute('aria-describedby'), passwordDescription: password.getAttribute('aria-describedby'),
          emailMessage: email.closest('.field').innerText, passwordMessage: password.closest('.field').innerText,
          emailFocusVisible: getComputedStyle(email).outlineStyle !== 'none' || getComputedStyle(email).boxShadow !== 'none',
        };
      });
      check('UI_' + width + '_ERRORES_VACIO', emptyStatus === 200 && fields.emailInvalid === 'true' && fields.passwordInvalid === 'true' && fields.emailMessage.includes('Este campo es obligatorio.') && fields.passwordMessage.includes('Este campo es obligatorio.'), { status: emptyStatus, ...fields });
      await page.locator('[name=email]').scrollIntoViewIfNeeded();
      await screenshot(page, '01-J-errores-' + width + '.png');
      await ctx.close();
    }

    const ctx = await browser.newContext({ locale: 'es-PE', viewport: { width: 1366, height: 768 } });
    const page = await ctx.newPage();
    await page.goto(base + '/');
    for (let i = 1; i <= 5; i++) {
      const status = await submit(page, creds.staff_admin.email, 'Incorrecta01J!');
      const message = (await page.locator('[data-testid=login-error]').innerText()).trim();
      check('ADMIN_FALLO_' + i, status === 200 && (i < 5 ? message.includes('Correo o contraseña incorrectos') : message.includes('15 minuto(s)')), { status, locked: message.includes('minuto(s)') });
    }
    const adminGet = await page.request.get(base + '/admin/login/');
    const adminPost = await page.request.post(base + '/admin/login/', { form: { username: creds.staff_admin.email, password: creds.staff_admin.password } });
    const sessionCookie = (await ctx.cookies()).some(c => c.name === 'audit01j_sessionid');
    check('ADMIN_BLOQUEADO_SIN_RUTA_ALTERNATIVA', adminGet.status() === 404 && adminPost.status() === 404 && !sessionCookie, { get: adminGet.status(), post: adminPost.status(), sessionCookie });
    await page.goto(base + '/');
    const blockedStatus = await submit(page, creds.staff_admin.email, creds.staff_admin.password);
    const blocked = (await page.locator('[data-testid=login-error]').innerText()).trim();
    check('ADMIN_BLOQUEADO_CLAVE_CORRECTA', blockedStatus === 200 && blocked.includes('15 minuto(s)'), { status: blockedStatus, message: blocked });
    await page.locator('[data-testid=login-error]').screenshot({ path: path.join(screenshots, '01-J-bloqueo-sin-campos.png') });
    result.screenshots.push('navegador/01-J-bloqueo-sin-campos.png');
    await ctx.close();
    check('UI_SIN_ERRORES_JS', result.errors.length === 0, { errors: result.errors });
  } finally {
    await browser.close();
    result.finished_at_utc = new Date().toISOString();
    fs.writeFileSync(path.join(out, 'navegador-01j.json'), JSON.stringify(result, null, 2) + '\n');
  }
  console.log(JSON.stringify({ checks: result.checks.length, failures: result.checks.filter(item => !item.ok).length, screenshots: result.screenshots.length }));
})().catch(err => { console.error(String(err)); process.exitCode = 1; });
