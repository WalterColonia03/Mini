# Mini · Sistema Minimarket R1-PMV & Planificación Integral

Repositorio oficial del proyecto de gestión comercial e inventario para minimarket, que incluye el código fuente del sistema en Django, su planificación ágil, contratos funcionales y auditorías por etapas.

---

## 🗺️ Estructura del Repositorio

Para desarrolladores y agentes de IA que revisen este repositorio:

```
├── r1-pmv/                    <- 💻 CÓDIGO FUENTE DE LA APLICACIÓN (Django 5)
│   ├── catalog/               <- Catálogo, productos y escaneo de códigos de barra
│   │   ├── barcodes.py        <- Normalización, validación y tipos de código de barras
│   │   ├── static/catalog/    <- JavaScript del lector/captura (`barcode_capture.js`)
│   │   └── templates/catalog/ <- Vistas y diálogo de captura (`barcode_capture.html`)
│   ├── sales/                 <- Ventas, carrito, cobro (efectivo, digital, QR, mixto)
│   ├── cash/                  <- Turnos de caja (apertura, control y arqueo/cierre)
│   ├── inventory/             <- Inventario, lotes (FEFO), kardex, mermas y ajustes
│   ├── identity/              <- Roles (ADMIN, CAJERO, ALMACENERO), login y sesiones
│   ├── config/                <- Configuración Django (`settings.py`, `urls.py`)
│   └── tests/                 <- Pruebas automatizadas y de integración
│
├── qr-minimarket/             <- 📱 Código QR estático de pagos (Yape sin comisión)
│   └── README.md              <- Aclaración de contenido de la carpeta
│
├── auditoria_por_etapas/      <- 🧪 Auditorías, evidencias y pruebas por etapas (00–17)
│   ├── resultados/            <- Reportes y dictámenes de auditoría
│   └── scripts/               <- Scripts de verificación y contrastes
│
└── 📄 Documentación Funcional y Técnica (Markdown en raíz):
    ├── 00_LEEME_PLANIFICACION.md               <- Guía de lectura del corte vigente
    ├── 01_Proyecto_y_Releases.md               <- Alcance general y versiones
    ├── 02_Diseno_Tecnico_R1_PMV.md             <- Arquitectura y diseño técnico
    ├── 03_Matriz_de_Trazabilidad_y_Pruebas.md  <- Matriz de pruebas
    ├── 07_Reglas_de_Negocio.md                 <- Reglas operativas del negocio
    ├── 08_Historias_de_Usuario.md              <- Catálogo normativo de historias (HU)
    └── 21_Alcance_Actual_y_Diferencias.md      <- Estado de implementación
```

---

## 🔍 Módulos Clave del Código (`r1-pmv/`)

Si buscas implementar o revisar funciones específicas:

1. **Lectura y Validación de Códigos de Barra:**
   * Lógica Python: [`r1-pmv/catalog/barcodes.py`](./r1-pmv/catalog/barcodes.py)
   * Captura en Navegador: [`r1-pmv/catalog/static/catalog/barcode_capture.js`](./r1-pmv/catalog/static/catalog/barcode_capture.js)
   * Plantilla UI: [`r1-pmv/catalog/templates/catalog/barcode_capture.html`](./r1-pmv/catalog/templates/catalog/barcode_capture.html)
   * Especificación funcional: [`auditoria_por_etapas/resultados/anexos/ETAPA-03-Barcode-to-PC.md`](./auditoria_por_etapas/resultados/anexos/ETAPA-03-Barcode-to-PC.md)

2. **Pagos Digitales, Yape y Mixtos:**
   * Flujo de venta: [`r1-pmv/sales/`](./r1-pmv/sales/)
   * Diseño de pagos: [`auditoria_por_etapas/PAGOS_YAPE_Y_MIXTOS.md`](./auditoria_por_etapas/PAGOS_YAPE_Y_MIXTOS.md)
   * Imagen QR: [`qr-minimarket/`](./qr-minimarket/)

3. **Control de Caja y Turnos:**
   * Modelos y servicios: [`r1-pmv/cash/`](./r1-pmv/cash/)

---

## 🤖 Guía para Agentes de IA y Asistentes Virtuales

Si eres una IA (ChatGPT, Claude, Gemini, etc.) analizando este proyecto:
- El **código ejecutable** está en la carpeta [`r1-pmv/`](./r1-pmv/).
- La carpeta `qr-minimarket/` contiene únicamente una imagen JPG de referencia para el código QR de cobro, no código de escaneo.
- Si necesitas descargar o procesar el repositorio completo en texto plano, puedes utilizar la herramienta:
  `https://gitingest.com/WalterColonia03/Mini`
