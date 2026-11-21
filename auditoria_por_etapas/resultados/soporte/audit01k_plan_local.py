"""Apply the user's explicit academic scope and literal refinements to existing HU."""
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[3]
source=ROOT/'08_Historias_de_Usuario.md'
body=source.read_text(encoding='utf-8')
assert 'DOC-01-06/C-04' not in body
context='''**Contexto vigente 01-K · 15/11/2026.** Proyecto universitario de demostración local ante profesor que representa al dueño de un minimarket. AS-IS: cuaderno y lápiz; TO-BE: control y consulta de operaciones por roles. Cada elemento visible, validación y mensaje debe corresponder literalmente a HU/CA/CP. Se revocan los extras de 01-J. La evaluación local no exige publicación comercial, infraestructura contratada ni documentos de una relación con un cliente real. Etapa 01 = HU-AUTH-01/02; etapa 02 = sesión y personal, división confirmada por el responsable. La aceptación de requisitos no sustituye los resultados de pruebas. [Alcance y caso de factura remitido a ventas](auditoria_por_etapas/resultados/soporte/01-K-alcance-local.md).

'''
body=body.replace('<!-- FUENTE-PRINCIPAL-20261112 -->','<!-- FUENTE-PRINCIPAL-20261112 -->\n\n'+context,1)
literal=(ROOT/'auditoria_por_etapas/resultados/soporte/01-K-literal-propuesta.md').read_text(encoding='utf-8')
start=literal.index('En `GET /`')
end=literal.index('## Bloqueo vinculado')
presentation=literal[start:end]
presentation=re.sub(r'^## Validación[^\n]+','**Validaciones de CA-01/02/03 · CP-HU-AUTH-01-002**',presentation,flags=re.M)
presentation=re.sub(r'\*\*Corrección de literal, no cambio de límite:.*?(?=\n\n|\Z)','**Fundamento 01-K:** se precisa el mensaje de máximo inclusivo, sin cambiar el límite ya aceptado; etiquetas y ayudas son presentación de la HU, no funciones nuevas.',presentation,flags=re.S)
marker='#### Casos de prueba escritos'
index=body.index(marker,body.index('### HU-AUTH-01 ·'))
body=body[:index]+'#### Presentación literal aceptada · HU-AUTH-01/CA-01..04\n\n'+presentation+'\n'+body[index:]
block=literal[literal.index('En el quinto fallo consecutivo'):literal.index('## Denegación vinculada')]
index=body.index(marker,body.index('### HU-AUTH-02 ·'))
body=body[:index]+'#### Mensaje y estados exactos · HU-AUTH-02/CA-01..03\n\n'+block+'\n'+body[index:]
denied=literal[literal.index('Una petición directa de un rol'):literal.index('## Distinción de alcance')]
index=body.index('#### Casos de prueba escritos',body.index('### HU-AUTH-01 ·'))
technical='''**Estados técnicos de la entrada · CA-01/04, CP-HU-AUTH-01-002/003.** El formulario conserva CSRF y un destino interno seguro. Una solicitud alterada sin token/cookie, o con token incorrecto, se rechaza con 403 antes de autenticar: título «403 Forbidden», encabezado «Prohibido (403)», mensaje «La verificación CSRF ha fallado. Solicitud abortada.» y pie «Más información disponible si se establece DEBUG=True.». Si falta cookie se añaden «Estás viendo este mensaje porqué esta web requiere una cookie CSRF cuando se envían formularios. Esta cookie se necesita por razones de seguridad, para asegurar que tu navegador no ha sido comprometido por terceras partes.» y «Si ha configurado su navegador para deshabilitar las cookies, vuelva a habilitarlas, al menos para este sitio o para solicitudes del "mismo origen".». Son literales de Django 5.2.18 con es-pe; DEBUG permanece desactivado en la demostración. PUT/DELETE con CSRF válido devuelven 405 sin texto de negocio; sin CSRF se aplica primero el rechazo 403. Una ruta inexistente, incluido `/admin/`, muestra título «Página no encontrada · Minimarket», estado «Error 404», encabezado «Página no encontrada», explicación «La dirección solicitada no existe o el registro ya no está disponible.» y enlace «Volver al inicio». Un destino externo se ignora y el ingreso vuelve a `/inicio/`; no aparece un mensaje extra. Estas medidas no agregan un límite de tráfico ni diagnósticos comerciales.

'''
body=body[:index]+denied+technical+body[index:]
old='**Investigación obligatoria.**'
start=body.index(old,body.index('### DOC-01-06'))
end=body.index('\n\n',start)
body=body[:start]+'''**Aplicabilidad académica 01-K.** El bloqueo por identificador de RN-17 y los eventos técnicos previos mantienen su función interna. No se añade límite por IP/proxy, diagnóstico de identidad ni política externa como requisito de ingreso. Las investigaciones anteriores sobre explotación pública quedan fuera de la demostración local por corrección expresa del responsable; no bloquean el cierre de AUTH-01/02 ni se presentan como funciones disponibles.''' +body[end:]
# Keep prior evidence but mark it explicitly historical, never current acceptance.
body=body.replace('**Evidencia de ejecución:** [01-', '**Evidencia de ejecución:** Antecedentes de sus builds; no determinan el estado académico vigente. [01-')
source.write_text(body,encoding='utf-8',newline='\r\n')
print('Precisiones literales integradas en HU/CA existentes; sin nuevas HU, CA ni CP')
