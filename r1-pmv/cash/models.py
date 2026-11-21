from __future__ import annotations

import uuid
from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import F, Q
from django.db.models.functions import Round


class CashRegister(models.Model):
    """The single cash register seed; shifts are delivered by HU-CAJA-01."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=32, unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.code


class CashShift(models.Model):
    class Status(models.TextChoices):
        OPEN = "OPEN", "Abierto"
        CLOSED = "CLOSED", "Cerrado"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cash_register = models.ForeignKey(CashRegister, on_delete=models.PROTECT, related_name="shifts")
    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="cash_shifts",
    )
    opening_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    status = models.CharField(max_length=6, choices=Status.choices, default=Status.OPEN)
    opened_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-opened_at", "-id"]
        constraints = [
            models.CheckConstraint(condition=Q(opening_amount__gte=0), name="cash_shift_opening_amount_gte_zero"),
            models.CheckConstraint(condition=Q(status__in=("OPEN", "CLOSED")), name="cash_shift_valid_status"),
            models.UniqueConstraint(
                fields=("cash_register",),
                condition=Q(status="OPEN"),
                name="one_open_shift_per_register",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.cash_register.code} · {self.seller.display_name} · {self.status}"


class CashShiftClose(models.Model):
    """Record of a cash shift closure with counted vs expected amounts."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cash_shift = models.OneToOneField(
        CashShift, on_delete=models.PROTECT, related_name="close"
    )
    counted_amount = models.DecimalField(max_digits=14, decimal_places=2)
    expected_amount = models.DecimalField(max_digits=14, decimal_places=2)
    difference = models.DecimalField(max_digits=14, decimal_places=2)
    closed_at = models.DateTimeField(auto_now_add=True)
    closed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="cash_shift_closes",
    )

    class Meta:
        ordering = ["-closed_at", "-id"]
        constraints = [
            models.CheckConstraint(condition=Q(counted_amount__gte=0, counted_amount__lte=Decimal("999999999999.99")), name="cash_close_counted_bounds"),
            models.CheckConstraint(condition=Q(expected_amount__gte=0, expected_amount__lte=Decimal("999999999999.99")), name="cash_close_expected_bounds"),
            models.CheckConstraint(condition=Q(difference__gte=Decimal("-999999999999.99"), difference__lte=Decimal("999999999999.99")), name="cash_close_difference_bounds"),
            models.CheckConstraint(condition=Q(difference=Round(F("counted_amount")-F("expected_amount"),2)), name="cash_close_difference_consistent"),
        ]

    @property
    def difference_type(self) -> str:
        if self.difference < 0:
            return "SHORTAGE"
        if self.difference > 0:
            return "SURPLUS"
        return "EXACT"

    @property
    def difference_amount(self) -> Decimal:
        return self.difference

    def get_difference_type_display(self) -> str:
        if self.difference < 0:
            return "Faltante"
        if self.difference > 0:
            return "Sobrante"
        return "Exacto"

    def __str__(self) -> str:
        return f"Cierre · {self.cash_shift} · {self.closed_at}"
