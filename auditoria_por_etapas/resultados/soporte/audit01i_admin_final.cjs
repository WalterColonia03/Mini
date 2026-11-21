/* Final-build checks: no alternative Django admin route or role escalation. */
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const crypto = require('node:crypto');
const assert = require('node:assert/strict');
const { chromium } = require(path.join(os.homedir(), '.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright-core'));
const root = path.resolve(__dirname, '../../..');
const data = path.join(root, 'auditoria_por_etapas/resultados/datos/01-I-20261115');
const out = path.join(root, 'auditoria_por_etapas/resultados/evidencias/01-I-20261115');
const creds = JSON.parse(fs.readFileSync(path.join(data, '.credentials.json'), 'utf8'));
const key = fs.readFileSync(path.join(data, '.django-key'), 'utf8').trim();
const base = 'http://127.0.0.1:8796';
const result = { at_utc: new Date().toISOString(), checks: [], services_sha256: crypto.createHash('sha256').update(fs.readFileSync(path.join(root, 'r1-pmv/identity/services.py'))).digest('hex') };
function check(id, ok, detail = {}) { result.checks.push({ id, ok, ...detail }); assert.equal(ok, true, id); }
async function submit(page, fixture) {
  await page.goto(base + '/');
  await page.locator('[name=email]').fill(fixture.email);
  await page.locator('[name=password]').fill(fixture.password);
  const [response] = await Promise.all([
    page.waitForResponse(r => r.request().method() === 'POST'),
    page.locator('button[type=submit]').click(),
  ]);
  await page.waitForLoadState('domcontentloaded');
  return response.status();
}
(async () => {
  const browser = await chromium.launch({ executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe', headless: true });
  try {
    const blocked = await browser.newContext();
    const page = await blocked.newPage();
    const nonce = crypto.randomBytes(24).toString('hex');
    const proof = await page.request.get(base + '/', { headers: { 'X-Audit01i-Challenge': nonce } });
    check('ADMIN_FINAL_SERVIDOR_PROPIO', proof.headers()['x-audit01i-proof'] === crypto.createHmac('sha256', key).update(nonce).digest('hex'));
    const publicStatus = await submit(page, creds.staff_admin);
    const message = (await page.locator('[data-testid=login-error]').innerText()).trim();
    check('ADMIN_FINAL_STAFF_BLOQUEADO', publicStatus === 200 && /[1-9]\d* minuto\(s\)/.test(message), { status: publicStatus, message });
    const adminGet = await page.request.get(base + '/admin/');
    const adminPost = await page.request.post(base + '/admin/login/', { form: { username: creds.staff_admin.email, password: creds.staff_admin.password } });
    const cookie = (await blocked.cookies()).some(c => c.name === 'audit01i_sessionid');
    check('ADMIN_FINAL_STAFF_SIN_BYPASS', adminGet.status() === 404 && adminPost.status() === 404 && !cookie, { get: adminGet.status(), post: adminPost.status(), session: cookie });
    await blocked.close();

    const privileged = await browser.newContext();
    const su = await privileged.newPage();
    const login = await submit(su, creds.super_seller);
    await su.waitForURL(base + '/inicio/');
    const role = (await su.locator('.role-pill').innerText()).trim();
    const adminPage = await su.goto(base + '/admin/identity/account/');
    const employees = await su.goto(base + '/empleados/');
    check('ADMIN_FINAL_SUPERUSER_RESPETA_ROL', login === 302 && role === 'Vendedor' && adminPage.status() === 404 && employees.status() === 403, { login, role, admin: adminPage.status(), employees: employees.status() });
    await privileged.close();
  } finally {
    await browser.close();
    fs.writeFileSync(path.join(out, 'admin-final.json'), JSON.stringify(result, null, 2) + '\n');
  }
  console.log(JSON.stringify({ checks: result.checks.length, failures: result.checks.filter(c => !c.ok).length }));
})().catch(err => { console.error(String(err)); process.exitCode = 1; });
