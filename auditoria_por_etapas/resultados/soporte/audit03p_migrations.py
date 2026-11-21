"""Rehearse catalog migrations on a NEW offline copy. Never configure source DB.

Only schema names, counts and hashes leave the copy; no business row is logged.
Refuses WAL/journal or an unstable source. Does not start a web server.
"""
from collections import Counter
from datetime import datetime, timezone
import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import secrets
import shutil
import sqlite3
import sys
import unicodedata

SUPPORT = Path(__file__).resolve().parent
RESULTS = SUPPORT.parent
ROOT = RESULTS.parent.parent
APP = ROOT / 'r1-pmv'
sys.path[:0] = [str(APP), str(SUPPORT)]

def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def db_state(connection, columns=None):
    tables = [r[0] for r in connection.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")]
    result = {}
    for table in tables:
        if table == 'django_migrations':
            continue
        cols = columns[table]['columns'] if columns else [r[1] for r in connection.execute(f'PRAGMA table_info("{table}")')]
        if not columns and table == 'catalog_category':
            cols = [c for c in cols if c not in ('name_normalized', 'state_version')]
        if not columns and table == 'catalog_product':
            cols = [c for c in cols if c != 'search_name']
        quoted = ','.join('"'+c+'"' for c in cols)
        encoded = sorted(json.dumps(row, default=str, ensure_ascii=False) for row in connection.execute(f'SELECT {quoted} FROM "{table}"'))
        result[table] = {'columns': cols, 'rows': len(encoded), 'sha256': hashlib.sha256('\n'.join(encoded).encode()).hexdigest()}
    return result

def main():
    source = APP / 'r1_pmv.sqlite3'
    for suffix in ('-wal', '-shm', '-journal'):
        if Path(str(source)+suffix).exists():
            raise RuntimeError('Source has SQLite sidecars; obtain a consistent offline backup first.')
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    run = RESULTS / 'datos' / ('etapa03k-migrations-'+stamp)
    out = RESULTS / 'evidencias' / ('03-P-migrations-'+stamp)
    protected = [*APP.glob('*.sqlite3'), *(RESULTS/'datos').rglob('*.sqlite3')]
    before_hashes = {str(p.relative_to(ROOT)): digest(p) for p in protected}
    run.mkdir(); out.mkdir()
    (run/'marker.json').write_text(json.dumps({'run': run.name}), encoding='utf-8')
    (run/'.django-key').write_text(secrets.token_urlsafe(48), encoding='utf-8')
    copy = run/'audit.sqlite3'
    shutil.copyfile(source, copy)
    if digest(source) != before_hashes[str(source.relative_to(ROOT))] or digest(copy) != digest(source):
        raise RuntimeError('Source changed during copy; copied database not used.')
    report = {'started_utc': stamp, 'source': str(source.relative_to(ROOT)), 'copy': str(copy.relative_to(ROOT)),
              'scope': 'catalog only, offline SQLite copy, no production deployment', 'source_sha256': digest(source)}
    with sqlite3.connect(copy) as db:
        report['integrity_before'] = db.execute('PRAGMA integrity_check').fetchone()[0]
        before = db_state(db)
        categories = list(db.execute('SELECT name FROM catalog_category'))
        products = list(db.execute('SELECT name, minimum_stock FROM catalog_product'))
        cat_keys = [' '.join(r[0].split()).casefold() for r in categories]
        prod_keys = [unicodedata.normalize('NFC', ' '.join(r[0].split()).casefold()) for r in products]
        report['preflight'] = {
            'categories': len(categories), 'products': len(products),
            'category_collision_groups': sum(v > 1 for v in Counter(cat_keys).values()),
            'category_invalid_keys': sum(not k or len(k)>120 for k in cat_keys),
            'product_collision_groups': sum(v > 1 for v in Counter(prod_keys).values()),
            'product_empty_keys': sum(not k for k in prod_keys),
            'invalid_minima': sum(r[1] is None or not 0 <= r[1] <= 999999 for r in products),
        }
    os.environ.update(AUDIT03_RUN_DIR=str(run), DJANGO_SETTINGS_MODULE='audit03k_settings')
    import django
    django.setup()
    from django.db import connection
    from django.db.migrations.executor import MigrationExecutor
    from django.core.management import call_command
    executor = MigrationExecutor(connection)
    targets = [('catalog', '0006_category_state_version')]
    plan = executor.migration_plan(targets)
    report['plan'] = [{'app': m.app_label, 'name': m.name, 'backwards': backwards} for m, backwards in plan]
    if any(m.app_label != 'catalog' or backwards for m, backwards in plan):
        raise RuntimeError('Non-catalog or reverse migration plan refused.')
    try:
        executor.migrate(targets)
        report['migration'] = 'applied' if plan else 'already-current'
        log = io.StringIO()
        with contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
            call_command('check')
            call_command('makemigrations', 'catalog', check=True, dry_run=True)
        (out/'checks.txt').write_text(log.getvalue(), encoding='utf-8')
        report['django_checks'] = 'passed'
    except Exception as error:
        report['migration'] = 'blocked'
        report['error_type'] = type(error).__name__  # Do not log names/UUIDs from data preflight.
    finally:
        connection.close()
    with sqlite3.connect(copy) as db:
        report['integrity_after'] = db.execute('PRAGMA integrity_check').fetchone()[0]
        report['foreign_key_violations'] = len(list(db.execute('PRAGMA foreign_key_check')))
        after = db_state(db, before)
        report['preserved_tables'] = {table: before[table] == after[table] for table in before}
        report['business_before'] = before
        report['business_after'] = after
        report['catalog_migrations_after'] = [r[0] for r in db.execute("SELECT name FROM django_migrations WHERE app='catalog' ORDER BY name")]
    report['protected_unchanged'] = {str(p.relative_to(ROOT)): digest(p)==before_hashes[str(p.relative_to(ROOT))] for p in protected}
    report['finished_utc'] = datetime.now(timezone.utc).isoformat()
    (out/'result.json').write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
    print(json.dumps({'evidence': str(out.relative_to(ROOT)), 'migration': report['migration'], 'plan': report['plan'],
                     'preflight': report['preflight'], 'business_preserved': all(report['preserved_tables'].values()),
                     'protected_unchanged': all(report['protected_unchanged'].values())}, ensure_ascii=False))
    if report['migration']=='blocked' or not all(report['preserved_tables'].values()) or not all(report['protected_unchanged'].values()):
        raise SystemExit(1)

if __name__ == '__main__':
    main()
