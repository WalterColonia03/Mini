"""Check prior stage-01 evidence without changing or rerunning historical data."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[3]
RESULTS = ROOT / "auditoria_por_etapas/resultados"
OLD = RESULTS / "evidencias/01-H-20261115"
OUT = RESULTS / "evidencias/01-I-20261115"
prior = OUT / "documentos-antes/auditoria_por_etapas__resultados__ETAPA-01.md"


def load(name):
    return json.loads((OLD / name).read_text(encoding="utf-8"))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


text = prior.read_text(encoding="utf-8")
links, missing = 0, []
for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", text):
    raw = target.strip().split("#", 1)[0]
    if not raw or re.match(r"^(?:https?:|mailto:)", raw):
        continue
    links += 1
    if not (RESULTS / unquote(raw)).exists():
        missing.append(raw)

browser = load("chrome-manifest.json")
roles = load("chrome-roles.json")
cross = load("chrome-efecto-entre-roles.json")
wait = load("espera-real-01h.json")
end = load("despues-espera.json")
pg = load("postgresql-01h-20261115T150253Z.json")
build = load("build-ultimo.json")
base = load("base-principal-observacion.json")
test_log = (OLD / "tests-identity-final.txt").read_text(encoding="utf-8")
initial = json.loads((OUT / "build-antes.json").read_text(encoding="utf-8"))
result = {
    "auditoria_examinada_sha256": digest(prior),
    "enlaces_locales_a_archivo": links,
    "enlaces_a_archivo_faltantes": sorted(set(missing)),
    "navegador_01h": {"principal": len(browser["checks"]), "roles": len(roles["checks"]), "efecto_entre_roles": len(cross["checks"]), "espera": len(wait["checks"])},
    "comprobaciones_navegador_sin_fallos": all(c.get("ok") for v in (browser, roles, cross, wait) for c in v["checks"]),
    "suite_83_confirmada": "Ran 83 tests" in test_log and bool(re.search(r"(?m)^OK\s*$", test_log)),
    "pg_cinco_escenarios_y_bypass_historico": len(pg["escenarios"]) == 5 and any(item.get("escenario") == "admin-bypass-concurrente" and item.get("resultado") == "PASS" for item in pg["escenarios"]),
    "espera_segundos_pared": wait["checks"][-1].get("elapsed_since_fifth_event_seconds"),
    "espera_segundos_monotonicos_finales": wait.get("wait_monotonic_seconds"),
    "contador_y_plazo_reiniciados": end["fallos"] == 0 and end["locked_until_utc"] is None,
    "build_previo_coincide_con_inicio_01i": build["build_sha256"] == initial["build_sha256"],
    "huella_bd_principal_observada_01h_y_01i": base["sha256"] == initial["documentos_y_bases"]["r1-pmv/r1_pmv.sqlite3"],
    "limitaciones": "Rutas de archivo verificadas, no contenido completo de todos los anexos ni destinos externos; la ejecución anterior conserva su propio build.",
}
path = OUT / "revision-evidencia-anterior.json"
path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(result, ensure_ascii=False))
