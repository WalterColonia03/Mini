from __future__ import annotations

import re
from decimal import Decimal

from django import forms

from .services import DISCOUNTS_DISABLED


def _validate_ascii_integer_quantity(raw_value: object, value: int) -> int:
    raw = str(raw_value or "").strip()
    if raw and (not raw.isascii() or raw.startswith("+")):
        raise forms.ValidationError("Ingrese una cantidad entera mayor que cero usando dígitos ASCII.")
    return value


class ProductSearchForm(forms.Form):
    query = forms.CharField(
        label="Buscar producto",
        required=False,
        max_length=160,
        widget=forms.TextInput(
            attrs={
                "type": "search",
                "autocomplete": "off",
                "placeholder": "Nombre o código de barras",
            }
        ),
    )


class AddDraftLineForm(forms.Form):
    product_id = forms.UUIDField(widget=forms.HiddenInput)
    quantity = forms.IntegerField(
        label="Cantidad",
        min_value=1,
        max_value=999999,
        widget=forms.NumberInput(attrs={"min": "1", "max": "999999", "step": "1", "inputmode": "numeric"}),
    )

    def clean_quantity(self) -> int:
        return _validate_ascii_integer_quantity(
            self.data.get(self.add_prefix("quantity"), ""),
            self.cleaned_data["quantity"],
        )


class UpdateDraftLineForm(forms.Form):
    quantity = forms.IntegerField(
        label="Cantidad",
        min_value=1,
        max_value=999999,
        widget=forms.NumberInput(attrs={"min": "1", "max": "999999", "step": "1", "inputmode": "numeric"}),
    )

    def clean_quantity(self) -> int:
        return _validate_ascii_integer_quantity(
            self.data.get(self.add_prefix("quantity"), ""),
            self.cleaned_data["quantity"],
        )


class BaseCheckoutForm(forms.Form):
    cash_received = forms.DecimalField(
        label="Efectivo recibido (S/)",
        min_value=Decimal("0.01"),
        max_value=Decimal("9999999.99"),
        max_digits=14,
        decimal_places=2,
        widget=forms.NumberInput(
            attrs={
                "min": "0.01",
                "max": "9999999.99",
                "step": "0.01",
                "inputmode": "decimal",
                "autofocus": True,
                "placeholder": "0.00",
            }
        ),
    )
    idempotency_key = forms.UUIDField(widget=forms.HiddenInput)
    expected_subtotal = forms.DecimalField(
        required=False,
        max_digits=14,
        decimal_places=2,
        widget=forms.HiddenInput,
    )
    draft_signature = forms.CharField(
        required=False,
        widget=forms.HiddenInput,
    )

    def clean_cash_received(self):
        raw = str(self.data.get(self.add_prefix("cash_received"), "")).strip()
        if raw:
            if not raw.isascii() or raw.startswith("+"):
                raise forms.ValidationError(
                    "Introduzca el monto usando únicamente dígitos ASCII (0-9) y punto decimal."
                )
            if "e" in raw.lower():
                raise forms.ValidationError("Introduzca un monto decimal válido sin notación científica.")
        value = self.cleaned_data["cash_received"].quantize(Decimal("0.01"))
        return Decimal("0.00") if value == 0 else value


class CheckoutForm(BaseCheckoutForm):
    def clean(self):
        cleaned = super().clean()
        name = self.add_prefix("discount_amount")
        values = self.data.getlist(name) if hasattr(self.data, "getlist") else [self.data.get(name, "")]
        if len(values) > 1 or any(value != "" and not re.fullmatch(r"0+(?:\.0{1,2})?", str(value)) for value in values):
            raise forms.ValidationError(DISCOUNTS_DISABLED)
        return cleaned


class ConfirmedCheckoutRetryForm(BaseCheckoutForm):
    """Validate the original amounts when recovering an already committed receipt."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["cash_received"].max_value = Decimal("999999999999.99")
        from django.core.validators import MaxValueValidator
        self.fields["cash_received"].validators = [v for v in self.fields["cash_received"].validators if not isinstance(v, MaxValueValidator)]
        self.fields["cash_received"].validators.append(MaxValueValidator(Decimal("999999999999.99")))
        self.fields["cash_received"].widget.attrs["max"] = "999999999999.99"

    discount_amount = forms.DecimalField(
        label="Descuento (S/) - opcional",
        required=False,
        min_value=Decimal("0.00"),
        max_value=Decimal("999999999999.99"),
        max_digits=14,
        decimal_places=2,
        widget=forms.NumberInput(attrs={"min": "0", "max": "999999999999.99", "step": "0.01", "inputmode": "decimal", "placeholder": "0.00"}),
    )

    def clean_discount_amount(self):
        raw = str(self.data.get(self.add_prefix("discount_amount"), "")).strip()
        if raw:
            if not raw.isascii() or raw.startswith("+"):
                raise forms.ValidationError(
                    "Introduzca el monto usando únicamente dígitos ASCII (0-9) y punto decimal."
                )
            if "e" in raw.lower():
                raise forms.ValidationError("Introduzca un monto decimal válido sin notación científica.")
        value = self.cleaned_data.get("discount_amount")
        if value is not None:
            value = value.quantize(Decimal("0.01"))
            if value == 0:
                return Decimal("0.00")
        return value
