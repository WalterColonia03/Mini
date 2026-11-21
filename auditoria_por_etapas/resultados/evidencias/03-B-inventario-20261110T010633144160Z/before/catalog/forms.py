from __future__ import annotations

import re
from decimal import Decimal

from django import forms
from django.core.validators import MaxValueValidator

from .models import Category, Product

BARCODE_PATTERN = re.compile(r"^[A-Za-z0-9\s\-]+$")


class CategoryForm(forms.Form):
    name = forms.CharField(
        label="Nombre de la categoría",
        max_length=120,
        error_messages={"required": "El nombre es obligatorio"},
        widget=forms.TextInput(attrs={"autofocus": True, "autocomplete": "off"}),
    )

    def clean_name(self) -> str:
        value = Category.normalize_name(self.cleaned_data["name"])
        if not any(ch.isalnum() for ch in value):
            raise forms.ValidationError("El nombre de la categoría debe contener letras o números.")
        return value


class ProductRegistrationForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ("name", "barcode", "category", "unit", "sale_price", "minimum_stock")
        labels = {
            "name": "Nombre del producto",
            "barcode": "Código de barras",
            "category": "Categoría",
            "unit": "Unidad de medida",
            "sale_price": "Precio final con IGV (S/)",
            "minimum_stock": "Existencia mínima",
        }
        help_texts = {
            "barcode": "Debe ser único. Se ignorarán espacios exteriores e internos al compararlo.",
            "sale_price": "Mayor que cero y con un máximo de dos decimales.",
            "minimum_stock": "Entero mayor o igual que cero. Si lo deja vacío, se guardará 10.",
        }
        widgets = {
            "name": forms.TextInput(attrs={"autocomplete": "off", "autofocus": True}),
            "barcode": forms.TextInput(attrs={"autocomplete": "off", "inputmode": "numeric"}),
            "sale_price": forms.NumberInput(attrs={"min": "0.01", "step": "0.01", "inputmode": "decimal"}),
            "minimum_stock": forms.NumberInput(attrs={"min": "0", "max": "999999", "step": "1", "inputmode": "numeric"}),
        }

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.fields["category"].queryset = Category.objects.filter(
            is_active=True
        ).order_by("name_normalized")
        self.fields["category"].error_messages.update(
            {
                "invalid_choice": "Seleccione una categoría válida de la lista.",
                "required": "Este campo es obligatorio.",
            }
        )
        self.fields["sale_price"].validators.append(
            MaxValueValidator(
                Decimal("9999999.99"),
                message="El precio no puede superar S/ 9,999,999.99.",
            )
        )
        self.fields["minimum_stock"].required = False
        self.fields["minimum_stock"].validators.append(
            MaxValueValidator(999999, message="Asegúrese de que este valor sea menor o igual a 999999.")
        )

    def clean_name(self) -> str:
        value = " ".join(self.cleaned_data["name"].split())
        if not any(ch.isalnum() for ch in value):
            raise forms.ValidationError("El nombre del producto debe contener letras o números.")
        if Product.objects.filter(name__iexact=value).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("Ya existe un producto registrado con este nombre.")
        return value

    def clean_sale_price(self):
        raw = str(self.data.get("sale_price", ""))
        if "e" in raw.lower():
            raise forms.ValidationError("Introduzca un número decimal válido sin notación científica.")
        return self.cleaned_data["sale_price"]

    def clean_minimum_stock(self) -> int:
        value = self.cleaned_data.get("minimum_stock")
        return 10 if value is None else value

    def clean_barcode(self) -> str:
        value = (self.cleaned_data.get("barcode") or "").strip()
        if not BARCODE_PATTERN.fullmatch(value):
            raise forms.ValidationError(
                "El código de barras solo puede contener letras, números, espacios o guiones."
            )
        normalized = Product.normalize_barcode(value)
        if Product.objects.filter(barcode_normalized=normalized).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("Ya existe un producto con este código de barras.")
        return value


class ProductEditForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ("name", "barcode", "category", "sale_price", "minimum_stock")
        labels = {
            "name": "Nombre del producto",
            "barcode": "Código de barras",
            "category": "Categoría",
            "sale_price": "Precio final con IGV (S/)",
            "minimum_stock": "Existencia mínima",
        }
        widgets = {
            "name": forms.TextInput(attrs={"autofocus": True, "autocomplete": "off"}),
            "barcode": forms.TextInput(attrs={"autocomplete": "off", "inputmode": "numeric"}),
            "sale_price": forms.NumberInput(attrs={"min": "0.01", "step": "0.01", "inputmode": "decimal"}),
            "minimum_stock": forms.NumberInput(attrs={"min": "0", "max": "999999", "step": "1", "inputmode": "numeric"}),
        }

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.fields["category"].required = False
        qs = Category.objects.filter(is_active=True)
        if self.instance and self.instance.pk and self.instance.category_id:
            qs = Category.objects.filter(pk=self.instance.category_id) | qs
        self.fields["category"].queryset = qs.order_by("name_normalized").distinct()
        self.fields["sale_price"].validators.append(
            MaxValueValidator(
                Decimal("9999999.99"),
                message="El precio no puede superar S/ 9,999,999.99.",
            )
        )
        self.fields["minimum_stock"].validators.append(
            MaxValueValidator(999999, message="Asegúrese de que este valor sea menor o igual a 999999.")
        )

    def clean_category(self):
        return self.cleaned_data.get("category") or self.instance.category

    def clean_name(self) -> str:
        value = " ".join(self.cleaned_data["name"].split())
        if not any(ch.isalnum() for ch in value):
            raise forms.ValidationError("El nombre del producto debe contener letras o números.")
        if Product.objects.filter(name__iexact=value).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("Ya existe un producto registrado con este nombre.")
        return value

    def clean_sale_price(self):
        raw = str(self.data.get("sale_price", ""))
        if "e" in raw.lower():
            raise forms.ValidationError("Introduzca un número decimal válido sin notación científica.")
        return self.cleaned_data["sale_price"]

    def clean_barcode(self) -> str:
        value = (self.cleaned_data.get("barcode") or "").strip()
        if not BARCODE_PATTERN.fullmatch(value):
            raise forms.ValidationError(
                "El código de barras solo puede contener letras, números, espacios o guiones."
            )
        normalized = Product.normalize_barcode(value)
        if Product.objects.filter(barcode_normalized=normalized).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("Ya existe un producto con este código de barras.")
        return value

