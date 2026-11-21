"""Add 01-H evidence to already accepted cases; do not accept new policy."""
from __future__ import annotations

import hashlib
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "08_Historias_de_Usuario.md"
BACKUP = ROOT / "auditoria_por_etapas/resultados/evidencias/01-H-20261115/documentos-antes/08_Historias_de_Usuario.md"

if hashlib.sha256(SOURCE.read_bytes()).digest() != hashlib.sha256(BACKUP.read_bytes()).digest():
    raise SystemExit("08 cambió desde el respaldo: no se sobrescribe")

cases = {
    "CP-HU-AUTH-01-001": (
        "VERIFICADO EN MUESTRA 01-H (15/11/2026), tres roles, correo normalizado y sesión tras recarga; sin aprobar los módulos de destino. Se conserva 01-E.",
        "01-H añade [tres roles en Chrome](auditoria_por_etapas/resultados/evidencias/01-H-20261115/chrome-roles.json) y [suite focal](auditoria_por_etapas/resultados/evidencias/01-H-20261115/tests-identity-final.txt), con build y límites en [ETAPA-01](auditoria_por_etapas/resultados/ETAPA-01.md#vigente-01-h).",
    ),
    "CP-HU-AUTH-01-002": (
        "VERIFICADO EN MUESTRA 01-H (15/11/2026), mensajes y casos seleccionados; no certifica ausencia de canales temporales. Se conserva 01-F.",
        "01-H añade [Chrome: credencial errónea/inexistente/inactiva](auditoria_por_etapas/resultados/evidencias/01-H-20261115/chrome-roles.json), [HTTP: CSRF, fronteras y destino](auditoria_por_etapas/resultados/evidencias/01-H-20261115/http-probes.json) y [suite focal](auditoria_por_etapas/resultados/evidencias/01-H-20261115/tests-identity-final.txt). La prueba de cookies pasó con nombres predeterminados y configurados tras una corrección de prueba, sin modificar el ingreso; ver [diff](auditoria_por_etapas/resultados/evidencias/01-H-20261115/identity-tests-cambio-01h.diff).",
    ),
    "CP-HU-AUTH-01-003": (
        "EJECUTADO PARCIAL en 01-H (15/11/2026): puertas identity y muestra de rutas, no RN-29 global ni datos comerciales preexistentes. Se conserva 01-E.",
        "01-H añade [Chrome: visitante y tres roles ante empleados](auditoria_por_etapas/resultados/evidencias/01-H-20261115/chrome-roles.json) y [suite focal](auditoria_por_etapas/resultados/evidencias/01-H-20261115/tests-identity-final.txt); la base de negocio de esta muestra está vacía.",
    ),
    "CP-HU-AUTH-02-001": (
        "VERIFICADO EN MUESTRA 01-H (15/11/2026), bloqueo entre contextos, reloj controlado y concurrencia PostgreSQL 18.4; la espera real de 15 minutos sigue heredada de 01-C.",
        "01-H añade [quinto fallo y otro contexto Chrome](auditoria_por_etapas/resultados/evidencias/01-H-20261115/chrome-roles.json), [límites de reloj controlado](auditoria_por_etapas/resultados/evidencias/01-H-20261115/tests-identity-final.txt) y [cinco escenarios PostgreSQL 18.4](auditoria_por_etapas/resultados/evidencias/01-H-20261115/postgresql-01h-latest.json); la ruta administrativa sigue eludiendo este bloqueo.",
    ),
    "CP-DOC-01-06-001": (
        "EJECUTADO PARCIAL EN MUESTRA 01-H (15/11/2026): C-01 INCUMPLE en aplicación, C-02 PARCIAL, C-03 CUMPLE en sonda; perímetro real, tráfico y retención siguen abiertos. Se conservan 01-F y 02-E.",
        "01-H añade [Chrome, incluido bypass](auditoria_por_etapas/resultados/evidencias/01-H-20261115/chrome-manifest.json), [sondas de seguridad](auditoria_por_etapas/resultados/evidencias/01-H-20261115/security-probes.json), [superficies de despliegue y retención](auditoria_por_etapas/resultados/evidencias/01-H-20261115/contract-probes.json) y [privacidad agregada](auditoria_por_etapas/resultados/evidencias/01-H-20261115/privacidad-agregada.json).",
    ),
}

source = SOURCE.read_text(encoding="utf-8")
for case, (state, extra) in cases.items():
    marker = f"##### {case} ·"
    if source.count(marker) != 1:
        raise SystemExit(f"Caso ausente o duplicado: {case}")
    start = source.index(marker)
    end_match = re.search(r"(?m)^##### CP-|^### HU-|^## ", source[start + len(marker):])
    end = start + len(marker) + end_match.start() if end_match else len(source)
    section = source[start:end]
    section, count = re.subn(r"(?m)^(\*\*Cubre:\*\* .+?\. \*\*Estado:\*\*) .+$", lambda m: m.group(1) + " " + state, section, count=1)
    if count != 1:
        raise SystemExit(f"Estado no reconocido: {case}")
    section, count = re.subn(r"(?m)^(\*\*Evidencia de ejecución:\*\* .+)$", lambda m: m.group(1) + " " + extra, section, count=1)
    if count != 1:
        raise SystemExit(f"Evidencia no reconocida: {case}")
    source = source[:start] + section + source[end:]

SOURCE.write_text(source, encoding="utf-8", newline="\r\n")
print("Actualizados estados y evidencia de", len(cases), "casos aceptados; sin cambiar criterios ni crear HU")
