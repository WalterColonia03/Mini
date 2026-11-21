from __future__ import annotations

import re
import uuid
from calendar import monthrange
from datetime import date
from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import F, Q
from django.utils import timezone

from catalog.models import Product


class InitialInventoryLoad(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.OneToOneField(
        Product,
        on_delete=models.PROTECT,
        related_name="initial_load",
    )
    responsible = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="initial_inventory_loads",
    )
    confirmed_at = models.DateTimeField(auto_now_add=True)
    # NULL means the original load predates snapshots; never backfill from current masters.
    product_snapshot_name = models.CharField(max_length=160, null=True, editable=False)
    product_snapshot_barcode = models.CharField(max_length=64, null=True, editable=False)
    unit_snapshot = models.CharField(max_length=8, null=True, editable=False)
    responsible_snapshot_name = models.CharField(max_length=120, null=True, editable=False)
    supplier_snapshot_name = models.CharField(max_length=160, null=True, editable=False)
    supplier_snapshot_ruc = models.CharField(max_length=11, null=True, editable=False)
    average_cost_snapshot = models.DecimalField(max_digits=14, decimal_places=4, null=True, editable=False)

    class Meta:
        ordering = ["-confirmed_at"]

    def __str__(self) -> str:
        return f"Carga inicial · {self.product.name}"


class Lot(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="lots")
    initial_load = models.ForeignKey(
        InitialInventoryLoad,
        on_delete=models.PROTECT,
        related_name="lots",
    )
    supplier = models.ForeignKey(
        "Supplier",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="lots",
    )
    responsible = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="received_lots",
    )
    is_initial = models.BooleanField(default=True)
    adjustment_origin = models.OneToOneField(
        "PhysicalAdjustment", null=True, blank=True, on_delete=models.PROTECT,
        related_name="created_lot", editable=False,
    )
    number = models.CharField(max_length=64)
    number_normalized = models.CharField(max_length=64, editable=False)
    initial_quantity = models.PositiveIntegerField()
    available_quantity = models.PositiveIntegerField()
    unit_cost = models.DecimalField(
        max_digits=14,
        decimal_places=4,
        validators=[MinValueValidator(Decimal("0.0001"))],
    )
    expiration_date = models.DateField()
    received_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["expiration_date", "received_at", "id"]
        constraints = [
            models.UniqueConstraint(fields=("product", "number_normalized"), condition=Q(is_initial=True), name="lot_initial_number_unique"),
            models.CheckConstraint(condition=Q(initial_quantity__gt=0), name="lot_initial_quantity_gt_zero"),
            models.CheckConstraint(condition=Q(available_quantity__gte=0), name="lot_available_quantity_gte_zero"),
            models.CheckConstraint(condition=Q(available_quantity__lte=F("initial_quantity")), name="lot_available_lte_initial"),
            models.CheckConstraint(condition=Q(unit_cost__gt=0), name="lot_unit_cost_gt_zero"),
        ]
        indexes = [models.Index(fields=("product", "expiration_date", "received_at"), name="lot_fefo_idx")]

    @staticmethod
    def normalize_number(value: str) -> str:
        return " ".join((value or "").split()).upper()

    @staticmethod
    def latest_expiration_date(business_date: date) -> date:
        year = business_date.year + 20
        day = min(business_date.day, monthrange(year, business_date.month)[1])
        return date(year, business_date.month, day)

    def clean(self) -> None:
        super().clean()
        if not isinstance(self.number, str) or "\x00" in self.number:
            raise ValidationError({"number": "El número de lote contiene un carácter no válido."})
        self.number = self.number.strip()
        self.number_normalized = self.normalize_number(self.number)
        if not self.number_normalized:
            raise ValidationError({"number": "Ingrese el número de lote."})
        if self.expiration_date:
            today = timezone.localdate()
            if self.expiration_date <= today and not self.adjustment_origin_id:
                raise ValidationError({"expiration_date": "El vencimiento debe ser posterior a hoy en Lima."})
            if self.expiration_date > self.latest_expiration_date(today):
                raise ValidationError({"expiration_date": "El vencimiento no puede superar 20 años en el futuro."})
        if self.initial_load_id and self.product_id != self.initial_load.product_id:
            raise ValidationError("El lote y la carga deben pertenecer al mismo producto.")

    def save(self, *args, **kwargs) -> None:
        fields = kwargs.get("update_fields")
        if not self._state.adding and (fields is None or "received_at" in fields):
            using = kwargs.get("using") or self._state.db
            original = type(self).objects.using(using).filter(pk=self.pk).values_list("received_at", flat=True).first()
            if original is not None and self.received_at != original:
                raise ValidationError({"received_at": "El instante de ingreso del lote no se puede modificar."})
        if self._state.adding or fields is None or "number" in fields or "number_normalized" in fields:
            self.number = self.number.strip()
            self.number_normalized = self.normalize_number(self.number)
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.product.name} · {self.number_normalized}"


# ── HU-PROV-01, HU-PROV-02, HU-PROV-04 · Proveedor ─────────────────────────


class InitialLoadLine(models.Model):
    """Original input values, separate from a lot's mutable stock capacity."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    load = models.ForeignKey(InitialInventoryLoad, on_delete=models.PROTECT, related_name="lines")
    lot = models.OneToOneField(Lot, on_delete=models.PROTECT, related_name="initial_line")
    number = models.CharField(max_length=64)
    quantity = models.PositiveIntegerField()
    unit_cost = models.DecimalField(max_digits=14, decimal_places=4)
    expiration_date = models.DateField()
    received_at = models.DateTimeField()

    class Meta:
        ordering = ["number", "id"]
        constraints = [
            models.UniqueConstraint(fields=("load", "number"), name="initial_line_number_unique"),
            models.CheckConstraint(condition=Q(quantity__gt=0), name="initial_line_quantity_positive"),
            models.CheckConstraint(condition=Q(unit_cost__gt=0), name="initial_line_cost_positive"),
        ]

SUPPLIER_RUC_PATTERN = re.compile(r"^[0-9]{11}$")
SUPPLIER_PHONE_PATTERN = re.compile(r"^[0-9\s+\-()]+$")
SUPPLIER_PHONE_DIGIT_PATTERN = re.compile(r"[0-9]")


class StockReceiptCounter(models.Model):
    key = models.CharField(max_length=16, primary_key=True, default="global")
    last_number = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [models.CheckConstraint(condition=Q(last_number__lte=99999999), name="receipt_counter_capacity")]


class StockReceipt(models.Model):
    """Confirmed entry, independent from the product's initial inventory load."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="stock_receipts")
    responsible = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="stock_receipts")
    supplier = models.ForeignKey("Supplier", null=True, blank=True, on_delete=models.PROTECT, related_name="stock_receipts")
    idempotency_key = models.UUIDField(unique=True, editable=False)
    content_signature = models.CharField(max_length=64, editable=False)
    correlative = models.CharField(max_length=10, unique=True, editable=False)
    confirmed_at = models.DateTimeField(auto_now_add=True)
    product_snapshot_name = models.CharField(max_length=160)
    product_snapshot_barcode = models.CharField(max_length=64)
    responsible_snapshot_name = models.CharField(max_length=120)
    supplier_snapshot_name = models.CharField(max_length=160, blank=True)
    supplier_snapshot_ruc = models.CharField(max_length=11, blank=True)
    average_cost_after = models.DecimalField(max_digits=14, decimal_places=4)

    class Meta:
        ordering = ["-confirmed_at", "-correlative"]
        constraints = [models.CheckConstraint(condition=Q(average_cost_after__gt=0), name="receipt_average_positive")]

    def __str__(self):
        return self.correlative


class StockReceiptLine(models.Model):
    """Immutable input values; lot capacity/balance can change in later operations."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    receipt = models.ForeignKey(StockReceipt, on_delete=models.PROTECT, related_name="lines")
    lot = models.OneToOneField(Lot, on_delete=models.PROTECT, related_name="receipt_line")
    number = models.CharField(max_length=64)
    quantity = models.PositiveIntegerField()
    unit_cost = models.DecimalField(max_digits=14, decimal_places=4)
    expiration_date = models.DateField()

    class Meta:
        ordering = ["number", "id"]
        constraints = [
            models.UniqueConstraint(fields=("receipt", "number"), name="receipt_line_number_unique"),
            models.CheckConstraint(condition=Q(quantity__gt=0), name="receipt_line_quantity_positive"),
            models.CheckConstraint(condition=Q(unit_cost__gt=0), name="receipt_line_cost_positive"),
        ]

    @property
    def amount(self):
        return self.quantity * self.unit_cost


class Supplier(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=160, verbose_name="Nombre comercial")
    ruc = models.CharField(max_length=11, unique=True, verbose_name="RUC")
    phone = models.CharField(max_length=20, blank=True, verbose_name="Teléfono")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    @staticmethod
    def normalize_name(value: str) -> str:
        return " ".join((value or "").split())

    @staticmethod
    def normalize_phone(value: str) -> str:
        return " ".join((value or "").split())

    def clean(self) -> None:
        super().clean()
        for field_name in ("name", "ruc", "phone"):
            raw = getattr(self, field_name, "")
            if isinstance(raw, str) and "\x00" in raw:
                raise ValidationError({field_name: "El campo contiene un carácter no válido."})
        self.name = self.normalize_name(self.name)
        if not self.name:
            raise ValidationError({"name": "El nombre del proveedor es obligatorio."})
        if not any(ch.isalnum() for ch in self.name):
            raise ValidationError({"name": "El nombre comercial debe contener letras o números."})
        if len(self.name) > 160:
            raise ValidationError({"name": "El nombre admite hasta 160 caracteres."})

        self.ruc = (self.ruc or "").strip()
        if not self.ruc:
            raise ValidationError({"ruc": "El RUC es obligatorio."})
        if not SUPPLIER_RUC_PATTERN.fullmatch(self.ruc):
            raise ValidationError({"ruc": "El RUC debe contener exactamente 11 dígitos numéricos."})

        self.phone = self.normalize_phone(self.phone)
        if self.phone:
            if len(self.phone) > 20:
                raise ValidationError({"phone": "El teléfono admite hasta 20 caracteres."})
            if not SUPPLIER_PHONE_PATTERN.fullmatch(self.phone) or not SUPPLIER_PHONE_DIGIT_PATTERN.search(self.phone):
                raise ValidationError(
                    {
                        "phone": (
                            "El teléfono debe incluir al menos un dígito y solo puede contener "
                            "números, espacios y signos (+, -, paréntesis)."
                        )
                    }
                )

    def __str__(self) -> str:
        return f"{self.name} ({self.ruc})"


# ── HU-INV-02 · Baja de inventario por merma ─────────────────────────────────

class StockWriteOff(models.Model):
    class Reason(models.TextChoices):
        EXPIRATION = "VENCIMIENTO", "Vencimiento"
        DAMAGE = "DAÑO", "Daño o rotura"
        THEFT = "ROBO", "Robo o faltante"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    lot = models.ForeignKey(Lot, on_delete=models.PROTECT, related_name="write_offs")
    quantity = models.PositiveIntegerField()
    # NULL denotes a historical cost that was never captured; do not infer it.
    unit_cost = models.DecimalField(max_digits=14, decimal_places=4, null=True, editable=False)
    reason = models.CharField(max_length=12, choices=Reason.choices)
    notes = models.TextField(blank=True)
    responsible = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="write_offs",
    )
    correlativo = models.CharField(max_length=20, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    # NULL is intentional for pre-snapshot records; no historical backfill.
    idempotency_key = models.UUIDField(unique=True, null=True, editable=False)
    content_signature = models.CharField(max_length=64, null=True, editable=False)
    product_snapshot_name = models.CharField(max_length=160, null=True, editable=False)
    product_snapshot_barcode = models.CharField(max_length=64, null=True, editable=False)
    unit_snapshot = models.CharField(max_length=8, null=True, editable=False)
    responsible_snapshot_name = models.CharField(max_length=120, null=True, editable=False)
    lot_snapshot_number = models.CharField(max_length=64, null=True, editable=False)
    lot_snapshot_expiration_date = models.DateField(null=True, editable=False)
    origin_snapshot = models.CharField(max_length=160, null=True, editable=False)

    @property
    def has_snapshot(self):
        return all(getattr(self, name) is not None for name in (
            "product_snapshot_name", "product_snapshot_barcode", "unit_snapshot",
            "responsible_snapshot_name", "lot_snapshot_number", "lot_snapshot_expiration_date", "origin_snapshot",
        ))

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(condition=Q(quantity__gt=0), name="writeoff_quantity_gt_zero"),
        ]

    def __str__(self) -> str:
        return f"Baja {self.correlativo} · {self.lot}"


# ── HU-INV-03 · Ajuste por conteo físico ─────────────────────────────────────

class PhysicalAdjustment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    lot = models.ForeignKey(Lot, on_delete=models.PROTECT, related_name="adjustments")
    delta = models.IntegerField(help_text="Positivo=entrada extra, negativo=faltante")
    unit_cost = models.DecimalField(max_digits=14, decimal_places=4, null=True, editable=False)
    reason = models.TextField()
    responsible = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="physical_adjustments",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    idempotency_key = models.UUIDField(unique=True, null=True, editable=False)
    content_signature = models.CharField(max_length=64, null=True, editable=False)
    product_snapshot_name = models.CharField(max_length=160, null=True, editable=False)
    product_snapshot_barcode = models.CharField(max_length=64, null=True, editable=False)
    unit_snapshot = models.CharField(max_length=8, null=True, editable=False)
    responsible_snapshot_name = models.CharField(max_length=120, null=True, editable=False)
    lot_snapshot_number = models.CharField(max_length=64, null=True, editable=False)
    lot_snapshot_expiration_date = models.DateField(null=True, editable=False)
    origin_snapshot = models.CharField(max_length=160, null=True, editable=False)
    cost_source = models.CharField(max_length=300, null=True, editable=False)

    @property
    def has_snapshot(self):
        return all(getattr(self, name) is not None for name in (
            "product_snapshot_name", "product_snapshot_barcode", "unit_snapshot",
            "responsible_snapshot_name", "lot_snapshot_number", "lot_snapshot_expiration_date", "origin_snapshot",
        ))

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(condition=~Q(delta=0), name="adjustment_delta_nonzero"),
        ]

    def __str__(self) -> str:
        return f"Ajuste {self.delta:+d} · {self.lot}"
