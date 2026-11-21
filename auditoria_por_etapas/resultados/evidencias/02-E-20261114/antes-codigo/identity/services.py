"""Identity services keep authentication decisions on the server."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from math import ceil

from django.contrib.auth import login
from django.contrib.auth.hashers import check_password
from django.db import IntegrityError, transaction
from django.http import HttpRequest
from django.utils import timezone
from django.utils.crypto import salted_hmac
from django.views.decorators.debug import sensitive_variables

from .models import Account, LoginAttempt, Role

INVALID_CREDENTIALS_MESSAGE = "Correo o contraseña incorrectos"


@dataclass(frozen=True)
class AuthenticationResult:
    account: Account | None
    locked_minutes: int = 0

    @property
    def authenticated(self) -> bool:
        return self.account is not None


@sensitive_variables()
@transaction.atomic
def authenticate_active_account(email: str, password: str) -> AuthenticationResult:
    """Apply the same persistent lockout to existing and unknown identifiers."""
    normalized = Account.normalize_email(email)
    identifier = salted_hmac("identity.login.throttle", normalized, algorithm="sha256").hexdigest()
    LoginAttempt.objects.get_or_create(identifier=identifier)
    attempt = LoginAttempt.objects.select_for_update().get(identifier=identifier)
    account = Account.objects.select_related("role").filter(email_normalized=normalized).first()
    if account is None:
        # Perform comparable password work without storing the submitted password.
        Account().set_password(password)
        valid_password = False
    else:
        valid_password = check_password(password, account.password)
    now = timezone.now()
    if attempt.locked_until and attempt.locked_until > now:
        return AuthenticationResult(None, max(1, ceil((attempt.locked_until - now).total_seconds() / 60)))
    if attempt.locked_until:
        attempt.failures = 0
        attempt.locked_until = None
    if account is not None and account.is_active and valid_password and account.role.code in Role.Code.values:
        # Keep the row stable for concurrent requests that have just found it
        # and are waiting to acquire its lock. Removing it here can make their
        # subsequent select_for_update().get() fail with DoesNotExist.
        attempt.failures = 0
        attempt.save(update_fields=("failures", "locked_until", "updated_at"))
        return AuthenticationResult(account)
    attempt.failures += 1
    if attempt.failures >= 5:
        attempt.locked_until = now + timedelta(minutes=15)
    attempt.save()
    return AuthenticationResult(None, 15 if attempt.locked_until else 0)


def create_server_session(request: HttpRequest, account: Account) -> None:
    """Rotate the session id and store only server-side identity context."""
    login(request, account, backend="django.contrib.auth.backends.ModelBackend")
    request.session["role_code"] = account.role.code


# ── Gestión de empleados ──────────────────────────────────────────────────────

from django.core.exceptions import ValidationError


def _lock_employee_administration(actor, action: str) -> None:
    """Serialize employee mutations, then revalidate the actor under that lock.

    All employee management services take the same ADMIN role row first. This
    serializes last-admin decisions and makes role/activity checks current.
    """
    Role.objects.select_for_update().get(code=Role.Code.ADMIN)
    actor.refresh_from_db()
    if not actor.is_active or actor.role.code != Role.Code.ADMIN:
        raise ValidationError(f"Solo el administrador activo puede {action} cuentas.")


def _lock_employee(account: Account) -> None:
    """Lock and refresh the supplied object without breaking the caller's reference."""
    Account.objects.select_for_update().get(pk=account.pk)
    account.refresh_from_db()


def _login_identifier(normalized_email: str) -> str:
    return salted_hmac("identity.login.throttle", normalized_email, algorithm="sha256").hexdigest()


def _reset_login_attempt(normalized_email: str) -> None:
    identifier = _login_identifier(normalized_email)
    LoginAttempt.objects.filter(identifier=identifier).update(
        failures=0,
        locked_until=None,
        updated_at=timezone.now(),
    )


def _delete_account_sessions(account: Account) -> None:
    from django.contrib.sessions.models import Session

    account_id = str(account.pk)
    keys_to_delete: list[str] = []
    for session_obj in Session.objects.all():
        try:
            data = session_obj.get_decoded()
        except Exception:
            continue
        if str(data.get("_auth_user_id")) == account_id:
            keys_to_delete.append(session_obj.session_key)
    if keys_to_delete:
        Session.objects.filter(session_key__in=keys_to_delete).delete()


def _sync_account_sessions_role(account: Account, role_code: str) -> None:
    from django.contrib.sessions.backends.db import SessionStore
    from django.contrib.sessions.models import Session

    account_id = str(account.pk)
    for session_obj in Session.objects.all():
        try:
            data = session_obj.get_decoded()
        except Exception:
            continue
        if str(data.get("_auth_user_id")) == account_id and data.get("role_code") != role_code:
            store = SessionStore(session_key=session_obj.session_key)
            store["role_code"] = role_code
            store.save()


@sensitive_variables("password")
@transaction.atomic
def create_employee(*, actor, display_name: str, email: str, password: str, role) -> Account:
    """Crea una cuenta de empleado. Solo el ADMIN puede ejecutar esta acción."""
    from .forms import _validate_strong_password
    from .models import Role as RoleModel

    _lock_employee_administration(actor, "crear")

    if role is None or role.code not in RoleModel.Code.values:
        raise ValidationError({"role": "Seleccione un rol válido del minimarket."})

    cleaned_name = (display_name or "").strip()
    if not cleaned_name:
        raise ValidationError({"display_name": "Este campo es obligatorio."})

    try:
        _validate_strong_password(password or "")
    except ValidationError as exc:
        raise ValidationError({"password": exc.messages}) from exc

    normalized = Account.normalize_email(email or "")
    if Account.objects.filter(email_normalized=normalized).exists():
        raise ValidationError({"email": "El correo ya está registrado."})

    try:
        with transaction.atomic():
            return Account.objects.create_user(
                (email or "").strip(), password, display_name=cleaned_name, role=role,
            )
    except IntegrityError:
        if Account.objects.filter(email_normalized=normalized).exists():
            raise ValidationError({"email": "El correo ya está registrado."}) from None
        raise


@sensitive_variables("new_password")
@transaction.atomic
def update_employee(
    *,
    actor,
    account: Account,
    display_name: str,
    email: str,
    role,
    new_password: str = "",
) -> Account:
    """Edita nombre, correo, rol y opcionalmente contraseña de un empleado. Solo ADMIN."""
    from .forms import _validate_strong_password
    from .models import Role as RoleModel

    _lock_employee_administration(actor, "editar")
    _lock_employee(account)

    if account.pk == actor.pk and role != account.role:
        raise ValidationError({"role": "No puedes cambiar el rol de tu propia cuenta."})

    if role is None or account.role.code not in RoleModel.Code.values or role.code not in RoleModel.Code.values:
        raise ValidationError({"role": "Seleccione un rol válido del minimarket."})

    cleaned_name = (display_name or "").strip()
    if not cleaned_name:
        raise ValidationError({"display_name": "Este campo es obligatorio."})

    if new_password:
        try:
            _validate_strong_password(new_password)
        except ValidationError as exc:
            raise ValidationError({"new_password": exc.messages}) from exc

    if role != account.role:
        from cash.models import CashShift
        from sales.services import discard_active_draft

        if CashShift.objects.filter(seller=account, status=CashShift.Status.OPEN).exists():
            raise ValidationError(
                {
                    "role": (
                        "No se puede cambiar el rol de un empleado con un turno de caja abierto. "
                        "Cierre el turno primero."
                    )
                }
            )
        if (
            account.role.code == RoleModel.Code.ADMIN
            and role.code != RoleModel.Code.ADMIN
            and not Account.objects.filter(role__code=RoleModel.Code.ADMIN, is_active=True)
            .exclude(pk=account.pk)
            .exists()
        ):
            raise ValidationError({"role": "No se puede cambiar el rol del único administrador activo."})
        if account.role.code == RoleModel.Code.SELLER:
            discard_active_draft(actor=account)

    normalized = Account.normalize_email(email or "")
    if Account.objects.filter(email_normalized=normalized).exclude(pk=account.pk).exists():
        raise ValidationError({"email": "El correo ya está registrado."})

    original_display_name = account.display_name
    original_email = account.email
    original_normalized = account.email_normalized
    original_role = account.role

    account.display_name = cleaned_name
    account.email = (email or "").strip()
    account.email_normalized = normalized
    account.role = role
    try:
        account.full_clean(exclude=["password"])
    except ValidationError:
        account.display_name = original_display_name
        account.email = original_email
        account.email_normalized = original_normalized
        account.role = original_role
        raise

    update_fields = ["display_name", "email", "email_normalized", "role", "updated_at"]
    if new_password:
        account.set_password(new_password)
        update_fields.append("password")
    try:
        with transaction.atomic():
            account.save(update_fields=update_fields)
    except IntegrityError:
        account.display_name = original_display_name
        account.email = original_email
        account.email_normalized = original_normalized
        account.role = original_role
        if Account.objects.filter(email_normalized=normalized).exclude(pk=account.pk).exists():
            raise ValidationError({"email": "El correo ya está registrado."}) from None
        raise

    if role != original_role:
        _sync_account_sessions_role(account, role.code)
    if normalized != original_normalized or new_password:
        _reset_login_attempt(original_normalized)
        _reset_login_attempt(normalized)
    return account


@transaction.atomic
def deactivate_employee(*, actor, account: Account) -> Account:
    """Desactiva la cuenta de un empleado. Solo ADMIN."""
    from cash.models import CashShift
    from sales.services import discard_active_draft
    from .models import Role as RoleModel

    _lock_employee_administration(actor, "desactivar")
    _lock_employee(account)
    if account.pk == actor.pk:
        raise ValidationError("No puedes desactivar tu propia cuenta.")
    if (
        account.role.code == RoleModel.Code.ADMIN
        and not Account.objects.filter(role__code=RoleModel.Code.ADMIN, is_active=True)
        .exclude(pk=account.pk)
        .exists()
    ):
        raise ValidationError("No se puede desactivar al único administrador activo.")
    if CashShift.objects.filter(seller=account, status=CashShift.Status.OPEN).exists():
        raise ValidationError(
            "No se puede desactivar a un vendedor con un turno de caja abierto. Cierre el turno primero."
        )
    if account.role.code == RoleModel.Code.SELLER:
        discard_active_draft(actor=account)

    account.is_active = False
    account.save(update_fields=["is_active", "updated_at"])
    _delete_account_sessions(account)
    return account


@transaction.atomic
def reactivate_employee(*, actor, account: Account) -> Account:
    """Reactiva la cuenta de un empleado inactivo. Solo ADMIN."""
    from .models import Role as RoleModel

    _lock_employee_administration(actor, "reactivar")
    _lock_employee(account)

    account.is_active = True
    account.save(update_fields=["is_active", "updated_at"])
    _reset_login_attempt(account.email_normalized)
    return account

