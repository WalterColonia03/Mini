from __future__ import annotations

import hashlib
import json
import uuid
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
    InitialLoadLine,
    Lot,
    StockReceipt,
    StockReceiptCounter,
    StockReceiptLine,
    Supplier,
)


@dataclass(frozen=True)
class LotInput:
    number: str
    quantity: int
    unit_cost: Decimal
    expiration_date: date


def _validate_lots(lots: list[LotInput], *, business_date: date, check_expiration=True) -> list[LotInput]:
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
        elif check_expiration and item.expiration_date <= business_date:
            errors.append(f"Lote {position}: el vencimiento debe ser posterior a hoy en Lima.")
        elif check_expiration and item.expiration_date > Lot.latest_expiration_date(business_date):
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

    total_quantity = sum(item.quantity for item in validated)
    weighted_total = sum(item.unit_cost * item.quantity for item in validated)
    initial_average = (weighted_total / total_quantity).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
    try:
        with transaction.atomic():
            load = InitialInventoryLoad.objects.create(
                product=locked_product, responsible=locked_actor,
                product_snapshot_name=locked_product.name,
                product_snapshot_barcode=locked_product.barcode,
                unit_snapshot=locked_product.unit,
                responsible_snapshot_name=locked_actor.display_name,
                supplier_snapshot_name=supplier.name if supplier else "",
                supplier_snapshot_ruc=supplier.ruc if supplier else "",
                average_cost_snapshot=initial_average,
            )
            created_lots = Lot.objects.bulk_create(
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
            InitialLoadLine.objects.bulk_create([
                InitialLoadLine(load=load, lot=lot, number=lot.number_normalized,
                    quantity=lot.initial_quantity, unit_cost=lot.unit_cost,
                    expiration_date=lot.expiration_date, received_at=lot.received_at)
                for lot in created_lots
            ])
    except IntegrityError as exc:
        raise ValidationError("La carga no pudo confirmarse porque otro intento ya fue registrado.") from exc

    locked_product.average_cost = initial_average
    locked_product.save(update_fields=("average_cost", "updated_at"))
    return load


def reset_average_cost_if_empty(product: Product) -> None:
    """RN-14: preserve the moving average on exits, reset only at physical zero.

    The caller holds the product row lock in its stock-changing transaction.
    Query persisted lots, including expired ones, rather than a prefetched stock
    value. Historical output costs must be captured before calling this helper.
    """
    if not Lot.objects.filter(product=product, available_quantity__gt=0).exists():
        product.average_cost = Decimal("0.0000")
        product.save(update_fields=("average_cost", "updated_at"))


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
    idempotency_key=None,
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
    try:
        key = uuid.uuid4() if idempotency_key is None else uuid.UUID(str(idempotency_key))
    except (ValueError, TypeError, AttributeError) as exc:
        raise ValidationError({"idempotency_key": "La clave de operación debe ser un UUID válido."}) from exc
    signature = hashlib.sha256(json.dumps({
        "lot": str(lot.pk), "quantity": quantity, "reason": reason, "notes": cleaned_notes,
    }, sort_keys=True, ensure_ascii=True).encode()).hexdigest()

    def replay():
        prior = StockWriteOff.objects.filter(idempotency_key=key).first()
        if prior is not None:
            if prior.responsible_id != locked_actor.pk or prior.content_signature != signature:
                raise ValidationError("La clave de operación ya fue utilizada para otra solicitud. Recargue el formulario e inténtelo nuevamente.")
            prior._replayed = True
        return prior

    previous = replay()
    if previous is not None:
        return previous
    lot_ref = LotModel.objects.filter(pk=lot.pk).values("id", "product_id").first()
    if lot_ref is None:
        raise ValidationError("El lote seleccionado ya no existe.")

    # All stock-changing operations acquire the product before its lots,
    # matching checkout and avoiding an inverted product/lot lock order.
    locked_product = Product.objects.select_for_update().get(pk=lot_ref["product_id"])
    locked_lot = LotModel.objects.select_for_update().filter(pk=lot_ref["id"]).first()
    if locked_lot is None:
        raise ValidationError("El lote seleccionado ya no existe.")

    previous = replay()
    if previous is not None:
        return previous

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

    receipt_line = getattr(locked_lot, "receipt_line", None)
    initial_line = getattr(locked_lot, "initial_line", None)
    origin = "Origen no disponible (registro anterior o incompleto)"
    if locked_lot.adjustment_origin_id:
        origin = f"AJUSTE {locked_lot.adjustment_origin_id}"
    elif receipt_line is not None and initial_line is None and receipt_line.receipt.product_id == locked_product.pk:
        origin = f"Recepción {receipt_line.receipt.correlative}"
    elif initial_line is not None and receipt_line is None and initial_line.load.product_id == locked_product.pk:
        origin = f"Carga inicial {initial_line.load_id}"

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
                    unit_cost=locked_product.average_cost,
                    reason=reason,
                    notes=cleaned_notes,
                    responsible=locked_actor,
                    correlativo=correlativo,
                    idempotency_key=key,
                    content_signature=signature,
                    product_snapshot_name=locked_product.name,
                    product_snapshot_barcode=locked_product.barcode,
                    unit_snapshot=locked_product.unit,
                    responsible_snapshot_name=locked_actor.display_name,
                    lot_snapshot_number=locked_lot.number_normalized or locked_lot.number,
                    lot_snapshot_expiration_date=locked_lot.expiration_date,
                    origin_snapshot=origin,
                )
            break
        except IntegrityError:
            previous = replay()
            if previous is not None:
                return previous
            if attempt == max_attempts - 1:
                raise ValidationError("No se pudo asignar el correlativo de la baja. Inténtalo nuevamente.")

    locked_lot.available_quantity -= quantity
    locked_lot.save(update_fields=["available_quantity"])
    reset_average_cost_if_empty(locked_product)
    return writeoff


# ═══════════════════════════════════════════════════════════════════════════════
# Sprint 3 — Ajuste por conteo físico (HU-INV-03)
# ═══════════════════════════════════════════════════════════════════════════════

@transaction.atomic
def register_physical_adjustment(
    *, actor, lot=None, delta: int, reason: str, product=None, number=None,
    expiration_date=None, unit_cost=None, cost_source="", idempotency_key=None,
) -> "PhysicalAdjustment":
    """Documented existing/new-lot adjustment; actor -> product -> lot lock order."""
    from .models import Lot as LotModel, PhysicalAdjustment

    locked_actor = _lock_admin_actor(actor, "Solo el administrador puede registrar ajustes físicos.")
    if isinstance(delta, bool) or not isinstance(delta, int):
        raise ValidationError({"delta": "El ajuste debe ser un número entero."})
    if delta == 0:
        raise ValidationError({"delta": "El ajuste no puede ser cero."})
    if abs(delta) > 999999:
        raise ValidationError({"delta": "El ajuste no puede superar 999,999 unidades por operación."})
    if not isinstance(reason, str) or not reason.strip():
        raise ValidationError({"reason": "El motivo del ajuste es obligatorio."})
    if "\x00" in reason:
        raise ValidationError({"reason": "El motivo del ajuste contiene un carácter no válido."})
    reason = reason.strip()
    if len(reason) > 300:
        raise ValidationError({"reason": "El motivo del ajuste admite hasta 300 caracteres."})
    if not isinstance(cost_source, str) or "\x00" in cost_source or len(cost_source.strip()) > 300:
        raise ValidationError({"cost_source": "La fuente del costo debe ser texto sin caracteres nulos y de hasta 300 caracteres."})
    cost_source = cost_source.strip()
    if unit_cost is not None and (
        not isinstance(unit_cost, Decimal) or not unit_cost.is_finite() or unit_cost <= 0
        or unit_cost > Decimal("9999999.9999") or unit_cost.as_tuple().exponent < -4
    ):
        raise ValidationError({"unit_cost": "El costo debe ser positivo, hasta S/ 9,999,999.9999 y con máximo cuatro decimales."})
    new_lot = product is not None
    if new_lot:
        if lot is not None or not isinstance(product, Product) or product.pk is None:
            raise ValidationError("Seleccione solo un producto para crear el lote nuevo o un lote existente.")
        if delta < 1:
            raise ValidationError({"delta": "Un lote nuevo requiere un ajuste positivo."})
        if not isinstance(number, str) or "\x00" in number:
            raise ValidationError({"number": "Ingrese un número de lote válido."})
        number = LotModel.normalize_number(number)
        if not number or len(number) > 64:
            raise ValidationError({"number": "El número de lote debe tener entre 1 y 64 caracteres."})
        if not isinstance(expiration_date, date) or isinstance(expiration_date, datetime):
            raise ValidationError({"expiration_date": "Indique una fecha de vencimiento fiable."})
        if expiration_date > LotModel.latest_expiration_date(timezone.localdate()):
            raise ValidationError({"expiration_date": "El vencimiento no puede superar 20 años en el futuro."})
        product_id = product.pk
    else:
        if not isinstance(lot, LotModel) or lot.pk is None:
            raise ValidationError("El lote seleccionado no es válido.")
        ref = LotModel.objects.filter(pk=lot.pk).values("id", "product_id").first()
        if ref is None:
            raise ValidationError("El lote seleccionado ya no existe.")
        product_id = ref["product_id"]
        if number is not None or expiration_date is not None:
            raise ValidationError("No cambie la identidad de un lote existente mediante un ajuste.")
    try:
        key = uuid.uuid4() if idempotency_key is None else uuid.UUID(str(idempotency_key))
    except (ValueError, TypeError, AttributeError) as exc:
        raise ValidationError({"idempotency_key": "La clave de operación debe ser un UUID válido."}) from exc
    signature = hashlib.sha256(json.dumps({
        "lot": str(lot.pk) if not new_lot else None, "product": str(product_id),
        "number": number if new_lot else None, "expiration_date": expiration_date.isoformat() if new_lot else None,
        "delta": delta, "reason": reason,
        "unit_cost": format(unit_cost, ".4f") if unit_cost is not None else None, "cost_source": cost_source,
    }, sort_keys=True, ensure_ascii=True).encode()).hexdigest()

    def replay():
        previous = PhysicalAdjustment.objects.filter(idempotency_key=key).first()
        if previous is not None:
            if previous.responsible_id != locked_actor.pk or previous.content_signature != signature:
                raise ValidationError("La clave de operación ya fue utilizada para otra solicitud. Recargue el formulario e inténtelo nuevamente.")
            previous._replayed = True
        return previous

    previous = replay()
    if previous is not None:
        return previous
    locked_product = Product.objects.select_for_update().filter(pk=product_id).first()
    if locked_product is None:
        raise ValidationError("El producto seleccionado ya no existe.")
    previous = replay()
    if previous is not None:
        return previous
    initial = InitialInventoryLoad.objects.filter(product=locked_product).first()
    if initial is None:
        raise ValidationError("El producto no tiene carga inicial confirmada. Investigue su apertura antes de registrar ajustes.")
    physical = sum(LotModel.objects.filter(product=locked_product).values_list("available_quantity", flat=True))
    if not new_lot:
        locked_lot = LotModel.objects.select_for_update().filter(pk=lot.pk).first()
        if locked_lot is None:
            raise ValidationError("El lote seleccionado ya no existe.")
        if locked_lot.available_quantity + delta < 0:
            raise ValidationError({"delta": "El ajuste negativo supera las existencias disponibles del lote."})
    if delta > 0 and physical == 0:
        if unit_cost is None or not cost_source:
            raise ValidationError({"unit_cost": "No se puede aumentar un stock físico en cero sin un costo fiable documentado. Indique costo positivo y fuente del costo."})
        output_cost = unit_cost
    else:
        output_cost = locked_product.average_cost
        if output_cost <= 0:
            raise ValidationError("El costo promedio del stock existente no es fiable. Investigue antes de ajustar.")
        if unit_cost is not None and unit_cost != output_cost:
            raise ValidationError({"unit_cost": "Con existencias físicas el ajuste utiliza el costo promedio vigente; no indique un costo diferente."})
    identifier = uuid.uuid4()
    if new_lot:
        # A named existing commercial lot must be selected explicitly, not duplicated by a count.
        identities = LotModel.objects.filter(product=locked_product).values_list("number_normalized", flat=True)
        if any(LotModel.normalize_number(value) == number for value in identities):
            raise ValidationError({"number": "Ese lote ya está registrado. Seleccione su origen existente; no cree otro lote por ajuste."})
        locked_lot = LotModel.objects.create(product=locked_product, initial_load=initial, is_initial=False,
            responsible=locked_actor, number=number, initial_quantity=delta, available_quantity=delta,
            unit_cost=output_cost, expiration_date=expiration_date)
        origin = f"AJUSTE {identifier}"
    else:
        receipt_line = getattr(locked_lot, "receipt_line", None)
        initial_line = getattr(locked_lot, "initial_line", None)
        if locked_lot.adjustment_origin_id:
            origin = f"AJUSTE {locked_lot.adjustment_origin_id}"
        elif receipt_line is not None and initial_line is None and receipt_line.receipt.product_id == product_id:
            origin = f"Recepción {receipt_line.receipt.correlative}"
        elif initial_line is not None and receipt_line is None and initial_line.load.product_id == product_id:
            origin = f"Carga inicial {initial_line.load_id}"
        else:
            origin = "Origen no disponible (registro anterior o incompleto)"
    try:
        with transaction.atomic():
            adjustment = PhysicalAdjustment.objects.create(id=identifier, lot=locked_lot, delta=delta,
                unit_cost=output_cost, reason=reason, responsible=locked_actor,
                idempotency_key=key, content_signature=signature,
                product_snapshot_name=locked_product.name, product_snapshot_barcode=locked_product.barcode,
                unit_snapshot=locked_product.unit, responsible_snapshot_name=locked_actor.display_name,
                lot_snapshot_number=locked_lot.number_normalized or locked_lot.number,
                lot_snapshot_expiration_date=locked_lot.expiration_date,
                origin_snapshot=origin, cost_source=cost_source or "Promedio vigente sobre existencias físicas",
            )
    except IntegrityError as exc:
        # A different actor reusing a key on another product cannot retrieve its document.
        raise ValidationError("La clave de operación ya fue utilizada para otra solicitud. Recargue el formulario e inténtelo nuevamente.") from exc
    if new_lot:
        locked_lot.adjustment_origin = adjustment
        locked_lot.save(update_fields=["adjustment_origin"])
    else:
        locked_lot.available_quantity += delta
        if delta > 0:
            # Mutable capacity is not the immutable received quantity stored in source lines.
            locked_lot.initial_quantity += delta
            locked_lot.save(update_fields=["available_quantity", "initial_quantity"])
        else:
            locked_lot.save(update_fields=["available_quantity"])
    if delta > 0 and physical == 0:
        locked_product.average_cost = output_cost
        locked_product.save(update_fields=["average_cost", "updated_at"])
    reset_average_cost_if_empty(locked_product)
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
    idempotency_key=None,
) -> StockReceipt:
    """Registra una entrada posterior (no inicial) de lotes y recalcula el costo promedio.

    Requiere que el producto ya tenga su carga inicial confirmada (HU-INV-01a).
    Solo ALMACENERO puede ejecutar esta acción.
    """
    from catalog.models import Product as ProductModel
    from .models import InitialInventoryLoad as IIL

    locked_actor = _lock_warehouse_actor(actor, "Solo el almacenero puede registrar entradas de inventario.")

    current_date = business_date or timezone.localdate()
    # Normalize before replay; a confirmed receipt remains retrievable after expiry
    # or deactivation. New receipts revalidate all current state below.
    validated = _validate_lots(lots, business_date=current_date, check_expiration=False)

    if not isinstance(product, ProductModel) or product.pk is None:
        raise ValidationError("El producto seleccionado no es válido.")
    if supplier is not None and (not isinstance(supplier, Supplier) or supplier.pk is None):
        raise ValidationError("El proveedor seleccionado no es válido.")
    try:
        key = uuid.uuid4() if idempotency_key is None else uuid.UUID(str(idempotency_key))
    except (ValueError, TypeError, AttributeError) as exc:
        raise ValidationError("La clave de recepción no es válida. Vuelva a abrir el formulario.") from exc
    content = {"product": str(product.pk), "supplier": str(supplier.pk) if supplier else None,
        "lots": sorted((item.number, item.quantity, format(item.unit_cost, ".4f"),
                        item.expiration_date.isoformat()) for item in validated)}
    signature = hashlib.sha256(json.dumps(content, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    # Serialize receipt identity and the global sequence before locking the product.
    # Atomic get_or_create handles first use; uniqueness is also enforced in the DB.
    StockReceiptCounter.objects.get_or_create(key="global")
    counter = StockReceiptCounter.objects.select_for_update().get(key="global")
    existing = StockReceipt.objects.filter(idempotency_key=key).first()
    if existing is not None:
        if existing.responsible_id != locked_actor.pk or existing.content_signature != signature:
            raise ValidationError("La clave de recepción ya fue utilizada con otro contenido o responsable.")
        return existing
    _validate_lots(validated, business_date=current_date)
    if counter.last_number >= 99999999:
        raise ValidationError("Se agotó la capacidad de referencias de recepción. Solicite revisión administrativa.")
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

    prior_identities = list(Lot.objects.filter(product=locked_product).values_list("number_normalized", "expiration_date"))
    for item in validated:
        if any(Lot.normalize_number(number) == item.number and expires != item.expiration_date
               for number, expires in prior_identities):
            raise ValidationError(f"El lote {item.number} ya existe con otro vencimiento. Aclare la fecha antes de confirmar.")

    # Keep the legacy mandatory FK as a technical link, never as receipt identity.
    existing_load = IIL.objects.get(product=locked_product)
    # RN-14 values all physical stock, including expired units, at the
    # previous moving average. Expiration alone does not remove inventory.
    previous_lots = Lot.objects.filter(product=locked_product, available_quantity__gt=0)
    previous_quantity = sum(previous_lots.values_list('available_quantity', flat=True))
    incoming_quantity = sum(item.quantity for item in validated)
    incoming_cost = sum(item.unit_cost * item.quantity for item in validated)
    average = ((previous_quantity * locked_product.average_cost + incoming_cost)
               / (previous_quantity + incoming_quantity)).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
    try:
        with transaction.atomic():
            counter.last_number += 1
            counter.save(update_fields=["last_number"])
            receipt = StockReceipt.objects.create(
                product=locked_product, responsible=locked_actor, supplier=supplier,
                idempotency_key=key, content_signature=signature,
                correlative=f"R-{counter.last_number:08d}", average_cost_after=average,
                product_snapshot_name=locked_product.name, product_snapshot_barcode=locked_product.barcode,
                responsible_snapshot_name=locked_actor.display_name,
                supplier_snapshot_name=supplier.name if supplier else "",
                supplier_snapshot_ruc=supplier.ruc if supplier else "",
            )
            created_lots = Lot.objects.bulk_create(
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
            StockReceiptLine.objects.bulk_create([
                StockReceiptLine(receipt=receipt, lot=lot, number=item.number, quantity=item.quantity,
                                 unit_cost=item.unit_cost, expiration_date=item.expiration_date)
                for lot, item in zip(created_lots, validated)
            ])
    except IntegrityError as exc:
        raise ValidationError("La entrada no pudo registrarse porque otro intento o lote entró en conflicto.") from exc

    locked_product.average_cost = average
    locked_product.save(update_fields=('average_cost', 'updated_at'))
    return receipt
