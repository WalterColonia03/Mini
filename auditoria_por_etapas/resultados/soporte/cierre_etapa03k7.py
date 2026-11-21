"""03-K7 closure: hashes of changed files, evidence presence, protected files, open ports. Read-only."""
import hashlib, json, socket
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
RES = ROOT / 'auditoria_por_etapas/resultados'
EVID = RES / 'evidencias'
h = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
changed = ['r1-pmv/catalog/services.py', 'r1-pmv/catalog/forms.py', 'r1-pmv/catalog/views.py',
           'r1-pmv/catalog/templates/catalog/product_edit.html', 'r1-pmv/catalog/test_audit03_stale_edit.py',
           'r1-pmv/catalog/test_audit03_edit.py', 'r1-pmv/catalog/tests.py',
           'auditoria_por_etapas/resultados/soporte/audit03k_run.py', 'auditoria_por_etapas/resultados/soporte/audit03k_settings.py',
           'auditoria_por_etapas/resultados/soporte/audit03k7_races.py', 'auditoria_por_etapas/resultados/soporte/audit03k7_pg.py',
           'auditoria_por_etapas/resultados/soporte/audit03k7_keyboard.cjs']
evidence = {
    'keyboard_pre_fix_codex': '03-K-keyboard-20261110T183956099863Z',
    'tests_first_stale_8_with_1_fail': '03-K-tests-20261110T184821961380Z',
    'tests_stale_8_ok': '03-K-tests-20261110T184947335287Z',
    'sqlite_race_ok_1': '03-K-sqlite-race-20261110T184949253446Z',
    'sqlite_race_baseline_read_then_write_counter_test': '03-K-sqlite-race-20261110T185008205808Z',
    'suite_318_harness_cookie_error': '03-K-tests-20261111T010526631267Z',
    'suite_318_ok': '03-K-tests-20261111T010655936590Z',
    'keyboard_post_fix_32_ok': '03-K-keyboard-20261111T010725864129Z',
    'postgresql_2_ok': '03-K7-postgresql-20261111T010817323136Z.json',
    'sqlite_race_final_ok': '03-K-sqlite-race-20261111T010846464247Z',
}
protected = [*(ROOT / 'r1-pmv').glob('*.sqlite3'), *(RES / 'datos').rglob('*.sqlite3')]
report = {
    'stage': '03-K7', 'generated_utc': datetime.now(timezone.utc).isoformat(),
    'changed_files_sha256': {p: h(ROOT / p) for p in changed},
    'evidence_present': {k: (EVID / v).exists() for k, v in evidence.items()},
    'evidence': evidence,
    'xlsx_present': (ROOT / 'PLANIFICACION_SCRUM_R1PMV.xlsx').exists(),
    'xlsx_last_confirmed_present_utc': '2026-11-10T18:50:10Z (03-K-sqlite-race-20261110T185008205808Z, hash unchanged within that run)',
    'protected_sqlite_count': len(protected),
    'original_db_sha256': h(ROOT / 'r1-pmv/r1_pmv.sqlite3'),
    'next': '03-K8',
}
report['note'] = 'Servers of each run report port_closed in their own result.json; this script does not start services.'
out = EVID / '03-K7-cierre.json'
out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({k: report[k] for k in ('evidence_present', 'xlsx_present', 'protected_sqlite_count')}, ensure_ascii=False))
