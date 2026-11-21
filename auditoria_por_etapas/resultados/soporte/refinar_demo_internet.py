"""Refine academic delivery requirements; does not alter product or operational data."""
from pathlib import Path
import importlib.util
import re

ROOT=Path(__file__).resolve().parents[3]
p=ROOT/'08_Historias_de_Usuario.md'
s=p.read_text(encoding='utf-8')
assert 'contrato-CT-ENTREGA-ACADEMICA' not in s
context='''**Contexto vigente DEMO-INTERNET · 15/11/2026.** El responsable exige demostración académica mediante URL pública HTTPS, cobro Yape porQR, efectivo y mixto, cancelaciones y distinción de medios, sin depender del dueño presente y con controles contra abuso de empleados. Las pruebas monetarias reales serán de importe pequeño y ejecutadas por personas autorizadas. No hacer nuevos yapeos de devolución. El mecanismo independiente para comprobar abonos y la política delegada de reintegros requieren resolución verificable; no se inventa integración ni se comparte acceso bancario. No es una empresa contratante ni exige comprar dominio. El cierre01-K sigue siendo evidencia local; no aprueba internet ni pagos nuevos. [Objetivo y secuencia](auditoria_por_etapas/OBJETIVO_Y_CRITERIOS_DE_ENTREGA.md), [escenarios y alternativas](auditoria_por_etapas/PAGOS_YAPE_Y_MIXTOS.md), [criterios de entrega](#contrato-CT-ENTREGA-ACADEMICA).

'''
s=re.sub(r'\*\*Contexto vigente 01-K[^\n]+\n',context,s,count=1)
s=s.replace('no determina el estado vigente de 01-K','no determina el estado vigente de DEMO-INTERNET',1)
# Select the explicitly requested Yape requirement, retaining honest implementation state.
start=s.index('### HU-VEN-07 ·'); end=s.index('<a id="EPIC-REP">',start)
b=s[start:end]
b=b.replace('**Prioridad MoSCoW:** W.','**Prioridad MoSCoW:** M.',1)
b=b.replace('**Alcance:** FUTURO; W en R1; requiere refinamiento antes de seleccionarse.', '**Alcance:** R1 seleccionado para ampliación académica DEMO-INTERNET por instrucción expresa del15/11/2026; implementación pendiente y mecanismo de comprobación sujeto a viabilidad.',1)
b=b.replace('**Contratos complementarios:** Condiciones comunes y CT-COHERENCIA-UI.', '**Contratos complementarios:** CT-ENTREGA-ACADEMICA, RN-02 y CT-COHERENCIA-UI. La antigua comprobación solo declarada por cajero no satisface por sí sola el objetivo antifraude; no se requiere dueño presente para cada venta.',1)
b=b.replace('**HU-VEN-07/CA-01.** Dado que el cliente paga con Yape, cuando el vendedor revisa fuera del sistema en el teléfono o medio habitual de la bodega y declara haber comprobado que el dinero realmente llegó, entonces el sistema habilita el registro del cobro con Yape (RN-02).', '**HU-VEN-07/CA-01.** Dado que el cliente paga al receptor autorizado del negocio, cuando el operador delegado comprueba el abono en un canal legítimo del receptor con permisos limitados y lo vincula inequívocamente al pedido, entonces registra importe, referencia, fecha, actor y origen de la comprobación; el sistema distingue una comprobación humana de una confirmación automática del proveedor. Un campo marcado por el cajero o una captura del comprador no acredita por sí solo recepción bancaria. Resolver el canal conforme RN-02 y CT-ENTREGA-ACADEMICA antes de habilitar cobros reales.')
b=b.replace('**HU-VEN-07/CA-05.** Dado que el vendedor declaró haber comprobado el ingreso y escribió un código de operación no utilizado previamente, cuando confirma la operación, entonces la venta queda registrada como pagada con Yape y se descuentan las existencias de mercadería.', '**HU-VEN-07/CA-05.** Dado un abono comprobado conforme CA-01, referencia no utilizada y total íntegramente cubierto, cuando se confirma el cobro autorizado, entonces se registra una sola venta con Yape y se descuenta stock una sola vez; no basta conocer un código ni declarar un importe. La verificación queda ligada al pedido, importe y receptor, y no se reutiliza tras cambiar esos datos.')
b=b.replace('Cobro Yape futuro con comprobación humana','Cobro Yape y origen de la comprobación')
b=b.replace('**Datos de prueba:** FUTURO; vendedor A dueño;', '**Datos de prueba:** Ampliación DEMO-INTERNET no implementada; vendedor A dueño del turno;')
b=b.replace('Válido registra Yape 20/código,', 'Solo con evidencia conforme CA-01 registra Yape 20/código,')
b=b.replace('1. Intentar confirmar sin declaración, con vacío yconusado.', '1. Intentar confirmar sin comprobación, con referencia vacía/usada, captura ajena y POST que solo declara pagado.')
b=b.replace('2. Confirmar con declaración y código nuevo.', '2. Confirmar mediante el mecanismo delegado documentado y referencia nueva; si no existe mecanismo aprobado, registrar NO EJECUTADO y no simular aprobación bancaria.')
addition='''<a id="HU-VEN-07-CA-07"></a>

**HU-VEN-07/CA-07.** Dado el cobro conQR, cuando se muestra al comprador, entonces corresponde al receptor del negocio configurado por ADMIN; el vendedor no puede sustituirlo por su cuenta. QR mostrado o escaneado no marca pagado. Cambio de receptor invalida solicitudes pendientes que lo usaban.

<a id="HU-VEN-07-CA-08"></a>

**HU-VEN-07/CA-08.** Dado un movimiento con código corto de seguridad, importe coincidente o datos incompletos, cuando se identifica el abono, entonces no se trata el código corto ni el importe como identificador único global. Si no hay identificación inequívoca en el canal real, el cobro queda pendiente de revisión, no se inventa una referencia ni se entrega stock bajo una venta pagada.

<a id="HU-VEN-07-CA-09"></a>

**HU-VEN-07/CA-09.** Dado un abono real seguido de cancelación, timeout o cambio de stock/precio, cuando no se puede concluir la venta, entonces se conserva el abono sin aplicar y su resolución pendiente; no se borra, no se atribuye a otro cliente y no se ordena otro envío automáticamente.

'''
b=b.replace('#### Casos de prueba escritos',addition+'#### Casos de prueba escritos',1)
b+='''<a id="CP-HU-VEN-07-002"></a>
##### CP-HU-VEN-07-002 · QR, identificación y abono sin aplicar

**Cubre:** HU-VEN-07/CA-07, HU-VEN-07/CA-08, HU-VEN-07/CA-09. **Estado:** DISEÑADO — NO EJECUTADO; mecanismo de consulta pendiente de decisión y disponibilidad.
**Precondiciones:** Entorno aislado, vendedor sin permisos de configurarQR; receptor ficticio para automatización; cuenta autorizada solo para ensayo humano acordado.
**Datos de prueba:** Pedido20; dos clientes pagan20; código corto123 repetido; referencia inequívoca A y B cuando la fuente las proporciona; QR ajeno; abono20 previo a cancelación.

1. Intentar sustituirQR como vendedor por UI yPOST; escanear sin transferir en ensayo controlado.
2. Intentar verificar solo con captura, importe o123; comprobar origen legítimo y referencia real para la variante válida.
3. Cancelar o provocar fallo tras registrar abono; recargar y consultar su estado desde otra sesión.

**Resultados esperados:** Sustitución denegada, escaneo no paga, datos ambiguos pendientes. Abono real persiste sin aplicación duplicada ni pérdida; el sistema no promete devolución bancaria. No atribuir verificación automática a un cotejo humano.

'''
s=s[:start]+b+s[end:]
# Mixed tender is an explicit new business need, not an inferred extra.
newhu='''<a id="HU-VEN-10"></a>

### HU-VEN-10 · Cobrar una venta combinando efectivo y Yape

**Épica:** EPIC-VEN. **Prioridad MoSCoW:** M. **Puntos Fibonacci:** 8 (orientativos; anteriores:—).

**Alcance:** R1 seleccionado para ampliación académica DEMO-INTERNET por solicitud explícita del responsable. **Implementación/verificación:** NO IMPLEMENTADA; depende del mecanismo de verificación Yape.

**Descripción de la HU:** Como vendedor, quiero aplicar efectivo y uno o varios abonos Yape comprobados a una misma venta, para atender a clientes que combinan medios de pago sin cobrar de más, mezclar clientes ni descuadrar la caja.

**Reglas relacionadas:** RN-02, RN-08, RN-29. **Dependencias funcionales:** HU-VEN-01c, HU-VEN-07, HU-CAJA-01/02, HU-VEN-05a/05b.

**Orden de producto:** 75.

**Estimación:** 8 es orientación de refinamiento, no horas ni compromiso de sprint; revisar tras elegir mecanismo de pagos y migración.

**Procedencia:** ETAPA-11; necesidad nueva expresada por usuario15/11/2026, no derivada solo del código.

**Contratos complementarios:** CT-ENTREGA-ACADEMICA, CT-COHERENCIA-UI; historial y reintegros conservan vínculos al origen.

#### Criterios de aceptación

<a id="HU-VEN-10-CA-01"></a>

**HU-VEN-10/CA-01.** Dado totalT, efectivo aplicadoE y suma de abonos Yape aplicadosY, cuando se confirma, entonces E+Y=T, todos los importes monetarios usan precisión de céntimos y cada abono cumple HU-VEN-07; faltante, importe negativo, dato no numérico o precisión excesiva rechaza sin mutación. Cero se admite solo como componente ausente, no como pago ficticio.

<a id="HU-VEN-10-CA-02"></a>

**HU-VEN-10/CA-02.** Dado efectivo entregadoR y componente efectivoE, cuando R>=E, entonces el vuelto es R-E y el efectivo esperado aumentaE; el componenteYape no aumenta gaveta. Un excedente digital no se convierte automáticamente en vuelto efectivo: queda sin aplicar o pendiente de resolución conforme política autorizada.

<a id="HU-VEN-10-CA-03"></a>

**HU-VEN-10/CA-03.** Dados varios abonos para una venta o clientes que pagan igual, cuando se aplican, entonces cada referencia se vincula a un único cobro permitido y conserva su importe, actor y receptor; no se reemplaza el primer abono ni se aplica el mismo saldo a dos ventas. Doble envío, pestañas concurrentes y reintento recuperan el resultado sin duplicar dinero, stock o venta.

<a id="HU-VEN-10-CA-04"></a>

**HU-VEN-10/CA-04.** Dada una venta mixta confirmada, cuando se consulta constancia, historial, turno o indicador, entonces se ven total, componentes aplicados, efectivo entregado y vuelto, sin sumar dos veces una venta ni presentar todo el total como efectivo. Abonos sin aplicar y reintegros se presentan separados de ventas cobradas.

<a id="HU-VEN-10-CA-05"></a>

**HU-VEN-10/CA-05.** Dada una venta mixta cancelada o reclamada, cuando se solicita resolverla, entonces se conserva su desglose original y el estado de cada componente; no se borra dinero recibido ni se marca devuelto por anular un registro. La devolución exige política delegada aceptada, límites acumulados y prueba del movimiento; no se emiten nuevos yapeos.

#### Casos de prueba escritos

<a id="CP-HU-VEN-10-001"></a>
##### CP-HU-VEN-10-001 · Mixto, vuelto, duplicación e historial

**Cubre:** HU-VEN-10/CA-01, HU-VEN-10/CA-02, HU-VEN-10/CA-03, HU-VEN-10/CA-04, HU-VEN-10/CA-05. **Estado:** DISEÑADO — NO EJECUTADO; ampliación no implementada.
**Precondiciones:** F-BASE aislada, turnoA100, receptor y mecanismo de verificación documentados; no realizar transferencias reales en pruebas automáticas.
**Datos de prueba:** Total30; Yape20 y billete20; variante dos abonos5+15; dos clientes con total30; referencia reutilizada; importes -1,0.001,NaN, faltante1 y exceso digital5.

1. Ejecutar mixto válido y leer pagos, stock, venta, constancia y turno.
2. Repetir con2abonos; ensayar referencias duplicadas en2clientes y conexiones concurrentes PostgreSQL.
3. Probar faltante, precisión y exceso; cancelar después de primer abono y recargar tras timeout.
4. Consultar desglose y solicitar devolución como rol sin permiso; conservar pendientes cuando la política no esté aprobada.

**Resultados esperados:** Venta30, efectivo aplicado10, vuelto10, gaveta110, Yape20; una venta y descuento de stock único. Dos abonos conservados, reutilización denegada y rechazos sin mutación. Abono tras cancelación sigue visible sin aplicar, sin falso reembolso. Ningún caso pendiente se cuenta aprobado.

'''
loc=s.index('<a id="EPIC-REP">')
s=s[:loc]+newhu+s[loc:]
# Keep unaccepted refund details out of implemented scope while exposing the current requirement.
for hu in ['HU-VEN-06a','HU-VEN-06b','HU-VEN-06c']:
    loc=s.index(f'### {hu} ·'); nextloc=s.index('#### Criterios de aceptación',loc)
    note=('**Cambio de objetivo DEMO-INTERNET:** cancelaciones/devoluciones son necesidad solicitada para la entrega; esta ficha histórica sigue en refinamiento y no está implementada. '
          'RN-08 y el mecanismo de devolución deben conciliarse con operación delegada sin dueño presente; NO se autorizan nuevos yapeos ni un reintegro efectivo automático. '
          'No usar esta etiqueta futura para excluir silenciosamente la necesidad del objetivo final; resolver CT-ENTREGA-ACADEMICA/C-04 antes de cerrar.\n\n')
    s=s[:nextloc]+note+s[nextloc:]
start=s.index('### RN-02 ·');end=s.index('\n---',start)
s=s[:start]+'''### RN-02 · Comprobación del abono Yape y separación del dinero

**Área:** Pagos con billetera digital

El dinero se recibe en la cuenta autorizada del negocio. Un QR, una captura del comprador, el importe coincidente o una declaración del cajero no son confirmación bancaria automática. El operador delegado necesita una fuente legítima del receptor, con permisos de consulta limitados y sin claves para transferir fondos; el flujo habitual no debe depender de que el dueño apruebe cada venta.

La modalidad se decide y prueba antes de habilitar dinero real. Yape Empresa/Ayudantes es una alternativa oficial de consulta delegada con costo y requisitos por confirmar para la cuenta; no se contrata por esta regla ni acredita API automática. Una pasarela con notificación verificable es otra alternativa sujeta a afiliación. La comprobación manual debe identificarse como tal y su riesgo residual de declaración falsa/colusión debe quedar expresamente aceptado; no simular conexión bancaria con scraping ni lectura de notificaciones. La selección pendiente bloquea la aprobación del cobro real, no el trabajo independiente del proyecto.

Registrar referencia inequívoca del abono disponible en la fuente receptora, importe, fecha, actor, receptor y origen de comprobación. Mantener exclusión de reutilización en base y bajo concurrencia; una referencia escrita no demuestra por sí sola autenticidad. El código de seguridad de3dígitos no es una clave única global y no sustituye un identificador de operación. Si no hay identificación inequívoca, mantener revisión; no inventar valores ni rechazar otro abono legítimo solo por repetir código corto.

Venta, intento de pago, dinero recibido, aplicación y devolución son hechos distintos. La suma aplicada debe cubrir exactamente el total. Cancelar el intento no borra el abono real ni lo marca devuelto. Se prohíben nuevos yapeos de devolución por instrucción expresa; la política alternativa y delegación de reintegros deben acordarse antes de habilitarlos. Conciliar cobros brutos, comisiones si aplican y dinero neto por separado, sin descontar una comisión del total pagado por el comprador.
'''+s[end:]
contract='''
<a id="contrato-CT-ENTREGA-ACADEMICA"></a>

### CT-ENTREGA-ACADEMICA · Internet, pagos y operación delegada

**Fundamento:** instrucciones del responsable15/11/2026: exposición pública por internet, QR Yape, pagos mixtos, cancelaciones, control de empleados no confiables, rapidez y ausencia habitual del dueño. Necesidades ACEPTADAS como objetivo; método de comprobación externa y política concreta de reintegros siguen en DECISIÓN PENDIENTE. No es autorización de gastos, afiliaciones, transferencias ni aprobación funcional. Las nuevas HU/CA y requisitos transversales se implementarán solo tras cerrar sus dependencias; no documentar funcionamiento inexistente.

**Horizontes:** R1 se amplía con HU-VEN-07/10 solicitadas. Las anulaciones06a/b/c y las vistas de caja/historial/reportes requieren refinamiento de política; son dependencias obligatorias del objetivo de entrega, aunque las fichas históricas conserven W hasta resolverlo. No congelar ni aprobar el objetivo mientras esas decisiones sigan abiertas. No se añaden automáticamente todos los reportes, facturación electrónica, múltiples cajas o una nueva tienda.

<a id="CT-ENTREGA-ACADEMICA-C-01"></a>

**CT-ENTREGA-ACADEMICA/C-01.** Dado el build candidato, cuando el profesor abre la URL desde otra red/equipo, entonces funciona porHTTPS público sin depender del servidor local del estudiante, conserva datos tras reinicio y permite el recorrido por roles; registrarURL, build, configuración sanitizada, motor, migraciones, estáticos y restauración aislada. Una URL del proveedor basta; no se exige dominio comprado.

<a id="CT-ENTREGA-ACADEMICA-C-02"></a>

**CT-ENTREGA-ACADEMICA/C-02.** Dados cobros efectivo, Yape y mixtos, cuando se confirma y concilia, entonces la suma aplicada cubre el total una vez, Yape no aumenta gaveta, vuelto depende solo del efectivo entregado/aplicado y se separan bruto, comisiones y neto cuando existan. No se anuncia validación bancaria automática si la fuente es humana.

<a id="CT-ENTREGA-ACADEMICA-C-03"></a>

**CT-ENTREGA-ACADEMICA/C-03.** Dado un cajero malicioso, otro empleado, dos clientes, pestañas paralelas o un fallo tras recibir dinero, cuando intentan reutilizar abono, cambiarQR/importe/rol, confirmar sin fuente válida o repetir operación, entonces permisos y persistencia impiden los efectos prohibidos; un timeout obliga a recuperar estado, no a cobrar o devolver otra vez. Registrar límites frente a colusión/declaración humana y no afirmar inmunidad al fraude.

<a id="CT-ENTREGA-ACADEMICA-C-04"></a>

**CT-ENTREGA-ACADEMICA/C-04.** Dado cancelación antes/después de abono, devolución, exceso, duplicado o reclamo tras cierre, cuando se tramita, entonces se conserva el origen y estado del dinero y mercadería, sin borrar venta ni reescribir cierre. No se emiten nuevos yapeos; tampoco se devuelve efectivo sin política explícita de delegación, topes, pruebas y control de abuso. Si la política no está resuelta, registrar la decisión y no aprobar esa capacidad.

<a id="CT-ENTREGA-ACADEMICA-C-05"></a>

**CT-ENTREGA-ACADEMICA/C-05.** Dados varios clientes y dueño ausente, cuando se atiende, entonces el recorrido normal usa permisos delegados definidos y no exige aprobación personal del dueño por cada cobro. Medir pasos y tiempo de captura/respuesta/espera del proveedor u operador por separado en el entorno público. La meta de rendimiento se fija contra la carga prevista antes de aceptación; rapidez no autoriza omitir comprobación de fondos ni ocultar cola de pendientes.

<a id="CT-ENTREGA-ACADEMICA-C-06"></a>

**CT-ENTREGA-ACADEMICA/C-06.** Dado el cierre de una etapa o entrega, cuando se informa aprobación, entonces cada requisito y literal seleccionado tiene CP y evidencia del mismo build/entorno; fallos, casos no ejecutados y decisiones abiertas permanecen visibles. Cerrar un sublote no cierra unaHU más amplia, otra etapa ni publicación. Un test frágil se corrige con fundamento conservando el fallo; un defecto de producto no se convierte en requisito para lograr verde.

'''
case_data=[
('001','Publicación y persistencia','01','URL candidata; ADMIN,ALMACENERO,VENDEDOR; una venta ficticia20 y copia aislada.','Abrir desde red externa; ingresar por rol; reiniciar servicio y recuperar venta; restaurar copia en base distinta.','HTTPS y permisos funcionan, estado y totales persisten; evidencia de build y restauración. SinURL o sin ejecución, NO EJECUTADO.'),
('002','Dinero separado por medio','02','Turno100; ventas efectivo20,Yape30,mixto30=10efectivo+20Yape; billete20 en mixto.','Ejecutar los tres modos; consultar pagos, constancias, historial y cierre; cotejar neto/comisión cuando exista.','Ventas80, efectivo aplicado30 y gaveta130, Yape50, vuelto10 en mixto; no duplicación ni mezcla de comisión con deuda del cliente.'),
('003','Abuso, carreras y recuperación','03','Dos clientes del mismo importe, referencia duplicada, QRajeno, vendedor desactivado; falla inyectada tras commit.','AlterarPOST/rol/importe/receptor; competir por referencia enPG; recargar y repetir después de timeout; consultar todas las tablas afectadas.','Denegaciones sin efecto; una aplicación y venta por cobro permitido; no fuga de datos ni reintegro duplicado. Fuente humana no se reporta como confirmación automática.'),
('004','Cancelación y política de reintegro','04','Intento sin abono, abono20 sin venta, venta mixta30, reclamo tras turno cerrado.','Cancelar cada estado; inspeccionar origen/pagos/stock/turno; revisar política de delegación; intentar devolución no autorizada y nuevo yapeo.','Sinabono no hay devolución; conabono persiste pendiente/resolución; no nuevo yapeo ni gaveta automática, cierre intacto. Política sin decisión impide declarar aprobado el reintegro.'),
('005','Atención con dueño ausente','05','Dueño desconectado; cajero delegado; clientes sucesivos efectivo/Yape/mixto y cola de solicitudes; métrica con red/carga indicadas.','Recorrer venta y medir acciones, p50/p95 del sistema y espera externa por separado; probar falta de respuesta y recuperación.','No se pide al dueño aprobar cada venta normal; el canal delegado funciona con límites registrados. Meta numérica y disponibilidad deben quedar acordadas y medidas antes del cierre; no se reemplazan por una afirmación de rapidez.'),
('006','Trazabilidad y cierre sin aprobación falsa','06','Inventario del build público, cuatro estados de caso: pasa,falla,noejecutado,pendiente; literales visibles y huellas.','Cruzar requisito→UI→servidor→datos→CP y viceversa; introducir un fallo/noejecutado; revisar porcentaje y estado; contrastar evidencia histórica.','Ningún fallo se oculta ni se contabiliza aprobado; extras y literales sin fuente bloquean el alcance afectado. Reporte identifica build, entorno, cobertura y cursor.'),
]
for ident,title,crit,data,steps,expected in case_data:
    contract+=f'''<a id="CP-ACA-{ident}"></a>
##### CP-ACA-{ident} · {title}

**Cubre:** CT-ENTREGA-ACADEMICA/C-{crit}. **Estado:** DISEÑADO — NO EJECUTADO en este corte documental.
**Precondiciones:** Versión candidata identificada; fixtures aislados y mecanismo/política definidos cuando corresponda. No mover dinero real mediante automatización.
**Datos de prueba:** {data}

1. {steps}
2. Registrar esperado/observado, persistencia, roles y evidencia; si falta una precondición consignar NO EJECUTADO.

**Resultados esperados:** {expected}

'''
s+=contract
# Derive counts after all changes, preserving IDs and old evidence.
spec=importlib.util.spec_from_file_location('views',ROOT/'auditoria_por_etapas/resultados/fuente_unica_20261112/regenerar_vistas.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
_,hs,tests,criteria=m.parse(s);n=m.counts(s,hs,tests,criteria)
s=re.sub(r'Alcance:\s*\d+ HU,\d+ seleccionadas para R1 y \d+ futuras;\d+ ideas excluidas', f'Alcance:{n["stories"]} HU,{n["selected"]} seleccionadas para R1 y {n["future"]} futuras;{n["outside_ideas"]} ideas excluidas',s,count=1)
s=re.sub(r'Los \d+ CA base se completan con \d+ criterios de contratos',f'Los {n["base_criteria"]} CA base se completan con {n["contract_criteria"]} criterios de contratos',s,count=1)
s=re.sub(r'En esta revisión hay \d+ casos escritos',f'En esta revisión hay {len(tests)} casos escritos',s,count=1)
s=re.sub(r'Las \d+ HU seleccionadas tienen',f'Las {n["selected"]} HU seleccionadas tienen',s,count=1)
s=re.sub(r'Las \d+ futuras mantienen',f'Las {n["future"]} futuras mantienen',s,count=1)
s=re.sub(r'Total:\d+ HU/\d+ SP orientativos; R1:\d+ SP',f'Total:{n["stories"]} HU/{n["fibonacci_catalog"]} SP orientativos; R1:{n["fibonacci_selected"]} SP',s,count=1)
for eid in n['epic_ids']:
    group=[h for h in hs if h['epic']==eid];sel=[h for h in group if h['selected']]
    values=f'{len(group)} | {len(sel)} | {len(group)-len(sel)} | {sum(h["sp"] for h in group)} | {sum(h["sp"] for h in sel)} |'
    s=re.sub(r'(?m)^(\| \['+eid+r'\]\(#[^)]+\) \|[^|]+\|)\s*\d+ \| \d+ \| \d+ \| \d+ \| \d+ \|$',lambda x:x[1]+' '+values,s)
errors=m.document_errors(*m.parse(s))
assert not errors,errors
p.write_text(s,encoding='utf-8')
print(m.generate())
