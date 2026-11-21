"""Apply the explicit local-demo decision and evidence to existing planning."""
from pathlib import Path
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / 'auditoria_por_etapas/resultados/evidencias/01-K-20261115'
BEFORE = OUT / 'documentos-antes-cierre'
BEFORE.mkdir(exist_ok=True)

def edit(name, transform):
    p = ROOT / name
    backup = BEFORE / name.replace('/', '__')
    if backup.exists():
        raise RuntimeError(f'Refusing repeated application: {name}')
    backup.write_bytes(p.read_bytes())
    p.write_text(transform(p.read_text(encoding='utf-8')), encoding='utf-8')

evidence = 'auditoria_por_etapas/resultados/evidencias/01-K-20261115/'
report = 'auditoria_por_etapas/resultados/ETAPA-01.md#vigente-01-k'
archive = 'auditoria_por_etapas/resultados/evidencias/01-J-20261115/antes/auditoria_por_etapas__resultados__ETAPA-01.md'

def update_plan(s):
    cases = {
        'CP-HU-AUTH-01-001': ('VERIFICADO 01-K PARA DEMOSTRACIÓN LOCAL (15/11/2026): tres roles; solo acceso y sesión de entrada.', 'chrome-roles.json', 'navegador-01k.json'),
        'CP-HU-AUTH-01-002': ('VERIFICADO 01-K PARA DEMOSTRACIÓN LOCAL (15/11/2026): rechazo uniforme, campos, fronteras y mensajes literales.', 'literales-browser.json', 'http-probes.json'),
        'CP-HU-AUTH-01-003': ('VERIFICADO 01-K EN EL ALCANCE DE ENTRADA POR ROL (15/11/2026): cuatro escenarios escritos GET/POST con CSRF y datos poblados, más 31 combinaciones de barreras por rol. Las reglas de propiedad de objetos y operaciones internas conservan sus etapas.', 'literales-permisos.txt', 'chrome-efecto-entre-roles.json'),
        'CP-HU-AUTH-02-001': ('VERIFICADO 01-K PARA DEMOSTRACIÓN LOCAL (15/11/2026): quinto fallo, bloqueo compartido, minutos restantes y fronteras de expiración con reloj controlado; evidencia de espera real 01-I heredada explícitamente.', 'identity-final-venv.txt', 'postgresql-01k-latest.json'),
    }
    for cid, (state, a, b) in cases.items():
        start = s.index(f'##### {cid} ·')
        end = s.index('**Precondiciones:**', start)
        old = s[start:end]
        old = re.sub(r'\*\*Estado:\*\*[^\n]*', f'**Estado:** {state}', old, count=1)
        old = re.sub(r'\*\*Evidencia de ejecución:\*\*.*', f'**Evidencia de ejecución:** [01-K: alcance, build y cobertura]({report}); [ejecución A]({evidence+a}), [ejecución B]({evidence+b}) y [139 pruebas identity]({evidence}identity-final-venv.txt). [Informe anterior íntegro, resultados de otros builds]({archive}); sus conclusiones operativas fueron sustituidas por el alcance académico expreso.', old, flags=re.S)
        s = s[:start] + old.rstrip() + '\n' + s[end:]
    s = s.replace('Perímetro, retención y sumidero reales siguen pendientes.', 'Las condiciones externas de publicación son NO APLICA a la demostración local 01-K; los eventos de las operaciones de otras etapas conservan su evaluación propia.')
    s = s.replace('**Revisión:14/11/2026.**', '**Antecedente de otras etapas (14/11/2026; no determina el estado vigente de 01-K).**', 1)
    # A requirement is not weakened: existing CA and written steps remain intact.
    s = s.replace('**Decisión de exposición.** Portal Django fuera de la navegación y acceso comercial; producción lo deshabilita o restringe a canal de mantenimiento autenticado y autorizado. No basta quitar enlace. Elegir configuración concreta al verificar despliegue; credenciales de mantenimiento no son cuentas compartidas de negocio.', '**Decisión de exposición vigente 01-K.** La aplicación de demostración no publica las rutas Django `/admin/` ni `/admin/login/`. Los tres roles acceden por el ingreso del sistema; no existe una interfaz alternativa de mantenimiento que forme parte de la entrega local. No se exige contratar ni diseñar un canal comercial externo para cerrar esta etapa.')
    return s

edit('08_Historias_de_Usuario.md', update_plan)

common = ('**Contexto vigente 01-K · 15/11/2026.** Proyecto universitario local, con profesor como dueño de minimarket representado. '
          'AS-IS: cuaderno y lápiz; TO-BE: control del negocio por roles. La división confirmada conserva etapa 01 (ingreso/bloqueo) y etapa 02 (sesión/personal). '
          'Las condiciones de contratación, alojamiento y publicación real no son pendientes de esta entrega local. '
          'Los cortes fechados inferiores son antecedentes y no reactivan esas condiciones. '
          '[Decisión y escenario fiscal remitido a ventas](auditoria_por_etapas/resultados/soporte/01-K-alcance-local.md).\n\n')
blocks = {
    '01_Proyecto_y_Releases.md': common,
    '02_Diseno_Tecnico_R1_PMV.md': common + '## Diseño de ingreso vigente 01-K\n\n`LoginForm` valida correo de hasta 254 caracteres, con mensaje inclusivo preciso; `Account.normalize_email` aplica `strip().casefold()`. `LoginAttempt` conserva el contador compartido y plazo de RN-17 en base; `authenticate_active_account` serializa su actualización y crea sesión solo si procede. `/admin/` permanece fuera de rutas. Se retiran diagnósticos y configuraciones de tráfico añadidos en 01-J. No hay migración nueva. Los errores de campos, rechazo, bloqueo y 403/404 se especifican literalmente en HU-AUTH-01/02 de08. La semántica del tablero y de los destinos sigue en sus módulos.\n\n',
    '16_Task_Breakdown.md': common + '## Tareas de cierre 01-K\n\n| Tarea | Fundamento / resultado | Estado |\n|---|---|---|\n| 01K-RETIRAR-J | Instrucción explícita: quitar diagnóstico, pruebas y configuración de tráfico de01-J; restaurar Compose de demostración | EJECUTADA, manifiesto de retirada |\n| S1-AUTH01-UI / 01K-LITERAL | Refinar presentación bajo CA existentes y corregir texto del máximo inclusivo254 | VERIFICADA, 79 checks literales y4 pruebas de formulario |\n| S1-AUTH01-SVC/AUTO / 01K-PERMISOS | 4 escenarios CP003 y31 combinaciones adicionales, GET/POST con CSRF; sin cambios en datos comerciales poblados | VERIFICADA,5 pruebas de permisos |\n| S1-AUTH02-SVC/AUTO | Cinco fallos, bloqueo15min, fronteras/otra sesión y carreras | REVALIDADA, identity139/139 y PG18.4 cinco escenarios |\n| 01K-DOC | Actualizar08, regenerar07/09/03 y reflejar alcance/cursor | EJECUTADA, cierre01K |\n\nNo nuevas HU, puntos ni compromisos de sprint:14 se conserva. Próximo cursor `02-LOCAL-TRAZABILIDAD-01`; la revisión de02 empieza con sus HU/CA/CP y su evidencia anterior. Los tres fallos de la regresión ampliada se remiten a caja/inventario/ventas, sin aprobarlos.\n\n',
    '21_Alcance_Actual_y_Diferencias.md': common + '## Resultado vigente de Etapa01\n\nEtapa01 cerrada para su demostración local:2HU,7CA y4CP de ingreso/bloqueo, con límites de cobertura del [informe01K](auditoria_por_etapas/resultados/ETAPA-01.md#vigente-01-k). `139/139` identity, `79/79` literales Chrome y `5/5` escenarios PostgreSQL18.4. La regresión ampliada obtuvo663/666: tres fallos externos se conservan y se remiten a sus etapas; no se declara cierre del sistema completo. Se elimina el agregado01J y se precisa el mensaje máximo254 sin cambiar el límite ni agregar reglas.\n\n',
}
for name, block in blocks.items():
    def transform(s, block=block):
        # Remove only active 01-H/01-I summaries; originals remain in the prior evidence.
        s = re.sub(r'(?m)^## (?:Revisión y correcciones 01-I|Revalidación acotada 01-H|Sublote 01-[HI] ·|Revisión Etapa 01 · 01-I)[^\n]*\n.*?(?=^## |\Z)', '', s, flags=re.S|re.M)
        first, rest = s.split('\n', 1)
        return first + '\n\n' + block + rest.lstrip('\n')
    edit(name, transform)

for name in ['auditoria_por_etapas/PROTOCOLO_COMUN.md', 'auditoria_por_etapas/CONTINUIDAD_Y_SEGUNDA_PASADA.md']:
    def scope_note(s):
        first, rest = s.split('\n', 1)
        note = ('> **Aclaración de alcance 15/11/2026, instrucción del responsable.** La evaluación actual es una demostración universitaria local. '
                'No agregar requisitos de contratación/publicación, diagnósticos ni límites por IP ajenos a HU/CA/CP. '
                'Los mensajes de la interfaz deben tener correspondencia literal en08. '
                'Las propuestas no se aceptan por existir en el código. Conservar etapas01 (ingreso/bloqueo) y02 (sesión/personal). '
                'El caso de conservación y búsqueda de factura pertenece a ventas/historial. '
                '[Alcance exacto](resultados/soporte/01-K-alcance-local.md). Esta instrucción prevalece sobre condiciones operativas anteriores; conservar evidencia sin convertirla en aprobación actual.\n\n')
        return first + '\n\n' + note + rest.lstrip('\n')
    edit(name, scope_note)

edit('auditoria_por_etapas/resultados/soporte/01-K-literal-propuesta.md', lambda s: s.replace(
    'Texto para integrar bajo los criterios y casos ya existentes de `HU-AUTH-01/02`. Precisa presentación y validaciones del ingreso especificado; no incorpora funciones, políticas de producción ni nuevos roles. Los estados se verificarán con el build final antes de declararlos cumplidos. Esta ficha no reemplaza la integración en `08`.',
    'Ficha incorporada a08 bajo los criterios y casos existentes de HU-AUTH-01/02 por instrucción expresa de alinear la demostración. La fuente vigente es08; esta ficha conserva el refinamiento de presentación, sin funciones nuevas. Resultado:79/79 comprobaciones de literales en Chrome y4 pruebas de formulario; ver ETAPA-01, sublote01-K.'))
print(json.dumps({'updated': len(list(BEFORE.iterdir())), 'source_sha256': hashlib.sha256((ROOT/'08_Historias_de_Usuario.md').read_bytes()).hexdigest()}))
