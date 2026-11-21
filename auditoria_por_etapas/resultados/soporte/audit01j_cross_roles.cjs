/* Continue from audit01j_roles.cjs while the fictional ADMIN lock is active. */
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const crypto = require('node:crypto');
const assert = require('node:assert/strict');
const { chromium } = require(path.join(os.homedir(), '.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright-core'));
const root = path.resolve(__dirname, '../../..');
const data = path.join(root, 'auditoria_por_etapas/resultados/datos/01-J-20261115');
const out = path.join(root, 'auditoria_por_etapas/resultados/evidencias/01-J-20261115/chrome-efecto-entre-roles.json');
const creds = JSON.parse(fs.readFileSync(path.join(data, '.credentials.json'), 'utf8'));
const key = fs.readFileSync(path.join(data, '.django-key'), 'utf8').trim();
const base = 'http://127.0.0.1:8798';
const evidence = { at_utc: new Date().toISOString(), checks: [] };
function record(id, ok, details = {}) { evidence.checks.push({ id, ok, ...details }); assert.equal(ok, true, id); }
async function submit(page, account) {
  await page.goto(base + '/');
  await page.locator('[name=email]').fill(account.email);
  await page.locator('[name=password]').fill(account.password);
  const [response] = await Promise.all([
    page.waitForResponse(r => r.url().startsWith(base + '/') && r.request().method() === 'POST'),
    page.locator('button[type=submit]').click(),
  ]);
  await page.waitForLoadState('domcontentloaded');
  return response.status();
}
(async () => {
  const browser = await chromium.launch({ executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe', headless: true });
  evidence.chrome = browser.version();
  try {
    const adminContext = await browser.newContext();
    const adminPage = await adminContext.newPage();
    const nonce = crypto.randomBytes(24).toString('hex');
    const proof = await adminPage.request.get(base + '/', { headers: { 'X-Audit01j-Challenge': nonce } });
    record('CROSS_PROOF', proof.headers()['x-audit01j-proof'] === crypto.createHmac('sha256', key).update(nonce).digest('hex'));
    const adminStatus = await submit(adminPage, creds.admin);
    const adminMessage = (await adminPage.locator('[data-testid=login-error]').innerText()).trim();
    record('CROSS_ADMIN_SIGUE_BLOQUEADO', adminStatus === 200 && /[1-9]\d* minuto\(s\)/.test(adminMessage), { status: adminStatus, message: adminMessage });
    for (const [name, label] of [['warehouse', 'Almacenero'], ['seller', 'Vendedor']]) {
      const ctx = await browser.newContext();
      const page = await ctx.newPage();
      const status = await submit(page, creds[name]);
      await page.waitForURL(base + '/inicio/');
      const role = (await page.locator('.role-pill').innerText()).trim();
      const employees = await page.goto(base + '/empleados/');
      record('CROSS_' + name.toUpperCase() + '_INGRESA_PERO_NO_EMPLEADOS', status === 302 && role === label && employees.status() === 403, { status, role, employees_status: employees.status() });
      await ctx.close();
    }
    const adminAgain = await submit(adminPage, creds.admin);
    const after = (await adminPage.locator('[data-testid=login-error]').innerText()).trim();
    record('CROSS_OTROS_ROLES_NO_DESBLOQUEAN_ADMIN', adminAgain === 200 && /[1-9]\d* minuto\(s\)/.test(after), { status: adminAgain, message: after });
    await adminContext.close();
  } finally {
    await browser.close();
    fs.writeFileSync(out, JSON.stringify(evidence, null, 2) + '\n');
  }
  console.log(JSON.stringify({ checks: evidence.checks.length, failures: evidence.checks.filter(x => !x.ok).length }));
})().catch(err => { console.error(String(err)); process.exitCode = 1; });
