"""Read-only code checks and derived documentation; never imports the application."""
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
APP = ROOT / "r1-pmv"
rows = list(csv.DictReader((OUT / "ETAPA-00-inventario-codigo.csv").open(encoding="utf-8-sig")))
baseline = json.loads((OUT / "ETAPA-00-fuentes-codigo.json").read_text(encoding="utf-8"))
comparison = []
for name, old in baseline.items():
    path = ROOT / name
    current = hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None
    comparison.append({"source": name, "sha256_05nov": old, "sha256_09nov": current, "unchanged": current == old})
all_code = []
for path in sorted(APP.rglob("*")):
    if not path.is_file() or path.suffix not in {".py", ".html", ".js", ".css"}:
        continue
    if any(p in {".venv", ".git", "__pycache__"} for p in path.parts):
        continue
    name = path.relative_to(ROOT).as_posix()
    all_code.append({"source": name, "sha256_09nov": hashlib.sha256(path.read_bytes()).hexdigest(),
                     "in_05nov_ast_html_inventory": name in baseline,
                     "state": "NO EXAMINADO"})
drift = {"date_client": "2026-11-09", "baseline_date": "2026-11-05", "compared": len(comparison),
         "changed": sum(not r["unchanged"] for r in comparison), "comparison": comparison,
         "all_local_code_sources": all_code,
         "scope": "Only source bytes; no database connection, tests or web requests."}
(OUT / "ETAPA-00-deriva-codigo-09nov.json").write_text(json.dumps(drift, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
routes = json.loads((OUT.parent / "evidencias" / "00-rutas-resueltas.json").read_text(encoding="utf-8"))
admin_routes = [r for r in routes if r["route"].startswith("/admin/")]
counts = Counter(r["tipo"] for r in rows)

def cell(value):
    return str(value).replace("|", "\\|").replace("\n", " ")

def table(headers, data):
    return "\n".join(["| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in headers) + "|"] + ["| " + " | ".join(cell(v) for v in row) + " |" for row in data])

parts = ["""# Etapa 00 — inventario de código y superficie web

Extracción inicial: 2026-11-05. Reanudación y cotejo de archivos: 2026-11-09 (America/Lima). Este anexo inventaría identificadores y conexiones estáticas; **ninguna HU, módulo ni prueba se declara aprobada por aparecer aquí**. Las ejecuciones acotadas del agente principal se informan en `../ETAPA-00.md`, sin extender sus resultados a otras filas.

## Fuentes y reproducción

- Aplicación activa: `r1-pmv`, Django; montaje raíz en `r1-pmv/config/urls.py:4`. `qr-minimarket` no es una segunda aplicación web: el inventario de fuentes lo registra como carpeta de imagen.
- `ETAPA-00-inventario-codigo.csv`: catálogo por tipo, módulo, fuente, línea, identificador y detalle, con estado `NO EXAMINADO`. Para localizar una ocurrencia use la combinación `tipo + fuente:línea + identificador`; si varias ocurrencias comparten una línea, consérvese además el orden de fila CSV. No son nuevos IDs de HU.
- `ETAPA-00-fuentes-codigo.json`: SHA256 de las 77 fuentes leídas por la extracción AST/HTML inicial. `ETAPA-00-deriva-codigo-09nov.json`: cotejo y manifiesto complementario de todos los `.py/.html/.js/.css` locales, excluidos dependencias, `.git` y cachés. El segundo manifiesto inventaría archivos técnicos no analizados por el primero; no inventaría sus reglas internas.
- `../evidencias/00-rutas-resueltas.json`: expansión del resolver hecha por el agente principal en configuración aislada el 05/11; **resolver una URL no equivale a solicitarla**. No se volvió a arrancar la aplicación para redactar este anexo.
- Reproducción de extracción estática: desde la raíz, `r1-pmv/.venv/Scripts/python.exe auditoria_por_etapas/resultados/anexos/inventariar_codigo_00.py`. Reescribe los tres archivos derivados iniciales; para conservar el corte original, copiar los artefactos antes de repetir en otra fecha.
- Reproducción del cotejo documental: `r1-pmv/.venv/Scripts/python.exe auditoria_por_etapas/resultados/anexos/cerrar_inventario_codigo_00.py`. No importa Django, no usa `.env`, no conecta a una base, no ejecuta pruebas y no modifica código de aplicación. La fecha de este constructor corresponde a esta continuación; actualizarla para otro corte.

## Cobertura sintáctica y sus límites
"""]
parts.append(f"Cotejo: **{len(comparison)} archivos comparados, {drift['changed']} cambios de bytes** respecto al corte 05/11. El manifiesto complementario enumera {len(all_code)} archivos de código/plantilla/estilo; {sum(not x['in_05nov_ast_html_inventory'] for x in all_code)} no tenían hash en el corte AST/HTML y no se puede afirmar su estabilidad entre fechas. La comparación no acredita ausencia de cambios anteriores al 05/11 ni ausencia de cambios Git sin confirmar.\n")
parts.append(table(["Tipo de ocurrencia", "Cantidad", "Interpretación"], [(k, n, "Inventariado; NO EXAMINADO semánticamente") for k, n in sorted(counts.items())]))
parts.append("""
Los 48 registros `vista` incluyen auxiliares; no son 48 endpoints. Las 41 rutas de negocio incluyen dos alias de confirmación. Las 36 plantillas incluyen base, errores 403/404 y `identity/protected_placeholder.html`; una plantilla presente no garantiza ruta ni estado accesible. Los 916 textos y 359 expresiones dinámicas son ocurrencias, con duplicados entre plantillas; no son mensajes únicos ni requisitos independientes. Los 180 mensajes de servidor son llamadas sintácticas (incluyen variables y f-strings), no los mensajes finales renderizados. Los 42 campos de formulario declarados y 11 derivados de ModelForm se superponen conceptualmente con campos del modelo. Los 125 campos son declaraciones directas: quedan fuera campos heredados de Django, M2M implícitos, campos de sesión y formularios generados por el admin.

El extractor no reemplaza el inventario funcional de cada etapa: no expande HTML generado por `{{ form }}`, mensajes localizados de Django, todos los estados de JavaScript, mensajes definidos como constantes ni callbacks heredados. Atributos HTML y restricciones se conservan como fuente, sin verificar normalización, valor inicial, límites, persistencia o error. El cierre funcional de cada campo sigue pendiente. Las fuentes técnicas complementarias incluyen migraciones, comandos de gestión, settings y arranque; se identificaron por archivo/hash y requieren lectura focalizada en las etapas correspondientes. Las reglas de formularios se contrastarán con servicios, modelos y base, no solo con widgets HTML.

## Módulos, modelos, formularios y pruebas definidas
""")
module_rows = []
for m in ["identity", "catalog", "inventory", "cash", "sales", "app_platform", "templates"]:
    cr = Counter(r["tipo"] for r in rows if r["modulo"] == m)
    module_rows.append([m, cr["ruta"], cr["modelo"], cr["formulario"], cr["plantilla"], cr["prueba_definida"]])
parts.append(table(["Módulo", "Rutas negocio", "Modelos", "Formularios", "Plantillas", "Métodos test_*"], module_rows))
parts.append("\nLos **191 métodos test_*** son definiciones estáticas (48 identidad, 36 catálogo, 41 inventario, 12 caja, 46 ventas, 8 plataforma), **cero ejecuciones de pruebas desde este anexo**. No se tomó la cifra histórica 191 como un resultado nuevo. `config/test_runner.py:10` descubre aplicaciones locales y la carpeta `tests`; no se inspeccionaron resultados de test por inferencia del nombre. El CSV identifica cada método con clase, archivo y línea. La carpeta `r1-pmv/tests` no aportó métodos test_* en este corte. Los tests de semillas/reset son código de prueba; no autorizan ejecutar reset ni esas semillas sobre datos del usuario.\n")
parts.append(table(["Módulo", "Tipo", "Identificador", "Fuente precisa"], [(r["modulo"], r["tipo"], r["identificador"], r["fuente"] + ":" + r["linea"]) for r in rows if r["tipo"] in {"modelo", "formulario"}]))
parts.append("""
## Todas las rutas de negocio y permisos declarados

A = Administrador (`ADMIN`), L = Almacenero (`ALMACENERO`), V = Vendedor (`VENDEDOR`); visitante = no autenticado, no un cuarto registro de `Role`. Fuente: `identity/models.py:11`. El decorador `identity/authorization.py:17` redirige al visitante y rechaza roles fuera de lista; esto es una descripción del código. Todas las combinaciones de actor/ruta/HTTP siguen `NO EJECUTADO` salvo los casos que el informe principal identifique con evidencia concreta.

`Auth` significa cuenta autenticada. En `/inicio/` se comprueba además que el código del rol sea válido (`identity/views.py:57`). GET/POST no implica que todas sus acciones estén permitidas en cualquier estado. En formularios, consultar el CSV para acciones y campos asociados y la columna `plantillas` para la pantalla fuente.
""")
roles = {"roles_required(Role.Code.ADMIN)": "A", "roles_required(Role.Code.WAREHOUSE)": "L", "roles_required(Role.Code.SELLER)": "V", "roles_required(Role.Code.ADMIN, Role.Code.WAREHOUSE)": "A,L", "roles_required(Role.Code.WAREHOUSE, Role.Code.ADMIN)": "A,L", "roles_required(Role.Code.SELLER, Role.Code.ADMIN)": "A,V", "roles_required(Role.Code.ADMIN, Role.Code.SELLER)": "A,V", "autenticado": "Auth", "publico/inspeccionar": "Público"}
route_rows = []
for r in rows:
    if r["tipo"] != "ruta":
        continue
    methods = r["metodos"].replace("require_http_methods", "").replace("require_", "").replace("(", "").replace(")", "").replace("[", "").replace("]", "").replace("'", "")
    route_rows.append([r["identificador"], "`" + r["detalle"] + "`", methods, roles.get(r["roles"], r["roles"]), r["vista"], r["plantillas"] or "Redirección/acción; ver vista"])
parts.append(table(["Nombre URL", "Ruta", "HTTP", "Roles", "Vista", "Plantilla"], route_rows))
parts.append("""
Restricciones adicionales ya localizadas, todavía no certificadas: `cash/views.py:50` limita confirmación de apertura al vendedor propietario; `cash/views.py:92` y `:111` limitan cierre/historial al propietario cuando el actor es vendedor. `sales/views.py:264` y `:305` limitan constancia/historial al vendedor propietario; administrador consulta más ampliamente. `sales/services.py:35` exige turno propio abierto y `:128`, `:155`, `:194` enlazan líneas/borrador/cobro al actor. Deben probarse con dos vendedores diferentes en las etapas 09–15; tres roles distintos no prueban aislamiento entre usuarios del mismo rol.

## Superficie adicional /admin/

Hay **65 patrones bajo `/admin/`**, además de las 41 rutas de negocio: **106 patrones resueltos**. Incluyen nueve grupos de modelo (ocho propios + Group de Django), redirecciones, vistas de infraestructura y dos patrones de captura; no son 65 páginas independientes ni 65 peticiones ejecutadas. Lista literal con nombre/callback en el JSON del resolver. Montaje: `config/urls.py:5`. Las clases admin están en `identity/admin.py:7`, `catalog/admin.py:6`, `inventory/admin.py:7` y `cash/admin.py:6`; `LotInline` explica por qué hay nueve clases propias pero ocho registros de modelos propios.

La autorización de Django Admin depende de `is_active/is_staff` y permisos Django; **no equivale al rol de negocio Administrador**. `identity/admin.py:23` expone estado staff/superuser/grupos/permisos; `identity/admin.py:26` muestra los campos de alta. Las plantillas, validaciones y acciones heredadas de Django no forman parte de las 36 plantillas locales y no fueron inventariadas campo a campo. No se entró al admin ni se creó superusuario en este trabajo.

Clasificación provisional de esa superficie: `EXTRA SIN REQUISITO` para sus operaciones administrativas frente a las HUs de negocio; decisión de despliegue/alcance pendiente. La guía `21_Alcance_Actual_y_Diferencias.md` advierte que su login no comparte RN-17. Opciones para etapa 15: documentarlo como herramienta técnica restringida y probar permisos/controles propios, o excluirlo del despliegue operativo según decisión explícita. No se deshabilita ni se modifica ahora por inferencia.
""")
parts.append(table(["Patrón admin", "Nombre"], [(r["route"], r["name"]) for r in admin_routes]))
parts.append("""
## Dependencias y enlace hacia planificación

| Origen → efecto | Fuentes precisas | Etapas y comprobación pendiente |
|---|---|---|
| Cuenta/rol/sesión → cada acción y propietario | `identity/models.py:58`, `authorization.py:17`, `services.py:31`, `:64` | 01–02; después repetir acceso directo en cada módulo y 15 |
| Categoría activa → producto activo/vendible | `catalog/models.py:35`, `catalog/services.py:12`, `:26`, `:36` | 03; impacto en carga, consulta y venta en 05/07/10/14 |
| Producto registrado sin lotes → todavía sin stock vendible | `catalog/models.py:106`, `:112`, `:122` propiedades de stock; `inventory/models.py:16`, `:37` | 03 → 05 → 10; el alta no reemplaza la carga inicial |
| Carga inicial/lotes → cantidades, costo promedio y vencimiento | `inventory/services.py:67`, `:134`; `inventory/models.py:37` | 05 y 07; fechas Lima, normalización y rechazo atómico pendientes |
| Proveedor → entrada posterior → lote y costo | `inventory/services.py:161`, `:182`, `:314`; `inventory/models.py:113` | 04 y 06; proveedor inactivo, carga previa y constancia de reposición pendientes |
| Merma/ajuste → lote, costo, movimiento consultado | `inventory/services.py:196`, `:260`; `inventory/views.py:387` | 08; el índice de movimientos no acredita saldo ni historias de bajas/ajustes completas |
| Caja activa CAJA-01 → turno vendedor → borrador | `cash/services.py:15`, `sales/services.py:35`, `:77` | 09–10; datos de caja y límites de concurrencia pendientes |
| Borrador → cobro → venta, correlativo, FEFO y efectivo | `sales/services.py:194`, `:295`, `:343`, `:377` | 11; idempotencia y concurrencia requieren pruebas propias, PostgreSQL cuando corresponda |
| Venta confirmada → constancia/historial y cierre | `sales/views.py:261`, `:275`, `:299`; `cash/services.py:43` | 09/12; administrador vs vendedor propietario; no comprobante fiscal |
| Catálogo/inventario/ventas → resumen del panel | `identity/views.py:183` | 13; panel diario no demuestra HU-REP-01 por rango/medio de pago |
| Settings/entorno/migraciones → todas las funciones | `config/settings.py:7`, `:20`, `config/env.py:11`, `:51`; manifiesto complementario | 00/15; comprobar DB efectiva, no usar APP_ENV=test solo como garantía de aislamiento |

Mapa de búsqueda, no aprobación: identidad se enlaza con AUTH/USR/VEN-01a; catálogo con CAT/PROD; inventario con PROV/INV/PROD-06; caja con CAJA; ventas con VEN; resumen con REP. El anexo `ETAPA-00-planificacion.md` determina selección R1, posterior, adicional o conflicto para cada HU/CA. No asignar el descuento a HU-VEN-03 (PDF/correo fuera de horizonte), ni preparación de borrador a HU-VEN-01a (bloqueo inactividad). Los alias de confirmación, shell base, errores y admin carecen de una HU autónoma validada: vincularlos como soporte técnico o proponer requisito, sin crear HUs ficticias por cada botón.

## Cursor exacto y trabajo no ejecutado

1. Mantener este inventario congelado como corte 05/11, cotejado 09/11. El informe principal enlaza la evidencia nueva de navegador; no sobrescribir `NO EXAMINADO` masivamente por haber pasado un arranque.
2. Primera revisión funcional: etapa 01, `HU-AUTH-01`/`HU-AUTH-02`, campos `LoginForm.email/password` (`identity/forms.py:6`), ruta `/`, servidor `authenticate_active_account` (`identity/services.py:31`), modelo `LoginAttempt` (`identity/models.py:27`) y mensajes. Comparar cada CA, no trasladar cobertura histórica de `03`.
3. Para cada etapa siguiente expandir las ocurrencias CSV a una matriz de campo/salida con valor inicial, tipo, longitud, normalización, precisión, obligatoriedad, mensaje y persistencia; incluir variantes HTML dinámicas y errores de Django. Registrar las pruebas fronterizas como pendientes hasta ejecutarlas.
4. En etapa 15 revisar `/admin/login/` primero y documentar la decisión de superficie administrativa; después permisos staff/grupos/objeto, comandos de mantenimiento y concurrencia. Inventario de subrutas completo para el resolver guardado, inventario semántico del admin `NO EXAMINADO`.
5. Semillas, reset, migraciones reversibles, restauración, despliegue, SUNAT, pagos digitales, reportes futuros y normas: no ejecutados ni aprobados por este anexo. Ningún módulo funcional se cierra aquí.
""")
(OUT / "ETAPA-00-codigo.md").write_text("\n".join(parts) + "\n", encoding="utf-8")
print(json.dumps({"compared": len(comparison), "changed": drift["changed"], "all_sources": len(all_code), "rows": len(rows), "business_routes": 41, "admin_patterns": len(admin_routes), "methods_defined": counts["prueba_definida"], "tests_executed": 0}))
