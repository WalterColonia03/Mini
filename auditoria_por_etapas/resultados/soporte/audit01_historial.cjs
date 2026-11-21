// E01-B-01 / NFR-06/07. Ejecutar contra audit01.py serve con la base preparada.
const { spawnSync } = require('node:child_process')
const { createHash, createHmac, randomBytes } = require('node:crypto')
const fs = require('node:fs')
const os = require('node:os')
const path = require('node:path')
const { DatabaseSync } = require('node:sqlite')
const assert = require('node:assert/strict')

const result = path.resolve(__dirname, '..')
const project = path.resolve(result, '../..')
const data = path.join(result, 'datos/etapa01-20261109')
const base = 'http://127.0.0.1:8766'
const pw = process.env.AUDIT01_PLAYWRIGHT || path.join(os.homedir(),
  '.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright-core')
const chrome = process.env.AUDIT01_CHROME || 'C:/Program Files/Google/Chrome/Application/chrome.exe'
const viewport = { width: 1366, height: 768 }
const id = new Date().toISOString().replace(/[:.]/g, '-')
const dir = path.join(result, 'evidencias', '01-C-historial-' + id)
const report = { inicioUtc: new Date().toISOString(), hito: 'E01-B-01', viewport, resultados: [], capturas: [] }
const hash = value => createHash('sha256').update(value).digest('hex')
const rel = file => path.relative(result, file).replaceAll('\\', '/')

function check(caso, cumple, observado) {
  report.resultados.push({ caso, cumple: Boolean(cumple), observado })
}

function readState(db, fixture, attemptKey) {
  const row = db.prepare('SELECT failures, locked_until FROM identity_loginattempt WHERE identifier = ?').get(attemptKey)
  const account = db.prepare('SELECT last_login FROM identity_account WHERE email_normalized = ?').get(fixture.email)
  assert.ok(account)
  return { fallos: row?.failures || 0, bloqueo: row?.locked_until || null, ultimoIngreso: account.last_login }
}

async function dom(page) {
  return page.evaluate(() => {
    const email = document.querySelector('[name=email]')
    const pass = document.querySelector('[type=password]')
    const active = document.activeElement
    const rect = active.getBoundingClientRect()
    const style = getComputedStyle(active)
    const button = document.querySelector('button[type=submit]')
    const hit = el => {
      const r = el.getBoundingClientRect()
      const x = (r.left + r.right) / 2
      const y = (r.top + r.bottom) / 2
      return x >= 0 && x < innerWidth && y >= 0 && y < innerHeight && el.contains(document.elementFromPoint(x, y))
    }
    return {
      ruta: location.pathname, hash: location.hash, titulo: document.title,
      foco: active.id || active.className || active.tagName, visible: rect.bottom > 0 && rect.top < innerHeight,
      indicador: { outline: style.outlineStyle, ancho: style.outlineWidth, sombra: style.boxShadow },
      correoVacio: email ? email.value.length === 0 : null,
      claveVacia: pass ? pass.value.length === 0 : null,
      alerta: document.querySelector('[data-testid=login-error]')?.innerText.trim() || null,
      ancho: innerWidth, alto: innerHeight, desbordeHorizontal: document.documentElement.scrollWidth > innerWidth,
      centrosOperables: email && pass && button ? [email, pass, button].map(hit) : null,
      tipoNavegacion: performance.getEntriesByType('navigation')[0]?.type || null,
    }
  })
}

async function capture(page, name) {
  // Las imágenes de campos nunca contienen texto introducido, ni siquiera identificadores ficticios.
  const mask = page.locator('input[type=email]:not(:placeholder-shown),input[type=password]:not(:placeholder-shown)')
  const file = path.join(dir, name + '.png')
  await page.screenshot({ path: file, mask: [mask], animations: 'disabled' })
  report.capturas.push({ archivo: path.basename(file), sha256: hash(fs.readFileSync(file)) })
}

async function run() {
  const proof = spawnSync(path.join(project, 'r1-pmv/.venv/Scripts/python.exe'),
    [path.join(__dirname, 'audit01.py'), 'proof'], { encoding: 'utf8' })
  assert.equal(proof.status, 0, 'No se pudo autenticar el servidor de etapa 01')
  const prepared = JSON.parse(fs.readFileSync(path.join(data, 'prepared.json')))
  assert.equal(path.resolve(prepared.database), path.join(data, 'audit.sqlite3'))
  function protectedHashes() {
    return Object.fromEntries(Object.keys(prepared.baseline).map(key => [key, hash(fs.readFileSync(path.join(project, key)))]))
  }
  assert.deepEqual(protectedHashes(), prepared.baseline)
  fs.mkdirSync(dir)
  const db = new DatabaseSync(prepared.database, { readOnly: true })
  const fixtures = JSON.parse(fs.readFileSync(path.join(data, '.credentials.json')))
  const secret = fs.readFileSync(path.join(data, '.django-key'), 'utf8').trim()
  const derived = createHash('sha256').update('identity.login.throttle' + secret).digest()
  const state = role => readState(db, fixtures[role], createHmac('sha256', derived).update(fixtures[role].email).digest('hex'))
  const counts = () => Object.fromEntries(['identity_account', 'catalog_product', 'inventory_lot', 'cash_cashshift', 'sales_sale']
    .map(table => [table, db.prepare('SELECT count(*) AS n FROM ' + table).get().n]))
  const initial = counts()
  let browser
  try {
    browser = await require(pw).chromium.launch({ executablePath: chrome, headless: true,
      ignoreDefaultArgs: ['--disable-back-forward-cache'] })
    report.herramientas = { chrome: browser.version(), playwright: require(path.join(pw, 'package.json')).version,
      node: process.version, windows: os.release(), headless: true, cacheRedSinIntercepcion: true }
    report.fuentes = Object.fromEntries(['identity/views.py', 'identity/services.py', 'identity/forms.py', 'identity/models.py',
      'identity/templates/identity/login.html', 'identity/templates/identity/base.html', 'identity/static/identity/app.css']
      .map(key => [key, hash(fs.readFileSync(path.join(project, 'r1-pmv', key)))]))
    const ctx = await browser.newContext({ viewport, locale: 'es-PE', timezoneId: 'America/Lima' })
    const page = await ctx.newPage()
    const events = []
    page.on('response', r => {
      if (r.request().resourceType() === 'document') events.push({
        metodo: r.request().method(), ruta: new URL(r.url()).pathname, status: r.status(),
        cacheControl: r.headers()['cache-control'] || null,
      })
    })
    const before = state('admin')
    assert.ok(!before.bloqueo && before.fallos < 4, 'El fixture admin requiere otra sesión de prueba')
    const get = await page.goto(base + '/')
    const first = await dom(page)
    check('GET / fresco', get.status() === 200 && first.foco === 'id_email' && first.correoVacio && first.claveVacia &&
      first.ancho === 1366 && first.alto === 768 && !first.desbordeHorizontal && first.centrosOperables.every(Boolean) &&
      get.headers()['cache-control']?.includes('no-store'), first)
    await capture(page, '01-ingreso')
    await page.locator('[name=email]').fill(fixtures.admin.email)
    await page.locator('[name=password]').fill(randomBytes(25).toString('hex'))
    const [post] = await Promise.all([page.waitForNavigation(), page.locator('button[type=submit]').click()])
    const rejection = await dom(page)
    const afterError = state('admin')
    const cookies = await ctx.cookies(base)
    const noSessionCookie = !cookies.some(cookie => cookie.name === 'audit01_sessionid')
    check('POST / rechazo', post.status() === 200 && post.request().method() === 'POST' && rejection.claveVacia &&
      !rejection.correoVacio && rejection.alerta === 'Correo o contraseña incorrectos' &&
      post.headers()['cache-control']?.includes('no-store') && afterError.fallos === before.fallos + 1 &&
      before.ultimoIngreso === afterError.ultimoIngreso && noSessionCookie,
      { dom: rejection, antes: before, despues: afterError, sinCookieSesion: noSessionCookie })
    await capture(page, '02-rechazo')
    for (const action of ['atras', 'recarga']) {
      const start = events.length
      const response = action === 'atras' ? await page.goBack() : await page.reload()
      const observation = await dom(page)
      const after = state('admin')
      const requests = events.slice(start)
      const mismoCorreo = await page.locator('[name=email]').inputValue() === fixtures.admin.email
      check(action + ' desde flujo de rechazo', observation.ruta === '/' && observation.claveVacia === true &&
        observation.alerta === null && after.fallos === afterError.fallos && after.ultimoIngreso === before.ultimoIngreso &&
        !requests.some(e => e.metodo === 'POST'),
        { dom: observation, correoCoincideConElEnviado: mismoCorreo, status: response?.status() ?? null, red: requests, despues: after })
      await capture(page, action === 'atras' ? '03-atras' : '04-recarga')
    }
    report.intercambiosHistorial = events.slice()
    const verify = await ctx.newPage()
    await verify.goto(base + '/inicio/')
    const hit = new URL(verify.url())
    check('Destino privado tras recarga', hit.origin === base && hit.pathname === '/' &&
      hit.searchParams.get('next') === '/inicio/' && await verify.locator('[name=email]').isVisible(),
      { ruta: hit.pathname, siguiente: hit.searchParams.get('next') })
    await verify.close()

    const keys = await browser.newContext({ viewport, locale: 'es-PE' })
    const keyboard = await keys.newPage()
    await keyboard.goto(base + '/')
    const focus = []
    for (const key of ['Shift+Tab', 'Shift+Tab', 'Enter', 'Tab', 'Tab', 'Tab']) {
      await keyboard.keyboard.press(key)
      await keyboard.evaluate(async () => {
        await new Promise(requestAnimationFrame)
        await Promise.all(document.activeElement.getAnimations().map(animation => animation.finished))
      })
      const s = await dom(keyboard)
      focus.push({ tecla: key, foco: s.foco, visible: s.visible, indicador: s.indicador })
      if (focus.length === 2) await capture(keyboard, '05-salto')
    }
    const ids = focus.map(s => s.foco)
    check('Orden de teclado y salto', ids[0] === 'brand' && ids[1] === 'skip-link' && ids[2] === 'contenido' &&
      ids[3] === 'id_email' && ids[4] === 'id_password' && ids[5].includes('button-primary') &&
      focus.every(s => s.visible), focus)
    const [empty] = await Promise.all([keyboard.waitForNavigation(), keyboard.keyboard.press('Enter')])
    const fields = await keyboard.locator('input[required]').evaluateAll(nodes => nodes.map(node => ({
      id: node.id, etiqueta: node.labels[0]?.textContent, invalido: node.getAttribute('aria-invalid'),
      errores: (node.getAttribute('aria-describedby') || '').split(/\s+/).map(id => document.getElementById(id)?.textContent || null),
    })))
    const stateAfterEmpty = state('admin')
    check('Errores asociados al enviar vacíos desde teclado', empty.status() === 200 && fields.length === 2 &&
      fields.every(f => f.etiqueta && f.invalido === 'true' && f.errores.every(Boolean)),
      { campos: fields, dom: await dom(keyboard), contadorFixture: stateAfterEmpty })
    await capture(keyboard, '06-errores-campos')
    await keys.close()

    for (const [role, label] of [['admin', 'Administrador'], ['almacen', 'Almacenero']]) {
      // El administrador corrige sus credenciales en la misma pestaña tras atrás y recarga.
      const session = role === 'admin' ? ctx : await browser.newContext({ viewport, locale: 'es-PE' })
      const view = role === 'admin' ? page : await session.newPage()
      if (role !== 'admin') await view.goto(base + '/')
      const old = state(role)
      await view.getByLabel('Correo de trabajo').fill('  ' + fixtures[role].email.toUpperCase() + '  ')
      await view.getByLabel('Contraseña', { exact: true }).fill(fixtures[role].password)
      const [response] = await Promise.all([view.waitForNavigation(), view.getByRole('button', { name: 'Iniciar sesión' }).click()])
      const pill = await view.locator('.role-pill').innerText()
      const hasPrivateLink = await view.locator('.sidebar-nav a[href="/empleados/"]').count() === 1
      const refreshed = await view.reload()
      const now = state(role)
      check('Ingreso y recarga de ' + label, response.status() === 200 && new URL(view.url()).pathname === '/inicio/' &&
        refreshed.status() === 200 && pill === label && await view.locator('.role-pill').innerText() === label &&
        hasPrivateLink === (role === 'admin') && now.ultimoIngreso !== old.ultimoIngreso && now.fallos === 0 && !now.bloqueo,
        { rolVisible: pill, enlaceEmpleados: hasPrivateLink, ruta: new URL(view.url()).pathname,
          antes: old, despues: now, recargaHTTP: refreshed.status() })
      await capture(view, '07-' + role)
      if (role === 'admin') {
        const start = events.length
        await view.goBack()
        const back = await dom(view)
        const unchanged = state(role)
        check('Atrás con sesión después de corregir credenciales', back.ruta === '/inicio/' &&
          back.claveVacia === null && unchanged.ultimoIngreso === now.ultimoIngreso && unchanged.fallos === 0,
          { ruta: back.ruta, titulo: back.titulo, tieneCampoClave: back.claveVacia !== null, red: events.slice(start), despues: unchanged })
      }
      const employees = role === 'admin' ? (await Promise.all([view.waitForNavigation(),
        view.locator('.sidebar-nav a[href="/empleados/"]').click()]))[0] : await view.goto(base + '/empleados/')
      check('Puerta de Empleados, ' + label, employees.status() === (role === 'admin' ? 200 : 403),
        { metodo: role === 'admin' ? 'menú' : 'URL directa', status: employees.status() })
      await session.close()
    }
    report.recorridoCompleto = true
  } finally {
    if (browser) await browser.close()
    report.finUtc = new Date().toISOString()
    const final = counts()
    check('Personas y muestra comercial', JSON.stringify(initial) === JSON.stringify(final), { inicial: initial, final })
    const hashes = protectedHashes()
    check('Bases protegidas', Object.keys(hashes).every(key => hashes[key] === prepared.baseline[key]), hashes)
    db.close()
    fs.writeFileSync(path.join(dir, 'resultados.json'), JSON.stringify(report, null, 2) + '\n', { flag: 'wx' })
    console.log(rel(dir), report.resultados.filter(x => x.cumple).length, '/', report.resultados.length)
  }
  if (report.resultados.some(x => !x.cumple)) process.exitCode = 1
}

run().catch(error => {
  // Un error del driver puede incluir valores introducidos. Informar únicamente la clase y la línea propia.
  console.error(error.name, error.stack?.split('\n').find(line => line.includes('audit01_historial.cjs:')) || '')
  process.exitCode = 1
})
