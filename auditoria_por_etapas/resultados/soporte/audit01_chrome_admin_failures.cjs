// Cinco rechazos ordinarios en un perfil efímero de Chrome, exclusivamente en admin.
const assert = require('node:assert/strict')
const { execFileSync } = require('node:child_process')
const crypto = require('node:crypto')
const fs = require('node:fs')
const os = require('node:os')
const path = require('node:path')
const { DatabaseSync } = require('node:sqlite')
const { chromium } = require(path.join(os.homedir(), '.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright-core'))
const results = path.resolve(__dirname, '..')
const root = path.resolve(results, '../..')
const data = path.join(results, 'datos/etapa01-20261109')
const base = 'http://127.0.0.1:8766'
const run = '01-chrome-admin-failures-' + new Date().toISOString().replace(/[:-]/g, '').replace('.', '-')
const output = path.join(results, 'evidencias', run)
const evidence = { date_utc: new Date().toISOString(), zone: 'America/Lima', attempts: [] }
let step = 'preparacion'

function proof() {
  execFileSync(path.join(root, 'r1-pmv/.venv/Scripts/python.exe'), [path.join(__dirname, 'audit01.py'), 'proof'], { stdio: 'pipe' })
}

function snapshot() {
  const database = path.join(data, 'audit.sqlite3')
  const prepared = JSON.parse(fs.readFileSync(path.join(data, 'prepared.json'), 'utf8'))
  assert.equal(path.resolve(prepared.database), database)
  const db = new DatabaseSync(database, { readOnly: true })
  try {
    db.exec('PRAGMA query_only = ON')
    assert.equal(db.prepare('PRAGMA query_only').get().query_only, 1)
    const sql = 'SELECT COUNT(*) AS rows, COALESCE(SUM(failures), 0) AS total_failures, COUNT(locked_until) AS rows_with_lock_date FROM identity_loginattempt'
    return { utc: new Date().toISOString(), sql, counts: db.prepare(sql).get() }
  } finally {
    db.close()
  }
}

async function runAudit() {
  fs.mkdirSync(output)
  proof()
  evidence.before = snapshot()
  const browser = await chromium.launch({ channel: 'chrome', headless: true })
  try {
    evidence.tool = 'Playwright Core / Chrome estable headless ' + browser.version()
    evidence.viewport = { width: 1366, height: 768 }
    const context = await browser.newContext({ viewport: evidence.viewport, locale: 'es-PE' })
    await context.route('**/*', route => new URL(route.request().url()).origin === base ? route.continue() : route.abort())
    const page = await context.newPage()
    assert.equal((await page.goto(base + '/admin/login/?next=/admin/')).status(), 200)
    const email = JSON.parse(fs.readFileSync(path.join(data, '.credentials.json'), 'utf8')).staff.email
    for (let number = 1; number <= 5; number++) {
      step = 'rechazo-' + number
      const form = page.locator('#login-form')
      assert.equal(await form.evaluate(node => new URL(node.action).origin), base)
      proof()
      await form.locator('[name=username]').fill(email)
      await form.locator('[name=password]').fill('audit-incorrect-' + crypto.randomBytes(24).toString('hex'))
      const navigation = page.waitForNavigation({ waitUntil: 'domcontentloaded' })
      await form.locator('[type=submit]').click()
      const response = await navigation
      const message = await page.locator('.errornote').innerText()
      const session = (await context.cookies(base)).some(cookie => cookie.name === 'audit01_sessionid')
      const passwordEmpty = !(await page.locator('[name=password]').inputValue())
      assert.deepEqual([response.status(), new URL(page.url()).pathname, session, passwordEmpty], [200, '/admin/login/', false, true])
      assert.ok(message.trim())
      if (number > 1) assert.equal(message, evidence.attempts[0].message)
      evidence.attempts.push({ number, status: response.status(), path: '/admin/login/', session, passwordEmpty, message })
    }
    await page.locator('.errornote').screenshot({ path: path.join(output, 'quinto-rechazo.png') })
    evidence.after = snapshot()
    evidence.status = 'completado'
    evidence.scope = 'Cinco contraseñas aleatorias erróneas de fixture staff, perfil nuevo, sólo formulario Django admin. Contadores globales de LoginAttempt leídos sin identificadores. Otros navegadores pueden modificar el agregado durante el intervalo.'
    evidence.limitations = 'No se intentó autenticación válida después de estos fallos. La política de bloqueo, tráfico y acceso administrativo queda pendiente de decisión y revisión adicional.'
    await context.close()
  } finally {
    await browser.close()
  }
}

runAudit().catch(error => {
  evidence.status = 'incompleto'
  evidence.stopped_at = step
  evidence.error_type = error.name
  process.exitCode = 1
}).finally(() => {
  fs.writeFileSync(path.join(output, 'observaciones.json'), JSON.stringify(evidence, null, 2) + '\n')
  console.log(JSON.stringify({ evidence: path.relative(results, output), status: evidence.status, attempts: evidence.attempts.length, stoppedAt: evidence.stopped_at }))
})
