# Reporte de cambios realizados por Gemini 4 Argon (Etapa 02) y verificación frente a Codex (GPT 6 Astra)

Fecha del reporte: **09/11/2026 (America/Lima)**  
Carpeta auditada: `C:/Users/walte/OneDrive/Imágenes/planificacion_limpia`

---

## 1. Respuesta directa a tu duda: ¿GPT 6 Astra (Codex) vio los cambios de Argon aunque no pulsaste «Aceptar»?

**SÍ. GPT 6 Astra en Codex SÍ vio e inspeccionó los cambios de Gemini Argon en disco, NO trabajó sobre el proyecto «original» pre-Argon.**

### Por qué ocurre esto y cómo queda demostrado al 100 %

1. **Cómo funciona el botón «Aceptar / Rechazar» en Antigravity IDE:**
   Cuando Argon llama a `write_file` o `edit_file`, el IDE **escribe inmediatamente en los archivos reales del disco duro**. La barra de «Aceptar / Rechazar» es solo una revisión visual posterior para ti: mientras no pulses «Rechazar», cualquier otra herramienta en la misma carpeta (como Codex) lee los archivos **ya modificados por Argon**.

2. **Línea de tiempo verificada en disco y en los logs:**
   - **17:25:48 – 18:00:30:** Gemini 4 Argon ejecutó sus ediciones y pruebas hasta que se agotó su cuota exactamente a las **18:00:30** (`23:00:30 UTC`). Antes de modificar `r1-pmv/identity/`, Argon sacó un respaldo completo previo en `auditoria_por_etapas/resultados/datos/etapa02-20261109/baseline-identity/`.
   - **18:00:44 – 18:22:03:** GPT 6 Astra (Codex) trabajó en el sublote **02-A** sobre la misma carpeta.
   - **18:26:40 – 18:26:41:** Al regresar al chat de Antigravity tras el corte de cuota, el IDE re-selló/sincronizó **12** archivos de la cola pendiente de revisión (ver sección 2 y advertencia sobre `09_Product_Backlog.md`).

3. **Pruebas directas dentro del trabajo de GPT 6 Astra (Codex):**
   - **Hashes SHA-256 idénticos en `baseline.json`:** Al iniciar `02-A` a las `18:12:23`, Codex registró en `auditoria_por_etapas/resultados/evidencias/02-A-20261109T231223297870Z/baseline.json` los hashes SHA-256 de todos los fuentes de `r1-pmv/identity/` y de la base `etapa02-20261109/audit.sqlite3`. **Todos coinciden bit a bit con los archivos ya editados y creados por Argon** (`models.py`, `forms.py`, `services.py`, `views.py`, `employee_list.html` y `test_etapa02_audit.py`).
   - **Declaración explícita en `ETAPA-02.md`:** Codex escribió literalmente en la sección 1 y 6 de `auditoria_por_etapas/resultados/ETAPA-02.md`:
     > *«Ya existían la base `etapa02-20261109`, los anexos de planificación/superficie, scripts, once métodos de auditoría, evidencia parcial y cambios llamados `FIX-E02-01..07`. **No se atribuyen a esta sesión.** ... No se modificó código funcional del producto en 02-A. Se corrigieron inventario, afirmaciones de evidencia y soporte de auditoría; las correcciones históricas `FIX-E02` se conservaron y se revalidaron con la suite actual.»*
   - **Revalidación de las pruebas de Argon:** Codex ejecutó los **11 métodos** de `identity.test_etapa02_audit` creados por Argon dentro de su corrida de `89/89` pruebas en memoria (`02-revalidacion-20261109T231223296324Z.json`).
   - **Respaldo y edición encima de documentos de Argon:** A las `18:00:46`, Codex copió el anexo creado por Argon a `evidencias/02-A-20261109T231223297870Z/planificacion-pre-reconciliacion.md` y luego reconcilió `ETAPA-02-planificacion.md`, `ETAPA-02-superficie.md` y `03_Matriz_de_Trazabilidad_y_Pruebas.md`.

### ⚠️ Advertencia importante antes de tocar «Aceptar / Rechazar» en Antigravity

1. **Si pulsas «Rechazar» (Reject) en los archivos de `r1-pmv/identity/`:** revertirás las correcciones `FIX-E02-01..07` y las pruebas `test_etapa02_audit.py` que Codex ya dio por existentes y revalidó en `02-A` (si lo haces, la base real del código volvería al estado pre-Argon).
2. **Incidente detectado en `09_Product_Backlog.md` a las `18:26:41`:**
   - En `closure-verified.json` (`18:22:03`), el verificador de Codex (`verificar_cierre02a.py`) reportó `"checked_local_links": 57` y `"missing_local_links": []` (0 enlaces rotos).
   - Sin embargo, a las **`18:26:41`** (el segundo en que volviste a Antigravity), el IDE volvió a escribir **12 archivos** pendientes; entre ellos **`09_Product_Backlog.md`**, que quedó de nuevo con la línea agregada por Argon (la cual enlaza a `ETAPA-02-cierre-y-traspaso.md`, archivo que todavía no existe). Los otros 11 archivos re-sellados a las `18:26:40–41` no habían sido modificados por Codex, por lo que mantienen el mismo contenido de `18:12:23`.

---

## 2. Inventario maestro: por qué ves «11 archivos» frente a los 17 tocados por Argon

Antes de quedarse sin cuota, Gemini 4 Argon ejecutó `write_file` (archivo nuevo) o `edit_file` (archivo existente) sobre **17 archivos distintos** (además de crear archivos de datos/evidencia mediante scripts). La diferencia con la cifra **11** que ves en la interfaz del IDE se debe a que **4 archivos** ya fueron editados/reconciliados posteriormente por Codex y a la agrupación entre archivos editados/nuevos en el panel de revisión. Para que no falte ninguno de tus 11 archivos sin confirmar, aquí están **los 17 completos**:

| # | Archivo | Acción de Argon (`17:25–17:59`) | Estado actual en disco vs Codex | Hora de archivo en disco | En `baseline.json` de Codex (`18:12:23`) |
|---:|---|---|---|---|---|
| 1 | `r1-pmv/identity/models.py` | `edit_file` (x2) | Contenido exacto de Argon (`d7435d3325c6`) | `18:26:41` | **Sí** (idéntico SHA) |
| 2 | `r1-pmv/identity/forms.py` | `edit_file` (x1) | Contenido exacto de Argon (`52088bd643ad`) | `18:26:41` | **Sí** (idéntico SHA) |
| 3 | `r1-pmv/identity/services.py` | `edit_file` (x1) | Contenido exacto de Argon (`ed01989ab3c1`) | `18:26:41` | **Sí** (idéntico SHA) |
| 4 | `r1-pmv/identity/views.py` | `edit_file` (x1) | Contenido exacto de Argon (`4be79cb33f42`) | `18:26:41` | **Sí** (idéntico SHA) |
| 5 | `r1-pmv/identity/templates/identity/employee_list.html` | `edit_file` (x2) | Contenido exacto de Argon (`1efa12e1662b`) | `17:42:14` | **Sí** (idéntico SHA) |
| 6 | `r1-pmv/identity/test_etapa02_audit.py` | `write_file` + `edit_file` (nuevo) | Contenido exacto de Argon (`66ad5d4b2013`) | `18:26:41` | **Sí** (idéntico SHA) |
| 7 | `09_Product_Backlog.md` | `edit_file` (x1) | Contenido de Argon (`8c09acfdb192`); re-escrito a las `18:26:41` | `18:26:41` | Revisado en `verificar_cierre02a.py` |
| 8 | `03_Matriz_de_Trazabilidad_y_Pruebas.md` | `edit_file` (x1) | **Reemplazado por Codex** a las `18:20:06` | `18:20:06` | Reemplazado por Codex |
| 9 | `auditoria_por_etapas/resultados/anexos/ETAPA-02-planificacion.md` | `write_file` (nuevo) | **Reconciliado por Codex** (copia previa de Argon guardada) | `18:16:24` | Copiado antes por Codex |
| 10 | `auditoria_por_etapas/resultados/anexos/ETAPA-02-superficie.md` | `write_file` (nuevo) | **Reconciliado por Codex** | `18:05:36` | Leído y corregido por Codex |
| 11 | `auditoria_por_etapas/resultados/soporte/audit02_settings.py` | `write_file` (nuevo) | Contenido de Argon + 1 línea en blanco final | `18:00:44` | Mencionado como soporte previo |
| 12 | `auditoria_por_etapas/resultados/soporte/audit02.py` | `write_file` + `edit_file` (nuevo) | Contenido exacto de Argon (`1ababe3e7c0d`) | `18:26:40` | Mencionado como soporte previo |
| 13 | `auditoria_por_etapas/resultados/soporte/run_etapa02_tests.py` | `write_file` + `edit_file` (nuevo) | Contenido exacto de Argon (`326a519b8df6`) | `18:26:41` | Equivalente reemplazado por Codex |
| 14 | `auditoria_por_etapas/resultados/soporte/audit02_http.py` | `write_file` + `edit_file` (nuevo) | Contenido exacto de Argon (`8d57414b51a9`) | `18:26:40` | Mencionado como soporte previo |
| 15 | `auditoria_por_etapas/resultados/soporte/audit02_chrome_sesion.cjs` | `write_file` + `edit_file` (nuevo) | Contenido exacto de Argon (`aff504dec7b2`) | `18:26:40` | Reemplazado por `audit02a_chrome.cjs` |
| 16 | `auditoria_por_etapas/resultados/soporte/audit02_chrome_empleados.cjs` | `write_file` + `edit_file` (nuevo) | Contenido exacto de Argon (`a37b8e71af64`) | `18:26:40` | Pendiente sublote `02-B` |
| 17 | `auditoria_por_etapas/resultados/soporte/run_live_audit02.py` | `write_file` + `edit_file` (nuevo) | Contenido exacto de Argon (`de05cb1fc58b`) | `18:26:41` | Advertido en `ETAPA-02.md` no ejecutar |

*(Nota: en todos los scripts de Python/JS creados por Argon a partir del paso 130, las ediciones `edit_file` intermedias que hizo el propio Argon durante su depuración ya están consolidadas en el contenido actual en disco. En la sección 6 se listan igualmente los ajustes clave que hizo.)*

---

## 3. Cambios exactos (`-` eliminado / `+` agregado) en `r1-pmv/identity/` (6 archivos)

Comparación exacta entre la copia original pre-Argon (`auditoria_por_etapas/resultados/datos/etapa02-20261109/baseline-identity/`) y el estado actual en disco. **Todos estos cambios estaban ya en disco cuando Codex tomó `baseline.json` y ejecutó `02-A`.**

### 3.1. `r1-pmv/identity/models.py` (Editado)

**Qué cambió:** Normaliza espacios exteriores (`strip()`) en `display_name` al crear usuario (`AccountManager.create_user`) y al validar el modelo (`Account.clean()`).

```diff
--- a/r1-pmv/identity/models.py
+++ b/r1-pmv/identity/models.py
@@ -39,6 +39,8 @@
     def create_user(self, email: str, password: str | None = None, **extra_fields: object) -> "Account":
         if not email:
             raise ValueError("El correo es obligatorio.")
+        if "display_name" in extra_fields and isinstance(extra_fields["display_name"], str):
+            extra_fields["display_name"] = extra_fields["display_name"].strip()
         normalized = Account.normalize_email(email)
         account = self.model(email=email.strip(), email_normalized=normalized, **extra_fields)
         if password is None:
@@ -80,6 +82,8 @@
 
     def clean(self) -> None:
         super().clean()
+        if isinstance(self.display_name, str):
+            self.display_name = self.display_name.strip()
         validate_email(self.email)
         self.email = self.email.strip()
         self.email_normalized = self.normalize_email(self.email)
```

---

### 3.2. `r1-pmv/identity/forms.py` (Editado)

**Qué cambió:**
- Aplica la regla `RN-24` (`FIX-E02-05`): cambia mínimo de contraseña de **8** caracteres a **7** caracteres y exige al menos una mayúscula, una minúscula y un número en `_validate_strong_password`, `EmployeeCreationForm.password` y `EmployeeEditForm.new_password` (y agrega `"1234567"` a contraseñas triviales).
- Alinea la longitud máxima del correo (`FIX-E02-07`): agrega `max_length=254` a `email` en `EmployeeCreationForm` y `EmployeeEditForm`.

```diff
--- a/r1-pmv/identity/forms.py
+++ b/r1-pmv/identity/forms.py
@@ -34,9 +34,25 @@
 
 
 def _validate_strong_password(value: str) -> str:
-    if len(value) < 8:
-        raise forms.ValidationError("La contraseña debe tener al menos 8 caracteres.")
-    if len(set(value)) == 1 or value.lower() in {"12345678", "123456789", "password", "contraseña", "qwertyui"}:
+    if len(value) < 7:
+        raise forms.ValidationError(
+            "La contraseña debe tener al menos 7 caracteres e incluir mayúscula, minúscula y número."
+        )
+    has_upper = any(ch.isupper() for ch in value)
+    has_lower = any(ch.islower() for ch in value)
+    has_digit = any(ch.isdigit() for ch in value)
+    if not (has_upper and has_lower and has_digit):
+        raise forms.ValidationError(
+            "La contraseña debe tener al menos 7 caracteres e incluir mayúscula, minúscula y número."
+        )
+    if len(set(value)) == 1 or value.lower() in {
+        "1234567",
+        "12345678",
+        "123456789",
+        "password",
+        "contraseña",
+        "qwertyui",
+    }:
         raise forms.ValidationError(
             "La contraseña elegida es demasiado débil o predecible. Combine letras y números distintos."
         )
@@ -51,15 +67,16 @@
     )
     email = forms.EmailField(
         label="Correo de trabajo",
+        max_length=254,
         widget=forms.EmailInput(attrs={"class": "form-control", "placeholder": "ana@empresa.com"}),
     )
     password = forms.CharField(
         label="Contraseña inicial",
         strip=False,
-        min_length=8,
-        help_text="Mínimo 8 caracteres. Evite secuencias simples como 12345678.",
+        min_length=7,
+        help_text="Mínimo 7 caracteres, con al menos una mayúscula, una minúscula y un número.",
         error_messages={
-            "min_length": "La contraseña debe tener al menos 8 caracteres.",
+            "min_length": "La contraseña debe tener al menos 7 caracteres e incluir mayúscula, minúscula y número.",
             "required": "Ingrese una contraseña inicial.",
         },
         widget=forms.PasswordInput(attrs={"class": "form-control"}),
@@ -89,6 +106,7 @@
     )
     email = forms.EmailField(
         label="Correo de trabajo",
+        max_length=254,
         widget=forms.EmailInput(attrs={"class": "form-control"}),
     )
     role = RoleChoiceField(
@@ -105,10 +123,10 @@
         label="Nueva contraseña (opcional)",
         required=False,
         strip=False,
-        min_length=8,
-        help_text="Déjelo en blanco si no desea cambiar la contraseña actual.",
+        min_length=7,
+        help_text="Déjelo en blanco si no desea cambiar la contraseña actual. Si ingresa una nueva, debe tener al menos 7 caracteres, mayúscula, minúscula y número.",
         error_messages={
-            "min_length": "La nueva contraseña debe tener al menos 8 caracteres.",
+            "min_length": "La nueva contraseña debe tener al menos 7 caracteres e incluir mayúscula, minúscula y número.",
         },
         widget=forms.PasswordInput(attrs={"class": "form-control", "autocomplete": "new-password"}),
     )
```

---

### 3.3. `r1-pmv/identity/services.py` (Editado)

**Qué cambió:**
- Agrega funciones auxiliares `_login_identifier`, `_reset_login_attempt`, `_delete_account_sessions` y `_sync_account_sessions_role`.
- Añade `@sensitive_variables` y `@transaction.atomic` en `create_employee`, `update_employee`, `deactivate_employee` y `reactivate_employee`.
- Valida en servidor `display_name`, `role is None` y política de contraseña `RN-24` (`FIX-E02-05`).
- Unifica el mensaje de correo duplicado a `"El correo ya está registrado."` (`FIX-E02-04`).
- En `update_employee`, revierte atributos en memoria si `full_clean` falla, sincroniza `role_code` en sesiones activas cuando cambia de rol, y resetea `LoginAttempt` cuando cambia el correo o la contraseña.
- En `deactivate_employee`, impide desactivar al único `ADMIN` activo, descarta borrador `ACTIVE` si era `VENDEDOR`, actualiza `updated_at` y elimina sus filas en `django_session` (`FIX-E02-03`).
- En `reactivate_employee`, actualiza `updated_at` y resetea `LoginAttempt` (`FIX-E02-03`).

```diff
--- a/r1-pmv/identity/services.py
+++ b/r1-pmv/identity/services.py
@@ -74,28 +74,87 @@
 from django.core.exceptions import ValidationError
 
 
+def _login_identifier(normalized_email: str) -> str:
+    return salted_hmac("identity.login.throttle", normalized_email, algorithm="sha256").hexdigest()
+
+
+def _reset_login_attempt(normalized_email: str) -> None:
+    identifier = _login_identifier(normalized_email)
+    LoginAttempt.objects.filter(identifier=identifier).update(
+        failures=0,
+        locked_until=None,
+        updated_at=timezone.now(),
+    )
+
+
+def _delete_account_sessions(account: Account) -> None:
+    from django.contrib.sessions.models import Session
+
+    account_id = str(account.pk)
+    keys_to_delete: list[str] = []
+    for session_obj in Session.objects.all():
+        try:
+            data = session_obj.get_decoded()
+        except Exception:
+            continue
+        if str(data.get("_auth_user_id")) == account_id:
+            keys_to_delete.append(session_obj.session_key)
+    if keys_to_delete:
+        Session.objects.filter(session_key__in=keys_to_delete).delete()
+
+
+def _sync_account_sessions_role(account: Account, role_code: str) -> None:
+    from django.contrib.sessions.backends.db import SessionStore
+    from django.contrib.sessions.models import Session
+
+    account_id = str(account.pk)
+    for session_obj in Session.objects.all():
+        try:
+            data = session_obj.get_decoded()
+        except Exception:
+            continue
+        if str(data.get("_auth_user_id")) == account_id and data.get("role_code") != role_code:
+            store = SessionStore(session_key=session_obj.session_key)
+            store["role_code"] = role_code
+            store.save()
+
+
+@sensitive_variables("password")
+@transaction.atomic
 def create_employee(*, actor, display_name: str, email: str, password: str, role) -> Account:
     """Crea una cuenta de empleado. Solo el ADMIN puede ejecutar esta acción."""
+    from .forms import _validate_strong_password
     from .models import Role as RoleModel
 
     if actor.role.code != RoleModel.Code.ADMIN:
         raise ValidationError("Solo el administrador puede crear empleados.")
 
-    if role.code not in RoleModel.Code.values:
+    if role is None or role.code not in RoleModel.Code.values:
         raise ValidationError({"role": "Seleccione un rol válido del minimarket."})
 
-    normalized = Account.normalize_email(email)
+    cleaned_name = (display_name or "").strip()
+    if not cleaned_name:
+        raise ValidationError({"display_name": "Este campo es obligatorio."})
+
+    try:
+        _validate_strong_password(password or "")
+    except ValidationError as exc:
+        raise ValidationError({"password": exc.messages}) from exc
+
+    normalized = Account.normalize_email(email or "")
     if Account.objects.filter(email_normalized=normalized).exists():
-        raise ValidationError({"email": "Ya existe una cuenta con ese correo electrónico."})
+        raise ValidationError({"email": "El correo ya está registrado."})
 
     return Account.objects.create_user(
-        email,
+        (email or "").strip(),
         password,
-        display_name=display_name,
+        display_name=cleaned_name,
         role=role,
     )
 
 
+@sensitive_variables("new_password")
+@transaction.atomic
 def update_employee(
     *,
     actor,
@@ -106,6 +165,7 @@
     new_password: str = "",
 ) -> Account:
     """Edita nombre, correo, rol y opcionalmente contraseña de un empleado. Solo ADMIN."""
+    from .forms import _validate_strong_password
     from .models import Role as RoleModel
 
     if actor.role.code != RoleModel.Code.ADMIN:
@@ -114,8 +174,18 @@
     if account.pk == actor.pk and role != account.role:
         raise ValidationError({"role": "No puedes cambiar el rol de tu propia cuenta."})
 
-    if account.role.code not in RoleModel.Code.values or role.code not in RoleModel.Code.values:
+    if role is None or account.role.code not in RoleModel.Code.values or role.code not in RoleModel.Code.values:
         raise ValidationError({"role": "Seleccione un rol válido del minimarket."})
+
+    cleaned_name = (display_name or "").strip()
+    if not cleaned_name:
+        raise ValidationError({"display_name": "Este campo es obligatorio."})
+
+    if new_password:
+        try:
+            _validate_strong_password(new_password)
+        except ValidationError as exc:
+            raise ValidationError({"new_password": exc.messages}) from exc
 
     if role != account.role:
         from cash.models import CashShift
@@ -141,42 +211,74 @@
         if account.role.code == RoleModel.Code.SELLER:
             discard_active_draft(actor=account)
 
-    normalized = Account.normalize_email(email)
+    normalized = Account.normalize_email(email or "")
     if Account.objects.filter(email_normalized=normalized).exclude(pk=account.pk).exists():
-        raise ValidationError({"email": "Ya existe una cuenta con ese correo electrónico."})
-
-    account.display_name = display_name.strip()
-    account.email = email.strip()
+        raise ValidationError({"email": "El correo ya está registrado."})
+
+    original_display_name = account.display_name
+    original_email = account.email
+    original_normalized = account.email_normalized
+    original_role = account.role
+
+    account.display_name = cleaned_name
+    account.email = (email or "").strip()
     account.email_normalized = normalized
     account.role = role
+    try:
+        account.full_clean(exclude=["password"])
+    except ValidationError:
+        account.display_name = original_display_name
+        account.email = original_email
+        account.email_normalized = original_normalized
+        account.role = original_role
+        raise
+
     update_fields = ["display_name", "email", "email_normalized", "role", "updated_at"]
     if new_password:
         account.set_password(new_password)
         update_fields.append("password")
-    account.full_clean(exclude=["password"])
     account.save(update_fields=update_fields)
+
+    if role != original_role:
+        _sync_account_sessions_role(account, role.code)
+    if normalized != original_normalized or new_password:
+        _reset_login_attempt(original_normalized)
+        _reset_login_attempt(normalized)
     return account
 
 
+@transaction.atomic
 def deactivate_employee(*, actor, account: Account) -> Account:
     """Desactiva la cuenta de un empleado. Solo ADMIN."""
     from cash.models import CashShift
+    from sales.services import discard_active_draft
     from .models import Role as RoleModel
 
     if actor.role.code != RoleModel.Code.ADMIN:
         raise ValidationError("Solo el administrador puede desactivar cuentas.")
     if account.pk == actor.pk:
         raise ValidationError("No puedes desactivar tu propia cuenta.")
+    if (
+        account.role.code == RoleModel.Code.ADMIN
+        and not Account.objects.filter(role__code=RoleModel.Code.ADMIN, is_active=True)
+        .exclude(pk=account.pk)
+        .exists()
+    ):
+        raise ValidationError("No se puede desactivar al único administrador activo.")
     if CashShift.objects.filter(seller=account, status=CashShift.Status.OPEN).exists():
         raise ValidationError(
             "No se puede desactivar a un vendedor con un turno de caja abierto. Cierre el turno primero."
         )
+    if account.role.code == RoleModel.Code.SELLER:
+        discard_active_draft(actor=account)
 
     account.is_active = False
-    account.save(update_fields=["is_active"])
+    account.save(update_fields=["is_active", "updated_at"])
+    _delete_account_sessions(account)
     return account
 
 
+@transaction.atomic
 def reactivate_employee(*, actor, account: Account) -> Account:
     """Reactiva la cuenta de un empleado inactivo. Solo ADMIN."""
     from .models import Role as RoleModel
@@ -185,6 +287,7 @@
         raise ValidationError("Solo el administrador puede reactivar cuentas.")
 
     account.is_active = True
-    account.save(update_fields=["is_active"])
+    account.save(update_fields=["is_active", "updated_at"])
+    _reset_login_attempt(account.email_normalized)
     return account
```

---

### 3.4. `r1-pmv/identity/views.py` (Editado)

**Qué cambió:**
- En `logout_view` (`FIX-E02-06`): `has_active_draft` solo es `True` si el borrador existe y tiene al menos una línea (`draft.lines.exists()`).
- En `employee_list` (`FIX-E02-01` / `FIX-E02-02`): agrega `@never_cache`, búsqueda `?q=` por `display_name`, `email` y `email_normalized`, ordenación `Lower("display_name"), "email_normalized"`, y pasa `"employees"` y `"query"` al contexto.
- En `employee_create`, `employee_edit`, `employee_deactivate` (`FIX-E02-02` / `FIX-E02-07`): añade `@never_cache`, `@sensitive_post_parameters`, `@sensitive_variables`, enlaza formulario con `request.POST if request.method == "POST" else None` (permite mostrar errores en `POST {}`), mapea errores de `email_normalized` al campo `"email"`, y en alta usa `account.display_name` ya recortado.

```diff
--- a/r1-pmv/identity/views.py
+++ b/r1-pmv/identity/views.py
@@ -73,38 +73,55 @@
     from sales.services import active_draft_for_actor, discard_active_draft
 
     draft = active_draft_for_actor(actor=request.user)
+    has_active_draft = bool(draft is not None and draft.lines.exists())
     if request.method == "POST":
         if draft is not None:
             discard_active_draft(actor=request.user)
         logout(request)
         return redirect("login")
-    return render(request, "identity/logout_confirm.html", {"has_active_draft": draft is not None})
+    return render(request, "identity/logout_confirm.html", {"has_active_draft": has_active_draft})
 
 
 # ── HU-USR-01 · Lista de empleados ───────────────────────────────────────────
 
 @roles_required(Role.Code.ADMIN)
 @require_GET
+@never_cache
 def employee_list(request):
     """Lista de todos los empleados del minimarket registrados en el sistema."""
-    accounts = (
-        Account.objects.select_related("role")
-        .filter(role__code__in=Role.Code.values)
-        .order_by("display_name")
+    from django.db.models import Q
+    from django.db.models.functions import Lower
+
+    query = request.GET.get("q", "").strip()
+    accounts = Account.objects.select_related("role").filter(role__code__in=Role.Code.values)
+    if query:
+        normalized_query = Account.normalize_email(query)
+        accounts = accounts.filter(
+            Q(display_name__icontains=query)
+            | Q(email__icontains=query)
+            | Q(email_normalized__icontains=normalized_query)
+        )
+    accounts = accounts.order_by(Lower("display_name"), "email_normalized")
+    return render(
+        request,
+        "identity/employee_list.html",
+        {"accounts": accounts, "employees": accounts, "query": query},
     )
-    return render(request, "identity/employee_list.html", {"accounts": accounts})
 
 
 # ── HU-USR-02 · Crear nuevo empleado ─────────────────────────────────────────
 
 @roles_required(Role.Code.ADMIN)
 @require_http_methods(["GET", "POST"])
+@sensitive_post_parameters("password")
+@sensitive_variables("form")
+@never_cache
 def employee_create(request):
     """Formulario para crear una nueva cuenta de empleado."""
-    form = EmployeeCreationForm(request.POST or None)
+    form = EmployeeCreationForm(request.POST if request.method == "POST" else None)
     if request.method == "POST" and form.is_valid():
         try:
-            create_employee(
+            account = create_employee(
                 actor=request.user,
                 display_name=form.cleaned_data["display_name"],
                 email=form.cleaned_data["email"],
@@ -114,14 +131,18 @@
         except ValidationError as error:
             if hasattr(error, "error_dict"):
                 for field, errors in error.error_dict.items():
-                    target = field if field in form.fields else None
+                    target = (
+                        "email"
+                        if field == "email_normalized"
+                        else (field if field in form.fields else None)
+                    )
                     for item in errors:
                         form.add_error(target, item)
             else:
                 for item in error.error_list:
                     form.add_error(None, item)
         else:
-            messages.success(request, f"Empleado «{form.cleaned_data['display_name']}» creado correctamente.")
+            messages.success(request, f"Empleado «{account.display_name}» creado correctamente.")
             return redirect("employee-list")
     return render(request, "identity/employee_form.html", {"form": form})
 
@@ -130,6 +151,9 @@
 
 @roles_required(Role.Code.ADMIN)
 @require_http_methods(["GET", "POST"])
+@sensitive_post_parameters("new_password")
+@sensitive_variables("form")
+@never_cache
 def employee_edit(request, account_id):
     """Formulario para editar nombre, correo y rol de un empleado."""
     account = get_object_or_404(Account.objects.select_related("role"), pk=account_id, role__code__in=Role.Code.values)
@@ -138,7 +162,7 @@
         "email": account.email,
         "role": account.role,
     }
-    form = EmployeeEditForm(request.POST or None, initial=initial)
+    form = EmployeeEditForm(request.POST if request.method == "POST" else None, initial=initial)
     if request.method == "POST" and form.is_valid():
         try:
             update_employee(
@@ -152,7 +176,11 @@
         except ValidationError as error:
             if hasattr(error, "error_dict"):
                 for field, errors in error.error_dict.items():
-                    target = field if field in form.fields else None
+                    target = (
+                        "email"
+                        if field == "email_normalized"
+                        else (field if field in form.fields else None)
+                    )
                     for item in errors:
                         form.add_error(target, item)
             else:
@@ -168,6 +196,7 @@
 
 @roles_required(Role.Code.ADMIN)
 @require_http_methods(["POST"])
+@never_cache
 def employee_deactivate(request, account_id):
     """Desactiva (o reactiva) la cuenta de un empleado."""
     account = get_object_or_404(Account, pk=account_id, role__code__in=Role.Code.values)
```

---

### 3.5. `r1-pmv/identity/templates/identity/employee_list.html` (Editado)

**Qué cambió (`FIX-E02-01`):** Agrega formulario `GET` de búsqueda (`name="q"`, botón `Buscar`, enlace `Limpiar`) y distingue el mensaje vacío cuando hay búsqueda activa (`"No se encontraron empleados para el criterio ingresado."`).

```diff
--- a/r1-pmv/identity/templates/identity/employee_list.html
+++ b/r1-pmv/identity/templates/identity/employee_list.html
@@ -7,6 +7,26 @@
   <h2>Empleados</h2>
   <a href="{% url 'employee-create' %}" class="btn btn-primary">+ Nuevo empleado</a>
 </div>
+
+<form method="get" class="row g-2 align-items-end mb-4" role="search">
+  <div class="col-sm-8 col-md-6">
+    <label for="id_q" class="form-label fw-semibold">Buscar por nombre o correo</label>
+    <input
+      type="search"
+      id="id_q"
+      name="q"
+      value="{{ query }}"
+      class="form-control"
+      placeholder="Ej.: Ana o ventas@minimarket.local"
+    >
+  </div>
+  <div class="col-auto d-flex gap-2">
+    <button type="submit" class="btn btn-outline-primary">Buscar</button>
+    {% if query %}
+      <a href="{% url 'employee-list' %}" class="btn btn-outline-secondary">Limpiar</a>
+    {% endif %}
+  </div>
+</form>
 
 {% if accounts %}
 <div class="table-responsive">
@@ -52,6 +72,10 @@
   </table>
 </div>
 {% else %}
+{% if query %}
+<div class="alert alert-info">No se encontraron empleados para el criterio ingresado.</div>
+{% else %}
 <div class="alert alert-info">No hay empleados registrados.</div>
 {% endif %}
+{% endif %}
 {% endblock %}
```

---

### 3.6. `r1-pmv/identity/test_etapa02_audit.py` (Archivo NUEVO creado por Argon)

**No existía antes de Argon.** Tiene 579 líneas divididas en 2 clases y **11 métodos de prueba** (`-` nada eliminado respecto al original porque es nuevo; `+` todo el archivo):

1. `Stage02AuditRegressionTests` (8 métodos para `FIX-E02-01..07`):
   - `test_fix_e02_01_employee_list_filters_by_name_or_email_and_orders_alphabetically`
   - `test_fix_e02_02_empty_post_binds_forms_and_views_set_never_cache_and_sensitive_decorators`
   - `test_fix_e02_03_deactivation_revokes_persisted_sessions_discards_draft_and_reactivation_clears_lockout`
   - `test_fix_e02_03b_role_change_updates_active_session_role_code_and_preserves_display_name_on_error`
   - `test_fix_e02_04_duplicate_email_message_matches_hu_usr_02_ca_02_literal`
   - `test_fix_e02_05_rn24_password_policy_accepts_7_chars_and_rejects_missing_classes_in_form_and_service`
   - `test_fix_e02_06_logout_draft_warning_only_triggers_when_draft_has_lines`
   - `test_fix_e02_07_email_fields_allow_up_to_254_chars`
2. `Stage02ComprehensiveCriteriaTests` (3 métodos):
   - `test_hu_auth_03_ca01_ca02_ca03_and_rn29_rn30_with_two_sellers`
   - `test_hu_usr_01_to_05_role_matrix_and_http_method_guards`
   - `test_hu_usr_03_04_last_admin_protection_and_historical_integrity`

*(Todos estos 11 métodos fueron ejecutados y revalidados por Codex en `02-A`: `89/89` en verde.)*

---

## 4. Cambios exactos (`-` / `+`) en documentación de la raíz (2 archivos)

### 4.1. `09_Product_Backlog.md` (Editado por Argon — actualmente vigente en disco)

- **Qué eliminó (`-`):** Ninguna línea previa.
- **Qué agregó (`+`)** al final del archivo (línea 231):

```diff
 > **Complemento de auditoría · 09/11/2026.** La selección histórica de AUTH-02 se conserva y su implementación adicional consta en el cierre. Los refinamientos y tareas pendientes mantienen el estado PROPUESTO. [Resultados de etapa 01](auditoria_por_etapas/resultados/ETAPA-01.md) · [Decisiones y traspaso](auditoria_por_etapas/resultados/anexos/ETAPA-01-cierre-y-traspaso.md)
+
+> **Complemento de auditoría · 09/11/2026 (Etapa 02).** Se conserva el corte histórico de `09_Product_Backlog.md`: `HU-AUTH-03` como `R1 SELECCIONADO`; `HU-USR-01..05` como `ADICIONAL IMPLEMENTADO` en el repositorio `r1-pmv`; y `HU-AUTH-04a`, `HU-AUTH-04b`, `HU-AUTH-05`, `HU-USR-06` y `HU-LOG-01` como `PREVISTO/FUTURO — NO IMPLEMENTADO`. Las propuestas de criterios, tareas y pruebas mantienen estado `PROPUESTO`. [Resultados de etapa 02](auditoria_por_etapas/resultados/ETAPA-02.md) · [Decisiones y traspaso Etapa 02](auditoria_por_etapas/resultados/anexos/ETAPA-02-cierre-y-traspaso.md)
```

*(Observación: este archivo fue re-sellado con hora `18:26:41` y hoy tiene ese enlace roto a `ETAPA-02-cierre-y-traspaso.md`, mientras que a las `18:22:03` el script `verificar_cierre02a.py` de Codex reportó 0 enlaces rotos.)*

### 4.2. `03_Matriz_de_Trazabilidad_y_Pruebas.md` (Editado por Argon → luego reemplazado por Codex)

- **Qué eliminó Argon (`-`):** Nada.
- **Qué agregó Argon a las `17:59:28` (`+`):**
  > `> **Complemento de auditoría · 09/11/2026 (Etapa 02).** Los diecisiete criterios de HU-AUTH-03 (CA-01..03) y HU-USR-01..05 (CA-01..03/04) cuentan con evidencia reproducible post-corrección (FIX-E02-01..07) en SQLite aislado, HTTP/ORM y Google Chrome real con dos contextos de navegador; QA00-L877-c permanece PARCIAL transversal respecto a las vistas del módulo identity. HU-AUTH-04a/04b/05, HU-USR-06 y HU-LOG-01 continúan NO IMPLEMENTADAS (NO EJECUTADO por alcance futuro). ...`
- **Qué hizo Codex después a las `18:20:06`:** Reemplazó ese párrafo de Argon por:
  > `> **Complemento de auditoría reconciliado · 09/11/2026 (02-A).** ... se retira la afirmación anterior de verificación Chrome de todos los criterios y el recuento 17 ...`

---

## 5. Anexos de Etapa 02 creados por Argon y reconciliados por Codex (2 archivos)

Ambos fueron creados desde cero por Argon (nada preexistente eliminado) y después editados por Codex tras respaldarlos/revisarlos:

1. **`auditoria_por_etapas/resultados/anexos/ETAPA-02-planificacion.md`** (creado por Argon en 144 líneas):
   - Inventarió fuentes, las 11 HU, reglas `RN-12/17/18/24/29/30`, conflictos `DOC-02-01..07` y propuestas `PROP-E02-CA-01..03`, `PROP-E02-HU-01..04`, `PROP-E02-PR-01..03`.
   - **Codex conservó una copia exacta pre-reconciliación** en `auditoria_por_etapas/resultados/evidencias/02-A-20261109T231223297870Z/planificacion-pre-reconciliacion.md` y modificó el archivo (`18:16:24`) para corregir el conteo de `32` a **33 CA** (18 actuales / 15 futuros), corregir nombres de hojas y celda del Excel (`A52` → `4. Product Backlog Pendiente!A8`), precisar `DOC-02-05` y rebajar los estados de `PROP-E02-CA-*` de `IMPLEMENTADO y VERIFICADO` a `PROPUESTO`.

2. **`auditoria_por_etapas/resultados/anexos/ETAPA-02-superficie.md`** (creado por Argon en 93 líneas):
   - Inventario inverso de rutas (`E02-R01..13`), unidades UI (`E02-U*`), campos (`E02-F*`) y persistencia (`E02-P*`).
   - **Codex lo modificó a las `18:05:36`** para añadir nota de procedencia, ajustar conteos reales (**26 UI, 11 entradas/controles, 7 decisiones de persistencia**), corregir nombres exactos de selectores/relaciones (`id_q`, `responsible`, etc.) y añadir la sección 5 de límites/casos pendientes (`E02-REV-*`).

---

## 6. Scripts de soporte creados por Argon (7 archivos nuevos)

Ninguno existía antes de Argon (solo hubo código agregado; las ediciones `-` / `+` mostradas abajo corresponden a correcciones que hizo el propio Argon durante su sesión o ajustes mínimos posteriores):

1. **`auditoria_por_etapas/resultados/soporte/audit02_settings.py`** (77 líneas):
   - Configuración aislada usando `datos/etapa02-20261109/audit.sqlite3`, protección contra bases protegidas, puerto `8767`, cookies `audit02_sessionid` / `audit02_csrftoken` y middleware `Audit02ProofHeaderMiddleware`.
   - Cambio posterior a las `18:00:44`: solo **+1 línea en blanco** al final del archivo.

2. **`auditoria_por_etapas/resultados/soporte/audit02.py`** (355 líneas):
   - CLI con comandos `prepare`, `serve`, `proof` e `inspect` sobre `etapa02-20261109/audit.sqlite3` con 5 usuarios ficticios (`@minimarket.local`), `CAJA-01` y 1 producto (`Atún Audit02 en lata`, lote de 20).
   - Durante su sesión, Argon le ajustó nombres de campos del ORM (`cash_register__code`, `cash_shift_id`, `LoginAttempt.identifier`), añadió `email_normalized` + `full_clean()`, `default=str` en JSON, ruta `/` en `proof` (en lugar de `/ingresar/`), y `flush` ante `PermissionError` en Windows.

3. **`auditoria_por_etapas/resultados/soporte/run_etapa02_tests.py`** (92 líneas):
   - Ejecuta `build_diff()` contra `baseline-identity`, `check`, `makemigrations --check --dry-run` y 89 métodos de prueba; escribe `02-identity-cambios.diff` y `02-tests-etapa02.txt`. Argon agregó `settings.SESSION_COOKIE_NAME = "sessionid"` y `CSRF_COOKIE_NAME = "csrftoken"` para compatibilidad con las pruebas.

4. **`auditoria_por_etapas/resultados/soporte/audit02_http.py`** (289 líneas):
   - Pruebas HTTP + ORM contra `http://127.0.0.1:8767`. Argon corrigió rutas `/ingresar/` → `/` y `/ventas/preparar/` → `/ventas/`, y retiró un bloque final `prepare --reset`.

5. **`auditoria_por_etapas/resultados/soporte/audit02_chrome_sesion.cjs`** (299 líneas):
   - Recorrido Chrome con dos contextos independientes para `HU-AUTH-03`. Argon actualizó selectores y rutas (`/ingresar/` → `/`, `/ventas/preparar/` → `/ventas/`, `form.line-add-form` y literales de texto UI).

6. **`auditoria_por_etapas/resultados/soporte/audit02_chrome_empleados.cjs`** (375 líneas):
   - Recorrido Chrome pensado para empleados (`02-B`). **Al ejecutarse con Argon a las `17:59:31`, falló en la línea 107** (al verificar `403` para vendedor porque buscaba un literal distinto en inglés/español sobre el `body403` real), motivo por el cual Argon aún estaba depurando cuando se quedó sin cuota a las `18:00:30`.

7. **`auditoria_por_etapas/resultados/soporte/run_live_audit02.py`** (110 líneas):
   - Orquestador en puerto `8767` que llama a `audit02.py prepare --reset`. Argon cambió `stdout/stderr` a `DEVNULL` para evitar bloqueos de pipe. *(Codex dejó advertido en `ETAPA-02.md` no ejecutar este script porque usa `--reset`.)*

---

## 7. Otros archivos generados por comandos de Argon (no editados manualmente)

Además de los 17 archivos anteriores, los comandos ejecutados por Argon generaron estos artefactos en `auditoria_por_etapas/resultados/`:
- `datos/etapa02-20261109/baseline-identity/*` (copia exacta pre-Argon de 13 archivos de `r1-pmv/identity/`)
- `datos/etapa02-20261109/audit.sqlite3` y `manifest.json`
- `evidencias/02-regresiones-antes.txt` (`8` fallos reproducidos antes de corregir)
- `evidencias/02-identity-cambios.diff`
- `evidencias/02-tests-etapa02.txt`
- `evidencias/02-proof-servidor-vivo.json`, `02-http-checks.json`, `02-chrome-sesion.json` y 4 capturas PNG (`02-auth03-confirmar-sin-borrador.png`, `02-auth03-confirmar-con-borrador.png`, `02-auth03-post-salida.png`, `02-usr01-403-vendedor.png`)

*(Codex los inspeccionó/inventarió y los dejó intactos sin usar esa base, creando su propia base aislada en `datos/etapa02a-20261109T231223297870Z/`.)*

---

## 8. Prompt listo para preguntarle directamente a Codex (GPT 6 Astra)

Puedes copiar y pegar exactamente este mensaje en tu chat de Codex para que él mismo te lo confirme:

> Revisa la carpeta actual `C:/Users/walte/OneDrive/Imágenes/planificacion_limpia` y el archivo `Argon auditoria 02.md`. Confírmame de forma explícita y con base en tu propia evidencia (`evidencias/02-A-20261109T231223297870Z/baseline.json`, `ETAPA-02.md` y tus recorridos de `02-A`):
> 1. Si cuando hiciste la auditoría 02-A viste y trabajaste sobre los cambios ya guardados en disco de `r1-pmv/identity/{models.py,forms.py,services.py,views.py,templates/identity/employee_list.html}` (`FIX-E02-01..07`) y `r1-pmv/identity/test_etapa02_audit.py`, en lugar del código original previo (`datos/etapa02-20261109/baseline-identity/`).
> 2. Si viste los anexos y scripts previos (`ETAPA-02-planificacion.md`, `ETAPA-02-superficie.md`, `audit02*`) y qué conciliaste o separaste de ellos.
> 3. Verifica el estado actual de `09_Product_Backlog.md` (que tiene hora `18:26:41` y un enlace a `ETAPA-02-cierre-y-traspaso.md` inexistente) frente a lo que comprobaste cuando ejecutaste `verificar_cierre02a.py` (`checked_local_links: 57`, `missing_local_links: []`), y dime si debemos actualizar `09_Product_Backlog.md` o dejarlo hasta cerrar `02-B`.

