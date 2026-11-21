# Selección previa · 03-PRECIO · 20/11/2026

Segunda pasada acotada respecto del 14/11. 08 SHA-256 d57a21c2b662cf2b38a9b8f7468eecec68734737ac46a2b76c9e675379fc6dd2. HEAD 7816d3328115cf5aa5bcdd0985fffd795b3ae084 con cambios locales. El cursor global de 02 y sus dependencias 11/15 permanecen en ESTADO_GENERAL. Inventario anterior conservado en ETAPA-03 §§1–2 (14/11) y anexo ETAPA-03-inventario.

| Inventario base de 08 | CA | CP de la ficha | Tratamiento previo |
|---|---|---|---|
| CAT-01 / CAT-02 | 01..02 / 01..03 | 001 de cada HU | Lista y alta ADMIN, dependencias de datos y rol |
| CAT-03 / CAT-04 | 01..02 cada una | 001 de cada HU | Renombrar y eliminar, horizonte futuro |
| PROD-01 / PROD-02 | 01..03 / 01..05 | ver fichas 08 | Consulta de catálogo ADMIN/ALMACENERO y alta ADMIN, dependencias |
| PROD-03 | 01..02 | ver ficha 08 | Captura de código seleccionada, lector físico heredado |
| PROD-04 | 01..05 | 001 y 002 | CA-01 seleccionado. Mínimo, código, nombre y reclasificación son superficies colindantes |
| PROD-05 | 01..03 | 001 | Disponibilidad comercial, evidencia histórica parcial |

27 CA base, 1 seleccionado en profundidad. Contrato suplementario PROP-E00-HU-02 para suspensión de categoría. Las 12 rutas de catalog/urls.py, campos, acciones, mensajes y asignación inversa de tareas conservan como punto de partida el inventario anterior. La muestra prioriza el cruce de versiones requerido para la entrega.

| Caso fijo | Resultado exigible | Capas |
|---|---|---|
| P1 · HU-PROD-04/CA-01, variante de CP-HU-PROD-04-001 | Venta histórica 2 × 10.00, nueva ficha 11.50 con la misma identidad. Categoría activa de productos distintos de enlatados. ADMIN edita, ADMIN y ALMACENERO ven el precio tras recarga, VENDEDOR lo consulta en su mostrador. Verificar límites de rol para catálogo/edición/categorías. | Servidor, Chrome aislado, HTTPS de prueba |
| P2 · DEC-12-ORDEN-LINEAS-RECIBO/C-04, paso 3 de su CP-001 | Borrador ordinario 1 × 10.00. Recargar preserva la línea. El intento sobre precio antiguo exige revisión; sin venta, descuento de stock ni ingreso por ese intento. Aceptación posterior vende 1 × 11.50 con desglose 9.75 + 1.75. Venta anterior, constancia e historial conservan el importe original. | Servidor, Chrome aislado, HTTPS de prueba. Carrera edición/cobro en PostgreSQL |
| P3 · CT-ENTREGA-ACADEMICA/C-03 y C-04; CP-ACA-003/004, escenario 20 de PAGOS_YAPE_Y_MIXTOS | Con aporte recibido de 3.00 al precio de 10.00, recuperar la versión del pedido o conservar obligación de 3.00 al cambiar a 11.50. Cero nuevo cobro por recarga. La sola declaración del cajero no acredita. | Inventariar soporte y traspasar a 10/11. Prueba monetaria humana dependiente de canal/reintegro |

Dependencias RN-01/03/06/27/28/29/30, CP-VISIBLE-001..004, caja única abierta por su titular, lote vigente, instantáneas de venta, cuenta y base exclusivamente ficticias. Registrar literalmente etiquetas y avisos observados y su respaldo. Separar revisión documental, corrección, ensayo local, público y monetario. El denominador es 3 escenarios; ningún caso compuesto ni RN global obtiene aprobación por una variante. Guardar cada corrida y causa de fallo. Si falla HTTPS, avanzar en local y conservar la brecha pública.
