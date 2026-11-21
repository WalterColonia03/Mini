"""Verifica el cierre de auditoría01 y el traspaso a02. Sólo lectura y un JSON nuevo."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import socket
import tempfile
from datetime import datetime
from zoneinfo import ZoneInfo

from verificar_cierre_01c import check_databases, check_shutdown

ROOT = Path(__file__).resolve().parents[3]
RESULT = ROOT / 'auditoria_por_etapas/resultados'
EVIDENCE = RESULT / 'evidencias'
DATA = RESULT / 'datos/etapa01-20261109'
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--archivo', default='01-D-cierre-final-20261109.json')
args = parser.parse_args()
assert re.fullmatch(r'01-D-cierre-[\w-]+\.json', args.archivo), 'Nombre de evidencia inválido'
OUTPUT = EVIDENCE / args.archivo
assert not OUTPUT.exists(), 'El cierre ya existe. Conservar el corte previo.'
rows = []
def record(case, passed, detail=None):
    rows.append({'caso': case, 'cumple': bool(passed), 'detalle': detail})

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

check_databases(record)
check_shutdown(record)
suite_path = EVIDENCE / '01-D-regresion-20261109-170211.json'
pg_path = EVIDENCE / '01-D-postgresql-20261109T220349Z.json'
unicode_path = EVIDENCE / '01-D-unicode-2026-11-09T21-59-32-996Z/observaciones.json'
suite = json.loads(suite_path.read_text(encoding='utf-8'))
pg = json.loads(pg_path.read_text(encoding='utf-8'))
unicode = json.loads(unicode_path.read_text(encoding='utf-8'))
for name, manifest in [('regresion20', suite), ('postgres4', pg)]:
    different = [n for n,h in manifest['fuentes_sha256'].items() if sha(ROOT/'r1-pmv'/n) != h]
    record('fuentes actuales de ' + name, not different, different)
record('resultado de regresión final', suite['ejecutados'] == 20 and
       suite['fallos'] == suite['errores'] == suite['omitidos'] == suite['exit_code'] == 0)
record('resultado PostgreSQL', len(pg['escenarios']) == 4 and
       all(s.get('resultado') == 'PASS' for s in pg['escenarios']))
record('limpieza PostgreSQL documentada', pg['limpieza'] == {'puerto_cerrado': True, 'carpeta_propia_eliminada': True})
with socket.socket() as probe:
    probe.settimeout(3)
    code = probe.connect_ex(('127.0.0.1', pg['puerto_loopback']))
record('puerto de clúster efímero cerrado', code == 10061, code)
left = list(Path(tempfile.gettempdir()).glob('audit01-pg-*'))
record('sin carpetas temporales de ensayo PG', not left, [p.name for p in left])
record('cuatro casos Unicode terminados', len(unicode['casos']) == 4 and unicode['resultado'].startswith('CUMPLE'))
for case in unicode['casos']:
    if 'captura' in case:
        image = unicode_path.parent / case['captura']
        record('captura Unicode ' + case['captura'], image.is_file() and sha(image) == case['sha256'])

reports = [RESULT/'ETAPA-01.md', RESULT/'ESTADO_GENERAL.md', RESULT/'anexos/ETAPA-01-cierre-y-traspaso.md']
docs = {p: p.read_text(encoding='utf-8') for p in reports}
for path, content in docs.items():
    missing = []
    for ref in re.findall(r'\]\(([^)]+)\)', content):
        if ref.startswith(('https:', 'http:', '#')):
            continue
        target = (path.parent/ref.split('#')[0]).resolve()
        if target != OUTPUT and not target.exists():
            missing.append(ref)
    record('enlaces ' + path.name, not missing, missing)
record('cierre y cursor etapa02 en informes', all('HU-AUTH-03' in docs[p] for p in reports)
       and all('AUDITORÍA' in docs[p] and 'HALLAZGOS ABIERTOS' in docs[p] for p in reports[:2]))
state = docs[reports[1]]
row02 = next(line for line in state.splitlines() if line.startswith('| 02 '))
record('etapa02 aún no ejecutada', 'NO EJECUTADO' in row02 and 'sin borrador' in row02)
for name in ['09_Product_Backlog.md','03_Matriz_de_Trazabilidad_y_Pruebas.md','21_Alcance_Actual_y_Diferencias.md']:
    file = ROOT/name
    docs[file] = file.read_text(encoding='utf-8')
    record('complemento fechado ' + name, 'Complemento de auditoría · 09/11/2026' in docs[file])

# Confirm that the preexisting 34 audit methods were preserved before the two appended cases.
tests = ROOT/'r1-pmv/identity/test_auth_audit01.py'
old = json.loads((EVIDENCE/'01-auth-tests-20261109-122521-777224.json').read_text(encoding='utf-8'))
original = old['source_sha256']['r1-pmv/identity/test_auth_audit01.py']
prefix = tests.read_bytes().split(b'    def test_unusable_password_follows_uniform_five_failure_lockout')[0]
variants = [prefix.rstrip(b'\r\n') + tail for tail in [b'', b'\n', b'\n\n', b'\n\n\n', b'\r\n', b'\r\n\r\n']]
record('métodos preexistentes preservados', any(hashlib.sha256(v).hexdigest() == original for v in variants),
       'Comparación del contenido previo, permitiendo la línea vacía final que ahora separa los métodos añadidos.')

fixtures = json.loads((DATA/'.credentials.json').read_text(encoding='utf-8'))
known = [(DATA/'.django-key').read_text(encoding='utf-8').strip()]
known += [f['password'] for f in fixtures.values()]
files = list(docs) + list(EVIDENCE.glob('01-D-*.json'))
files += list((EVIDENCE/unicode_path.parent.name).glob('*.json'))
files += [p for p in (RESULT/'soporte').glob('*01d.py')]
files += [RESULT/'soporte/audit01_campos_unicode.cjs']
leaked = [str(p.relative_to(ROOT)) for p in files if any(s and s in p.read_text(encoding='utf-8') for s in known)]
record('secretos conocidos en entregables nuevos', not leaked, {'archivos': len(files), 'coincidencias': leaked})
payload = {'fecha_lima': datetime.now(ZoneInfo('America/Lima')).isoformat(), 'alcance': 'Cierre operativo/documental de auditoría01',
           'comprobaciones': rows, 'cumplidas': sum(r['cumple'] for r in rows), 'total': len(rows),
           'sha256': {str(p.relative_to(ROOT)): sha(p) for p in [*docs, suite_path, pg_path, unicode_path, tests]},
           'limite': 'Estas comprobaciones operativas conservan los hallazgos abiertos y los estados funcionales del informe.'}
with OUTPUT.open('x', encoding='utf-8') as file:
    json.dump(payload, file, indent=2, ensure_ascii=False)
print(json.dumps({'evidencia': str(OUTPUT.relative_to(ROOT)), 'cumplidas': payload['cumplidas'], 'total': len(rows),
                  'revisar': [r['caso'] for r in rows if not r['cumple']]}, ensure_ascii=False))
raise SystemExit(int(payload['cumplidas'] != len(rows)))
