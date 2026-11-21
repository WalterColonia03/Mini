"""Integrate the authorized, verified 01-I corrections in the source plan."""
from __future__ import annotations

import hashlib
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "08_Historias_de_Usuario.md"
BACKUP = ROOT / "auditoria_por_etapas/resultados/evidencias/01-I-20261115/documentos-antes/08_Historias_de_Usuario.md"
if hashlib.sha256(SOURCE.read_bytes()).digest() != hashlib.sha256(BACKUP.read_bytes()).digest():
    raise SystemExit("08 cambió desde la línea base: no se sobrescribe")

cases = {
    "CP-HU-AUTH-01-001": (
        "VERIFICADO EN MUESTRA 01-I (15/11/2026), tres roles y sesión persistida; sin aprobar operaciones de los módulos de destino.",
        "01-I revalida [tres roles en Chrome](auditoria_por_etapas/resultados/evidencias/01-I-20261115/chrome-roles-final.json), [657 pruebas integradas](auditoria_por_etapas/resultados/evidencias/01-I-20261115/regresion-integrada-final.txt) y [foco/errores](auditoria_por_etapas/resultados/evidencias/01-I-20261115/foco-y-errores-final.json). El contenido comercial de los destinos conserva sus propias etapas.",
    ),
    "CP-HU-AUTH-01-002": (
        "VERIFICADO EN MUESTRA 01-I (15/11/2026), mensajes uniformes y casos seleccionados; no certifica ausencia de canales temporales.",
        "01-I añade [mensajes de rechazo y bloqueo](auditoria_por_etapas/resultados/evidencias/01-I-20261115/chrome-roles-final.json), [CSRF y fronteras HTTP](auditoria_por_etapas/resultados/evidencias/01-I-20261115/http-probes.json) y [regresiones de seguridad](auditoria_por_etapas/resultados/evidencias/01-I-20261115/regresion-seguridad-final.txt).",
    ),
    "CP-HU-AUTH-01-003": (
        "EJECUTADO PARCIAL en 01-I (15/11/2026): muestra de roles, rechazos con CSRF y datos comerciales ficticios preexistentes; no RN-29 global.",
        "01-I verifica [peticiones denegadas con datos preexistentes](auditoria_por_etapas/resultados/evidencias/01-I-20261115/regresion-seguridad-final.txt) y [efecto entre roles en Chrome](auditoria_por_etapas/resultados/evidencias/01-I-20261115/chrome-efecto-entre-roles-final.json); no cubre todas las rutas ni objetos.",
    ),
    "CP-HU-AUTH-02-001": (
        "VERIFICADO EN MUESTRA 01-I (15/11/2026), bloqueo entre contextos, reloj controlado y concurrencia PostgreSQL 18.4; la secuencia de reloj real distingue los dos builds del sublote.",
        "01-I añade [quinto fallo y otro contexto](auditoria_por_etapas/resultados/evidencias/01-I-20261115/chrome-roles-final.json), [fronteras de reloj y ausencia de hash durante bloqueo](auditoria_por_etapas/resultados/evidencias/01-I-20261115/regresion-seguridad-final.txt), [PG 18.4](auditoria_por_etapas/resultados/evidencias/01-I-20261115/postgresql-01i-latest.json), [bloqueo en build final antes de vencer](auditoria_por_etapas/resultados/evidencias/01-I-20261115/pre-expiracion-build-final.json) y [espera real](auditoria_por_etapas/resultados/evidencias/01-I-20261115/espera-real-01i.json). El quinto fallo ocurrió en el build intermedio; el servidor se reinició con la corrección de diagnóstico y mantuvo el mismo plazo. El acceso posterior y el [contador cero](auditoria_por_etapas/resultados/evidencias/01-I-20261115/despues-espera.json) se observaron en el build final.",
    ),
    "CP-DOC-01-06-001": (
        "EJECUTADO PARCIAL EN MUESTRA 01-I (15/11/2026): `/admin/` no se publica en la aplicación comercial; rechazo y diagnóstico de fallo de bitácora verificados en muestra. Perímetro, retención y sumidero reales siguen pendientes.",
        "01-I comprueba [admin ausente con staff/superuser](auditoria_por_etapas/resultados/evidencias/01-I-20261115/admin-final.json), [fallo de persistencia de auditoría](auditoria_por_etapas/resultados/evidencias/01-I-20261115/regresion-seguridad-final.txt) y [concurrencia PG](auditoria_por_etapas/resultados/evidencias/01-I-20261115/postgresql-01i-latest.json). El estado 01-H de bypass corresponde al build anterior y permanece en la evidencia histórica.",
    ),
}

source = SOURCE.read_text(encoding="utf-8")
for case, (state, extra) in cases.items():
    marker = f"##### {case} ·"
    if source.count(marker) != 1:
        raise SystemExit(f"Caso ausente o duplicado: {case}")
    start = source.index(marker)
    match = re.search(r"(?m)^##### CP-|^### HU-|^## ", source[start + len(marker):])
    end = start + len(marker) + match.start() if match else len(source)
    section = source[start:end]
    section, count = re.subn(r"(?m)^(\*\*Cubre:\*\* .+?\. \*\*Estado:\*\*) .+$", lambda m: m.group(1) + " " + state, section, count=1)
    if count != 1:
        raise SystemExit(f"Estado no reconocido: {case}")
    section, count = re.subn(r"(?m)^(\*\*Evidencia de ejecución:\*\* .+)$", lambda m: m.group(1) + " " + extra, section, count=1)
    if count != 1:
        raise SystemExit(f"Evidencia no reconocida: {case}")
    source = source[:start] + section + source[end:]

rn = "La pantalla informa los minutos restantes sin exponer datos sensibles."
if source.count(rn) != 1:
    raise SystemExit("No se reconoce el texto vigente de RN-17")
source = source.replace(rn, rn + "\n\n**Precisión técnica 01-I.** Con bloqueo vigente, el servicio comprueba primero su plazo y no ejecuta la derivación o comparación de contraseña para identificadores existentes ni inexistentes. El quinto rechazo recibe quince minutos completos a partir de la comprobación de credenciales. Esto no reemplaza un límite de tráfico en el punto de entrada. [Fundamento y pruebas](auditoria_por_etapas/resultados/ETAPA-01.md#vigente-01-i).", 1)

decision = "**Decisión de exposición.** Portal Django fuera de la navegación y acceso comercial; producción lo deshabilita o restringe a canal de mantenimiento autenticado y autorizado. No basta quitar enlace. Elegir configuración concreta al verificar despliegue; credenciales de mantenimiento no son cuentas compartidas de negocio."
if source.count(decision) != 1:
    raise SystemExit("No se reconoce DOC-01-06")
source = source.replace(decision, decision + "\n\n**Concreción 01-I.** Para la aplicación comercial se adopta despublicar por completo las rutas Django `/admin/`; no se crea un canal alternativo ni se conceden permisos técnicos a los roles de negocio. La corrección es la alternativa de menor superficie para cumplir C-01 bajo la instrucción de corregir defectos de esta auditoría; no presupone que el negocio no necesite mantenimiento. Si se requiere interfaz técnica, diseñar y verificar por separado su aislamiento, acceso y controles antes de habilitarla. [Decisión, impacto y evidencia](auditoria_por_etapas/resultados/ETAPA-01.md#vigente-01-i).", 1)

SOURCE.write_text(source, encoding="utf-8", newline="\r\n")
print("08 actualizado: cinco casos existentes y dos precisiones técnicas, sin nuevas HU")
