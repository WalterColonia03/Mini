"""Casos escritos de los contratos transversales; no ejecutan el producto."""
SUPPS = {}
def scenario(key, hus, data, steps, expected):
    SUPPS[key] = dict(hus=hus.split(), data=data, steps=steps.split(' || '), expected=expected)

scenario('DOC-03AB-01', 'HU-INV-01b',
 'ALMACENERO; Leche con carga confirmada; lote C, 10 unidades a S/6, vence 12/12/2026; sin SOL y sin proveedor. Repetir como ADMIN y VENDEDOR.',
 'Confirmar la recepción directa. || Consultar referencia, autor, fecha, lotes y origen. || Restaurar y enviar la misma petición con cada rol denegado.',
 'Recepción propia con origen directo y «Sin proveedor asignado»; no afirma autorización externa o solicitud aprobada. ADMIN/VENDEDOR no crean recepción, lotes, stock, promedio ni correlativo.')
scenario('DOC-03AH-01', 'HU-INV-01a HU-INV-01b HU-INV-02 HU-INV-03 HU-VEN-01c HU-REP-07',
 'F-COSTO: físico18, promedio3; 8 vencidas y10 vigentes. Entrada10 a6. Salida1. Ajuste+2. Variante físico0 sin costo. Dos conexiones PostgreSQL independientes.',
 'Recibir10; retirar1; ajustar+2. || Restaurar y probar ajuste positivo sin costo con físico0. || Restaurar y solapar recepción/salida; inyectar fallo después de escribir la primera mutación.',
 'Físico28/promedio4.0714; salida deja27/promedio4.0714 y snapshot4.0714; ajuste deja29/mismo promedio. Cero físico exige costo positivo documentado y rechaza si falta. Carrera equivale a un orden serial válido; fallo revierte todas las mutaciones. Costos históricos y NULL no se recalculan.')
scenario('DOC-03AI-01', 'HU-INV-01b HU-INV-04',
 'Clave UUID11111111-1111-4111-8111-111111111111; lote C, cantidad10, costo6; otra clave22222222-2222-4222-8222-222222222222; contador0; variante contador99999999.',
 'Confirmar; perder la respuesta y reintentar igual. || Reenviar misma clave con cantidad11 y con otro actor. || Recibir de nuevo el lote comercial C con segunda clave y misma caducidad. || Probar cantidad0 y corregir conservando clave. || Solapar dos envíos iguales en PostgreSQL; probar agotamiento de contador.',
 'Primera recepción R-00000001; reintento recupera la misma sin nuevos efectos; divergencia/actor ajeno rechaza sin filtrar datos. Otro ingreso real conserva identidad/procedencia distinta. Inválido no consume clave exitosa; corrección puede confirmar. Carrera crea una sola recepción. Contador agotado informa capacidad y no muta; nunca reinicia o reutiliza referencia.')
scenario('DEC-11-MODELO-AUDITORIA-VENTAS', 'HU-VEN-01c HU-VEN-02a HU-INV-04 HU-REP-07',
 'Variante de Leche: lotes A3+B2, promedio3; venta5 a10, recibido50; turno100. Venta antigua con costo/asignación desconocidos.',
 'Cobrar y leer asignaciones, movimiento y snapshots. || Editar maestros y consultar constancia. || Restaurar e inyectar fallo en cada inserción de la transacción; repetir doble POST. || Consultar el legado incompleto.',
 'Asignaciones A3/B2 suman5; venta50, caja150 y stock0, promedio vigente0 con costo histórico3. Snapshot original estable sin costos en constancia. Cada fallo devuelve todas las tablas y contador al estado previo; reintento no duplica. Legado indica dato no disponible, nunca deduce lote aplicando FEFO actual.')
scenario('DEC-11-DESCUENTOS-ALCANCE', 'HU-VEN-01b HU-VEN-01c HU-VEN-02a',
 'Nueva venta2×10; descuento ausente,0,1,-1,abc. Venta histórica con subtotal20, descuento2,total18 y clave confirmada.',
 'Recorrer formulario nuevo y enviar cada variante desde petición directa. || Consultar la venta histórica y repetir su confirmación con la clave/contenido originales.',
 'Nueva venta solo acepta cero/ausente: total20, base16.95, IGV3.05; no ofrece descuento discrecional. Otros valores rechazan con «Los descuentos no están habilitados para nuevas ventas», sin mutación. Histórico/reintento conserva18 y su constancia, sin recalcular a20 ni duplicar stock/caja.')
scenario('DEC-12-PERMISOS-HISTORIAL-Y-MENU', 'HU-AUTH-01 HU-VEN-05a HU-VEN-05b HU-CAJA-05 HU-VEN-02a HU-PROD-01',
 'ADMIN, ALMACENERO, vendedorA, vendedorB y visitante; ventas/turnos de A y B; cookie de cuenta luego desactivada.',
 'Recorrer menú y URLs de catálogo, POS, inventario, ventas, constancia y caja con cada identidad. || Alterar IDs/filtros hacia registros ajenos. || Desactivar A y repetir con su cookie anterior.',
 'Permisos coinciden con RN-29 en menú y servidor. ADMIN consulta global sin operar turno; A solo propios y POS sin costos; ALMACENERO no cobra; visitante/revocado no acceden. Ninguna constancia expone costo, incluso para ADMIN. Totales y filtros respetan la misma propiedad que filas/detalles.')
scenario('DOC-02-04', 'HU-USR-03 HU-USR-04 HU-USR-05 HU-AUTH-03 HU-AUTH-02',
 'Último ADMIN activo; vendedorA con turno abierto; cuenta B bloqueada por5 fallos; clave nueva ficticia PruebaNueva9!; sesiones de B en2 navegadores.',
 'Intentar degradar/desactivar último ADMIN y A. || Revisar/cancelar/confirmar destino explícito de B y repetirlo. || Cambiar correo/reactivar B; intentar ingresar durante bloqueo. || Confirmar reset/desbloqueo explícito y comprobar cookies/evento. || Salir con y sin turno/borrador.',
 'Invariantes rechazan sin mutar cuenta/sesión/turno. Cancelación no cambia; repetir destino no alterna. Correo/reactivación no limpian bloqueo. Reset válido aplica RN-24, revoca cookies y deja evento sin clave; desbloqueo solo por acción explícita. Mensaje de salida describe turno/borrador realmente existentes; confirmar descarta borrador y conserva turno.')
scenario('DOC-01-06', 'HU-AUTH-01 HU-AUTH-02 HU-AUTH-03 HU-USR-03 HU-LOG-01',
 'Entrada comercial; perfiles ficticios staff/superuser y tres roles; error controlado cuyo exc_info contiene CANARIO-SECRETO-PRUEBA; requestID conocido.',
 'Solicitar /admin/ y /admin/login/ desde entrada comercial. || Ejecutar ingreso, salida, reset, cambio de estado y mutación fallida. || Inspeccionar eventos persistidos y destino externo tras commit. || Provocar error sensible y fallo del registrador.',
 'No existe vía comercial alternativa que eluda permisos/límites. Eventos guardan actor/fecha/acción/objeto/resultado/requestID, sin secretos. Mutación y evento transaccional confirman juntos; rollback no genera evento externo de éxito. CANARIO no aparece en logs. Fallo de log no concede acceso; diagnóstico sanitizado. UI LOG futura no excusa falta de eventos actuales.')
scenario('DEC-10-BLOQUEO-INACTIVIDAD', 'HU-VEN-01a HU-AUTH-02 HU-VEN-01b',
 'A con turno/borrador; dos pestañas; 299 y300 segundos; polling cada30s; reloj cliente manipulado; A/B/inactivo y cinco contraseñas erróneas.',
 'Suspender interacción hasta300s manteniendo polling. || Reanudar pestaña y enviar petición directa. || Probar identidad distinta, incorrecta e inactiva. || Desbloquear A válidamente después del plazo permitido; variar precio/stock durante bloqueo.',
 'Servidor protege datos/operaciones de la sesión desde300s; pestañas comparten bloqueo. Polling/reloj cliente no reinician actividad. Errores no pierden borrador ni abren acceso, aplican RN-17. Reautenticación correcta conserva turno/borrador y exige revisar precio/stock cambiado antes de cobro.')
scenario('DEC-05-LOTE-ESPACIOS', 'HU-INV-01a HU-INV-01b HU-INV-02 HU-INV-03',
 'Lotes « ab  12 », «AB 12», «AB12»; longitudes0/1/64/65; cantidades0/1/999999/1000000/true; costos0/0.0001/9999999.9999/10000000/1e2/1.00001; vencimiento hoy/mañana/aniversario20años/+1día; hoy Lima12/11/2026.',
 'Enviar variantes independientes por UI y petición directa. || Desactivar producto/categoría/proveedor entre formulario y POST. || Alterar management form, enviar una fila válida más filas vacías y probar más de cuatro lotes válidos. || Repetir alrededor de medianoche UTC y Lima.',
 'Normaliza a AB 12: duplicado interno rechaza; AB12 distinto. Solo rangos/tipos/fechas válidos; boolean, NUL, exponente y precisión excesiva rechazan íntegros con error junto al campo y valores válidos conservados. Límite fecha20años por aniversario; cuatro tarjetas no son máximo comercial. Filas vacías se omiten si existe una válida; management form inválido nunca500. Estado obsoleto no ingresa stock.')
scenario('DEC-04-RUC-VALIDACION', 'HU-PROV-01 HU-PROV-02 HU-PROV-04 HU-INV-01b',
 'Dos «Distribuidora Sol» con RUC20123456789/20987654321; teléfono+51 999 111 222; destino false/omitido/inválido; variante RUC10dígitos/duplicado/Unicode.',
 'Crear y distinguir homónimos. || Desactivar proveedor con destino false y repetir; probar omitido. || Confirmar recepción con proveedor desactivado tras abrir formulario. || Consultar historia y texto de validación RUC.',
 'Homónimos permitidos y distinguidos por nombre+RUC; teléfono visible. Solo11 dígitos ASCII únicos, sin certificar SUNAT. False repetido mantiene inactivo; omitido/inválido rechaza sin cambio. Proveedor desactivado no se sustituye silenciosamente por ninguno; recepción rechazada completa. Historia conserva proveedor original.')
scenario('RN-05', 'HU-INV-02 HU-INV-03',
 'E vencido3 unidades; baja por robo1 con/sin explicación; ajuste ADMIN+2 a lote nuevo con fecha fiable; producto inactivo con carga confirmada; dos conexionesPG.',
 'Registrar robo explicado y consultar constancia. || Restaurar y probar sin explicación y DAÑO en vencido. || Registrar ajuste positivo, incluida variante vencida no vendible. || Solapar venta/baja/ajuste y reintentar la misma operación.',
 'Robo explicado conserva causa real, lote/autor/fecha/costo; tiene constancia de merma inmutable dedicada. Sin explicación/daño vencido rechazan. Ajuste de ADMIN tiene origen propio; no simula compra y permite saneamiento físico de inactivos. Cantidad recibida original no se reescribe. Carreras sin negativos/duplicados; promedio RN-14 y caja/ventas originales preservados.')
scenario('DEC-08-KARDEX-COMPRAS', 'HU-INV-04 HU-INV-01b HU-VEN-01c',
 'Movimientos conocidos +20,+10,-5,-2,+1 con asignaciones;26filas para paginar; legado sin asignación; ADMIN/ALMACENERO/VENDEDOR.',
 'Consultar orden completo y saldos; filtrar solo salidas y período intermedio. || Navegar páginas con empate de instante. || Abrir venta multilote y legado sin evidencia. || Comparar base antes/después de GET.',
 'Saldos20,30,25,23,24; filtros no reconstruyen falso saldo omitiendo entradas. Paginación25 con orden instante+ID y filtros/totales del conjunto completo. Salidas enlazan asignación persistida; legado desconocido rotulado. GET no muta y VENDEDOR no obtiene costos.')
scenario('DEC-07-VENCIDOS-FILTRO', 'HU-PROD-01 HU-PROD-06 HU-PROD-05 HU-DASH-03',
 'Producto inactivo con E3 vencidas; Arroz activo5 mínimo10; lotes futuros1/30/31días; filtros1/30/3650/0/3651/abc; panelADMIN.',
 'Consultar vencidos, críticos y próximos; cambiar días. || Reactivar categoría con producto individual suspendido. || Revisar rótulos/totales/enlaces del panel.',
 'Vencido inactivo visible y no sugiere compra por stock bajo; crítico solo producto/categoría activos. Filtro1..3650, inválido informa y usa30; rótulos/listas/conteos coinciden en Lima. Reactivación no activa producto. Panel mínimo muestra su ventana30 y totales diarios; no promete reportes/ranking futuros.')
scenario('DEC-11-TOPE-EFECTIVO-FORM', 'HU-CAJA-01 HU-CAJA-02 HU-VEN-01b HU-VEN-01c HU-PROD-02',
 'Montos vacío,0,0.01,9999999.99,10000000.00,1e2,++1,Unicode y1.001; cierre acumulado10000000.00; diferencia-5; cantidad de borrador0/1/999999/1000000.',
 'Validar UI/servicio según campo: apertura/contado≥0, precio>0 y efectivo≥total. || Cerrar acumulado que supera tope por operación pero cabe en numeric(14,2). || Intentar nueva venta que excede capacidad acumulada. || Insertar/actualizar valores inválidos directamente en base aislada y capturar checks.',
 'Validaciones coherentes en todas las capas, usando Decimal. Venta/precio/efectivo/apertura tope9999999.99; cierre permite acumulado válido hasta999999999999.99, diferencia negativa legítima. Exceso se rechaza antes de venta sin bloquear cierre válido. Check borrador exige1..999999 y no se atribuye como nuevo el mínimo ya existente. Rechazos sin efectos.')
scenario('DEC-12-ORDEN-LINEAS-RECIBO', 'HU-VEN-01b HU-VEN-02a HU-VEN-05a HU-VEN-05b HU-CAJA-05',
 'Borrador líneas A,B,C con UUID desordenados; dos turnos con apertura idéntica;26ventas; precio cambia10→11; fechas incompletas/invertidas; ancho390×844.',
 'Cobrar y reabrir/ imprimir constancia. || Repetir historial empatado y paginar con filtros. || Consultar borrador por GET tras cambio de precio; luego revisar y confirmar por POST. || Recorrer menú ADMIN/VENDEDOR con teclado y móvil.',
 'Posiciones A,B,C persistidas; orden de turnos con desempateID; legado sin posición usa orden declarado, no finge orden original. Filtros inválidos muestran error sin500; navegación preserva parámetros. GET no cambia precio; POST exige revisión explícita antes de cobro. Menús solo ofrecen acciones propias; sin promesas de función futura disponible.')
scenario('DOC-00-01', 'HU-PROD-02 HU-PROD-04 HU-USR-02 HU-PROV-02',
 'Catálogo74 HU/219CA,33seleccionadas/41futuras y8ideas;60criterios de encargos y4J-CA; nombre «Leche», variante « leche », «Léche»; homónimos de personas/proveedores.',
 'Validar unicidad de IDs, campos, prioridad, Fibonacci y enlaces HU→CA→caso→evidencia. || Comparar vistas07/09/03 con fuente08 y controles de auditoría. || Revisar nombre/mínimo de producto y homónimos.',
 'Cada HU/CA tiene una definición vigente y pruebas escritas con datos/esperado. SP orientativos no equivalen a compromiso del equipo ni horas trabajadas. Producto normalizado duplicado rechaza, acentos se conservan; personas/proveedores homónimos permitidos. No se inventa Sprint/equipo ni se marca verificado por redactar documentación.')
scenario('CT-ROLLBACK-01-POST-ESCRITURA', 'HU-INV-01a HU-INV-01b HU-VEN-01c HU-CAJA-02',
 'Instancia PostgreSQL17 aislada, versión menor registrada; cuentas ficticias; proceso HTTP propio; barrera posterior a escritura efectiva; copia de respaldo con hashes y recuentos.',
 'Interrumpir proceso tras escritura y antes de commit; reconectar e inspeccionar todas las tablas. || En pruebas separadas, interrumpir/reiniciar motor antes/durante/después del commit y reintentar con misma clave. || Ejecutar recorrido navegador ADMIN→ALMACENERO→VENDEDOR→ADMIN, permisos cruzados, concurrencia real, restauración y pipelineCI/despliegue aislado.',
 'Sin efectos parciales; commit confirmado con respuesta perdida recupera única operación. Respaldo/restauración conserva integridad y balances. Informar versión/comando/barrera/capa HTTP o Client y omisiones. Estado inicial NO EJECUTADO; PG18.4/SQLite previos no demuestran PG17, caída post-escritura ni navegador actual completo.')

scenario('PROP-E00-HU-02', 'HU-CAT-01 HU-CAT-02 HU-PROD-05',
 'ADMINA y ADMINB; categoríaLácteos activa con producto activo e inactivo, lotes y borrador; versiónv1; ALMACENERO/VENDEDOR.',
 'Abrir revisión de desactivación, recargar y cancelar. || Confirmar revisión vigente. || Restaurar; A abrev1, B desactiva/reactiva a v3, A confirma desdev1. || Reactivar categoría y consultar productos. || Probar roles denegados.',
 'J-CA1: revisión explica nombre/estado/efecto y cancelar no muta. J-CA2: destino explícito conserva lotes/borradores/ventas; reactivar respeta suspensión individual. J-CA3: versión antigua rechaza incluso tras volver al mismo estado. J-CA4: noADMIN no revisa/confirma; stock/costo/estado intactos.')

VISIBLE = [
 ('CP-VISIBLE-001','Promesa de operación y resultado real',
  'Una fila por cada texto de éxito, error, ayuda, botón, enlace, estado, etiqueta e impresión; registrar literal, ruta, rol y estado de datos. Ejemplo: recepción «registrada» con lote inválido.',
  ['Inventariar plantillas, textos dinámicos y respuestas del servidor; recorrerlos en navegador con cada rol.', 'Enlazar cada promesa con HU/RN/CA; provocar éxito, rechazo y fallo de red.', 'Comparar mensaje con respuesta, persistencia y lo que ve el siguiente rol.'],
  'Ningún éxito antes de commit ni error con mutación oculta; mensaje precisa causa y acción posible. Extra sin requisito se registra para decisión, sin aceptarlo por estar implementado. No se rebaja el requisito para hacer coincidir un bug.'),
 ('CP-VISIBLE-002','Cantidades, dinero, filtros y estado comercial',
  'Leche18físico/10vendible; vencidos/inactivos; venta20/base16.95/IGV3.05; filtrosvacíos e inválidos;26filas.',
  ['Comparar cada contador, total, alerta y etiqueta con consulta autorizada a datos de prueba.', 'Cambiar filtros, página, fechaLima y estado del producto desde otra sesión.', 'Revisar rótulos y contenido en pantalla e impresión.'],
  'Unidades y conceptos explícitos; físico no se llama vendible; total filtrado no es total de página. No afirmar «sin productos» cuando hay un fallo de consulta. Mensajes/estados obsoletos exigen revisión sin cobro silencioso.'),
 ('CP-VISIBLE-003','Permisos, navegación y disponibilidad anunciada',
  'ADMIN/ALMACENERO/A/B/visitante/revocado; pantallas vacías, cargadas, bloqueadas y error; móvil390×844 y escritorio.',
  ['Recorrer menús, enlaces de retorno, acciones por teclado y URLs directas.', 'Cambiar de rol/cuenta y probar ID ajeno, cookie vieja y pestaña antigua.', 'Revisar enlaces de funciones futuras, canal fiscal y ayudas de lector.'],
  'Menú y autorización coinciden; no anuncia operación disponible que termina sistemáticamente denegada. Función futura se etiqueta y no ofrece acción engañosa. Constancia interna no simula boleta/factura ni validación SUNAT. La ayuda describe el lector y la confirmación realmente implementados.'),
 ('CP-VISIBLE-004','Registro completo de cobertura inversa',
  'Inventario con identificador literal estable, build/hash, rol, ruta/estado, requisito, caso, evidencia y observado; excluir solo con motivo explícito.',
  ['Conciliar inventario estático con recorrido dinámico por roles; incluir textos condicionales.', 'Buscar elementos sin requisito o sin prueba y abrir hallazgo trazable.', 'Revisar ausencia de pendientes en cada tramo antes de declarar cobertura de ese tramo.'],
  'Se distingue CUMPLE/INCUMPLE/PARCIAL/NO EJECUTADO/NO EXAMINADO/FUTURO/EXTRA SIN REQUISITO/CONFLICTO. Una lista de plantillas o una suite verde no equivale a cobertura visual completa. El inventario sin recorrer permanece pendiente, nunca se marca verificado por inferencia.')
]
