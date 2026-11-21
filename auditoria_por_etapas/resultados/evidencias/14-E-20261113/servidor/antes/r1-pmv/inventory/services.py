from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone

from catalog.models import Category, Product
from identity.models import Account, Role

from .models import (
    SUPPLIER_PHONE_DIGIT_PATTERN,
    SUPPLIER_PHONE_PATTERN,
    SUPPLIER_RUC_PATTERN,
    InitialInventoryLoad,
    Lot,
    Supplier,
)


@dataclass(frozen=True)
class LotInput:
    number: str
    quantity: int
    unit_cost: Decimal
    expiration_date: date


def _validate_lots(lots: list[LotInput], *, business_date: date) -> list[LotInput]:
    if not lots:
        raise ValidationError("Ingrese al menos un lote.")

    normalized_numbers: set[str] = set()
    validated: list[LotInput] = []
    errors: list[str] = []
    for position, item in enumerate(lots, start=1):
        number = ""
        if not isinstance(item.number, str):
            errors.append(f"Lote {position}: ingrese el número.")
        elif "\x00" in item.number:
            errors.append(f"Lote {position}: el número contiene un carácter no válido.")
        else:
            number = Lot.normalize_number(item.number)
            if not number:
                errors.append(f"Lote {position}: ingrese el número.")
            elif len(number) > 64:
                errors.append(f"Lote {position}: el número no puede superar 64 caracteres.")
            elif number in normalized_numbers:
                errors.append(f"Lote {position}: el número {number} está repetido.")

        if isinstance(item.quantity, bool) or not isinstance(item.quantity, int):
            errors.append(f"Lote {position}: la cantidad debe ser un número entero.")
        elif item.quantity < 1 or item.quantity > 999999:
            errors.append(f"Lote {position}: la cantidad debe estar entre 1 y 999999 unidades.")

        if (
            not isinstance(item.unit_cost, Decimal)
            or not item.unit_cost.is_finite()
            or item.unit_cost <= 0
            or item.unit_cost > Decimal("9999999.9999")
            or item.unit_cost.as_tuple().exponent < -4
        ):
            errors.append(
                f"Lote {position}: el costo debe ser mayor que cero, no superar S/ 9,999,999.9999 y tener hasta cuatro decimales."
            )

        if not isinstance(item.expiration_date, date) or isinstance(item.expiration_date, datetime):
            errors.append(f"Lote {position}: indique una fecha de vencimiento válida.")
        elif item.expiration_date <= business_date:
            errors.append(f"Lote {position}: el vencimiento debe ser posterior a hoy en Lima.")
        elif item.expiration_date > Lot.latest_expiration_date(business_date):
            errors.append(f"Lote {position}: el vencimiento no puede superar 20 años en el futuro.")

        if number:
            normalized_numbers.add(number)
        if not errors:
            validated.append(
                LotInput(
                    number=number,
                    quantity=item.quantity,
                    unit_cost=item.unit_cost,
                    expiration_date=item.expiration_date,
                )
            )
    if errors:
        raise ValidationError(errors)
    return validated


def _lock_warehouse_actor(actor, message: str) -> Account:
    """Lock the actor row before stock checks so concurrent revocation cannot commit."""
    if not getattr(actor, "is_authenticated", False) or getattr(actor, "pk", None) is None:
        raise PermissionDenied(message)
    # Lock only the account row: joining Role here can make PostgreSQL's
    # READ COMMITTED recheck lose the joined row when role changes concurrently.
    locked_actor = Account.objects.select_for_update().filter(pk=actor.pk).first()
    if locked_actor is None or not locked_actor.is_active or locked_actor.role.code != Role.Code.WAREHOUSE:
        raise PermissionDenied(message)
    return locked_actor


def _lock_admin_actor(actor, message: str) -> Account:
    """Lock the admin actor row so concurrent revocation/demotion cannot commit."""
    if not getattr(actor, "is_authenticated", False) or getattr(actor, "pk", None) is None:
        raise PermissionDenied(message)
    # Lock only the account row: joining Role here can make PostgreSQL's
    # READ COMMITTED recheck lose the joined row when role changes concurrently.
    locked_actor = Account.objects.select_for_update().filter(pk=actor.pk).first()
    if locked_actor is None or not locked_actor.is_active or locked_actor.role.code != Role.Code.ADMIN:
        raise PermissionDenied(message)
    return locked_actor


def _lock_writeoff_actor(actor, message: str) -> Account:
    """Lock the actor row for write-offs (ADMIN or WAREHOUSE)."""
    if not getattr(actor, "is_authenticated", False) or getattr(actor, "pk", None) is None:
        raise PermissionDenied(message)
    # Lock only the account row: joining Role here can make PostgreSQL's
    # READ COMMITTED recheck lose the joined row when role changes concurrently.
    locked_actor = Account.objects.select_for_update().filter(pk=actor.pk).first()
    if (
        locked_actor is None
        or not locked_actor.is_active
        or locked_actor.role.code not in (Role.Code.ADMIN, Role.Code.WAREHOUSE)
    ):
        raise PermissionDenied(message)
    return locked_actor


def _lock_receipt_supplier(supplier):
    if supplier is None:
        return None
    if not isinstance(supplier, Supplier) or supplier.pk is None:
        raise ValidationError("El proveedor seleccionado no es válido.")
    try:
        current = Supplier.objects.select_for_update().get(pk=supplier.pk)
    except Supplier.DoesNotExist as exc:
        raise ValidationError("El proveedor seleccionado ya no existe.") from exc
    if not current.is_active:
        raise ValidationError("El proveedor seleccionado está inactivo.")
    return current


@transaction.atomic
def confirm_initial_load(
    *,
    actor: Account,
    product: Product,
    lots: list[LotInput],
    supplier=None,
    business_date: date | None = None,
) -> InitialInventoryLoad:
    """Persist one complete initial load or leave no residue."""
    locked_actor = _lock_warehouse_actor(actor, "No tiene permiso para confirmar cargas de inventario.")

    current_date = business_date or timezone.localdate()
    validated = _validate_lots(lots, business_date=current_date)
    if not isinstance(product, Product) or product.pk is None:
        raise ValidationError("El producto seleccionado no es válido.")
    # Always lock Product before Category to match catalog/sales lock ordering.
    locked_product = Product.objects.select_for_update().filter(pk=product.pk).first()
    if locked_product is None:
        raise ValidationError("El producto seleccionado ya no existe.")
    locked_category = Category.objects.select_for_update().get(pk=locked_product.category_id)
    if (
        not locked_product.is_active
        or not locked_product.controls_expiration
        or not locked_category.is_active
    ):
        raise ValidationError("El producto no está disponible para la carga inicial.")
    supplier = _lock_receipt_supplier(supplier)
    if InitialInventoryLoad.objects.filter(product=locked_product).exists():
        raise ValidationError("Este producto ya tiene una carga inicial confirmada.")

    repeated = set(
        Lot.objects.filter(
            product=locked_product,
            number_normalized__in=[item.number for item in validated],
        ).values_list("number_normalized", flat=True)
    )
    if repeated:
        raise ValidationError(f"El lote {sorted(repeated)[0]} ya existe para este producto.")

    try:
        with transaction.atomic():
            load = InitialInventoryLoad.objects.create(product=locked_product, responsible=locked_actor)
            Lot.objects.bulk_create(
                [
                    Lot(
                        product=locked_product,
                        initial_load=load,
                        supplier=supplier,
                        responsible=locked_actor,
                        number=item.number,
                        number_normalized=item.number,
                        initial_quantity=item.quantity,
                        available_quantity=item.quantity,
                        unit_cost=item.unit_cost,
                        expiration_date=item.expiration_date,
                    )
                    for item in validated
                ]
            )
    except IntegrityError as exc:
        raise ValidationError("La carga no pudo confirmarse porque otro intento ya fue registrado.") from exc

    total_quantity = sum(item.quantity for item in validated)
    weighted_total = sum(item.unit_cost * item.quantity for item in validated)
    locked_product.average_cost = (weighted_total / total_quantity).quantize(
        Decimal("0.0001"), rounding=ROUND_HALF_UP
    )
    locked_product.save(update_fields=("average_cost", "updated_at"))
    return load


def _recalculate_product_average_cost(product: Product, *, current_date: date | None = None) -> None:
    """Recalcula el costo promedio ponderado con lotes disponibles vigentes (con fallback a disponibles)."""
    ref_date = current_date or timezone.localdate()
    locked_product = Product.objects.select_for_update().get(pk=product.pk)
    all_lots = list(
        Lot.objects.filter(
            product=locked_product,
            available_quantity__gt=0,
            expiration_date__gt=ref_date,
        )
    )
    if not all_lots:
        all_lots = list(Lot.objects.filter(product=locked_product, available_quantity__gt=0))
    total_qty = sum(l.available_quantity for l in all_lots)
    total_cost = sum(l.unit_cost * l.available_quantity for l in all_lots)
    if total_qty > 0:
        locked_product.average_cost = (total_cost / total_qty).quantize(
            Decimal("0.0001"), rounding=ROUND_HALF_UP
        )
        locked_product.save(update_fields=("average_cost", "updated_at"))


# ═══════════════════════════════════════════════════════════════════════════════
# Sprint 3 — Proveedores (HU-PROV-01, HU-PROV-02, HU-PROV-04)
# ═══════════════════════════════════════════════════════════════════════════════

@transaction.atomic
def create_supplier(*, actor, name: str, ruc: str, phone: str = "") -> Supplier:
    """Registra un nuevo proveedor (ADMIN)."""
    _lock_admin_actor(actor, "Solo el administrador puede registrar proveedores.")

    errors: dict[str, str] = {}
    if not isinstance(name, str):
        errors["name"] = "El nombre del proveedor es obligatorio."
        norm_name = ""
    elif "\x00" in name:
        errors["name"] = "El nombre contiene un carácter no válido."
        norm_name = ""
    else:
        norm_name = Supplier.normalize_name(name)
        if not norm_name:
            errors["name"] = "El nombre del proveedor es obligatorio."
        elif not any(ch.isalnum() for ch in norm_name):
            errors["name"] = "El nombre comercial debe contener letras o números."
        elif len(norm_name) > 160:
            errors["name"] = "El nombre admite hasta 160 caracteres."

    if not isinstance(ruc, str):
        errors["ruc"] = "El RUC es obligatorio."
        norm_ruc = ""
    elif "\x00" in ruc:
        errors["ruc"] = "El RUC contiene un carácter no válido."
        norm_ruc = ""
    else:
        norm_ruc = ruc.strip()
        if not norm_ruc:
            errors["ruc"] = "El RUC es obligatorio."
        elif not SUPPLIER_RUC_PATTERN.fullmatch(norm_ruc):
            errors["ruc"] = "El RUC debe contener exactamente 11 dígitos numéricos."

    if phone is None:
        norm_phone = ""
    elif not isinstance(phone, str):
        errors["phone"] = "El teléfono no es válido."
        norm_phone = ""
    elif "\x00" in phone:
        errors["phone"] = "El teléfono contiene un carácter no válido."
        norm_phone = ""
    else:
        norm_phone = Supplier.normalize_phone(phone)
        if norm_phone:
            if len(norm_phone) > 20:
                errors["phone"] = "El teléfono admite hasta 20 caracteres."
            elif not SUPPLIER_PHONE_PATTERN.fullmatch(norm_phone) or not SUPPLIER_PHONE_DIGIT_PATTERN.search(norm_phone):
                errors["phone"] = (
                    "El teléfono debe incluir al menos un dígito y solo puede contener "
                    "números, espacios y signos (+, -, paréntesis)."
                )

    if errors:
        raise ValidationError(errors)

    if Supplier.objects.filter(ruc=norm_ruc).exists():
        raise ValidationError({"ruc": "El RUC ya está registrado."})

    supplier = Supplier(name=norm_name, ruc=norm_ruc, phone=norm_phone)
    supplier.full_clean(validate_unique=False)
    try:
        with transaction.atomic():
            supplier.save()
    except IntegrityError as exc:
        raise ValidationError({"ruc": "El RUC ya está registrado."}) from exc
    return supplier


@transaction.atomic
def toggle_supplier_status(*, actor, supplier: Supplier, is_active: bool | None = None) -> Supplier:
    """Activa o desactiva un proveedor (ADMIN)."""
    _lock_admin_actor(actor, "Solo el administrador puede cambiar el estado de proveedores.")
    if is_active is not None and type(is_active) is not bool:
        raise ValidationError("El estado solicitado del proveedor no es válido.")
    if not isinstance(supplier, Supplier) or supplier.pk is None:
        raise ValidationError("El proveedor seleccionado ya no existe.")

    current = Supplier.objects.select_for_update().filter(pk=supplier.pk).first()
    if current is None:
        raise ValidationError("El proveedor seleccionado ya no existe.")

    target = (not current.is_active) if is_active is None else is_active
    changed = current.is_active != target
    if changed:
        current.is_active = target
        current.save(update_fields=["is_active", "updated_at"])

    supplier.name = current.name
    supplier.ruc = current.ruc
    supplier.phone = current.phone
    supplier.is_active = current.is_active
    supplier.updated_at = current.updated_at
    supplier._state_changed = changed
    return supplier


# ═══════════════════════════════════════════════════════════════════════════════
# Sprint 3 — Baja por merma (HU-INV-02)
# ═══════════════════════════════════════════════════════════════════════════════

def _next_writeoff_correlativo() -> str:
    from .models import StockWriteOff

    highest_seq = StockWriteOff.objects.count()
    recent_codes = (
        StockWriteOff.objects.filter(correlativo__startswith="B-")
        .order_by("-correlativo")
        .values_list("correlativo", flat=True)[:20]
    )
    for code in recent_codes:
        suffix = code[2:]
        if suffix.isdigit():
            highest_seq = max(highest_seq, int(suffix))
    return f"B-{highest_seq + 1:08d}"


@transaction.atomic
def write_off_stock(
    *,
    actor,
    lot: "Lot",
    quantity: int,
    reason: str,
    notes: str = "",
) -> "StockWriteOff":
    """Registra una baja de inventario por merma (ALMACENERO o ADMIN)."""
    from .models import Lot as LotModel, StockWriteOff

    locked_actor = _lock_writeoff_actor(actor, "No tiene permiso para registrar bajas de inventario.")

    if isinstance(quantity, bool) or not isinstance(quantity, int):
        raise ValidationError({"quantity": "La cantidad a dar de baja debe ser un número entero."})
    if quantity <= 0:
        raise ValidationError({"quantity": "La cantidad a dar de baja debe ser mayor que cero."})
    if quantity > 999999:
        raise ValidationError({"quantity": "La cantidad a dar de baja no puede superar 999,999 unidades por operación."})

    if not isinstance(reason, str) or "\x00" in reason or reason not in StockWriteOff.Reason.values:
        raise ValidationError({"reason": "Seleccione un motivo válido."})

    if not isinstance(notes, str):
        raise ValidationError({"notes": "El detalle debe ser texto válido."})
    if "\x00" in notes:
        raise ValidationError({"notes": "El detalle contiene un carácter no válido."})
    cleaned_notes = notes.strip()

    if not isinstance(lot, LotModel) or lot.pk is None:
        raise ValidationError("El lote seleccionado no es válido.")
    lot_ref = LotModel.objects.filter(pk=lot.pk).values("id", "product_id").first()
    if lot_ref is None:
        raise ValidationError("El lote seleccionado ya no existe.")

    # All stock-changing operations acquire the product before its lots,
    # matching checkout and avoiding an inverted product/lot lock order.
    locked_product = Product.objects.select_for_update().get(pk=lot_ref["product_id"])
    locked_lot = LotModel.objects.select_for_update().filter(pk=lot_ref["id"]).first()
    if locked_lot is None:
        raise ValidationError("El lote seleccionado ya no existe.")

    if quantity > locked_lot.available_quantity:
        raise ValidationError({"quantity": "La cantidad supera las existencias disponibles del lote."})

    today = timezone.localdate()
    if locked_lot.expiration_date <= today and reason == StockWriteOff.Reason.DAMAGE:
        raise ValidationError({
            "reason": "El lote está vencido; seleccione Vencimiento por caducidad o Robo o faltante si esa es la causa real."
        })
    if locked_lot.expiration_date > today and reason == StockWriteOff.Reason.EXPIRATION:
        raise ValidationError({"reason": "El lote aún no ha vencido; seleccione la causa real de la baja."})

    if reason in (StockWriteOff.Reason.DAMAGE, StockWriteOff.Reason.THEFT) and not cleaned_notes:
        raise ValidationError({"notes": "Detalle obligatorio para Daño o rotura y Robo o faltante."})

    # Distinct lots can be written off concurrently. A collision must not
    # abort the transaction or lose a legitimate write-off.
    max_attempts = 32
    for attempt in range(max_attempts):
        correlativo = _next_writeoff_correlativo()
        try:
            with transaction.atomic():
                writeoff = StockWriteOff.objects.create(
                    lot=locked_lot,
                    quantity=quantity,
                    reason=reason,
                    notes=cleaned_notes,
                    responsible=locked_actor,
                    correlativo=correlativo,
                )
            break
        except IntegrityError:
            if attempt == max_attempts - 1:
                raise ValidationError("No se pudo asignar el correlativo de la baja. Inténtalo nuevamente.")

    locked_lot.available_quantity -= quantity
    locked_lot.save(update_fields=["available_quantity"])
    _recalculate_product_average_cost(locked_product, current_date=today)
    return writeoff


# ═══════════════════════════════════════════════════════════════════════════════
# Sprint 3 — Ajuste por conteo físico (HU-INV-03)
# ═══════════════════════════════════════════════════════════════════════════════

@transaction.atomic
def register_physical_adjustment(
    *,
    actor,
    lot: "Lot",
    delta: int,
    reason: str,
) -> "PhysicalAdjustment":
    """Registra un ajuste positivo o negativo por conteo físico (ADMIN)."""
    from .models import Lot as LotModel, PhysicalAdjustment

    locked_actor = _lock_admin_actor(actor, "Solo el administrador puede registrar ajustes físicos.")

    if isinstance(delta, bool) or not isinstance(delta, int):
        raise ValidationError({"delta": "El ajuste debe ser un número entero."})
    if delta == 0:
        raise ValidationError({"delta": "El ajuste no puede ser cero."})
    if abs(delta) > 999999:
        raise ValidationError({"delta": "El ajuste no puede superar 999,999 unidades por operación."})

    if not isinstance(reason, str):
        raise ValidationError({"reason": "El motivo del ajuste es obligatorio."})
    if "\x00" in reason:
        raise ValidationError({"reason": "El motivo del ajuste contiene un carácter no válido."})
    reason = reason.strip()
    if not reason:
        raise ValidationError({"reason": "El motivo del ajuste es obligatorio."})
    if len(reason) > 300:
        raise ValidationError({"reason": "El motivo del ajuste admite hasta 300 caracteres."})

    if not isinstance(lot, LotModel) or lot.pk is None:
        raise ValidationError("El lote seleccionado no es válido.")
    lot_ref = LotModel.objects.filter(pk=lot.pk).values("id", "product_id").first()
    if lot_ref is None:
        raise ValidationError("El lote seleccionado ya no existe.")

    # All stock-changing operations acquire the product before its lots,
    # matching checkout and avoiding an inverted product/lot lock order.
    locked_product = Product.objects.select_for_update().get(pk=lot_ref["product_id"])
    locked_lot = LotModel.objects.select_for_update().filter(pk=lot_ref["id"]).first()
    if locked_lot is None:
        raise ValidationError("El lote seleccionado ya no existe.")

    new_qty = locked_lot.available_quantity + delta
    if new_qty < 0:
        raise ValidationError({"delta": "El ajuste negativo supera las existencias disponibles del lote."})

    adjustment = PhysicalAdjustment.objects.create(
        lot=locked_lot,
        delta=delta,
        reason=reason,
        responsible=locked_actor,
    )
    locked_lot.available_quantity = new_qty
    # Si el ajuste es positivo, la cantidad inicial también debe crecer para
    # no violar el constraint lot_available_lte_initial (available <= initial).
    if delta > 0:
        locked_lot.initial_quantity = locked_lot.initial_quantity + delta
        locked_lot.save(update_fields=["available_quantity", "initial_quantity"])
    else:
        locked_lot.save(update_fields=["available_quantity"])
    _recalculate_product_average_cost(locked_product)
    return adjustment


# ═══════════════════════════════════════════════════════════════════════════════
# Sprint 3 — HU-INV-01b · Recalcular costo promedio en entradas posteriores
# ═══════════════════════════════════════════════════════════════════════════════

@transaction.atomic
def register_stock_entry(
    *,
    actor,
    product: "Product",
    lots: list,
    supplier=None,
    business_date=None,
) -> "InitialInventoryLoad":
    """Registra una entrada posterior (no inicial) de lotes y recalcula el costo promedio.

    Requiere que el producto ya tenga su carga inicial confirmada (HU-INV-01a).
    Solo ALMACENERO puede ejecutar esta acción.
    """
    from catalog.models import Product as ProductModel
    from .models import InitialInventoryLoad as IIL

    locked_actor = _lock_warehouse_actor(actor, "Solo el almacenero puede registrar entradas de inventario.")

    current_date = business_date or timezone.localdate()
    validated = _validate_lots(lots, business_date=current_date)

    if not isinstance(product, ProductModel) or product.pk is None:
        raise ValidationError("El producto seleccionado no es válido.")
    locked_product = ProductModel.objects.select_for_update().filter(pk=product.pk).first()
    if locked_product is None:
        raise ValidationError("El producto seleccionado ya no existe.")
    locked_category = Category.objects.select_for_update().get(pk=locked_product.category_id)
    if (
        not locked_product.is_active
        or not locked_product.controls_expiration
        or not locked_category.is_active
    ):
        raise ValidationError("El producto no está disponible para registrar entradas.")
    supplier = _lock_receipt_supplier(supplier)
    if not IIL.objects.filter(product=locked_product).exists():
        raise ValidationError("El producto no tiene carga inicial confirmada. Use la carga inicial primero.")

    repeated = set(
        Lot.objects.filter(
            product=locked_product,
            number_normalized__in=[item.number for item in validated],
        ).values_list("number_normalized", flat=True)
    )
    if repeated:
        raise ValidationError(f"El lote {sorted(repeated)[0]} ya existe para este producto.")

    # Reutilizamos la InitialInventoryLoad existente como referencia técnica,
    # marcando is_initial=False para distinguir las entradas posteriores (BUG-024)
    # y registrando al almacenero responsable de cada lote (BUG-032).
    existing_load = IIL.objects.get(product=locked_product)
    # RN-14 uses the previous moving average, not the purchase costs of the
    # lots left by FEFO. Preserve the existing eligible-stock policy.
    previous_lots = Lot.objects.filter(product=locked_product, available_quantity__gt=0)
    eligible = previous_lots.filter(expiration_date__gt=current_date)
    previous_quantity = sum(eligible.values_list('available_quantity', flat=True))
    incoming_quantity = sum(item.quantity for item in validated)
    incoming_cost = sum(item.unit_cost * item.quantity for item in validated)
    try:
        with transaction.atomic():
            Lot.objects.bulk_create(
                [
                    Lot(
                        product=locked_product,
                        initial_load=existing_load,
                        supplier=supplier,
                        responsible=locked_actor,
                        is_initial=False,
                        number=item.number,
                        number_normalized=item.number,
                        initial_quantity=item.quantity,
                        available_quantity=item.quantity,
                        unit_cost=item.unit_cost,
                        expiration_date=item.expiration_date,
                    )
                    for item in validated
                ]
            )
    except IntegrityError as exc:
        raise ValidationError("La entrada no pudo registrarse porque otro intento o lote entró en conflicto.") from exc

    locked_product.average_cost = (
        (previous_quantity * locked_product.average_cost + incoming_cost)
        / (previous_quantity + incoming_quantity)
    ).quantize(Decimal('0.0001'), rounding=ROUND_HALF_UP)
    locked_product.save(update_fields=('average_cost', 'updated_at'))
    return existing_load
