// Repetir desde la raíz, con el servidor aislado de audit01.py en 8766:
// node auditoria_por_etapas/resultados/soporte/espera_real_01c.cjs
// Reserva exclusiva del fixture vendedor durante 16 minutos. Sin preparar datos ni cambiar relojes.
const fs = require('node:fs');
const path = require('node:path');
const { homedir } = require('node:os');
const { randomUUID } = require('node:crypto');
const { spawnSync } = require('node:child_process');
const { setTimeout: delay } = require('node:timers/promises');
const assert = require('node:assert/strict');

const projectRoot = path.resolve(__dirname, '../../..');
const python = path.join(projectRoot, 'r1-pmv/.venv/Scripts/python.exe');
const data = path.join(__dirname, '../datos/etapa01-20261109');
const base = 'http://127.0.0.1:8766';
const runtime = path.join(homedir(), '.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright-core');
const { chromium } = require(runtime);
const output = path.join(__dirname, '../evidencias', '01-C-espera-' + new Date().toISOString().replace(/[-:.]/g, '') + '.json');
const evidence = { inicio_utc: new Date().toISOString(), base: 'SQLite de etapa01-20261109',
  caso: 'AUTH-02 CA01–03 / RN-17 con reloj real y fixture VENDEDOR', eventos: [] };
const initialTick = performance.now();
const monotonic = () => Math.round(performance.now() - initialTick);
const wrong = randomUUID();
const expectedMessage = n => n === 0 ? 'Correo o contraseña incorrectos' :
  'Demasiados intentos fallidos consecutivos. Inténtelo nuevamente en ' + n + ' minuto(s).';

function verifyServer() {
  const res = spawnSync(python, [path.join(__dirname, 'audit01.py'), 'proof'], { encoding: 'utf8', windowsHide: true });
  assert.equal(res.status, 0, 'Falló la identificación de la instancia sin credenciales.');
}

// Lee exclusivamente la cuenta del fixture y su fila. La cookie permanece en stdin.
const observePython = `import json, os, sys
from pathlib import Path
root, support = Path.cwd(), Path.cwd() / "auditoria_por_etapas/resultados/soporte"
sys.path[:0] = [str(support), str(root / "r1-pmv")]
os.environ["DJANGO_SETTINGS_MODULE"] = "audit01_settings"
from django.conf import settings
db = settings.DATABASES["default"]
data = support.parent / "datos/etapa01-20261109"
assert Path(db["NAME"]).resolve() == (data / "audit.sqlite3").resolve()
db["NAME"] = (data / "audit.sqlite3").resolve().as_uri() + "?mode=ro"
db["OPTIONS"] = {"uri": True}
import django
django.setup()
from django.utils.crypto import salted_hmac
from django.contrib.sessions.models import Session
from django.utils.timezone import now
from identity.models import Account, LoginAttempt
form = json.loads((data / ".credentials.json").read_text(encoding="utf-8"))["vendedor"]
account = Account.objects.get(email_normalized=Account.normalize_email(form["email"]))
assert account.role.code == "VENDEDOR" and account.is_active and not account.is_staff
attempt = LoginAttempt.objects.filter(pk=salted_hmac("identity.login.throttle", account.email_normalized, algorithm="sha256").hexdigest()).first()
value = json.load(sys.stdin)
session = Session.objects.filter(pk=value, expire_date__gt=now()).first() if value else None
identity = session.get_decoded() if session else {}
print(json.dumps({"observado_utc": now().isoformat(), "rol_bd": account.role.code,
   "sesion_del_vendedor": identity.get("_auth_user_id") == str(account.pk) and identity.get("role_code") == "VENDEDOR",
   "last_login": account.last_login.isoformat() if account.last_login else None,
   "fallos": attempt.failures if attempt else 0, "locked_until": attempt.locked_until.isoformat() if attempt and attempt.locked_until else None}))
`;

async function observe(context) {
  const cookie = context && (await context.cookies(base)).find(c => c.name === 'audit01_sessionid');
  // Python ejecuta el programa desde -c para que stdin transporte únicamente la cookie.
  const result = spawnSync(python, ['-c', observePython], { cwd: projectRoot, input: JSON.stringify(cookie?.value || ''),
    windowsHide: true, encoding: 'utf8' });
  assert.equal(result.status, 0, 'No se pudo comprobar la BD en modo lectura.');
  return JSON.parse(result.stdout);
}

async function run() {
  verifyServer();
  const fixture = JSON.parse(fs.readFileSync(path.join(data, '.credentials.json'), 'utf8')).vendedor;
  let phase = 'entorno';
  let browser;
  try {
    browser = await chromium.launch({ channel: 'chrome', headless: true });
    evidence.navegador = 'Google Chrome ' + browser.version() + ' headless / 1366×768';
    evidence.inicial = await observe(null);
    assert.ok(!evidence.inicial.locked_until || Date.parse(evidence.inicial.locked_until) <= Date.now(), 'Fixture con bloqueo vigente.');
    async function freshPage() {
      const context = await browser.newContext({ viewport: { width: 1366, height: 768 }, locale: 'es-PE' });
      await context.route('**/*', route => new URL(route.request().url()).origin === base ? route.continue() : route.abort());
      const page = await context.newPage();
      await page.goto(base, { waitUntil: 'domcontentloaded' });
      return page;
    }
    async function submit(page, name, password, options = {}) {
      phase = name;
      await page.locator('input[name=email]').fill(options.upper ? '  ' + fixture.email.toUpperCase() + '  ' : fixture.email);
      await page.locator('input[name=password]').fill(password);
      const sent = monotonic();
      const [post] = await Promise.all([
        page.waitForResponse(r => r.url() === base + '/' && r.request().method() === 'POST'),
        page.locator('button[type=submit]').click(),
      ]);
      await page.waitForLoadState('domcontentloaded');
      const received = monotonic();
      const state = await observe(page.context());
      const event = { caso: name, envio_ms: sent, respuesta_ms: received, http_post: post.status(),
        http_date: (await post.allHeaders()).date, ruta_final: new URL(page.url()).pathname, bd: state };
      evidence.eventos.push(event);
      if (options.success) {
        assert.equal(event.ruta_final, '/inicio/');
        assert.equal(state.sesion_del_vendedor, true);
        assert.equal(state.fallos, 0);
        assert.equal(state.locked_until, null);
        event.menu_visible = [];
        for (const label of ['Apertura de caja', 'Preparar venta', 'Cerrar turno']) {
          assert.ok(await page.getByRole('link', { name: label, exact: false }).first().isVisible());
          event.menu_visible.push(label);
        }
      } else {
        const alert = page.getByTestId('login-error');
        event.mensaje = (await alert.innerText()).trim();
        assert.equal(event.mensaje, expectedMessage(options.minutes));
        assert.equal(state.sesion_del_vendedor, false);
        assert.equal(state.fallos, options.failures);
        assert.equal(event.ruta_final, '/');
        assert.equal(await page.locator('input[name=password]').inputValue(), '');
        if (options.minutes === 0) assert.equal(state.locked_until, null);
      }
      return event;
    }
    const first = await freshPage();
    const initialSuccess = await submit(first, 'Éxito normalizado antes de la serie', fixture.password, { upper: true, success: true });
    assert.ok(!evidence.inicial.last_login || Date.parse(initialSuccess.bd.last_login) > Date.parse(evidence.inicial.last_login));
    await first.context().close();
    const errors = await freshPage();
    let fifth;
    for (let i = 1; i <= 5; i++) {
      fifth = await submit(errors, 'Clave errónea ' + i, wrong, { failures: i, minutes: i === 5 ? 15 : 0 });
      assert.equal(fifth.bd.last_login, initialSuccess.bd.last_login);
    }
    assert.ok(fifth.bd.locked_until);
    const unlock = Date.parse(fifth.bd.locked_until);
    const started = unlock - 900000;
    assert.ok(started <= Date.parse(fifth.bd.observado_utc) && Date.parse(fifth.bd.observado_utc) - started < 10000);
    await errors.context().close();
    const other = await freshPage();
    async function stillLocked(name, minutes) {
      verifyServer();
      const e = await submit(other, name, fixture.password, { upper: true, failures: 5, minutes });
      assert.equal(e.bd.locked_until, fifth.bd.locked_until);
      assert.equal(e.bd.last_login, initialSuccess.bd.last_login);
    }
    await stillLocked('Otra sesión, clave correcta al comenzar', 15);
    console.log('ESPERA INICIADA: vencimiento UTC ' + fifth.bd.locked_until);
    for (const [remaining, minutes] of [[100, 2], [45, 1]]) {
      await delay(Math.max(0, unlock - remaining * 1000 - Date.now()));
      await stillLocked('Otra sesión, faltan ' + minutes + ' minuto(s) mostrados', minutes);
    }
    await delay(Math.max(0, unlock + 1500 - Date.now()));
    verifyServer();
    const final = await submit(other, 'Éxito tras vencimiento real', fixture.password, { success: true });
    assert.ok(Date.parse(final.bd.last_login) > unlock);
    evidence.desde_quinto_hasta_exito_monotonico_ms = final.envio_ms - fifth.envio_ms;
    assert.ok(evidence.desde_quinto_hasta_exito_monotonico_ms >= 900000);
    evidence.resultado = 'CUMPLE en esta ejecución';
  } catch (error) {
    evidence.resultado = 'INCOMPLETO';
    evidence.ultima_fase = phase;
    evidence.tipo_error = error.name;
    // Las trazas crudas del navegador y los datos del formulario nunca se archivan.
    if (error.code === 'ERR_ASSERTION') evidence.linea = error.stack.match(/espera_real_01c\.cjs:(\d+)/)?.[1];
    process.exitCode = 1;
  } finally {
    await browser?.close();
    evidence.fin_utc = new Date().toISOString();
    fs.writeFileSync(output, JSON.stringify(evidence, null, 2) + '\n', { flag: 'wx' });
    console.log(evidence.resultado, path.basename(output), evidence.ultima_fase || '', evidence.linea || '');
  }
}
run().catch(() => { console.error('Preparación fallida. Verificar proof y fixture aislada.'); process.exitCode = 1; });
