"""Adapta soportes históricos a una corrida propia, sin editar producto ni soportes fuente."""
from pathlib import Path
import hashlib, json
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
SOURCE=ROOT/'auditoria_por_etapas/resultados/soporte'
target=HERE/'pg12'
target.mkdir(exist_ok=True)
source=SOURCE/'audit12_pg.py'
s=source.read_text(encoding='utf-8')
s=s.replace('ROOT = Path(__file__).resolve().parents[3]','ROOT = Path(__file__).resolve().parents[4]')
s=s.replace('RESULTS = ROOT / "auditoria_por_etapas/resultados"','RESULTS = Path(__file__).resolve().parent / "pg12"')
s=s.replace('pg_root = (Path(tempfile.gettempdir()) / f"audit12-pg-{secrets.token_hex(8)}").resolve()', 'pg_root = (RESULTS / f"audit12-pg-{secrets.token_hex(8)}").resolve()\n    assert pg_root.is_relative_to(RESULTS.resolve())')
s=s.replace('shutil.rmtree(pg_root, ignore_errors=True)', '# Clúster propio detenido conservado como evidencia; sin borrado recursivo.\n        report["cluster_retained"] = str(pg_root.relative_to(ROOT))')
s=s.replace('assert all(code == 302 for code, _ in results_t)', 'assert len(results_t) == 2 and not t1.is_alive() and not t2.is_alive(), "Both independent workers must finish"\n        assert all(code == 302 for code, _ in results_t)')
s=s.replace('sys.path.insert(0, str(APP))', 'sys.dont_write_bytecode = True\n        sys.path.insert(0, str(APP))')
(HERE/'audit12_pg.py').write_text(s,encoding='utf-8')
s=(SOURCE/'audit12_settings.py').read_text(encoding='utf-8').replace('RESULTS = Path(__file__).resolve().parents[1]', 'RESULTS = Path(__file__).resolve().parent / "pg12"')
(HERE/'audit12_settings.py').write_text(s,encoding='utf-8')
manifest={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [source,SOURCE/'audit12_settings.py']}
(target/'source-hashes.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
print('Copia aislada preparada; no usa HTTP por sockets: Django Client + PostgreSQL real')
