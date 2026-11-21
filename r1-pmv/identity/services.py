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


def _record_login_rejection(*, account, normalized, action, outcome, metadata) -> None:
    """Persist a rejection, with a sanitized diagnostic if persistence fails."""
    from .audit import record_transactional_event, safe_record_rejection_event

    event = {
        "actor": account,
        "actor_identifier": normalized,
        "action": action,
        "target_type": "Account",
        "target_id": str(account.pk) if account is not None else "",
        "outcome": outcome,
    }
    try:
        # Isolate an audit insert failure from the lockout transaction.
        with transaction.atomic():
            record_transactional_event(**event, metadata=metadata)
    except Exception as exc:
        try:
            safe_record_rejection_event(
                **event,
                metadata={**metadata, "audit_persist_error": type(exc).__name__},
                persist_db=False,
            )
        except Exception:
            # Logging must never grant access or discard the lockout decision.
            pass


@sensitive_variables()
@transaction.atomic
def authenticate_active_account(email: str, password: str) -> AuthenticationResult:
    """Apply the same persistent lockout to existing and unknown identifiers."""
    from .models import IdentityAuditEvent

    normalized = Account.normalize_email(email)
    identifier = salted_hmac("identity.login.throttle", normalized, algorithm="sha256").hexdigest()
    # Personnel changes lock the account before changing its login attempts.
    account = (
        Account.objects.select_for_update()
        .filter(email_normalized=normalized).first()
    )
    LoginAttempt.objects.get_or_create(identifier=identifier)
    attempt = LoginAttempt.objects.select_for_update().get(identifier=identifier)
    now = timezone.now()
    if attempt.locked_until and attempt.locked_until > now:
        minutes = max(1, ceil((attempt.locked_until - now).total_seconds() / 60))
        _record_login_rejection(
            account=account, normalized=normalized, action="LOGIN_LOCKED",
            outcome=IdentityAuditEvent.Outcome.LOCKED,
            metadata={"locked_minutes": minutes, "failures": attempt.failures, "already_locked": True},
        )
        return AuthenticationResult(None, minutes)
    if attempt.locked_until:
        attempt.failures = 0
        attempt.locked_until = None
    if account is None:
        # Match password work for unknown and known identities when unlocked.
        Account().set_password(password)
        valid_password = False
    else:
        valid_password = check_password(password, account.password)
    # The fifth failure starts a full 15-minute block after password checking.
    now = timezone.now()
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
    locked_now = bool(attempt.locked_until)
    _record_login_rejection(
        account=account, normalized=normalized,
        action="LOGIN_LOCKED" if locked_now else "LOGIN_FAILED",
        outcome=IdentityAuditEvent.Outcome.LOCKED if locked_now else IdentityAuditEvent.Outcome.REJECTED,
        metadata={
            "failures": attempt.failures,
            "locked_minutes": 15 if locked_now else 0,
            "account_exists": account is not None,
            "account_active": bool(account.is_active) if account is not None else False,
        },
    )
    return AuthenticationResult(None, 15 if locked_now else 0)


def create_server_session(request: HttpRequest, account: Account) -> None:
    """Rotate the session id, store server-side context, and record commit-bound login audit."""
    from .audit import record_transactional_event
    from .models import IdentityAuditEvent

    with transaction.atomic():
        login(request, account, backend="django.contrib.auth.backends.ModelBackend")
        request.session["role_code"] = account.role.code
        record_transactional_event(
            actor=account,
            action="LOGIN_SUCCESS",
            target_type="Account",
            target_id=str(account.pk),
            outcome=IdentityAuditEvent.Outcome.SUCCESS,
            request_id=getattr(request, "request_id", None),
            metadata={"role": account.role.code},
        )


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


def _active_lockout_until(normalized_email: str):
    identifier = _login_identifier(normalized_email)
    attempt = LoginAttempt.objects.filter(identifier=identifier).first()
    if attempt and attempt.locked_until and attempt.locked_until > timezone.now():
        return attempt.locked_until
    return None


def _carry_login_attempt(old_normalized_email: str, new_normalized_email: str) -> None:
    """Conserva fallos/bloqueos al cambiar correo para no levantar sanciones silenciosamente."""
    if old_normalized_email == new_normalized_email:
        return
    old_id = _login_identifier(old_normalized_email)
    new_id = _login_identifier(new_normalized_email)
    rows = {
        row.identifier: row
        for row in LoginAttempt.objects.select_for_update()
        .filter(identifier__in=[old_id, new_id])
        .order_by("identifier")
    }
    old_row = rows.get(old_id)
    if old_row is None or (old_row.failures == 0 and old_row.locked_until is None):
        return
    now = timezone.now()
    new_row = rows.get(new_id)
    candidates = [dt for dt in (old_row.locked_until, new_row.locked_until if new_row else None) if dt is not None]
    merged_locked_until = max(candidates) if candidates else None
    merged_failures = max(old_row.failures, new_row.failures if new_row else 0)
    LoginAttempt.objects.update_or_create(
        identifier=new_id,
        defaults={
            "failures": merged_failures,
            "locked_until": merged_locked_until,
            "updated_at": now,
        },
    )
    old_row.failures = 0
    old_row.locked_until = None
    old_row.save(update_fields=["failures", "locked_until", "updated_at"])


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

    from .audit import record_transactional_event
    from .models import IdentityAuditEvent

    try:
        with transaction.atomic():
            account = Account.objects.create_user(
                (email or "").strip(), password, display_name=cleaned_name, role=role,
            )
            record_transactional_event(
                actor=actor,
                action="EMPLOYEE_CREATED",
                target_type="Account",
                target_id=str(account.pk),
                outcome=IdentityAuditEvent.Outcome.SUCCESS,
                metadata={"role": role.code},
            )
            return account
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
    unlock_account: bool = False,
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
    if new_password:
        _delete_account_sessions(account)
    if unlock_account:
        _reset_login_attempt(original_normalized)
        _reset_login_attempt(normalized)
    elif normalized != original_normalized:
        _carry_login_attempt(original_normalized, normalized)

    from .audit import record_transactional_event
    from .models import IdentityAuditEvent

    if role != original_role:
        record_transactional_event(
            actor=actor,
            action="ROLE_CHANGED",
            target_type="Account",
            target_id=str(account.pk),
            outcome=IdentityAuditEvent.Outcome.SUCCESS,
            metadata={"old_role": original_role.code, "new_role": role.code},
        )
    if new_password:
        record_transactional_event(
            actor=actor,
            action="PASSWORD_RESET",
            target_type="Account",
            target_id=str(account.pk),
            outcome=IdentityAuditEvent.Outcome.SUCCESS,
            metadata={"sessions_revoked": True, "unlocked": bool(unlock_account)},
        )
    if unlock_account:
        record_transactional_event(
            actor=actor,
            action="ACCOUNT_UNLOCKED",
            target_type="Account",
            target_id=str(account.pk),
            outcome=IdentityAuditEvent.Outcome.SUCCESS,
            metadata={"email_changed": normalized != original_normalized},
        )
    if not (role != original_role or new_password or unlock_account):
        record_transactional_event(
            actor=actor,
            action="EMPLOYEE_UPDATED",
            target_type="Account",
            target_id=str(account.pk),
            outcome=IdentityAuditEvent.Outcome.SUCCESS,
            metadata={
                "email_changed": normalized != original_normalized,
                "lockout_preserved": bool(_active_lockout_until(normalized)),
            },
        )
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

    from .audit import record_transactional_event
    from .models import IdentityAuditEvent

    record_transactional_event(
        actor=actor,
        action="EMPLOYEE_DEACTIVATED",
        target_type="Account",
        target_id=str(account.pk),
        outcome=IdentityAuditEvent.Outcome.SUCCESS,
        metadata={
            "role": account.role.code,
            "sessions_revoked": True,
            "lockout_preserved": bool(_active_lockout_until(account.email_normalized)),
        },
    )
    return account


@transaction.atomic
def reactivate_employee(*, actor, account: Account) -> Account:
    """Reactiva la cuenta de un empleado inactivo sin borrar bloqueos vigentes. Solo ADMIN."""
    from .audit import record_transactional_event
    from .models import IdentityAuditEvent

    _lock_employee_administration(actor, "reactivar")
    _lock_employee(account)

    account.is_active = True
    account.save(update_fields=["is_active", "updated_at"])
    lockout_preserved = bool(_active_lockout_until(account.email_normalized))
    record_transactional_event(
        actor=actor,
        action="EMPLOYEE_REACTIVATED",
        target_type="Account",
        target_id=str(account.pk),
        outcome=IdentityAuditEvent.Outcome.SUCCESS,
        metadata={"lockout_preserved": lockout_preserved},
    )
    return account

