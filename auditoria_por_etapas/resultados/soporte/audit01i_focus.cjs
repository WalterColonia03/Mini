/* Focus, inline errors and skip link: real browser, no fixture credentials. */
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const assert = require('node:assert/strict');
const { chromium } = require(path.join(os.homedir(), '.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright-core'));
const root = path.resolve(__dirname, '../../..');
const out = path.join(root, 'auditoria_por_etapas/resultados/evidencias/01-I-20261115');
const base = 'http://127.0.0.1:8796';
const result = { started_at_utc: new Date().toISOString(), checks: [], screenshots: [] };
function check(id, ok, detail = {}) { result.checks.push({ id, ok, ...detail }); assert.equal(ok, true, id); }
(async () => {
  const browser = await chromium.launch({ executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe', headless: true });
  result.chrome = browser.version();
  try {
    for (const width of [1366, 390, 320]) {
      const ctx = await browser.newContext({ locale: 'es-PE', viewport: { width, height: width === 1366 ? 768 : 844 } });
      const page = await ctx.newPage();
      await page.goto(base + '/', { waitUntil: 'networkidle' });
      await page.locator('.skip-link').focus();
      await page.locator('[name=email]').focus();
      await page.waitForTimeout(250);
      const hidden = await page.locator('.skip-link').evaluate(el => ({ bottom: el.getBoundingClientRect().bottom, active: document.activeElement === el }));
      check('FOCUS_' + width + '_SALTO_OCULTO_SIN_FOCO', !hidden.active && hidden.bottom <= 0, hidden);
      const [response] = await Promise.all([
        page.waitForResponse(r => r.request().method() === 'POST'),
        page.locator('button[type=submit]').click(),
      ]);
      await page.waitForLoadState('domcontentloaded');
      await page.locator('[name=email]').focus();
      await page.waitForTimeout(250);
      const focused = await page.locator('[name=email]').evaluate(el => {
        const c = getComputedStyle(el);
        const id = el.getAttribute('aria-describedby');
        const linked = id ? document.getElementById(id) : null;
        return { focused: document.activeElement === el, outline: c.outline, boxShadow: c.boxShadow, errorReferenceExists: !!linked, errorText: linked?.innerText || '' };
      });
      check('FOCUS_' + width + '_ERROR_ASOCIADO_Y_ANILLO', response.status() === 200 && focused.focused && focused.errorReferenceExists && focused.errorText.includes('Este campo es obligatorio.') && (focused.boxShadow !== 'none' || !focused.outline.startsWith('0px')), focused);
      const shot = 'navegador/01-I-formulario-error-' + width + '.png';
      await page.locator('form').screenshot({ path: path.join(out, shot) });
      result.screenshots.push(shot);
      await ctx.close();
    }
  } finally {
    await browser.close();
    fs.writeFileSync(path.join(out, 'foco-y-errores.json'), JSON.stringify(result, null, 2) + '\n');
  }
  console.log(JSON.stringify({ checks: result.checks.length, failures: result.checks.filter(c => !c.ok).length }));
})().catch(err => { console.error(String(err)); process.exitCode = 1; });
