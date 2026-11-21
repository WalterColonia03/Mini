// Bordes visuales pendientes de E01-F01. Usa únicamente el servidor aislado audit01.
const assert = require('node:assert/strict')
const { execFileSync } = require('node:child_process')
const { createHash, randomUUID } = require('node:crypto')
const fs = require('node:fs')
const os = require('node:os')
const path = require('node:path')
const { DatabaseSync } = require('node:sqlite')
const { chromium } = require(path.join(os.homedir(), '.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright-core'))
const result = path.resolve(__dirname, '..')
const root = path.resolve(result, '../..')
const data = path.join(result, 'datos/etapa01-20261109')
const base = 'http://127.0.0.1:8766'
const directory = path.join(result, 'evidencias', '01-D-unicode-' + new Date().toISOString().replace(/[:.]/g, '-'))
const evidence = { inicio_utc: new Date().toISOString(), casos: [], viewport: { width: 1366, height: 768 } }

async function run() {
  execFileSync(path.join(root, 'r1-pmv/.venv/Scripts/python.exe'), [path.join(__dirname, 'audit01.py'), 'proof'], { stdio: 'pipe', windowsHide: true })
  const prepared = JSON.parse(fs.readFileSync(path.join(data, 'prepared.json'), 'utf8'))
  assert.equal(path.resolve(prepared.database), path.join(data, 'audit.sqlite3'))
  const db = new DatabaseSync(prepared.database, { readOnly: true })
  const fixture = JSON.parse(fs.readFileSync(path.join(data, '.credentials.json'), 'utf8')).admin
  const count = () => db.prepare('SELECT count(*) AS n FROM identity_loginattempt').get().n
  const account = () => db.prepare('SELECT last_login FROM identity_account WHERE email_normalized = ?').get(fixture.email).last_login
  const before = account()
  fs.mkdirSync(directory)
  const browser = await chromium.launch({ channel: 'chrome', headless: true })
  evidence.navegador = browser.version()
  evidence.base = 'datos/etapa01-20261109/audit.sqlite3'
  try {
    const cases = [
      { nombre: 'Espacios NBSP, tabulador y mayúsculas', email: '\u00a0\t' + fixture.email.toUpperCase() + '\u00a0', password: fixture.password, success: true, delta: 0 },
      { nombre: 'Correo compuesto sólo por espacios', email: '     ', field: 'Este campo es obligatorio.', delta: 0 },
      { nombre: 'Parte local Unicode', email: 'josé.audit01@example.invalid', field: 'Introduzca una dirección de correo electrónico válida.', delta: 0 },
      { nombre: 'Dominio IDN de identificador ficticio inexistente', email: 'nuevo@münchen.invalid', general: 'Correo o contraseña incorrectos', delta: 1 },
    ]
    for (const [index, item] of cases.entries()) {
      const context = await browser.newContext({ viewport: evidence.viewport, locale: 'es-PE' })
      await context.route('**/*', route => new URL(route.request().url()).origin === base ? route.continue() : route.abort())
      const page = await context.newPage()
      await page.goto(base)
      const rows = count()
      await page.locator('[name=email]').fill(item.email)
      await page.locator('[name=password]').fill(item.password || randomUUID())
      const [response] = await Promise.all([page.waitForResponse(r => r.url() === base + '/' && r.request().method() === 'POST'), page.locator('button[type=submit]').click()])
      await page.waitForLoadState('domcontentloaded')
      const saved = {
        caso: item.nombre, http_post: response.status(), ruta: new URL(page.url()).pathname,
        filas_antes: rows, filas_despues: count(),
        cookie_sesion_presente: (await context.cookies(base)).some(cookie => cookie.name === 'audit01_sessionid'),
      }
      if (item.success) {
        saved.rol = await page.locator('.role-pill').innerText()
        saved.last_login_actualizado = before !== account()
        assert.equal(saved.http_post, 302)
        assert.equal(saved.ruta, '/inicio/')
        assert.equal(saved.rol, 'Administrador')
        assert.ok(saved.cookie_sesion_presente && saved.last_login_actualizado)
      } else {
        saved.error_campo = await page.locator('#id_email_error').allTextContents()
        saved.error_general = await page.locator('[data-testid=login-error]').allTextContents()
        saved.clave_vacia = (await page.locator('[name=password]').inputValue()).length === 0
        assert.equal(saved.http_post, 200)
        assert.ok(!saved.cookie_sesion_presente && saved.clave_vacia)
        assert.equal(item.field ? saved.error_campo[0]?.trim() : saved.error_general[0]?.trim(), item.field || item.general)
        const capture = path.join(directory, 'caso-' + (index + 1) + '.png')
        await page.locator('.login-card').screenshot({ path: capture, mask: [page.locator('[name=email]')], maskColor: '#e5e7eb' })
        saved.captura = path.basename(capture)
        saved.sha256 = createHash('sha256').update(fs.readFileSync(capture)).digest('hex')
      }
      // Una repetición del IDN puede reutilizar la fila conservada del primer ensayo.
      assert.ok(saved.filas_despues - rows <= item.delta)
      assert.ok(saved.filas_despues >= rows)
      evidence.casos.push(saved)
      await context.close()
    }
    evidence.resultado = 'CUMPLE en los cuatro casos'
  } finally {
    await browser.close()
    db.close()
    evidence.fin_utc = new Date().toISOString()
    fs.writeFileSync(path.join(directory, 'observaciones.json'), JSON.stringify(evidence, null, 2) + '\n', { flag: 'wx' })
    console.log(path.relative(result, directory), evidence.casos.length)
  }
}
run().catch(error => { console.error(error.name); process.exitCode = 1 })
