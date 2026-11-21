from __future__ import annotations

from decimal import Decimal

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.db.models import F

from identity.models import Account, Role

from .barcodes import BARCODE_PATTERN, DUPLICATE_MESSAGE, reading_keys
from .models import Category, Product, ProductBarcodeKey


def _validate_sale_price(value) -> Decimal:
    # Keep service callers on the same Decimal-only contract as cash and sales.
    # The operation maximum is checked after an existing edit can be recovered.
    if not isinstance(value, Decimal) or not value.is_finite():
        raise ValidationError({"sale_price": "Ingrese un precio decimal válido con hasta dos decimales."})
    exponent = value.as_tuple().exponent
    if value <= 0 or not isinstance(exponent, int) or not -2 <= exponent <= 0:
        raise ValidationError({"sale_price": "Ingrese un precio positivo con hasta dos decimales, sin notación científica."})
    return value


def _save_product(product: Product, **kwargs) -> None:
    """Translate only an identified uniqueness conflict, after rollback."""
    try:
        with transaction.atomic():
            product.save(**kwargs)
    except IntegrityError as exc:
        others = Product.objects.exclude(pk=product.pk)
        if (others.filter(barcode_normalized=product.barcode_normalized).exists()
                or ProductBarcodeKey.objects.filter(reading_key__in=reading_keys(
                    product.barcode, product.barcode_type)).exclude(product_id=product.pk).exists()):
            raise ValidationError({"barcode": DUPLICATE_MESSAGE}) from exc
        if others.filter(search_name=product.search_name).exists():
            raise ValidationError({"name": "Ya existe un producto registrado con este nombre."}) from exc
        raise


@transaction.atomic
def create_category(*, actor: Account, name: str) -> Category:
    """Create a new active product category (ADMIN only)."""
    if not actor.is_authenticated or actor.role.code != Role.Code.ADMIN:
        raise PermissionDenied("No tiene permiso para crear categorías.")
    name = Category.normalize_name(name)
    if not name:
        raise ValidationError({"name": "El nombre es obligatorio"})
    normalized = name.casefold()
    if Category.objects.filter(name_normalized=normalized).exists():
        raise ValidationError({"name": "La categoría ya existe"})
    category = Category(name=name, name_normalized=normalized)
    category.full_clean(validate_unique=False)
    try:
        # Recover outside a savepoint: a duplicate race must not leave the
        # outer transaction broken or turn a validation failure into HTTP 500.
        with transaction.atomic():
            category.save()
    except IntegrityError as exc:
        if Category.objects.filter(name_normalized=normalized).exists():
            raise ValidationError({"name": "La categoría ya existe"}) from exc
        raise
    return category


STALE_CATEGORY_MESSAGE = "La categoría cambió desde que abrió esta pantalla. Revise el estado actual antes de continuar."
STALE_PRODUCT_MESSAGE = "El producto cambió desde que abrió esta pantalla. Revise la versión actual antes de guardar."


def product_edit_snapshot(product: Product) -> dict:
    return {
        "id": str(product.pk),
        "name": product.name,
        "barcode": product.barcode,
        "barcode_type": product.barcode_type,
        "category_id": str(product.category_id),
        "sale_price": str(product.sale_price),
        "minimum_stock": product.minimum_stock,
        "is_active": product.is_active,
    }


def _lock_unchanged_product(product: Product, snapshot) -> None:
    """Compare the opened version and take the row write lock in one statement.

    SQLite ignores SELECT ... FOR UPDATE, so a read-then-write check could let two
    stale forms pass or fail with a lock error. A conditional UPDATE is atomic on
    SQLite and is re-evaluated after a row-lock wait on PostgreSQL.
    """
    from decimal import Decimal, InvalidOperation

    stale = ValidationError(STALE_PRODUCT_MESSAGE, code="stale_product")
    if not isinstance(snapshot, dict) or set(snapshot) != set(product_edit_snapshot(product)):
        raise stale
    if snapshot["id"] != str(product.pk):
        raise stale
    try:
        price = Decimal(snapshot["sale_price"])
    except (InvalidOperation, TypeError, ValueError):
        raise stale from None
    if (type(snapshot["minimum_stock"]) is not int or type(snapshot["is_active"]) is not bool
            or not price.is_finite()):
        raise stale
    try:
        locked = Product.objects.filter(
            pk=product.pk, name=snapshot["name"], barcode=snapshot["barcode"],
            barcode_type=snapshot["barcode_type"],
            category_id=snapshot["category_id"], sale_price=price,
            minimum_stock=snapshot["minimum_stock"], is_active=snapshot["is_active"],
        ).update(updated_at=F("updated_at"))
    except (ValidationError, ValueError, TypeError):
        raise stale from None
    if not locked:
        raise stale


def _matches_requested(current: Product, name, barcode, sale_price, minimum_stock, category, barcode_type=None) -> bool:
    from decimal import Decimal, InvalidOperation

    try:
        same_price = current.sale_price == Decimal(str(sale_price))
    except (InvalidOperation, TypeError, ValueError):
        return False
    return (
        same_price
        and current.name == (name or "").strip()
        and current.barcode == (barcode or "").strip()
        and (barcode_type is None or current.barcode_type == barcode_type)
        and type(minimum_stock) is int and current.minimum_stock == minimum_stock
        and (category is None or current.category_id == category.pk)
    )


def toggle_category_status(
    *, actor: Account, category: Category, is_active: bool | None = None,
    expected_version: int | None = None,
) -> Category:
    """Set a category state, retaining toggle behavior for existing callers."""
    if not actor.is_authenticated or actor.role.code != Role.Code.ADMIN:
        raise PermissionDenied("No tiene permiso para cambiar el estado de categorías.")
    if is_active is not None and type(is_active) is not bool:
        raise ValidationError("Seleccione un estado válido para la categoría.")
    if expected_version is not None and (type(expected_version) is not int or expected_version < 0):
        raise ValidationError("Vuelva a abrir la confirmación desde Categorías.")
    row = Category.objects.filter(pk=category.pk)
    eligible = row if expected_version is None else row.filter(state_version=expected_version)
    if is_active is not None:
        eligible = eligible.exclude(is_active=is_active)
    # Compare the version and write in one statement, including on SQLite.
    with transaction.atomic():
        changed = eligible.update(is_active=~F("is_active") if is_active is None else is_active,
                                  state_version=F("state_version") + 1)
        active, version = row.values_list("is_active", "state_version").get()
        if not changed and expected_version is not None and expected_version != version:
            raise ValidationError(STALE_CATEGORY_MESSAGE, code="stale_category")
    category.is_active = active
    category.state_version = version
    return category


@transaction.atomic
def update_product(
    *,
    actor: Account,
    product: Product,
    name: str,
    barcode: str,
    sale_price,
    minimum_stock: int,
    category: Category | None = None,
    expected_snapshot: dict | None = None,
    barcode_type: str | None = None,
) -> Product:
    """Edit a registered product's commercial data (ADMIN only)."""
    from sales.models import SaleLine

    if not actor.is_authenticated or actor.role.code != Role.Code.ADMIN:
        raise PermissionDenied("No tiene permiso para editar productos.")
    sale_price = _validate_sale_price(sale_price)
    if expected_snapshot is not None:
        try:
            _lock_unchanged_product(product, expected_snapshot)
        except ValidationError:
            # A repeated submission (double click, reload) whose values are already
            # stored is not a conflict; anything else must be reviewed first.
            current = Product.objects.filter(pk=product.pk).first()
            if current is not None and _matches_requested(current, name, barcode, sale_price,
                                                          minimum_stock, category, barcode_type):
                return current
            raise
    current = Product.objects.select_for_update().get(pk=product.pk)
    if expected_snapshot is not None and product_edit_snapshot(current) != expected_snapshot:
        raise ValidationError(STALE_PRODUCT_MESSAGE, code="stale_product")
    clean_bc = (barcode or "").strip()
    if clean_bc != current.barcode and not BARCODE_PATTERN.fullmatch(clean_bc):
        raise ValidationError(
            {"barcode": "El código de barras solo puede contener letras, números, espacios o guiones."}
        )
    old_barcode = current.barcode
    product.name = name.strip()
    product.barcode = clean_bc
    product.barcode_normalized = Product.normalize_barcode(clean_bc)
    product.barcode_type = current.barcode_type if barcode_type is None else barcode_type
    product.sale_price = sale_price
    product.minimum_stock = minimum_stock
    update_fields = ["name", "barcode", "barcode_normalized", "barcode_type", "sale_price", "minimum_stock", "updated_at"]
    if category is not None:
        try:
            category = Category.objects.select_for_update().get(pk=category.pk)
        except Category.DoesNotExist:
            raise ValidationError({"category": "Seleccione una categoría activa."}) from None
        if not category.is_active and category.pk != current.category_id:
            raise ValidationError({"category": "Seleccione una categoría activa."})
        product.category = category
        update_fields.append("category")
    product.full_clean(validate_unique=False)
    if product.sale_price > Decimal("9999999.99"):
        raise ValidationError({"sale_price": "El precio no puede superar S/ 9999999.99."})
    _save_product(product, update_fields=update_fields)
    if old_barcode and old_barcode != product.barcode:
        SaleLine.objects.filter(product__isnull=True, product_snapshot_barcode=old_barcode).update(
            product=product
        )
    return product


@transaction.atomic
def toggle_product_availability(
    *, actor: Account, product: Product, is_active: bool | None = None, expected_version: str | None = None
) -> Product:
    """Set the requested state, or toggle for existing callers without a target."""
    if not actor.is_authenticated or actor.role.code != Role.Code.ADMIN:
        raise PermissionDenied("No tiene permiso para cambiar la disponibilidad de productos.")
    if is_active is not None and type(is_active) is not bool:
        raise ValidationError("Seleccione un estado válido para el producto.")
    current = Product.objects.select_for_update().get(pk=product.pk)
    target = not current.is_active if is_active is None else is_active
    if current.is_active != target:
        if expected_version is not None and expected_version != current.updated_at.isoformat():
            raise ValidationError("La ficha cambió. Revise la disponibilidad actual antes de confirmar.")
        current.is_active = target
        current.save(update_fields=["is_active", "updated_at"])
    product.is_active = current.is_active
    product.updated_at = current.updated_at
    return product


@transaction.atomic
def register_canned_product(
    *,
    actor: Account,
    name: str,
    barcode: str,
    category: Category,
    unit: str,
    sale_price,
    minimum_stock: int | None,
    barcode_type: str = Product.BarcodeType.UNCLASSIFIED,
) -> Product:
    """Register a zero-stock product with server-side authorization."""
    if not actor.is_authenticated or actor.role.code != Role.Code.ADMIN:
        raise PermissionDenied("No tiene permiso para registrar productos.")
    sale_price = _validate_sale_price(sale_price)

    # The category may have been suspended after form validation.
    try:
        category = Category.objects.select_for_update().get(pk=category.pk, is_active=True)
    except Category.DoesNotExist:
        raise ValidationError({"category": "Seleccione una categoría activa."}) from None

    product = Product(
        name=name,
        barcode=barcode,
        barcode_type=barcode_type,
        barcode_normalized=Product.normalize_barcode(barcode),
        category=category,
        unit=unit,
        sale_price=sale_price,
        minimum_stock=10 if minimum_stock is None else minimum_stock,
        controls_expiration=True,
    )
    # Unique normalized keys also close races between validated forms.
    product.full_clean(validate_unique=False)
    if product.sale_price > Decimal("9999999.99"):
        raise ValidationError({"sale_price": "El precio no puede superar S/ 9999999.99."})
    _save_product(product, force_insert=True)
    return product
