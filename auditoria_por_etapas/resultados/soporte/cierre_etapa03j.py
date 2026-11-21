"""Coteja el corte 03-J. --write crea el manifiesto una sola vez."""
import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import re

RESULTS = Path(__file__).resolve().parents[1]
ROOT = RESULTS.parent.parent
E = RESULTS / 'evidencias'
INVENTORY = E / '03-J-inventario-20261110T171113912354Z.json'
TESTS = E / '03-J-tests-20261110T172054000837Z'
BROWSER = E / '03-J-browser-20261110T172105045406Z'
RACE = E / '03-J-sqlite-race-20261110T172006895618Z/result.json'
PG = E / '03-J-postgresql-20261110T172019957099Z.json'
OUTPUT = E / '03-J-cierre.json'
RECORDED_RUNS = [TESTS, BROWSER, RACE.parent,
                 E / '03-J-tests-20261110T171321742969Z', E / '03-J-tests-20261110T171341873895Z',
                 E / '03-J-browser-20261110T171546908471Z', E / '03-J-sqlite-race-20261110T171905215655Z']


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def verify(write):
    before = read(INVENTORY)
    tests, web, server, sqlite, pg = [read(p) for p in (TESTS / 'result.json', BROWSER / 'browser.json', BROWSER / 'result.json', RACE, PG)]
    initial, final = [read(BROWSER / p) for p in ('orm-initial.json', 'orm-final.json')]
    prior = read(E / '03-I-cierre.json')
    criteria = prior['criteria']
    matrix = RESULTS / 'anexos/ETAPA-03-inventario.md'
    rows = [line.split('|')[4].strip().split(' muestra')[0].split(' tras')[0]
            for line in matrix.read_text(encoding='utf-8').splitlines() if re.match(r'\| (?:CAT|PROD)\d+/CA\d+ ·', line)]
    docs = [matrix, RESULTS / 'ETAPA-03.md', RESULTS / 'ESTADO_GENERAL.md', RESULTS / 'anexos/ETAPA-03-J-estado-categoria.md']
    changed = {ROOT / p for p, h in before['source_hashes'].items() if digest(ROOT / p) != h}
    additions = [ROOT / 'r1-pmv/catalog' / name for name in ['migrations/0006_category_state_version.py',
        'test_audit03_category_confirmation.py', 'templates/catalog/category_state_confirm.html']]
    links = set()
    for doc in docs + [p for p in changed if p.suffix == '.md']:
        for link in re.findall(r'\]\(([^)]+)\)', doc.read_text(encoding='utf-8')):
            if '://' not in link and not link.startswith('#'):
                links.add((doc.parent / link.split('#')[0]).resolve())
    missing = [str(p) for p in links if not p.is_file() and not (write and p == OUTPUT)]
    artifacts = [p for run in RECORDED_RUNS for p in run.iterdir() if p.is_file()] + [INVENTORY, PG]
    retained = RESULTS / 'datos' / server['run'] / 'audit.sqlite3'
    sources = [*changed, *additions, *docs, *(RESULTS/'soporte').glob('audit03j*.*'), Path(__file__).resolve()]
    manifest = {str(p.relative_to(ROOT).as_posix()): digest(p) for p in sorted(set(sources + artifacts + [retained]))}
    protected = {p: digest(ROOT / p) == h for p, h in before['protected_hashes'].items()}
    complete_runs = [read(run / 'result.json') for run in RECORDED_RUNS if (run / 'result.json').is_file()] + [pg]
    checks = {
        'catalog': tests['methods'] == 98 and tests['failures'] == 0,
        'browser': len(web['cases']) == len({c['id'] for c in web['cases']}) == 32 and all(c['ok'] for c in web['cases']) and not web['errors'] and server['browser_exit'] == 0,
        'races': len(sqlite['cases']) == 3 and len(pg['cases']) == 4 and all(c['ok'] for c in sqlite['cases'] + pg['cases']),
        'migration_and_conflicts': pg['cases'][0]['id'] == 'PG-J0-migration-0006' and all(sorted(x['status'] for x in c['responses']) == [302, 409] for c in sqlite['cases'] + pg['cases'][1:]),
        'servers_closed': pg['port_closed'] and all(d['port_closed'] for d in complete_runs if d.get('action') == 'browser'),
        'original_and_prior': all(protected.values()) and all(all(d['protected_unchanged'].values()) for d in complete_runs),
        'business_state': initial.keys() == final.keys() and all(initial[k] == final[k] for k in initial if k != 'category_versions') and [v['state_version'] for v in final['category_versions']] == [2],
        'coverage': len(criteria) == len({c['id'] for c in criteria}) == len(rows) == 27 and Counter(rows) == prior['counts'] == {'CUMPLE': 21, 'PREVISTO/FUTURO': 6},
        'links': not missing,
    }
    if OUTPUT.exists():
        checks['saved_hashes_match'] = manifest == read(OUTPUT)['files_sha256']
    print(json.dumps({'checks': checks, 'missing': missing}, ensure_ascii=False))
    if not all(checks.values()):
        raise SystemExit(1)
    if write:
        report = {'authority': before['authority'], 'checks': checks, 'files_sha256': manifest,
                  'protected_unchanged': protected, 'criteria': criteria, 'counts': prior['counts'],
                  'supplementary': {f'J-CA{i}': 'CUMPLE en la muestra' for i in range(1, 5)},
                  'initial_sqlite_attempt': 'Error interno observado en consola. Intento inicial sin result.json.',
                  'cursor': '03-K / HU-PROD-03 CA01 / PROP-03G-SCAN-T01. Prueba física en alta aislada.'}
        with OUTPUT.open('x', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
            f.write('\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true')
    verify(parser.parse_args().write)
