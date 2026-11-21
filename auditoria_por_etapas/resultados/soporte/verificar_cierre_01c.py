"""Cierre operativo 01-C. Lee los archivos de auditoría y escribe solo un JSON nuevo."""

import argparse
from contextlib import closing
from datetime import datetime
import errno
import hashlib
import json
from pathlib import Path
import re
import socket
import sqlite3
import subprocess
from urllib.parse import unquote
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[3]
RESULT = ROOT / "auditoria_por_etapas/resultados"
DATA = RESULT / "datos/etapa01-20261109"
EVIDENCE = RESULT / "evidencias"
REPORTS = [RESULT / "ETAPA-01.md", RESULT / "ESTADO_GENERAL.md"]
APPLICATION = ROOT / "r1-pmv"
PROTECTED = [APPLICATION / "r1_pmv.sqlite3", RESULT / "datos/etapa00-20261105/audit.sqlite3"]
COMMERCIAL_APPS = {"catalog", "inventory", "cash", "sales"}
TEXT_FORMATS = {".md", ".json", ".txt", ".diff", ".py", ".js", ".cjs", ".mjs", ".ps1"}


def sha256(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def artifact_01c(path):
    if not path.is_relative_to(EVIDENCE):
        return False
    name = path.relative_to(EVIDENCE).parts[0].lower()
    return name.startswith(("01-c-", "01-chrome-b02-", "01-chrome-admin-failures-", "01-retencion-"))


def check_databases(record):
    prepared = json.loads((DATA / "prepared.json").read_text(encoding="utf-8"))
    baseline = {Path(key).as_posix(): value for key, value in prepared["baseline"].items()}
    for path in PROTECTED:
        name = path.relative_to(ROOT).as_posix()
        actual = sha256(path)
        record("sha256:" + name, actual == baseline.get(name), actual)
    db = (DATA / "audit.sqlite3").resolve()
    if Path(prepared["database"]).resolve() != db:
        record("base de etapa 01 identificada", False)
        return
    with closing(sqlite3.connect(db.as_uri() + "?mode=ro", uri=True)) as conn:
        conn.execute("PRAGMA query_only = ON")
        conn.execute("BEGIN")
        counts = conn.execute("""
            SELECT count(*),
                   count(CASE WHEN display_name GLOB 'AUD01 *' AND email LIKE '%@example.invalid' THEN 1 END),
                   count(CASE WHEN display_name GLOB 'AUD01HTTP *' AND email LIKE '%@example.invalid' THEN 1 END)
              FROM identity_account
        """).fetchone()
        identity = dict(zip(("total", "AUD01", "AUD01HTTP"), counts))
        identity["filas_de_intentos"] = conn.execute("SELECT count(*) FROM identity_loginattempt").fetchone()[0]
        identity["sesiones_almacenadas"] = conn.execute("SELECT count(*) FROM django_session").fetchone()[0]
        record("cuentas ficticias", counts == (15, 5, 10), identity)
        tables = [name for name, in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
                  if name.partition("_")[0] in COMMERCIAL_APPS]
        sums = {app: 0 for app in COMMERCIAL_APPS}
        for name in tables:
            identifier = '"' + name.replace('"', '""') + '"'
            sums[name.partition("_")[0]] += conn.execute("SELECT count(*) FROM " + identifier).fetchone()[0]
        found_apps = {name.partition("_")[0] for name in tables}
        record("tablas comerciales sin filas", found_apps == COMMERCIAL_APPS and not any(sums.values()),
               {"tablas": len(tables), "filas_por_app": sums})


def check_shutdown(record):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.settimeout(3)
        status = probe.connect_ex(("127.0.0.1", 8766))
    record("loopback rechaza conexión a 8766", status == errno.ECONNREFUSED, status)
    # PowerShell returns aggregates only. Do not put other processes' commands in stdout or the report.
    command = r"""
    $ErrorActionPreference = 'Stop'
    $ports = [System.Net.NetworkInformation.IPGlobalProperties]::GetIPGlobalProperties().GetActiveTcpListeners()
    $python = @(Get-CimInstance Win32_Process -Filter "Name LIKE 'python%.exe' OR Name='py.exe'")
    $workers = @($python | Where-Object { $_.CommandLine -match '(?:^|[\\/"\s])audit01\.py"?\s+"?serve"?(?:\s|$)' })
    [PSCustomObject]@{port=@($ports | Where-Object Port -eq 8766).Count; workers=$workers.Count;
      unknown=@($python | Where-Object { -not $_.CommandLine }).Count} | ConvertTo-Json -Compress
    """
    result = subprocess.run(["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", command],
                            capture_output=True, timeout=30, check=True)
    observed = json.loads(result.stdout)
    record("sin listener TCP 8766 IPv4/IPv6", observed["port"] == 0, observed["port"])
    record("sin proceso Python audit01.py serve", observed["workers"] == observed["unknown"] == 0,
           {"coincidencias": observed["workers"], "procesos_python_sin_linea_visible": observed["unknown"]})


def check_publication(record, target, cursor):
    suite = json.loads((EVIDENCE / "01-C-regresion-identity-20261109.json").read_text(encoding="utf-8"))
    previous = json.loads((EVIDENCE / "01-http-202611091226025a110c.json").read_text(encoding="utf-8"))
    for label, expected in (("suite 01-C", suite["sha256_modulos"]), ("HTTP 01-B", previous["source_hashes"])):
        different = [name for name, digest in expected.items() if sha256(APPLICATION / name) != digest]
        record("fuentes cotejadas con manifiesto de " + label, not different,
               {"archivos": len(expected), "diferencias": different})
    referenced = set()
    documents = {doc: doc.read_text(encoding="utf-8") for doc in REPORTS}
    for doc, content in documents.items():
        missing = []
        refs_01c = []
        for ref in re.findall(r"\]\((<[^>]+>|[^)]+)\)", content):
            ref = unquote(ref.strip("<>").split("#", 1)[0])
            if not ref or re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:", ref):
                continue
            path = (doc.parent / ref).resolve()
            if path == target:
                continue  # Created exclusively after this report has been assembled.
            if not path.is_relative_to(ROOT) or not path.exists():
                missing.append(ref)
            elif artifact_01c(path):
                refs_01c.append(path.relative_to(RESULT).as_posix())
                referenced.add(path)
        record("enlaces locales:" + doc.name, not missing, missing)
        record("referencia a evidencia 01-C:" + doc.name, bool(refs_01c), sorted(set(refs_01c)))
        if cursor:
            if doc.name == "ESTADO_GENERAL.md":
                scope = next((line for line in content.splitlines() if re.match(r"^\|\s*01\b", line)), "")
            else:
                scope = "\n".join(line for line in content.splitlines()[:12] if "cursor" in line.lower())
            record("cursor declarado:" + doc.name, cursor in scope, cursor)

    files = {p for p in EVIDENCE.rglob("*") if p.is_file() and artifact_01c(p)}
    # Include runs that were interrupted, new closure reports and scripts directly linked by either report.
    scripts = {Path(__file__).resolve(), *RESULT.glob("soporte/*01c*"), *RESULT.glob("soporte/audit01_*.cjs")}
    for doc, content in documents.items():
        for ref in re.findall(r"\]\((soporte/[^)]+)\)", content):
            script = (doc.parent / ref.split("#", 1)[0]).resolve()
            if script.is_file() and script.is_relative_to(RESULT / "soporte"):
                scripts.add(script)
    inputs = [p for p in (set(documents) | scripts | files) if p.is_file() and p.suffix.lower() in TEXT_FORMATS]
    known = [(DATA / ".django-key").read_text(encoding="utf-8").strip()]
    fixtures = json.loads((DATA / ".credentials.json").read_text(encoding="utf-8"))
    known.extend(fixture[key] for fixture in fixtures.values() for key in ("email", "password"))
    affected = []
    for path in sorted(inputs):
        text = path.read_text(encoding="utf-8-sig")
        if any(value and value in text for value in known):
            affected.append(path.relative_to(RESULT).as_posix())
    record("barrido de credenciales conocidas en texto", not affected and len(fixtures) == 5,
           {"archivos": len(inputs), "archivos_con_coincidencias": affected,
            "alcance": "Correos y claves literales de los cinco fixtures persistentes y llave Django de ETAPA-01. "
                       "Excluye binarios y claves efímeras de las dos corridas HTTP."})
    manifests = {}
    for path in sorted(files):
        if path.suffix.lower() == ".json":
            data = json.loads(path.read_text(encoding="utf-8-sig"))
            for item in data.get("capturas", []):
                capture = (path.parent / item["archivo"]).resolve()
                ok = (capture.is_relative_to(path.parent) and capture.is_file()
                      and sha256(capture) == item["sha256"])
                record("integridad de captura:" + path.parent.name + "/" + capture.name, ok)
        if path in referenced or path.parent in referenced:
            manifests[path.relative_to(RESULT).as_posix()] = sha256(path)
    return {"informes": {p.name: sha256(p) for p in REPORTS}, "evidencias_enlazadas": manifests}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cursor", help="ID del próximo caso que debe constar en la cabecera y en la fila de 01")
    parser.add_argument("--archivo", help="Nombre fechado del JSON nuevo, p. ej. 01-C-cierre-20261109.json")
    args = parser.parse_args()
    now = datetime.now(ZoneInfo("America/Lima"))
    name = args.archivo or now.strftime("01-C-cierre-%Y%m%d-%H%M%S-%f.json")
    if not re.fullmatch(r"01-C-cierre-[0-9]{8}(?:-[\w-]+)?\.json", name):
        parser.error("Nombre de cierre no válido")
    out = EVIDENCE / name
    if out.exists():
        parser.error("El destino ya existe. Utilice un nombre nuevo.")
    rows = []

    def record(case, passed, detail=None):
        rows.append({"caso": case, "resultado": "CUMPLE" if passed else "INCUMPLE", "detalle": detail})

    hashes = {}
    for label, check in (("bases", lambda: check_databases(record)), ("cierre de procesos", lambda: check_shutdown(record)),
                         ("publicación", lambda: check_publication(record, out, args.cursor))):
        try:
            result = check()
            if result:
                hashes.update(result)
        except (OSError, ValueError, KeyError, sqlite3.Error, subprocess.SubprocessError) as exc:
            rows.append({"caso": label, "resultado": "NO VERIFICADO", "tipo": type(exc).__name__})
    passed = sum(row["resultado"] == "CUMPLE" for row in rows)
    payload = {"fecha_lima": now.isoformat(), "alcance": "Cierre operativo y documental de 01-C",
               "comprobaciones": rows, "comprobaciones_cumplidas": passed, "total": len(rows), "sha256": hashes}
    with out.open("x", encoding="utf-8") as file:
        json.dump(payload, file, ensure_ascii=False, indent=2)
        file.write("\n")
    print(json.dumps({"archivo": out.relative_to(ROOT).as_posix(), "cumplidas": passed, "total": len(rows),
                      "revisar": [row["caso"] for row in rows if row["resultado"] != "CUMPLE"]}, ensure_ascii=False))
    return int(passed != len(rows))


if __name__ == "__main__":
    raise SystemExit(main())
