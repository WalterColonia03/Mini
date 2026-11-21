// Recorrido de interfaz local. Node 24, Playwright Core y el canal Chrome instalado.
// Se conservan únicamente rutas, estados, conteos y recortes de UI sin credenciales.
const assert = require('node:assert/strict')
const { execFileSync } = require('node:child_process')
const fs = require('node:fs')
const os = require('node:os')
const path = require('node:path')
const { DatabaseSync } = require('node:sqlite')
const { chromium } = require(path.join(os.homedir(), '.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright-core'))

const results = path.resolve(__dirname, '..')
const root = path.resolve(results, '../..')
const data = path.join(results, 'datos/etapa01-20261109')
const run = '01-chrome-b02-' + new Date().toISOString().replace(/[:-]/g, '').replace('.', '-')
const output = path.join(results, 'evidencias', run)
const base = 'http://127.0.0.1:8766'
const viewport = { width: 1366, height: 768 }
const evidence = { date_utc: new Date().toISOString(), zone: 'America/Lima', viewport, cases: {} }
let step = 'preparacion'

function proof() {
  execFileSync(path.join(root, 'r1-pmv/.venv/Scripts/python.exe'), [path.join(__dirname, 'audit01.py'), 'proof'], { stdio: 'pipe' })
}

function businessCounts() {
  const db = new DatabaseSync(path.join(data, 'audit.sqlite3'), { readOnly: true })
  try {
    const tables = db.prepare("SELECT name FROM sqlite_schema WHERE type='table' ORDER BY name").all()
    return Object.fromEntries(tables.filter(({ name }) => /^(catalog|inventory|cash|sales)_[a-z_]+$/.test(name))
      .map(({ name }) => [name, db.prepare('SELECT COUNT(*) AS n FROM "' + name + '"').get().n]))
  } finally {
    db.close()
  }
}

async function isolated(browser, onExternal = () => {}) {
  const context = await browser.newContext({ viewport, screen: viewport, locale: 'es-PE' })
  await context.route('**/*', route => {
    if (new URL(route.request().url()).origin === base) return route.continue()
    onExternal()
    return route.abort()
  })
  return context
}

async function verifyForm(page, route, selector) {
  const form = page.locator(selector)
  const target = await form.evaluate(node => ({ origin: new URL(node.action).origin, method: node.method, route: new URL(node.action).pathname }))
  assert.deepEqual(target, { origin: base, method: 'post', route })
  proof()
}

async function submit(page, route, selector, fixture, loginField) {
  await verifyForm(page, route, selector)
  const creds = JSON.parse(fs.readFileSync(path.join(data, '.credentials.json'), 'utf8'))[fixture]
  const form = page.locator(selector)
  await form.locator(loginField).fill(creds.email)
  await form.locator('input[type=password]').fill(creds.password)
  const post = page.waitForResponse(res => res.request().method() === 'POST' && new URL(res.url()).pathname === route)
  const nav = page.waitForNavigation({ waitUntil: 'domcontentloaded' })
  await form.locator('[type=submit]').click()
  const [response, document] = await Promise.all([post, nav])
  return { post: response.status(), document: document.status(), final: new URL(page.url()).pathname }
}

async function boundary(browser) {
  const ctx = await isolated(browser)
  try {
    const page = await ctx.newPage()
    let postCount = 0
    page.on('request', request => { if (request.method() === 'POST') postCount++ })
    assert.equal((await page.goto(base)).status(), 200)
    const email = page.getByLabel('Correo de trabajo')
    await email.focus()
    const typed = 'a'.repeat(64) + '@' + ['b'.repeat(63), 'c'.repeat(63), 'd'.repeat(63), 'e'.repeat(63)].join('.')
    assert.equal(typed.length, 320)
    await email.pressSequentially(typed)
    const after320 = (await email.inputValue()).length
    await email.press('x')
    const after321 = (await email.inputValue()).length
    const maxLength = await email.evaluate(el => el.maxLength)
    assert.deepEqual([maxLength, after320, after321, postCount], [320, 320, 320, 0])
    evidence.cases.keyboard_maxlength = { maxLength, after320, after321, postCount }
  } finally {
    await ctx.close()
  }
}

async function missing(browser) {
  const ctx = await isolated(browser)
  try {
    const page = await ctx.newPage()
    const destination = '/ruta-auditoria-01-inexistente/'
    await page.goto(base + '/?next=' + encodeURIComponent(destination))
    const result = await submit(page, '/', '[data-testid=login-form]', 'almacen', '[name=email]')
    assert.deepEqual(result, { post: 302, document: 404, final: destination })
    const panel = page.getByTestId('not-found')
    assert.equal(await panel.getByRole('heading').innerText(), 'Página no encontrada')
    await panel.screenshot({ path: path.join(output, 'next-404.png') })
    const nav = page.waitForNavigation({ waitUntil: 'domcontentloaded' })
    await panel.getByRole('link', { name: 'Volver al inicio' }).click()
    const returned = (await nav).status()
    const role = await page.locator('.topbar-user .role-pill').innerText()
    const returnPath = new URL(page.url()).pathname
    assert.deepEqual([returned, returnPath, role.toLocaleLowerCase('es')], [200, '/inicio/', 'almacenero'])
    evidence.cases.next_missing = { role, ...result, heading: 'Página no encontrada', returned, returnPath }
  } finally {
    await ctx.close()
  }
}

async function externalDestination(browser) {
  let attemptedExternal = 0
  const ctx = await isolated(browser, () => { attemptedExternal++ })
  try {
    const page = await ctx.newPage()
    const next = 'https://example.invalid/'
    await page.goto(base + '/?next=' + encodeURIComponent(next))
    assert.equal(await page.locator('input[name=next]').inputValue(), next)
    const before = attemptedExternal
    const post = page.waitForResponse(res => res.request().method() === 'POST' && res.url().startsWith(base + '/'))
    const result = await submit(page, '/', '[data-testid=login-form]', 'almacen', '[name=email]')
    const response = await post
    const location = new URL(await response.headerValue('location'), base)
    assert.equal(location.href, base + '/inicio/')
    assert.deepEqual(result, { post: 302, document: 200, final: '/inicio/' })
    const role = await page.locator('.topbar-user .role-pill').innerText()
    assert.equal(role.toLocaleLowerCase('es'), 'almacenero')
    assert.equal(attemptedExternal - before, 0)
    evidence.cases.next_external = {
      supplied: next, ...result, location_local: true, location_path: location.pathname,
      external_requests_blocked_during_submit: attemptedExternal - before, role,
    }
  } finally {
    await ctx.close()
  }
}

async function admin(browser, fixture, staff) {
  const ctx = await isolated(browser)
  try {
    const page = await ctx.newPage()
    const entry = await page.goto(base + '/admin/')
    const loginPath = new URL(page.url()).pathname
    assert.equal(loginPath, '/admin/login/')
    assert.equal(entry.status(), 200)
    const result = await submit(page, loginPath, '#login-form', fixture, '[name=username]')
    const sessionCookie = (await ctx.cookies(base)).some(cookie => cookie.name === 'audit01_sessionid')
    if (staff) {
      assert.deepEqual(result, { post: 302, document: 200, final: '/admin/' })
      assert.equal(sessionCookie, true)
      const heading = await page.locator('#content h1').innerText()
      await page.locator('#content').screenshot({ path: path.join(output, 'admin-staff.png') })
      evidence.cases.admin_staff = { entry: loginPath, ...result, sessionCookie, heading }
    } else {
      assert.deepEqual(result, { post: 200, document: 200, final: loginPath })
      assert.equal(sessionCookie, false)
      const note = page.locator('.errornote')
      const message = await note.innerText()
      assert.ok(message.trim())
      const passwordEmpty = !(await page.locator('#login-form input[type=password]').inputValue())
      assert.equal(passwordEmpty, true)
      await note.screenshot({ path: path.join(output, 'admin-rechazo.png') })
      evidence.cases.admin_nonstaff = { entry: loginPath, ...result, sessionCookie, message, passwordEmpty }
    }
  } finally {
    await ctx.close()
  }
}

async function runAudit() {
  fs.mkdirSync(output)
  proof()
  evidence.database = 'datos/etapa01-20261109/audit.sqlite3'
  evidence.loopback_proof_verified = true
  const before = businessCounts()
  assert.ok(Object.keys(before).length > 0 && Object.values(before).every(n => n === 0))
  const browser = await chromium.launch({ channel: 'chrome', headless: true })
  try {
    evidence.tool = 'Playwright Core / Google Chrome estable headless ' + browser.version() + ' / ' + os.type() + ' ' + os.release()
    step = 'keyboard_maxlength'
    await boundary(browser)
    step = 'next_missing'
    await missing(browser)
    step = 'next_external'
    await externalDestination(browser)
    step = 'admin_nonstaff'
    await admin(browser, 'almacen', false)
    step = 'admin_staff'
    await admin(browser, 'staff', true)
    assert.deepEqual(businessCounts(), before)
    evidence.commercial_counts_before_and_after = before
    evidence.status = 'completado'
  } finally {
    await browser.close()
  }
}

runAudit().catch(error => {
  // Los mensajes del driver pueden contener datos de un fill. No registrarlos.
  evidence.status = 'incompleto'
  evidence.stopped_at = step
  evidence.error_type = error.name
  if (error.code === 'ERR_ASSERTION') evidence.failing_check = error.stack.split('\n').find(line => line.includes(__filename))?.trim()
  process.exitCode = 1
}).finally(() => {
  fs.writeFileSync(path.join(output, 'observaciones.json'), JSON.stringify(evidence, null, 2) + '\n')
  console.log(JSON.stringify({ evidence: path.relative(results, output), status: evidence.status, stoppedAt: evidence.stopped_at }))
})
