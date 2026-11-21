from __future__ import annotations

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction

from identity.models import Account, Role

from .models import Category, Product


@transaction.atomic
def create_category(*, actor: Account, name: str) -> Category:
    """Create a new active product category (ADMIN only)."""
    if not actor.is_authenticated or actor.role.code != Role.Code.ADMIN:
        raise PermissionDenied("No tiene permiso para crear categorías.")
    name = name.strip()
    if not name:
        raise ValidationError({"name": "Ingrese el nombre de la categoría."})
    normalized = name.casefold()
    if Category.objects.filter(name_normalized=normalized).exists():
        raise ValidationError({"name": "Ya existe una categoría con ese nombre."})
    return Category.objects.create(name=name)


@transaction.atomic
def toggle_category_status(*, actor: Account, category: Category) -> Category:
    """Toggle the is_active flag for a category (ADMIN only)."""
    if not actor.is_authenticated or actor.role.code != Role.Code.ADMIN:
        raise PermissionDenied("No tiene permiso para cambiar el estado de categorías.")
    category.is_active = not category.is_active
    category.save(update_fields=["is_active"])
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
) -> Product:
    """Edit a registered product's commercial data (ADMIN only)."""
    import re
    from sales.models import SaleLine

    if not actor.is_authenticated or actor.role.code != Role.Code.ADMIN:
        raise PermissionDenied("No tiene permiso para editar productos.")
    clean_bc = (barcode or "").strip()
    if not re.fullmatch(r"[A-Za-z0-9\s\-]+", clean_bc):
        raise ValidationError(
            {"barcode": "El código de barras solo puede contener letras, números, espacios o guiones."}
        )
    old_barcode = product.barcode
    product.name = name.strip()
    product.barcode = clean_bc
    product.barcode_normalized = Product.normalize_barcode(clean_bc)
    product.sale_price = sale_price
    product.minimum_stock = minimum_stock
    update_fields = ["name", "barcode", "barcode_normalized", "sale_price", "minimum_stock", "updated_at"]
    if category is not None:
        if not category.is_active and category.pk != product.category_id:
            raise ValidationError({"category": "Seleccione una categoría activa."})
        product.category = category
        update_fields.append("category")
    try:
        product.full_clean(validate_unique=False)
        product.save(update_fields=update_fields)
    except IntegrityError as exc:
        raise ValidationError({"barcode": "Ya existe un producto con este código de barras."}) from exc
    if old_barcode and old_barcode != product.barcode:
        SaleLine.objects.filter(product__isnull=True, product_snapshot_barcode=old_barcode).update(
            product=product
        )
    return product


@transaction.atomic
def toggle_product_availability(*, actor: Account, product: Product) -> Product:
    """Toggle the is_active flag for a product (ADMIN only)."""
    if not actor.is_authenticated or actor.role.code != Role.Code.ADMIN:
        raise PermissionDenied("No tiene permiso para cambiar la disponibilidad de productos.")
    product.is_active = not product.is_active
    product.save(update_fields=["is_active", "updated_at"])
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
) -> Product:
    """Register a zero-stock canned product with server-side authorization."""
    if not actor.is_authenticated or actor.role.code != Role.Code.ADMIN:
        raise PermissionDenied("No tiene permiso para registrar productos.")

    product = Product(
        name=name,
        barcode=barcode,
        barcode_normalized=Product.normalize_barcode(barcode),
        category=category,
        unit=unit,
        sale_price=sale_price,
        minimum_stock=10 if minimum_stock is None else minimum_stock,
        controls_expiration=True,
    )
    # The database remains the final arbiter for the normalized unique code,
    # which also closes the race between two simultaneous registrations.
    product.full_clean(validate_unique=False)
    try:
        with transaction.atomic():
            product.save(force_insert=True)
    except IntegrityError as exc:
        if Product.objects.filter(barcode_normalized=Product.normalize_barcode(barcode)).exists():
            raise ValidationError({"barcode": "Ya existe un producto con este código de barras."}) from exc
        raise
    return product
