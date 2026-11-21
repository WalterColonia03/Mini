from __future__ import annotations

from decimal import Decimal

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.db.models import Sum

from identity.models import Account, Role

from .models import CashRegister, CashShift, CashShiftClose


MAX_CASH_AMOUNT = Decimal("9999999.99")
MAX_CASH_ACCUMULATED = Decimal("999999999999.99")
MONEY = Decimal("0.01")


def _validate_cash_amount(value: object, *, field_name: str, maximum=MAX_CASH_AMOUNT) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, Decimal) or not value.is_finite():
        raise ValidationError({field_name: "Ingrese un monto válido con hasta dos decimales."})
    exponent = value.as_tuple().exponent
    if value < 0 or not isinstance(exponent, int) or exponent < -2 or exponent > 0:
        raise ValidationError({field_name: "Ingrese un monto no negativo con hasta dos decimales."})
    if value > maximum:
        raise ValidationError({field_name: f"El monto no puede superar S/ {maximum:.2f}."})
    normalized = value.quantize(MONEY)
    if normalized == 0:
        return Decimal("0.00")
    return normalized


@transaction.atomic
def open_cash_shift(*, actor: Account, opening_amount: Decimal) -> CashShift:
    """Open the seeded cash register for the authenticated seller."""
    if actor is None or not getattr(actor, "is_authenticated", False) or getattr(actor, "pk", None) is None:
        raise PermissionDenied("No tiene permiso para abrir caja.")
    # Match employee role/deactivation changes on the same account row while
    # keeping FK FOR KEY SHARE checks unblocked (no_key=True = FOR NO KEY UPDATE).
    # Lock only the account row: joining Role here can make PostgreSQL's
    # recheck lose the joined row when the role changes while this waits.
    actor = Account.objects.select_for_update(no_key=True).filter(pk=actor.pk).first()
    if actor is None or not actor.is_active or actor.role.code != Role.Code.SELLER:
        raise PermissionDenied("No tiene permiso para abrir caja.")
    opening_amount = _validate_cash_amount(opening_amount, field_name="opening_amount")

    cash_register = (
        CashRegister.objects.select_for_update().filter(is_active=True, code="CAJA-01").first()
    )
    if cash_register is None:
        raise ValidationError("La caja única CAJA-01 no está disponible.")
    if CashShift.objects.filter(status=CashShift.Status.OPEN).exists():
        raise ValidationError("Ya existe un turno abierto. Cierre ese turno antes de abrir otro.")

    try:
        with transaction.atomic():
            return CashShift.objects.create(
                cash_register=cash_register,
                seller=actor,
                opening_amount=opening_amount,
                status=CashShift.Status.OPEN,
            )
    except IntegrityError as exc:
        raise ValidationError("Otro vendedor abrió la caja antes de completar este intento.") from exc


@transaction.atomic
def close_cash_shift(*, actor: Account, counted_amount: Decimal) -> CashShiftClose:
    """Close the seller's open cash shift and record the counted vs expected amounts."""
    if actor is None or not getattr(actor, "is_authenticated", False) or getattr(actor, "pk", None) is None:
        raise PermissionDenied("No tiene permiso para cerrar caja.")
    # Lock Account (FOR NO KEY UPDATE) before CashShift so concurrent role/deactivation
    # checks never invert lock order and FK FOR KEY SHARE checks remain unblocked.
    actor = Account.objects.select_for_update(no_key=True).filter(pk=actor.pk).first()
    if actor is None or not actor.is_active or actor.role.code != Role.Code.SELLER:
        raise PermissionDenied("No tiene permiso para cerrar caja.")
    counted_amount = _validate_cash_amount(counted_amount, field_name="counted_amount", maximum=MAX_CASH_ACCUMULATED)

    shift = (
        CashShift.objects.select_for_update()
        .filter(seller=actor, status=CashShift.Status.OPEN)
        .first()
    )
    if shift is None:
        raise ValidationError("No tienes un turno de caja abierto para cerrar.")

    # Reject close if there is an active draft with lines
    from sales.models import SaleDraft  # deferred import avoids circular
    if (
        SaleDraft.objects.filter(
            cash_shift=shift,
            status=SaleDraft.Status.ACTIVE,
            lines__isnull=False,
        ).exists()
    ):
        raise ValidationError(
            "Hay una venta en preparación con productos. "
            "Descártala o cóbrala antes de cerrar el turno."
        )

    # Calculate expected = opening + sum of confirmed sales
    from sales.models import Sale  # deferred import
    sales_total = (
        Sale.objects.filter(cash_shift=shift).aggregate(
            s=Sum("total_amount")
        )["s"]
        or Decimal("0.00")
    )
    expected_amount = shift.opening_amount + sales_total
    if expected_amount > MAX_CASH_ACCUMULATED:
        raise ValidationError("El acumulado supera la capacidad del cierre. Requiere revisión de los datos registrados.")
    difference = counted_amount - expected_amount

    close = CashShiftClose.objects.create(
        cash_shift=shift,
        counted_amount=counted_amount,
        expected_amount=expected_amount,
        difference=difference,
        closed_by=actor,
    )
    shift.status = CashShift.Status.CLOSED
    shift.save(update_fields=["status"])
    return close
