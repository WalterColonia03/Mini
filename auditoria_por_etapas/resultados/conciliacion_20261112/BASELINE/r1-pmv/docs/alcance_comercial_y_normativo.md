# Alcance comercial y revisión normativa — R1-PMV

Fecha de consulta: 5 de noviembre de 2026. Este documento distingue lo que hace la versión académica de las condiciones que deben resolverse antes de ofrecerla para operar un minimarket real. La aplicabilidad depende del negocio, sus productos, régimen tributario y forma de operación; no es una certificación legal ni de seguridad.

## Comprobantes y tributación

- El sistema registra ventas y genera una **constancia interna**; la pantalla de constancia indica expresamente que no es un comprobante de pago autorizado por SUNAT. No se identificó integración con el sistema de emisión electrónica de SUNAT ni con un proveedor de emisión. Por tanto, no debe presentarse como facturación electrónica ni como sustituto de boletas o facturas.
- SUNAT indica que la mayoría de contribuyentes están obligados a emitir comprobantes electrónicos, con excepciones concretas; la obligación exacta debe contrastarse con el régimen y situación del cliente. El padrón de obligados dejó de estar disponible el 1 de junio de 2026. [SUNAT: sujetos obligados a emitir comprobantes electrónicos](https://cpe.sunat.gob.pe/informacion_general/obligados_cpe).
- Como alternativa operativa a estudiar, SUNAT ofrece emisión mediante SOL y sus aplicaciones; usar un proceso externo exige definir la conciliación con las ventas y evitar omisiones o duplicidades. Esa conciliación no está automatizada aquí. [SUNAT: Sistema de Emisión SOL](https://cpe.sunat.gob.pe/sistema_emision/see_sol).
- El cálculo actual divide el precio total entre 1,18 y muestra IGV de 18 % para todas las ventas. No se ha implementado clasificación tributaria por producto, exoneraciones ni otras situaciones fiscales. No se debe presentar ese cálculo uniforme como liquidación tributaria completa; validar el catálogo y régimen con un especialista antes de utilizar datos reales.

## Datos personales y seguridad

- Se almacenan datos de cuentas y proveedores, y se aplican permisos por rol y controles de sesión. Eso no demuestra por sí solo cumplimiento integral de protección de datos. Se necesita definir responsables, finalidad, información a titulares, retención, gestión de derechos, accesos, respaldos, respuesta a incidentes y medidas acordes al riesgo, y contrastar su aplicación concreta con la Ley 29733 y su reglamento vigente. [MINJUSDH: reglamento de la Ley de Protección de Datos Personales](https://www.gob.pe/institucion/minjus/noticias/1067368-ejecutivo-aprueba-nuevo-reglamento-de-la-ley-de-proteccion-de-datos-personales).
- El reglamento entró en vigor el 31 de marzo de 2025 salvo disposiciones específicas. El MINJUSDH explica obligaciones de notificación de incidentes bajo las condiciones correspondientes; debe comprobarse la norma y sus supuestos antes de definir el procedimiento. [MINJUSDH: explicación del nuevo reglamento](https://www.gob.pe/institucion/minjus/noticias/1099347-minjusdh-realizo-conferencia-virtual-para-explicar-aspectos-de-la-ley-de-proteccion-de-datos-personales-y-su-nuevo-reglamento).
- El proyecto admite PostgreSQL y usa bloqueos transaccionales. SQLite se documenta para demostración local: no demuestra el comportamiento concurrente de producción. Antes de operar con varios usuarios hacen falta pruebas concurrentes sobre PostgreSQL, restauración de respaldos, revisión de despliegue y una evaluación de seguridad. No se ha acreditado certificación ISO u otro estándar.

## Atención al consumidor

- El sistema no incluye un Libro de Reclamaciones. Esto no significa que deba estar integrado al sistema interno: el negocio debe disponer del mecanismo que le corresponda por su actividad. Indecopi ofrece la herramienta «Tu Libro» y señala las obligaciones de los establecimientos abiertos al público. [Indecopi: implementación del Libro de Reclamaciones](https://www.gob.pe/institucion/indecopi/noticias/1296574-los-emprendedores-ya-pueden-generar-su-libro-de-reclamaciones-de-manera-rapida-y-sencilla-sin-costo-alguno).

## Condiciones previas a una oferta de producción

1. Definir el alcance contractual: productos admitidos, impuestos, comprobantes, devoluciones, métodos de pago y responsabilidades del cliente y proveedor.
2. Resolver y probar la emisión de comprobantes correspondiente y su conciliación con cada venta, incluidas anulaciones y contingencias.
3. Validar impuestos, operación de caja, mermas e inventario con el negocio y un profesional tributario; incluir productos con distintos tratamientos cuando corresponda.
4. Probar permisos, concurrencia, integridad y recuperación con PostgreSQL y una configuración de producción, además de documentar soporte y respaldo.
5. Verificar las obligaciones aplicables al negocio y a los datos tratados; no afirmar cumplimiento total o rentabilidad garantizada sin evidencia independiente.

## Limitación específica del acceso

El ingreso principal bloquea durante 15 minutos el correo normalizado tras cinco fallos y comparte ese estado entre sesiones. Este control no limita el tráfico distribuido, el acceso separado de Django en `/admin/` no lo utiliza y falta definir limpieza de registros de intentos. Deben verificarse concurrencia en PostgreSQL y protección adicional antes de producción. El bloqueo de pantalla por inactividad y el cierre automático de sesiones previas siguen pendientes de contraste con sus historias.
