"""Prepend 01-I design/task notes without overwriting concurrent user edits."""
from __future__ import annotations

import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BACKUP = ROOT / "auditoria_por_etapas/resultados/evidencias/01-I-20261115/documentos-antes"
sections = {
    "02_Diseno_Tecnico_R1_PMV.md": """## Revisión y correcciones 01-I · 15/11/2026

El enrutador comercial ya no publica `/admin/`; cualquier interfaz de mantenimiento requerirá un canal separado diseñado y validado antes de habilitarse. El servicio comprueba primero el plazo de bloqueo y evita el hash mientras está vigente; los quince minutos del quinto fallo empiezan después de verificar credenciales. Si falla la inserción del evento de rechazo se intenta un diagnóstico externo sanitizado y se mantiene la denegación. WhiteNoise sirve estáticos recolectados en el WSGI local y la imagen los recolecta al construirse. Se verificaron navegador, servidor y PostgreSQL 18.4; el build de imagen y la topología real no se ejecutaron. Límites agregados, conservación y privacidad de eventos, IDNA y soporte siguen pendientes; las notas 01-H inferiores describen su build histórico. [Decisiones, costos y evidencia](auditoria_por_etapas/resultados/soporte/01-I-inventario-y-disposiciones.md).
""",
    "16_Task_Breakdown.md": """## Sublote 01-I · 15/11/2026 · correcciones de ingreso

Se ejecutaron `01I-ADMIN-01`, `01I-HASH-01`, `01I-LOG-01` y `01I-STATIC-01` en la aplicación comercial y se revalidaron con datos ficticios; la corrección de estáticos tiene pendiente el build de imagen y despliegue real. `01I-UX-01` no reprodujo en tres anchos la sospecha previa de solapamiento del enlace de salto. Persisten `SEC-15-TRAFICO-01`, `SEC-15-RETENCION-01`, `SEC-15-OBS-01`, diagnóstico IDNA y definición de canal técnico de soporte si se necesita, sin umbrales ni plazos inventados. La etapa 01 sigue parcial por perímetro y permisos globales; las tareas 01-H inferiores son históricas cuando describen el bypass o WSGI anterior. Cursor `01-J-PERIMETRO-RETENCION-IDNA-01`; global `16-NORMATIVA-BASELINE-01`. [Informe y pruebas](auditoria_por_etapas/resultados/ETAPA-01.md#vigente-01-i).
""",
    "21_Alcance_Actual_y_Diferencias.md": """## Revisión Etapa 01 · 01-I · 15/11/2026

La aplicación comercial deja de exponer Django admin, evita el cálculo de contraseña en un bloqueo vigente, diagnostica de forma sanitizada los fallos al guardar rechazos y sirve estáticos recolectados en la muestra WSGI; el build de Docker y el perímetro real siguen sin probar. La ejecución aislada cubre visitante, tres roles, vencimiento real y cinco carreras PostgreSQL 18.4; no cierra permisos globales, otras etapas, tráfico ni retención. El informe anterior y sus observaciones se conservan como evidencia de sus propios builds. [Inventario y disposición](auditoria_por_etapas/resultados/soporte/01-I-inventario-y-disposiciones.md) · [Informe](auditoria_por_etapas/resultados/ETAPA-01.md#vigente-01-i).
""",
}

for name in sections:
    current = ROOT / name
    backup = BACKUP / name
    if hashlib.sha256(current.read_bytes()).digest() != hashlib.sha256(backup.read_bytes()).digest():
        raise SystemExit(f"Cambio concurrente en {name}; no se sobrescribe")

for name, section in sections.items():
    path = ROOT / name
    original = path.read_bytes()
    line_end = b"\r\n" if b"\r\n" in original else b"\n"
    split = original.find(line_end)
    if split < 0:
        raise SystemExit(f"Falta encabezado en {name}")
    inserted = ("\n\n" + section).replace("\n", line_end.decode()).encode("utf-8")
    path.write_bytes(original[:split] + inserted + original[split:])
    print(f"Actualizado {name}")
