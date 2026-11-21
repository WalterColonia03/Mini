/* Check the already active lock without advancing time; finish after expiry. */
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const crypto = require('node:crypto');
const assert = require('node:assert/strict');
const { chromium } = require(path.join(os.homedir(), '.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright-core'));
const root = path.resolve(__dirname, '../../..');
const data = path.join(root, 'auditoria_por_etapas/resultados/datos/01-I-20261115');
const output = path.join(root, 'auditoria_por_etapas/resultados/evidencias/01-I-20261115');
const fixture = JSON.parse(fs.readFileSync(path.join(data, '.credentials.json'), 'utf8')).admin;
const key = fs.readFileSync(path.join(data, '.django-key'), 'utf8').trim();
const initial = JSON.parse(fs.readFileSync(path.join(output, 'antes-espera.json'), 'utf8'));
const base = 'http://127.0.0.1:8796';
const result = { started_at_utc: new Date().toISOString(), fuente_estado: 'antes-espera.json', clock_adjusted: false, checks: [] };
function check(id, ok, details = {}) { result.checks.push({ id, ok, ...details }); assert.equal(ok, true, id); }
async function submit(page) {
  await page.goto(base + '/');
  await page.locator('[name=email]').fill(fixture.email.toUpperCase());
  await page.locator('[name=password]').fill(fixture.password);
  const [response] = await Promise.all([
    page.waitForResponse(r => r.url().startsWith(base + '/') && r.request().method() === 'POST'),
    page.locator('button[type=submit]').click(),
  ]);
  await page.waitForLoadState('domcontentloaded');
  return response.status();
}
(async () => {
  const browser = await chromium.launch({ executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe', headless: true });
  result.chrome_version = browser.version();
  try {
    const ctx = await browser.newContext();
    const page = await ctx.newPage();
    const nonce = crypto.randomBytes(24).toString('hex');
    const proof = await page.request.get(base + '/', { headers: { 'X-Audit01i-Challenge': nonce } });
    check('WAIT_SERVIDOR_PROPIO', proof.headers()['x-audit01i-proof'] === crypto.createHmac('sha256', key).update(nonce).digest('hex'));
    const before = await submit(page);
    const message = (await page.locator('[data-testid=login-error]').innerText()).trim();
    const beforeTime = new Date();
    check('WAIT_CLAVE_CORRECTA_ANTES_VENCIMIENTO', before === 200 && /[1-9]\d* minuto\(s\)/.test(message), { status: before, message, at_utc: beforeTime.toISOString() });
    const expires = Date.parse(initial.locked_until_utc);
    const delayMs = Math.max(0, expires - Date.now() + 2500);
    check('WAIT_RELOJ_Y_PLAZO', Number.isFinite(expires) && delayMs > 0 && delayMs < 16 * 60 * 1000 && initial.fallos === 5, { wait_ms: delayMs });
    const monotonicStart = process.hrtime.bigint();
    await new Promise(resolve => setTimeout(resolve, delayMs));
    result.wait_monotonic_seconds = Number(process.hrtime.bigint() - monotonicStart) / 1e9;
    const after = await submit(page);
    await page.waitForURL(base + '/inicio/');
    const role = (await page.locator('.role-pill').innerText()).trim();
    const reload = await page.reload();
    const observedAt = new Date();
    const fifth = Date.parse(initial.evento_quinto_fallo_utc);
    check('WAIT_DESPUES_VENCIMIENTO_ENTRA_PERSISTE', after === 302 && role === 'Administrador' && reload.status() === 200 && observedAt.getTime() >= expires, { status: after, role, reload: reload.status(), at_utc: observedAt.toISOString(), elapsed_since_fifth_event_seconds: (observedAt.getTime() - fifth) / 1000 });
    await ctx.close();
  } finally {
    await browser.close();
    result.finished_at_utc = new Date().toISOString();
    fs.writeFileSync(path.join(output, 'espera-real-01i.json'), JSON.stringify(result, null, 2) + '\n');
  }
  console.log(JSON.stringify({ checks: result.checks.length, failures: result.checks.filter(x => !x.ok).length, elapsed_since_fifth_event_seconds: result.checks.at(-1).elapsed_since_fifth_event_seconds }));
})().catch(e => { console.error(String(e)); process.exitCode = 1; });
