from __future__ import annotations

import uuid
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.db.models import Sum
from django.utils import timezone

from cash.models import CashShift
from catalog.models import Category, Product
from identity.models import Account, Role
from inventory.models import Lot
from inventory.services import reset_average_cost_if_empty

from .models import Sale, SaleCounter, SaleDraft, SaleDraftLine, SaleLine

MONEY = Decimal("0.01")
MAX_SALE_MONEY = Decimal("999999999999.99")
IGV_FACTOR = Decimal("1.18")
DISCOUNTS_DISABLED = "Los descuentos no están habilitados para nuevas ventas"


@dataclass(frozen=True)
class DraftTotals:
    total: Decimal
    base: Decimal
    igv: Decimal


def _require_seller(actor: Account, message: str = "No tiene permiso para preparar ventas.") -> None:
    if (
        not getattr(actor, "is_authenticated", False)
        or getattr(actor, "pk", None) is None
        or not getattr(actor, "is_active", False)
        or actor.role.code != Role.Code.SELLER
    ):
        raise PermissionDenied(message)


def _normalize_uuid(value: object, message: str) -> uuid.UUID:
    if isinstance(value, uuid.UUID):
        return value
    if isinstance(value, str) and "\x00" not in value:
        try:
            return uuid.UUID(value.strip())
        except ValueError as exc:
            raise ValidationError(message) from exc
    raise ValidationError(message)


def _validate_money_decimal(value: object, *, field_label: str) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, Decimal) or not value.is_finite():
        raise ValidationError(f"El monto de {field_label} no es válido.")
    exponent = value.as_tuple().exponent
    if value < 0 or not isinstance(exponent, int) or exponent < -2:
        raise ValidationError(
            f"El monto de {field_label} debe ser no negativo y tener como máximo dos decimales."
        )
    if value > MAX_SALE_MONEY:
        raise ValidationError(f"El monto de {field_label} excede el límite permitido.")
    normalized = value.quantize(MONEY)
    return Decimal("0.00") if normalized == 0 else normalized


def _verify_idempotent_sale(
    *,
    existing: Sale,
    actor: Account,
    draft_id: uuid.UUID,
    cash_received: Decimal,
    discount_amount: Decimal,
    expected_subtotal: Decimal | None,
) -> Sale:
    if existing.seller_id != actor.pk or existing.draft_id != draft_id:
        raise ValidationError("La clave de cobro ya corresponde a otra venta.")
    if existing.cash_received != cash_received or existing.discount_amount != discount_amount:
        raise ValidationError(
            "La clave de cobro ya fue usada con otros montos. Revisa e intenta nuevamente."
        )
    recorded_subtotal = (existing.total_amount + existing.discount_amount).quantize(MONEY)
    if expected_subtotal is not None and recorded_subtotal != expected_subtotal:
        raise ValidationError("La clave de cobro ya corresponde a otra venta con distinto subtotal.")
    return existing


def _lock_seller_actor(actor: Account, message: str = "No tiene permiso para preparar ventas.") -> Account:
    """Lock the seller account row first inside transactions to prevent role/status races."""
    if not getattr(actor, "is_authenticated", False) or getattr(actor, "pk", None) is None:
        raise PermissionDenied(message)
    # Lock only the account row first (matching open_cash_shift and employee services):
    # joining Role here can lose the row on PostgreSQL READ COMMITTED recheck.
    locked_actor = Account.objects.select_for_update().filter(pk=actor.pk).first()
    if locked_actor is None or not locked_actor.is_active or locked_actor.role.code != Role.Code.SELLER:
        raise PermissionDenied(message)
    return locked_actor


def _own_open_shift(*, actor: Account, lock: bool = False) -> CashShift:
    queryset = CashShift.objects.select_related("seller")
    if lock:
        queryset = queryset.select_for_update()
    shift = queryset.filter(seller=actor, status=CashShift.Status.OPEN).first()
    if shift is None:
        raise ValidationError("Necesitas un turno de caja abierto a tu nombre para preparar una venta.")
    return shift


def sellable_stock_for_product(product: Product) -> int:
    """Return stock usable today in Lima, without reserving or modifying lots."""
    return (
        Lot.objects.filter(
            product=product,
            available_quantity__gt=0,
            expiration_date__gt=timezone.localdate(),
        ).aggregate(quantity=Sum("available_quantity"))["quantity"]
        or 0
    )


def active_draft_for_actor(*, actor: Account) -> SaleDraft | None:
    if not actor.is_authenticated or actor.role.code != Role.Code.SELLER:
        return None
    return (
        SaleDraft.objects.filter(seller=actor, status=SaleDraft.Status.ACTIVE)
        .select_related("cash_shift")
        .prefetch_related("lines__product")
        .first()
    )


def draft_totals(draft: SaleDraft | None) -> DraftTotals:
    total = Decimal("0.00")
    if draft is not None:
        total = sum((line.amount for line in draft.lines.all()), start=total).quantize(MONEY)
    base = (total / IGV_FACTOR).quantize(MONEY, rounding=ROUND_HALF_UP)
    return DraftTotals(total=total, base=base, igv=total - base)


def draft_signature(draft_id, lines) -> str:
    """Serialize the displayed review in the same line order in UI and service."""
    return f"{draft_id}|" + "|".join(
        f"{line.product_id}:{line.product.name}:{line.product.barcode}:{line.quantity}:{line.unit_price:.2f}"
        for line in lines
    )


def _check_reviewed_draft(*, draft, lines, expected_subtotal, expected_signature):
    # Existing internal service callers do not have a UI review; web callers
    # provide both. This is an optimistic concurrency check, not authentication.
    if expected_subtotal is None and expected_signature is None:
        return
    total = sum((line.unit_price * line.quantity for line in lines), Decimal("0.00")).quantize(MONEY)
    if (expected_subtotal is None or expected_signature is None
            or total != expected_subtotal or draft_signature(draft.pk, lines) != expected_signature):
        raise ValidationError("La venta en preparación cambió. Revisa el resumen antes de confirmar el cobro.")


def _locked_draft_lines_and_products(draft):
    # All products are locked in UUID order before their categories, matching
    # catalog edits and the ordering introduced for audit 03-Q.
    lines = list(SaleDraftLine.objects.select_for_update(of=("self",)).filter(draft=draft))
    products = {
        product.pk: product for product in Product.objects.select_for_update(of=("self",))
        .filter(pk__in=[line.product_id for line in lines]).order_by("pk")
    }
    for line in lines:
        line.product = products[line.product_id]
    return lines, products


@transaction.atomic
def add_product_to_draft(*, actor: Account, product_id, quantity: int) -> SaleDraft:
    """Add a valid product without moving stock or cash."""
    actor = _lock_seller_actor(actor)
    if not isinstance(quantity, int) or isinstance(quantity, bool) or quantity <= 0:
        raise ValidationError({"quantity": "Ingrese una cantidad entera mayor que cero."})
    if quantity > 999999:
        raise ValidationError({"quantity": "La cantidad debe estar entre 1 y 999999 unidades."})

    shift = _own_open_shift(actor=actor, lock=True)
    product = Product.objects.select_for_update(of=("self",)).filter(pk=product_id).first()
    if product is None:
        raise ValidationError("El producto seleccionado no está disponible para la venta.")
    category = Category.objects.select_for_update().filter(pk=product.category_id).first()
    if not product.is_active or category is None or not category.is_active:
        raise ValidationError("El producto seleccionado no está disponible para la venta.")
    available = sellable_stock_for_product(product)
    if available <= 0:
        raise ValidationError("El producto no tiene existencias vendibles disponibles.")

    draft = (
        SaleDraft.objects.select_for_update()
        .filter(cash_shift=shift, status=SaleDraft.Status.ACTIVE)
        .first()
    )
    try:
        if draft is None:
            if quantity > available:
                raise ValidationError({"quantity": "La cantidad supera las existencias vendibles disponibles."})
            draft = SaleDraft.objects.create(cash_shift=shift, seller=actor)
            SaleDraftLine.objects.create(draft=draft, product=product, quantity=quantity, unit_price=product.sale_price)
        else:
            line = SaleDraftLine.objects.select_for_update().filter(draft=draft, product=product).first()
            final_quantity = quantity if line is None else line.quantity + quantity
            if final_quantity > available:
                raise ValidationError({"quantity": "La cantidad supera las existencias vendibles disponibles."})
            if line is None:
                SaleDraftLine.objects.create(
                    draft=draft,
                    product=product,
                    quantity=quantity,
                    unit_price=product.sale_price,
                )
            else:
                line.quantity = final_quantity
                line.unit_price = product.sale_price
                line.save(update_fields=("quantity", "unit_price", "updated_at"))
    except IntegrityError as exc:
        raise ValidationError("No se pudo preparar la venta. Inténtalo nuevamente.") from exc
    return draft


@transaction.atomic
def update_draft_line(*, actor: Account, line_id, quantity: int) -> SaleDraft:
    actor = _lock_seller_actor(actor)
    if not isinstance(quantity, int) or isinstance(quantity, bool) or quantity <= 0:
        raise ValidationError({"quantity": "Ingrese una cantidad entera mayor que cero."})
    if quantity > 999999:
        raise ValidationError({"quantity": "La cantidad debe estar entre 1 y 999999 unidades."})
    shift = _own_open_shift(actor=actor, lock=True)
    line = (
        SaleDraftLine.objects.select_for_update(of=("self",))
        .select_related("draft", "draft__cash_shift")
        .filter(pk=line_id, draft__seller=actor, draft__status=SaleDraft.Status.ACTIVE)
        .first()
    )
    if line is None:
        raise ValidationError("La línea de venta ya no está disponible.")
    if line.draft.cash_shift_id != shift.pk:
        raise ValidationError("La línea no pertenece a tu turno abierto.")
    product = Product.objects.select_for_update(of=("self",)).get(pk=line.product_id)
    category = Category.objects.select_for_update().get(pk=product.category_id)
    if not product.is_active or not category.is_active:
        raise ValidationError("El producto seleccionado no está disponible para la venta.")
    available = sellable_stock_for_product(product)
    if quantity > available:
        raise ValidationError({"quantity": "La cantidad supera las existencias vendibles disponibles."})
    line.quantity = quantity
    line.unit_price = product.sale_price
    line.save(update_fields=("quantity", "unit_price", "updated_at"))
    return line.draft


@transaction.atomic
def remove_draft_line(*, actor: Account, line_id) -> None:
    actor = _lock_seller_actor(actor)
    shift = _own_open_shift(actor=actor, lock=True)
    line = (
        SaleDraftLine.objects.select_for_update(of=("self",))
        .select_related("draft", "draft__cash_shift")
        .filter(pk=line_id, draft__seller=actor, draft__status=SaleDraft.Status.ACTIVE)
        .first()
    )
    if line is None:
        raise ValidationError("La línea de venta ya no está disponible.")
    if line.draft.cash_shift_id != shift.pk:
        raise ValidationError("La línea no pertenece a tu turno abierto.")
    draft = SaleDraft.objects.select_for_update().get(pk=line.draft_id)
    line.delete()
    if not SaleDraftLine.objects.filter(draft=draft).exists():
        draft.status = SaleDraft.Status.DISCARDED
        draft.discarded_at = timezone.now()
        draft.save(update_fields=("status", "discarded_at", "updated_at"))


@transaction.atomic
def discard_active_draft(*, actor: Account) -> bool:
    """Discard the seller draft; cash shifts and lots remain untouched."""
    actor = _lock_seller_actor(actor)
    shift_ids = set(
        CashShift.objects.filter(seller=actor, status=CashShift.Status.OPEN).values_list("pk", flat=True)
    ) | set(
        SaleDraft.objects.filter(seller=actor, status=SaleDraft.Status.ACTIVE).values_list("cash_shift_id", flat=True)
    )
    if shift_ids:
        list(CashShift.objects.select_for_update().filter(pk__in=sorted(shift_ids)).order_by("pk"))
    draft = (
        SaleDraft.objects.select_for_update()
        .filter(seller=actor, status=SaleDraft.Status.ACTIVE)
        .first()
    )
    if draft is None:
        return False
    SaleDraftLine.objects.filter(draft=draft).delete()
    draft.status = SaleDraft.Status.DISCARDED
    draft.discarded_at = timezone.now()
    draft.save(update_fields=("status", "discarded_at", "updated_at"))
    return True


def checkout_sale(
    *,
    actor: Account,
    draft_id,
    cash_received: Decimal,
    idempotency_key: uuid.UUID,
    discount_amount: Decimal | None = Decimal("0.00"),
    expected_subtotal: Decimal | None = None,
    expected_signature: str | None = None,
) -> Sale:
    """Confirm and pay a sale draft, applying FEFO stock deduction."""
    from .models import Sale, SaleCounter, SaleLine  # local import avoids circular

    _require_seller(actor, "No tiene permiso para cobrar ventas.")
    normalized_key = _normalize_uuid(idempotency_key, "La clave de cobro no es válida.")
    normalized_draft_id = _normalize_uuid(draft_id, "El borrador de venta no está disponible o no te pertenece.")
    cash_received = _validate_money_decimal(cash_received, field_label="efectivo recibido")
    if cash_received <= 0:
        raise ValidationError("El efectivo recibido debe ser mayor que cero.")
    # Recover a committed sale with its original amounts before applying the new-sale policy.
    existing = Sale.objects.filter(idempotency_key=normalized_key).first()
    try:
        discount_amount = Decimal("0.00") if discount_amount is None else _validate_money_decimal(
            discount_amount, field_label="descuento"
        )
    except ValidationError:
        if existing is not None:
            raise
        raise ValidationError(DISCOUNTS_DISABLED) from None
    if existing is not None:
        return _verify_idempotent_sale(
            existing=existing,
            actor=actor,
            draft_id=normalized_draft_id,
            cash_received=cash_received,
            discount_amount=discount_amount,
            expected_subtotal=expected_subtotal,
        )

    if discount_amount:
        raise ValidationError(DISCOUNTS_DISABLED)

    # Load and validate the draft
    draft = (
        SaleDraft.objects.select_related("cash_shift")
        .prefetch_related("lines__product")
        .filter(pk=normalized_draft_id, seller=actor, status=SaleDraft.Status.ACTIVE)
        .first()
    )
    if draft is None:
        raise ValidationError("El borrador de venta no está disponible o no te pertenece.")

    # Validate own open shift
    shift = _own_open_shift(actor=actor, lock=False)
    if draft.cash_shift_id != shift.pk:
        raise ValidationError("El borrador no pertenece a tu turno abierto.")

    lines = list(draft.lines.select_related("product", "product__category").all())
    if not lines:
        raise ValidationError("El borrador no tiene productos.")

    # Revalidate product availability, price consistency, and stock (FEFO) before entering the transaction lock
    price_changed_messages: list[str] = []
    for line in lines:
        if not line.product.is_active or not line.product.category.is_active:
            raise ValidationError(
                f"El producto «{line.product.name}» ya no está disponible para la venta. "
                "Quítalo de la venta en preparación para continuar."
            )
        if line.unit_price != line.product.sale_price:
            price_changed_messages.append(line.product.name)
        available = (
            Lot.objects.filter(
                product=line.product,
                available_quantity__gt=0,
                expiration_date__gt=timezone.localdate(),
            ).aggregate(qty=Sum("available_quantity"))["qty"]
            or 0
        )
        if available < line.quantity:
            raise ValidationError(
                f"Stock insuficiente para '{line.product.name}'. "
                f"Disponible: {available}, solicitado: {line.quantity}."
            )
    if price_changed_messages:
        # Persist refreshed prices only while the actor, shift, and active draft
        # are locked. A concurrent checkout must never mutate an already sold draft.
        messages = []
        with transaction.atomic():
            locked_actor = _lock_seller_actor(actor, "No tiene permiso para cobrar ventas.")
            locked_shift = _own_open_shift(actor=locked_actor, lock=True)
            locked_draft = SaleDraft.objects.select_for_update().filter(
                pk=normalized_draft_id, seller=locked_actor, cash_shift=locked_shift,
                status=SaleDraft.Status.ACTIVE,
            ).first()
            if locked_draft is None:
                raise ValidationError("El borrador de venta ya no está disponible.")
            locked_lines, _ = _locked_draft_lines_and_products(locked_draft)
            _check_reviewed_draft(draft=locked_draft, lines=locked_lines,
                                  expected_subtotal=expected_subtotal, expected_signature=expected_signature)
            for line in locked_lines:
                if line.unit_price != line.product.sale_price:
                    old_price = line.unit_price
                    line.unit_price = line.product.sale_price
                    line.save(update_fields=["unit_price", "updated_at"])
                    messages.append(
                        f"El precio de «{line.product.name}» cambió de S/ {old_price:.2f} a S/ {line.unit_price:.2f}. "
                        "Verifica el nuevo total antes de confirmar el cobro."
                    )
        raise ValidationError(messages or ["La venta cambió. Revisa el resumen antes de confirmar el cobro."])

    # Compute totals
    total = sum((line.unit_price * line.quantity for line in lines), Decimal("0.00")).quantize(MONEY)
    if total <= 0:
        raise ValidationError("El total de la venta debe ser mayor que cero.")
    base = (total / IGV_FACTOR).quantize(MONEY, rounding=ROUND_HALF_UP)
    igv = (total - base).quantize(MONEY)

    if cash_received < total:
        raise ValidationError(
            f"El efectivo recibido (S/ {cash_received}) es insuficiente para cubrir el total (S/ {total})."
        )
    change_given = (cash_received - total).quantize(MONEY)

    # Atomic section: lock actor & shift, check idempotency again, generate correlative, persist
    with transaction.atomic():
        locked_actor = _lock_seller_actor(actor, "No tiene permiso para cobrar ventas.")
        # Re-lock the shift
        shift = (
            CashShift.objects.select_for_update()
            .filter(seller=locked_actor, status=CashShift.Status.OPEN)
            .first()
        )
        if shift is None:
            raise ValidationError("No tienes un turno de caja abierto.")

        # Idempotency check inside lock
        existing = Sale.objects.filter(idempotency_key=normalized_key).first()
        if existing is not None:
            return _verify_idempotent_sale(
                existing=existing,
                actor=locked_actor,
                draft_id=normalized_draft_id,
                cash_received=cash_received,
                discount_amount=discount_amount,
                expected_subtotal=expected_subtotal,
            )

        # A concurrent request can change or discard the draft after the initial
        # checks. Re-read it while holding the same shift lock used by edits.
        locked_draft = SaleDraft.objects.select_for_update().filter(
            pk=normalized_draft_id, seller=locked_actor, cash_shift=shift, status=SaleDraft.Status.ACTIVE
        ).first()
        if locked_draft is None:
            raise ValidationError("El borrador de venta ya no está disponible.")
        locked_lines, locked_products = _locked_draft_lines_and_products(locked_draft)
        snapshot = [(line.pk, line.product_id, line.quantity, line.unit_price) for line in lines]
        current = [(line.pk, line.product_id, line.quantity, line.unit_price) for line in locked_lines]
        if snapshot != current:
            raise ValidationError("La venta en preparación cambió. Revisa el resumen antes de confirmar el cobro.")
        # Lock catalog rows as well so a price or availability change cannot
        # silently race the final confirmation.
        _check_reviewed_draft(draft=locked_draft, lines=locked_lines,
                              expected_subtotal=expected_subtotal, expected_signature=expected_signature)
        # Lock products before categories, like catalog edits. Locking categories
        # through the joins above can deadlock with a simultaneous reclassification.
        locked_categories = {
            category.pk: category for category in Category.objects.select_for_update()
            .filter(pk__in=[product.category_id for product in locked_products.values()])
            .order_by("pk")
        }
        for line in locked_lines:
            product = locked_products[line.product_id]
            if (not product.is_active or not locked_categories[product.category_id].is_active
                    or product.sale_price != line.unit_price):
                raise ValidationError("Un producto o precio cambió. Revisa la venta antes de confirmar el cobro.")
            # Use the locked current record for the sale snapshot, not the
            # earlier joined object, which can predate a concurrent edit.
            line.product = product
        draft = locked_draft
        lines = locked_lines

        # Generate correlative atomically
        counter, _ = SaleCounter.objects.select_for_update().get_or_create(
            id=1, defaults={"next_value": 1}
        )
        correlative = f"V-{counter.next_value:08d}"
        counter.next_value += 1
        counter.save(update_fields=["next_value"])

        # Create Sale
        sale = Sale.objects.create(
            cash_shift=shift,
            seller=locked_actor,
            draft=draft,
            total_amount=total,
            discount_amount=discount_amount,
            base_amount=base,
            igv_amount=igv,
            cash_received=cash_received,
            change_given=change_given,
            correlative=correlative,
            idempotency_key=normalized_key,
        )

        # Create SaleLines with product snapshots
        for line in lines:
            SaleLine.objects.create(
                sale=sale,
                product=line.product,
                product_snapshot_name=line.product.name,
                product_snapshot_barcode=line.product.barcode,
                quantity=line.quantity,
                unit_price=line.unit_price,
                unit_cost=line.product.average_cost,
                amount=(line.unit_price * line.quantity).quantize(MONEY),
            )

        # Apply FEFO stock deduction
        for line in lines:
            remaining = line.quantity
            lots = Lot.objects.select_for_update().filter(
                product=line.product,
                available_quantity__gt=0,
                expiration_date__gt=timezone.localdate(),
            ).order_by("expiration_date", "received_at", "id")

            for lot in lots:
                if remaining <= 0:
                    break
                deduct = min(lot.available_quantity, remaining)
                lot.available_quantity -= deduct
                lot.save(update_fields=["available_quantity"])
                remaining -= deduct

            if remaining > 0:
                raise ValidationError(
                    f"No hay suficiente stock para completar el cobro de '{line.product.name}'."
                )
            reset_average_cost_if_empty(line.product)

        # Mark draft as discarded
        draft.status = SaleDraft.Status.DISCARDED
        draft.discarded_at = timezone.now()
        draft.save(update_fields=("status", "discarded_at", "updated_at"))

    return sale
