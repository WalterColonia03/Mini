"""Read-only code identity preflight on a NEW verified offline SQLite copy.
No Django setup, .env, migration, network, product mutation or inferred classification.
"""
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import shutil
import sqlite3
import unicodedata

ROOT = Path(__file__).resolve().parents[3]
RESULTS = ROOT / 'auditoria_por_etapas/resultados'
SOURCE = ROOT / 'r1-pmv/r1_pmv.sqlite3'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None


def normalized(value):
    return ''.join(unicodedata.normalize('NFKC', value or '').split()).casefold()


def check_digit_ok(value):
    if len(value) not in (12, 13, 14) or not re.fullmatch(r'[0-9]+', value):
        return False
    total = sum(int(ch) * (3 if i % 2 == 0 else 1) for i, ch in enumerate(reversed(value[:-1])))
    return (10 - total % 10) % 10 == int(value[-1])


def candidate_key(value):
    # A mathematical candidate only. Neither this function nor its caller assigns a GTIN type.
    return value.zfill(14) if check_digit_ok(value) else None


def classify(value):
    key = normalized(value)
    if not key:
        kind = 'empty'
    elif re.fullmatch(r'[0-9]+', key):
        kind = 'digits_' + str(len(key))
    else:
        kind = 'other_text'
    return {'kind': kind, 'normalized_length': len(key), 'leading_zero': key.startswith('0'),
            'checksum_12_13_14': check_digit_ok(key), 'all_zero': bool(key) and set(key)=={'0'},
            'current_format_valid': len((value or '').strip()) in range(1,65) and bool(re.fullmatch(r'[A-Za-z0-9\s\-]+',(value or '').strip())),
            'type_assigned': False}


def groups(rows, keyfn):
    found = defaultdict(list)
    for alias, raw, stored, active in rows:
        key = keyfn(raw)
        if key is not None:
            found[key].append(alias)
    return [{'group':f'G{i+1:03}', 'members':v} for i,v in enumerate(sorted(found.values())) if len(v)>1]


def synthetic_checks():
    tests=[]
    def case(name, actual, expected):
        tests.append({'id':name,'ok':actual==expected,'actual':actual,'expected':expected})
    a,b,c='012345678905','0012345678905','00012345678905'
    case('valid-upc12',check_digit_ok(a),True)
    case('valid-ean13',check_digit_ok(b),True)
    case('valid-gtin14-padded',check_digit_ok(c),True)
    case('same-mathematical-candidate',len({candidate_key(x) for x in (a,b,c)}),1)
    case('literal-policy-preserves-three',len({normalized(x) for x in (a,b,c)}),3)
    case('bad-checksum-rejected-as-candidate',candidate_key('0012345678906'),None)
    case('internal-numeric-cannot-be-assigned',classify(a)['type_assigned'],False)
    case('internal-text-preserved',normalized(' 00 CAT-03 '),'00cat-03')
    case('leading-zero-never-stripped',normalized(b),b)
    case('unicode-input-not-current-format',classify('００１２３４５６７８９０５')['current_format_valid'],False)
    case('ean8-not-treated-as-upc12',candidate_key('96385074'),None)
    case('all-zero-flag',classify('000000000000')['all_zero'],True)
    # A packaging indicator creates a distinct mathematical candidate, not an alias of a unit.
    payload='1001234567890'
    total=sum(int(ch)*(3 if i%2==0 else 1) for i,ch in enumerate(reversed(payload)))
    packaging=payload+str((10-total%10)%10)
    case('packaging-checksum',check_digit_ok(packaging),True)
    case('packaging-not-unit',candidate_key(packaging)==candidate_key(a),False)
    sample=[('P1',a,normalized(a),True),('P2',b,normalized(b),False),('P3','00 CAT-03','00cat-03',True)]
    case('candidate-group-includes-inactive',groups(sample,lambda raw:candidate_key(normalized(raw))),[{'group':'G001','members':['P1','P2']}])
    return tests


def main():
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    run=RESULTS/'datos'/('etapa03y-identity-'+stamp)
    out=RESULTS/'evidencias'/('03-Y-identity-'+stamp)
    protected=[*(ROOT/'r1-pmv').glob('*.sqlite3'),*(RESULTS/'datos').rglob('*.sqlite3'),ROOT/'PLANIFICACION_SCRUM_R1PMV.xlsx']
    hashes={str(p.relative_to(ROOT)):digest(p) for p in protected}
    def offline():
        if any(Path(str(SOURCE)+suffix).exists() for suffix in ('-wal','-shm','-journal')):
            raise RuntimeError('Source has SQLite sidecars; obtain a consistent offline backup first.')
    offline()
    run.mkdir();out.mkdir()
    (run/'marker.json').write_text(json.dumps({'run':run.name,'purpose':'read-only identity preflight'}),encoding='utf-8')
    (out/'inventory-before.json').write_text(json.dumps({'id':'AUD03Y-PREFLIGHT-IDENTIDAD01','criteria':['PROD01/CA02','PROD02/CA03','PROD03/CA02'],
        'proposals':['DEC-03X-IDENTIDAD','PROP-03X-CA01','PROP-03X-CA02','PROP-03X-T01'],
        'actions':['copy offline source','classify syntactic candidates','report collision groups'],
        'not_executed':['migration','relabel data','merge UUID','application browser','phone'],
        'input_fields':['barcode','barcode_normalized','is_active'], 'output':'counts and pseudonymous groups only'},indent=2),encoding='utf-8')
    copy=run/'audit.sqlite3'
    report={'started_utc':stamp,'scope':'identity analysis only; no policy applied','source':str(SOURCE.relative_to(ROOT)),
            'copy':str(copy.relative_to(ROOT)),'source_sha256':hashes[str(SOURCE.relative_to(ROOT))]}
    try:
        shutil.copyfile(SOURCE,copy);offline()
        assert digest(SOURCE)==report['source_sha256']==digest(copy), 'Unstable source copy'
        copy_before=digest(copy)
        # mode=ro and query_only reinforce the analysis-only contract, even for the private copy.
        with sqlite3.connect(copy.resolve().as_uri()+'?mode=ro',uri=True) as db:
            db.execute('PRAGMA query_only=ON')
            report['integrity']=db.execute('PRAGMA integrity_check').fetchone()[0]
            report['foreign_key_violation_count']=len(db.execute('PRAGMA foreign_key_check').fetchall())
            raw=list(db.execute('SELECT barcode,barcode_normalized,is_active FROM catalog_product ORDER BY id'))
            rows=[(f'P{i+1:03}',*row) for i,row in enumerate(raw)]
            report['products']=len(rows)
            report['profiles']=[{'row':alias,'active':bool(active),**classify(code),'stored_key_matches':stored==normalized(code)} for alias,code,stored,active in rows]
            report['class_counts']=dict(Counter(p['kind'] for p in report['profiles']))
            report['current_normalized_collision_groups']=groups(rows,normalized)
            report['hypothetical_gtin14_groups']=groups(rows,lambda raw:candidate_key(normalized(raw)))
            report['strip_all_zeros_groups_unsafe']=groups(rows,lambda raw:normalized(raw).lstrip('0'))
            report['confirmed_gtin_count']=None
            report['historical_category_migrations']=list(db.execute("SELECT name FROM django_migrations WHERE app='catalog' ORDER BY name"))
        report['copy_unchanged']=digest(copy)==copy_before
        report['synthetic_tests']=synthetic_checks()
        assert report['integrity']=='ok' and not report['foreign_key_violation_count'] and report['copy_unchanged']
        assert all(t['ok'] for t in report['synthetic_tests'])
    except Exception as exc:
        # No row data or connection strings in errors.
        report['error_type']=type(exc).__name__
    finally:
        report['protected_unchanged']={str(p.relative_to(ROOT)):digest(p)==hashes[str(p.relative_to(ROOT))] for p in protected}
        report['protected_absent_at_start']=[k for k,v in hashes.items() if v is None]
        report['finished_utc']=datetime.now(timezone.utc).isoformat()
        (out/'result.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'evidence':str(out.relative_to(ROOT)),'products':report.get('products'),'classes':report.get('class_counts'),
        'candidate_groups':report.get('hypothetical_gtin14_groups'),'tests':len(report.get('synthetic_tests',[])),
        'error':report.get('error_type'),'copy_unchanged':report.get('copy_unchanged'),'protected_unchanged':all(report['protected_unchanged'].values())},ensure_ascii=False))
    if report.get('error_type') or not all(report['protected_unchanged'].values()): raise SystemExit(1)

if __name__=='__main__':main()
