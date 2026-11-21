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
            models.UniqueConstraint(fields=("product", "number_normalized"), name="lot_number_unique_per_product"),
            models.CheckConstraint(condition=Q(initial_quantity__gt=0), name="lot_initial_quantity_gt_zero"),
            models.CheckConstraint(condition=Q(available_quantity__gte=0), name="lot_available_quantity_gte_zero"),
            models.CheckConstraint(condition=Q(available_quantity__lte=F("initial_quantity")), name="lot_available_lte_initial"),
            models.CheckConstraint(condition=Q(unit_cost__gt=0), name="lot_unit_cost_gt_zero"),
        ]
        indexes = [models.Index(fields=("product", "expiration_date", "received_at"), name="lot_fefo_idx")]

    @staticmethod
    def normalize_number(value: str) -> str:
        return (value or "").strip().upper()

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
            if self.expiration_date <= today:
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
        self.number = self.number.strip()
        self.number_normalized = self.normalize_number(self.number)
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.product.name} · {self.number_normalized}"


# ── HU-PROV-01, HU-PROV-02, HU-PROV-04 · Proveedor ─────────────────────────

SUPPLIER_RUC_PATTERN = re.compile(r"^[0-9]{11}$")
SUPPLIER_PHONE_PATTERN = re.compile(r"^[0-9\s+\-()]+$")
SUPPLIER_PHONE_DIGIT_PATTERN = re.compile(r"[0-9]")


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
    reason = models.CharField(max_length=12, choices=Reason.choices)
    notes = models.TextField(blank=True)
    responsible = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="write_offs",
    )
    correlativo = models.CharField(max_length=20, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)

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
    reason = models.TextField()
    responsible = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="physical_adjustments",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(condition=~Q(delta=0), name="adjustment_delta_nonzero"),
        ]

    def __str__(self) -> str:
        return f"Ajuste {self.delta:+d} · {self.lot}"
