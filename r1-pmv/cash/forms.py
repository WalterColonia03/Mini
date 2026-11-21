from decimal import Decimal

from django import forms


def _clean_cash_amount(form: forms.Form, field_name: str) -> Decimal:
    raw = str(form.data.get(field_name, "")).strip()
    if not raw.isascii() or raw.startswith("+"):
        raise forms.ValidationError("Introduzca el monto usando únicamente dígitos ASCII (0-9) y punto decimal.")
    if "e" in raw.lower():
        raise forms.ValidationError("Introduzca un monto decimal válido sin notación científica.")
    value = form.cleaned_data[field_name].quantize(Decimal("0.01"))
    if value == 0:
        return Decimal("0.00")
    return value


class CashOpeningForm(forms.Form):
    opening_amount = forms.DecimalField(
        label="Monto inicial (S/)",
        min_value=Decimal("0.00"),
        max_value=Decimal("9999999.99"),
        max_digits=12,
        decimal_places=2,
        widget=forms.NumberInput(
            attrs={
                "min": "0.00",
                "max": "9999999.99",
                "step": "0.01",
                "inputmode": "decimal",
                "autofocus": True,
                "placeholder": "0.00",
            }
        ),
    )

    def clean_opening_amount(self):
        return _clean_cash_amount(self, "opening_amount")


class CashCloseForm(forms.Form):
    counted_amount = forms.DecimalField(
        label="Monto contado (S/)",
        min_value=Decimal("0.00"),
        max_value=Decimal("999999999999.99"),
        max_digits=14,
        decimal_places=2,
        widget=forms.NumberInput(
            attrs={
                "min": "0.00",
                "max": "999999999999.99",
                "step": "0.01",
                "inputmode": "decimal",
                "autofocus": True,
                "placeholder": "0.00",
            }
        ),
    )

    def clean_counted_amount(self):
        return _clean_cash_amount(self, "counted_amount")
