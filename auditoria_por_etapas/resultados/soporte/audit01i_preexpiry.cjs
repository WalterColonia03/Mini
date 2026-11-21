/* Confirm the active lock after restarting with the final rejection-audit fix. */
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const crypto = require('node:crypto');
const assert = require('node:assert/strict');
const { chromium } = require(path.join(os.homedir(), '.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright-core'));
const root = path.resolve(__dirname, '../../..');
const data = path.join(root, 'auditoria_por_etapas/resultados/datos/01-I-20261115');
const out = path.join(root, 'auditoria_por_etapas/resultados/evidencias/01-I-20261115');
const fixture = JSON.parse(fs.readFileSync(path.join(data, '.credentials.json'), 'utf8')).admin;
const key = fs.readFileSync(path.join(data, '.django-key'), 'utf8').trim();
const base = 'http://127.0.0.1:8796';
const result = { at_utc: new Date().toISOString(), checks: [], services_sha256: crypto.createHash('sha256').update(fs.readFileSync(path.join(root, 'r1-pmv/identity/services.py'))).digest('hex') };
function check(id, ok, extra = {}) { result.checks.push({ id, ok, ...extra }); assert.equal(ok, true, id); }
(async () => {
  const browser = await chromium.launch({ executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe', headless: true });
  try {
    const ctx = await browser.newContext();
    const page = await ctx.newPage();
    const nonce = crypto.randomBytes(24).toString('hex');
    const proof = await page.request.get(base + '/', { headers: { 'X-Audit01i-Challenge': nonce } });
    check('PRE_FINAL_SERVIDOR_PROPIO', proof.headers()['x-audit01i-proof'] === crypto.createHmac('sha256', key).update(nonce).digest('hex'));
    await page.goto(base + '/');
    await page.locator('[name=email]').fill(fixture.email);
    await page.locator('[name=password]').fill(fixture.password);
    const [response] = await Promise.all([
      page.waitForResponse(r => r.request().method() === 'POST'),
      page.locator('button[type=submit]').click(),
    ]);
    const text = (await page.locator('[data-testid=login-error]').innerText()).trim();
    const session = (await ctx.cookies()).some(c => c.name === 'audit01i_sessionid');
    check('PRE_FINAL_BLOQUEO_PERSISTE', response.status() === 200 && /[1-9]\d* minuto\(s\)/.test(text) && !session, { status: response.status(), message: text, session });
    await ctx.close();
  } finally {
    await browser.close();
    fs.writeFileSync(path.join(out, 'pre-expiracion-build-final.json'), JSON.stringify(result, null, 2) + '\n');
  }
  console.log(JSON.stringify({ checks: result.checks.length, failures: result.checks.filter(x => !x.ok).length }));
})().catch(err => { console.error(String(err)); process.exitCode = 1; });
