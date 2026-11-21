"""Consolidate only the bounded 03-AG audit, keeping historical cuts intact."""
import json
from pathlib import Path

results = Path(__file__).resolve().parents[1]
summary = ('**Continuación 03-AG / 06-B.** Reposición y costo histórico verificados: '
           'corregidos el costo ausente del detalle de venta y el promedio posterior a FEFO. '
           '12 controles finales Chrome, 3 casos PostgreSQL y350/350 métodos. '
           'Migración ensayada en copia SQLite y PostgreSQL, original intacto. '
           'Ventas antiguas conservan costo desconocidoNULL. '
           '[Detalle y evidencia](anexos/ETAPA-03-AG-costo-historico.md).')
cursor = ('**03-AH / 06-C / AUD03AH-COSTO-VENCIDOS01.** Dos lotes con costos y vencimientos distintos: '
          'vender por FEFO, avanzar fecha hasta vencer uno y reponer; contrastar stock físico/vigente '
          'y valoración con RN14/BUG005. Después merma/ajuste y conservación de costos históricos. '
          'RN01, despliegue y retiro sanitario siguen pendientes; no cerrar otros módulos.')
for filename in ['ETAPA-03.md', 'ESTADO_GENERAL.md']:
    p = results/filename
    content = p.read_text(encoding='utf-8')
    paragraphs = content.split('\n\n')
    index = next(i for i,p in enumerate(paragraphs) if p.startswith('**Continuación 03-AF'))
    paragraphs[index] = summary+' '+cursor
    content = '\n\n'.join(paragraphs)
    if filename == 'ESTADO_GENERAL.md':
        lines = content.splitlines()
        for i, line in enumerate(lines):
            if line.startswith('| 03 Categorías'):
                lines[i] = '| 03 Categorías y productos | 11/11/2026 | 9HU/27CA:23 CUMPLE muestras previas,4 futuros;4 suplementarios | Frontera03-AG costo histórico corregido/verificado | Despliegue, cinco fichas y procesos integrales pendientes | 03-AH / 06-C / AUD03AH-COSTO-VENCIDOS01 |'
            elif line.startswith('| 06 Entradas/'):
                lines[i] = '| 06 Entradas/reposición | 11/11/2026 | INV01b/CA01–02 muestras de costo móvil e histórico03-AG;SOL previstos | PARCIAL,06-B verificado en muestra todos-vigentes | RN01 conflicto; valoración vencidos/ajustes, recepción integral y despliegue pendientes | 06-C / AUD03AH-COSTO-VENCIDOS01 |'
            elif line.startswith('| 11 Cobro/'):
                lines[i] = '| 11 Cobro/descuentos | 11/11/2026 | VEN01c,RN25/27/28;frontera RN28 verificada03-AG | NO EJECUTADO como etapa; muestra costo histórico favorable | Costos antiguosNULL, migración pendiente; no cierre integral | HU-VEN-01c/CA01; leer frontera03-AG y conservar pendientes |'
            elif line.startswith('> Leer PROTOCOLO_COMUN completo'):
                lines[i] = '> Leer PROTOCOLO_COMUN completo, ESTADO_GENERAL, ETAPA-03 y anexo03-AG. '+cursor
        content = '\n'.join(lines)+'\n'
    else:
        content = content.replace('El encabezado y 03-AF contienen el estado actual', 'El encabezado y 03-AG contienen el estado actual')
    content += '\n\n## Continuación 03-AG / 06-B\n\n'+summary+'\n\n'+cursor+'\n'
    p.write_text(content,encoding='utf-8')
with (results/'ETAPA-06.md').open('a',encoding='utf-8') as f:
    f.write('\n\n## Continuación 06-B / 03-AG\n\n'+summary+'\n\n'+cursor+'\n')
paths = {
    'before':'03-AG-ag-before-20261111T174621048542Z-47ee298c',
    'after':'03-AG-ag-after-20261111T175014153472Z-89caf8ce',
    'tests':'03-K-tests-20261111T174910780567Z',
    'migration':'03-AG-migrations-20261111T174944578832Z',
    'postgres':'03-AG-postgresql-20261111T174840857500Z.json',
}
index = {'date_lima':'2026-11-11','files':paths,'cursor':cursor,'checks':{}}
for name, path in paths.items():
    file = results/'evidencias'/path
    data = json.loads((file if file.is_file() else file/'result.json').read_text(encoding='utf-8'))
    assert all(data['protected_unchanged'].values())
    if name in ['before','after']:
        browser=json.loads((file/'browser.json').read_text(encoding='utf-8'))
        assert data['browser_exit']==0 and data['port_closed'] and not browser.get('error')
        index['checks'][name] = len(browser['checks'])
    elif name=='tests':
        assert data['failures']==0
        index['checks'][name] = data['methods']
    elif name=='postgres':
        assert not data.get('error') and data['port_closed'] and all(c['ok'] for c in data['cases'])
        index['checks'][name] = len(data['cases'])
    else:
        assert data['legacy_costs_null'] and all(data['preserved_tables'].values())
        index['checks'][name] = 'old columns preserved, legacy costs NULL'
(results/'evidencias/03-AG-indice.json').write_text(json.dumps(index,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(index['checks']))
