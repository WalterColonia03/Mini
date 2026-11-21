"""Regresión secuencial 01-D, incluidos dos casos de credenciales preexistentes."""
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime
import hashlib
import io
import json
import os
from pathlib import Path
import sys
import time
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[3]
RESULT = ROOT / 'auditoria_por_etapas/resultados'
sys.path[:0] = [str(Path(__file__).parent), str(ROOT / 'r1-pmv')]
os.environ['DJANGO_SETTINGS_MODULE'] = 'audit01_settings'
from django.conf import settings
assert Path(settings.DATABASES['default']['NAME']).resolve() == (RESULT / 'datos/etapa01-20261109/audit.sqlite3').resolve()
settings.DATABASES['default']['NAME'] = ':memory:'
settings.DATABASES['default']['TEST']['NAME'] = ':memory:'
settings.SESSION_COOKIE_NAME = 'sessionid'
settings.CSRF_COOKIE_NAME = 'csrftoken'
from django.db.backends.signals import connection_created

def verify_memory(sender, connection, **kwargs):
    with connection.cursor() as cursor:
        cursor.execute('PRAGMA database_list')
        assert all(not row[2] for row in cursor.fetchall())

connection_created.connect(verify_memory, weak=False)
import django
django.setup()
from django.test.runner import DiscoverRunner

old = json.loads((RESULT / 'evidencias/01-C-regresion-identity-20261109.json').read_text(encoding='utf-8'))
labels = list(old['resultados']) + [
    'identity.test_auth_audit01.LoginAudit01Tests.test_unusable_password_follows_uniform_five_failure_lockout',
    'identity.test_auth_audit01.LoginAudit01Tests.test_legacy_pbkdf2_account_accepts_normalized_login_after_failure',
]
now = datetime.now(ZoneInfo('America/Lima'))
started = time.monotonic()
stream = io.StringIO()

class AuditRunner(DiscoverRunner):
    def run_suite(self, suite, **kwargs):
        result = super().run_suite(suite, **kwargs)
        self.audit_result = result
        return result

runner = AuditRunner(verbosity=2, interactive=False)
with redirect_stderr(stream), redirect_stdout(stream):
    failures = runner.run_tests(labels)
result = runner.audit_result
payload = {
    'fecha_lima': now.isoformat(), 'duracion_s': round(time.monotonic() - started, 3),
    'motor': 'SQLite en memoria, ruta verificada en cada conexión', 'django': django.get_version(),
    'metodos': labels, 'ejecutados': result.testsRun, 'fallos': len(result.failures),
    'errores': len(result.errors), 'omitidos': len(result.skipped), 'exit_code': failures,
    'ids_con_incidencia': [test.id() for test, _ in result.failures + result.errors],
    'fuentes_sha256': {name: hashlib.sha256((ROOT / 'r1-pmv' / name).read_bytes()).hexdigest()
                       for name in ['identity/test_auth_audit01.py', 'identity/tests.py',
                                    'identity/views.py', 'identity/services.py', 'identity/models.py', 'identity/forms.py']},
    'reproduccion': './r1-pmv/.venv/Scripts/python.exe -B ./auditoria_por_etapas/resultados/soporte/regresion_final_01d.py',
}
path = RESULT / 'evidencias' / now.strftime('01-D-regresion-%Y%m%d-%H%M%S.json')
with path.open('x', encoding='utf-8') as file:
    json.dump(payload, file, ensure_ascii=False, indent=2)
print(json.dumps({'evidencia': str(path.relative_to(ROOT)), 'ejecutados': result.testsRun,
                  'fallos': payload['fallos'], 'errores': payload['errores'], 'omitidos': payload['omitidos']}))
raise SystemExit(failures)
