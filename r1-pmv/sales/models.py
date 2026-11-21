from __future__ import annotations

import uuid
from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import F, Q

from cash.models import CashShift
from catalog.models import Product


class SaleCounter(models.Model):
    """Single-row counter for global correlative numbers."""

    id = models.PositiveIntegerField(primary_key=True, default=1)
    next_value = models.PositiveIntegerField(default=1)

    class Meta:
        pass

    def __str__(self) -> str:
        return f"SaleCounter(next={self.next_value})"


class SaleDraft(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "En preparación"
        DISCARDED = "DISCARDED", "Descartado"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cash_shift = models.ForeignKey(CashShift, on_delete=models.PROTECT, related_name="sale_drafts")
    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="sale_drafts",
    )
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    discarded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        constraints = [
            models.CheckConstraint(
                condition=Q(status__in=("ACTIVE", "DISCARDED")),
                name="sale_draft_valid_status",
            ),
            models.UniqueConstraint(
                fields=("cash_shift",),
                condition=Q(status="ACTIVE"),
                name="one_active_sale_draft_per_shift",
            ),
        ]

    def __str__(self) -> str:
        return f"Venta en preparación · {self.seller.display_name} · {self.status}"


class SaleDraftLine(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    draft = models.ForeignKey(SaleDraft, on_delete=models.PROTECT, related_name="lines")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="sale_draft_lines")
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["created_at", "id"]
        constraints = [
            models.CheckConstraint(condition=Q(quantity__gt=0), name="sale_draft_line_quantity_gt_zero"),
            models.CheckConstraint(condition=Q(quantity__lte=999999), name="sale_draft_line_quantity_max"),
            models.CheckConstraint(condition=Q(unit_price__gt=0), name="sale_draft_line_unit_price_gt_zero"),
            models.UniqueConstraint(fields=("draft", "product"), name="sale_draft_line_one_product"),
        ]

    @property
    def amount(self) -> Decimal:
        return self.unit_price * self.quantity

    def __str__(self) -> str:
        return f"{self.product.name} × {self.quantity}"


class Sale(models.Model):
    """Confirmed, immutable sale — amounts are stored as snapshots."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cash_shift = models.ForeignKey(CashShift, on_delete=models.PROTECT, related_name="sales")
    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="sales"
    )
    draft = models.OneToOneField(
        SaleDraft, on_delete=models.PROTECT, related_name="sale", null=True, blank=True
    )
    # NULL means that the historical value was never recorded.
    seller_snapshot_name = models.CharField(max_length=120, null=True, editable=False)
    cash_register_snapshot_code = models.CharField(max_length=32, null=True, editable=False)
    # Amount snapshots — never recalculate
    total_amount = models.DecimalField(max_digits=14, decimal_places=2)
    base_amount = models.DecimalField(max_digits=14, decimal_places=2)
    igv_amount = models.DecimalField(max_digits=14, decimal_places=2)
    discount_amount = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    # Payment
    cash_received = models.DecimalField(max_digits=14, decimal_places=2)
    change_given = models.DecimalField(max_digits=14, decimal_places=2)
    # Correlative: format V-00000001
    correlative = models.CharField(max_length=12, unique=True, editable=False)
    # Idempotency key sent with the form
    idempotency_key = models.UUIDField(unique=True)
    confirmed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-confirmed_at", "-correlative", "-id"]
        constraints = [
            models.CheckConstraint(condition=Q(**{field+"__gte":0,field+"__lte":Decimal("999999999999.99")}), name="sale_"+field+"_bounds")
            for field in ("total_amount", "base_amount", "igv_amount", "discount_amount", "cash_received", "change_given")
        ]

    def __str__(self) -> str:
        return f"{self.correlative} · {self.seller_snapshot_name or 'Vendedor histórico no disponible'}"

    @property
    def has_original_line_order(self) -> bool:
        lines = list(self.lines.all())
        return bool(lines) and all(line.position is not None for line in lines)


class SaleLine(models.Model):
    """One line of a confirmed sale with historical product snapshots."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sale = models.ForeignKey(Sale, on_delete=models.PROTECT, related_name="lines")
    position = models.PositiveIntegerField(null=True, editable=False)
    product = models.ForeignKey(
        Product,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="sale_lines",
    )
    product_snapshot_name = models.CharField(max_length=160)
    product_snapshot_barcode = models.CharField(max_length=64)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=14, decimal_places=2)
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    # NULL means an older sale whose cost was not captured; never backfill
    # from today's product cost. New checkouts capture four decimal places.
    unit_cost = models.DecimalField(max_digits=14, decimal_places=4, null=True, editable=False)

    class Meta:
        ordering = [F("position").asc(nulls_last=True), "id"]
        constraints = [
            models.CheckConstraint(condition=Q(position__isnull=True) | Q(position__gt=0), name="sale_line_position_positive"),
            models.UniqueConstraint(fields=("sale", "position"), name="sale_line_unique_position"),
        ]

    def __str__(self) -> str:
        return f"{self.product_snapshot_name} × {self.quantity}"


class SaleLotAllocation(models.Model):
    """Actual lot consumption recorded with the confirmed sale, never inferred."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    line = models.ForeignKey(SaleLine, on_delete=models.PROTECT, related_name="lot_allocations")
    lot = models.ForeignKey("inventory.Lot", on_delete=models.PROTECT, related_name="sale_allocations")
    quantity = models.PositiveIntegerField()
    lot_snapshot_number = models.CharField(max_length=64, editable=False)
    lot_snapshot_expiration_date = models.DateField(editable=False)
    lot_snapshot_received_at = models.DateTimeField(editable=False)

    class Meta:
        ordering = ["lot_snapshot_expiration_date", "lot_snapshot_received_at", "lot_id"]
        constraints = [
            models.CheckConstraint(condition=Q(quantity__gt=0), name="sale_allocation_quantity_positive"),
            models.UniqueConstraint(fields=("line", "lot"), name="sale_allocation_unique_line_lot"),
        ]

    def clean(self):
        super().clean()
        if self.line_id and self.lot_id and self.line.product_id != self.lot.product_id:
            raise ValidationError({"lot": "El lote no corresponde al producto de la venta."})
