from __future__ import annotations

import unicodedata
import uuid
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models, router, transaction
from django.db.models import Q
from django.utils import timezone

from .barcodes import BARCODE_PATTERN, FORMAT_MESSAGE, DUPLICATE_MESSAGE, normalize_literal, reading_keys


class Category(models.Model):
    """Foundation category needed by the R1 product registration flow."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=120)
    name_normalized = models.CharField(max_length=120, unique=True, editable=False)
    is_active = models.BooleanField(default=True)
    state_version = models.PositiveBigIntegerField(default=0, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name_normalized"]

    @staticmethod
    def normalize_name(value: str) -> str:
        return " ".join((value or "").split())

    def clean(self) -> None:
        super().clean()
        self.name = self.normalize_name(self.name)
        self.name_normalized = self.name.casefold()
        if not self.name:
            raise ValidationError({"name": "El nombre es obligatorio"})
        if not any(ch.isalnum() for ch in self.name):
            raise ValidationError({"name": "El nombre de la categoría debe contener letras o números."})
        # casefold can expand characters; the unique database key has the same
        # bound as the display name. Report it on the editable field.
        if len(self.name_normalized) > 120:
            raise ValidationError({"name": "El nombre normalizado no puede superar 120 caracteres."})

    def save(self, *args, **kwargs) -> None:
        self.name = self.normalize_name(self.name)
        self.name_normalized = self.name.casefold()
        if kwargs.get("update_fields") and "name" in kwargs["update_fields"]:
            kwargs["update_fields"] = set(kwargs["update_fields"]) | {"name_normalized"}
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.name


class Product(models.Model):
    """Product sold by unit and registered by HU-PROD-02.

    Stock is intentionally derived from lots.  There is no editable stock field,
    which prevents product registration from making an item sellable by itself.
    """

    class Unit(models.TextChoices):
        UNIT = "UND", "Unidad (UND)"

    class BarcodeType(models.TextChoices):
        UNCLASSIFIED = "UNCLASSIFIED", "Sin clasificar (registro anterior)"
        INTERNAL = "INTERNAL", "Código interno"
        GTIN = "GTIN", "GTIN del fabricante"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="products")
    name = models.CharField(max_length=160)
    # Search independently of the database locale; preserve the commercial name.
    search_name = models.TextField(editable=False, unique=True)
    barcode = models.CharField(max_length=64)
    barcode_type = models.CharField(max_length=12, choices=BarcodeType.choices, default=BarcodeType.UNCLASSIFIED)
    barcode_normalized = models.CharField(max_length=64, unique=True, editable=False)
    unit = models.CharField(max_length=3, choices=Unit.choices, default=Unit.UNIT)
    sale_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    minimum_stock = models.PositiveIntegerField(
        default=10,
        validators=[MaxValueValidator(999999, message="Asegúrese de que este valor sea menor o igual a 999999.")],
    )
    controls_expiration = models.BooleanField(default=True, editable=False)
    average_cost = models.DecimalField(
        max_digits=14,
        decimal_places=4,
        default=Decimal("0.0000"),
        validators=[MinValueValidator(Decimal("0.0000"))],
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name", "barcode_normalized"]
        constraints = [
            models.CheckConstraint(condition=Q(sale_price__gt=0), name="product_sale_price_gt_zero"),
            models.CheckConstraint(condition=Q(minimum_stock__gte=0), name="product_minimum_stock_gte_zero"),
            models.CheckConstraint(condition=Q(minimum_stock__lte=999999), name="product_minimum_stock_lte_max"),
            models.CheckConstraint(condition=Q(average_cost__gte=0), name="product_average_cost_gte_zero"),
            models.CheckConstraint(condition=Q(controls_expiration=True), name="product_requires_expiration"),
            models.CheckConstraint(condition=Q(unit="UND"), name="product_unit_und_in_r1"),
            models.CheckConstraint(condition=Q(barcode_type__in=["UNCLASSIFIED", "INTERNAL", "GTIN"]), name="product_barcode_type_valid"),
        ]

    @staticmethod
    def normalize_search_name(value: str) -> str:
        return unicodedata.normalize("NFC", " ".join((value or "").split()).casefold())

    @staticmethod
    def normalize_barcode(value: str) -> str:
        return normalize_literal(value)

    def clean_fields(self, exclude=None) -> None:
        # Validate the trimmed values through Django's ordinary field errors.
        # ModelForm excludes fields it has already rejected.
        self.name = " ".join((self.name or "").split())
        self.search_name = self.normalize_search_name(self.name)
        self.barcode = (self.barcode or "").strip()
        self.barcode_normalized = self.normalize_barcode(self.barcode)
        if "minimum_stock" not in (exclude or ()):
            value = self.minimum_stock
            invalid_integer = isinstance(value, bool)
            if isinstance(value, (float, Decimal)):
                number = Decimal(str(value))
                invalid_integer = not number.is_finite() or number != number.to_integral_value()
            if invalid_integer:
                # IntegerField coerces numeric objects with int(), which would
                # silently truncate a fractional value supplied to a service.
                raise ValidationError({"minimum_stock": "El mínimo debe ser un número entero."})
        super().clean_fields(exclude=exclude)

    def clean(self) -> None:
        super().clean()
        # La validación de categoría verifica que la categoría esté activa al crear o al cambiar de categoría.
        if self.category_id and not self.category.is_active:
            if not (self.pk and Product.objects.filter(pk=self.pk, category_id=self.category_id).exists()):
                raise ValidationError({"category": "Seleccione una categoría activa."})
        if not self.controls_expiration:
            raise ValidationError({"controls_expiration": "El control de vencimiento es obligatorio para este producto."})
        keys = reading_keys(self.barcode, self.barcode_type)
        if ProductBarcodeKey.objects.filter(reading_key__in=keys).exclude(product_id=self.pk).exists():
            raise ValidationError({"barcode": DUPLICATE_MESSAGE})

    def save(self, *args, **kwargs) -> None:
        self.name = " ".join(self.name.split())
        self.search_name = self.normalize_search_name(self.name)
        fields = kwargs.get("update_fields")
        if fields is not None:
            fields = set(fields)
            if not fields:
                return
            if "name" in fields:
                fields.add("search_name")
            if "barcode" in fields:
                fields.add("barcode_normalized")
            kwargs["update_fields"] = fields
        self.barcode = self.barcode.strip()
        self.barcode_normalized = self.normalize_barcode(self.barcode)
        using = kwargs.get("using") or router.db_for_write(type(self), instance=self)
        with transaction.atomic(using=using):
            current = None
            if not self._state.adding:
                current = Product.objects.using(using).select_for_update().filter(pk=self.pk).values(
                    "barcode", "barcode_type"
                ).first()
            code, kind = self.barcode, self.barcode_type
            if current and fields is not None:
                if "barcode" not in fields:
                    code = current["barcode"]
                if "barcode_type" not in fields:
                    kind = current["barcode_type"]
            if (not current or current["barcode"] != code) and not BARCODE_PATTERN.fullmatch(code):
                raise ValidationError({"barcode": FORMAT_MESSAGE})
            keys = reading_keys(code, kind)
            super().save(*args, **kwargs)
            claims = ProductBarcodeKey.objects.using(using).filter(product_id=self.pk)
            old_keys = set(claims.values_list("reading_key", flat=True))
            # Reserve additions before releasing old spellings. The UNIQUE
            # constraint is the arbiter for concurrent validated requests.
            ProductBarcodeKey.objects.using(using).bulk_create([
                ProductBarcodeKey(product_id=self.pk, reading_key=key)
                for key in sorted(keys - old_keys)
            ])
            if old_keys - keys:
                claims.filter(reading_key__in=old_keys - keys).delete()

    @property
    def physical_stock(self) -> int:
        if self._state.adding or self.pk is None or not hasattr(self, "lots"):
            return 0
        prefetched = getattr(self, "_prefetched_objects_cache", {}).get("lots")
        if prefetched is not None:
            return sum(lot.available_quantity for lot in prefetched)
        return sum(self.lots.values_list("available_quantity", flat=True))

    @property
    def sellable_stock(self) -> int:
        if self._state.adding or self.pk is None or not hasattr(self, "lots"):
            return 0
        today = timezone.localdate()
        prefetched = getattr(self, "_prefetched_objects_cache", {}).get("lots")
        if prefetched is not None:
            return sum(
                lot.available_quantity
                for lot in prefetched
                if lot.expiration_date > today
            )
        return sum(
            self.lots.filter(expiration_date__gt=today).values_list(
                "available_quantity", flat=True
            )
        )

    @property
    def is_sellable(self) -> bool:
        return self.is_active and self.category.is_active and self.sellable_stock > 0

    def __str__(self) -> str:
        return f"{self.name} ({self.barcode})"


class ProductBarcodeKey(models.Model):
    """One scanner spelling belongs to at most one product, including inactive."""

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="barcode_keys")
    reading_key = models.CharField(max_length=64, unique=True)

    class Meta:
        ordering = ["reading_key"]
