# R1-PMV — Sistema de ventas para minimarket

Aplicación Django para la operación del minimarket: autenticación, empleados, catálogo, inventario por lotes, caja y ventas. La [guía de alcance y diferencias](../21_Alcance_Actual_y_Diferencias.md) distingue el sistema disponible de los requisitos pendientes en la planificación.

## Roles

- **Administrador:** gestiona empleados, categorías, productos y proveedores; consulta stock, movimientos, ventas y turnos; registra mermas y ajustes.
- **Almacenero:** consulta productos, proveedores y existencias; registra cargas, entradas y mermas.
- **Vendedor:** abre y cierra su turno, registra ventas en efectivo y consulta sus ventas y constancias.

Los permisos concretos se validan en el servidor. La constancia de venta de R1 es interna y no sustituye una boleta o factura oficial.

## Arranque local

Requiere Python y las dependencias de `requirements.txt`. Desde esta carpeta en PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Complete `DJANGO_SECRET_KEY` en `.env`. Para una demostración local con SQLite, configure contraseñas de semilla en la sesión y ejecute:

```powershell
$env:SEED_ADMIN_PASSWORD = '<contraseña-temporal>'
$env:SEED_WAREHOUSE_PASSWORD = '<contraseña-temporal>'
$env:SEED_SELLER_PASSWORD = '<contraseña-temporal>'
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py seed_pmv
.\.venv\Scripts\python.exe manage.py seed_demo
.\.venv\Scripts\python.exe manage.py runserver --insecure
```

Abra `http://127.0.0.1:8000/`. La opción `--insecure` sirve los archivos de estilo solo para esta demostración local; no se usa para un despliegue público. `seed_pmv` crea las cuentas ficticias `admin.demo@pmv.invalid`, `almacen.demo@pmv.invalid` y `vendedor.demo@pmv.invalid`, además de una cuenta inactiva de prueba. Las contraseñas de las cuentas existentes no se sustituyen si sus datos no cambiaron. Use estas semillas solo para demostración.

El portal Django `/admin/` no está publicado en la aplicación comercial; el mantenimiento requiere un canal independiente. La imagen ejecuta `collectstatic` durante su construcción y WhiteNoise sirve los recursos recopilados con `DEBUG=false`. En otros métodos de despliegue, ejecute `python manage.py collectstatic --noinput` al preparar cada versión.

## Verificación

```powershell
$env:DJANGO_SECRET_KEY = 'test-only-key'
$env:APP_ENV = 'test'
$env:DATABASE_URL = 'sqlite'
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
.\.venv\Scripts\python.exe manage.py test
```

La configuración también admite PostgreSQL mediante `DATABASE_URL`; consulte `.env.example` y `docs/seguridad.md` antes de un despliegue.
