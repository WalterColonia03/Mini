from __future__ import annotations

import re
from decimal import Decimal

from django import forms
from django.core import signing
from django.core.validators import MaxValueValidator

from .models import Category, Product

from .barcodes import BARCODE_PATTERN


def _clean_price_input(raw_value, value):
    raw = str(raw_value or "").strip()
    if raw and (not raw.isascii() or raw.startswith("+")):
        raise forms.ValidationError(
            "Introduzca el precio usando únicamente dígitos ASCII (0-9) y punto decimal."
        )
    if "e" in raw.lower():
        raise forms.ValidationError("Introduzca un número decimal válido sin notación científica.")
    return value


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
    barcode_type = forms.ChoiceField(
        label="Tipo de código", choices=[("", "Seleccione el tipo"), ("INTERNAL", "Código interno"), ("GTIN", "Código de fabricante (GTIN)")],
        help_text="Use GTIN para etiquetas de fabricante EAN/UPC. Los códigos internos conservan su texto; no se convierten por su longitud.",
    )
    class Meta:
        model = Product
        fields = ("name", "barcode_type", "barcode", "category", "unit", "sale_price", "minimum_stock")
        labels = {
            "name": "Nombre del producto",
            "barcode": "Código de barras",
            "barcode_type": "Tipo de código",
            "category": "Categoría",
            "unit": "Unidad de medida",
            "sale_price": "Precio final con IGV (S/)",
            "minimum_stock": "Existencia mínima",
        }
        help_texts = {
            "name": "Nombre único. Distinga marca, contenido o presentación; se ignoran mayúsculas y espacios redundantes.",
            "barcode": "Interno: letras, números, espacios y guiones, hasta 64 caracteres. GTIN: 12 o 13 dígitos, o representación de 14 con cero inicial, con dígito de control válido. No se convierten cajas en unidades.",
            "sale_price": "De S/ 0,01 a S/ 9 999 999,99, con un máximo de dos decimales.",
            "minimum_stock": "Entero de 0 a 999 999. Si lo deja vacío, se guardará 10.",
        }
        error_messages = {
            "name": {"max_length": "El nombre admite hasta %(limit_value)d caracteres."},
            "barcode": {"max_length": "El código de barras admite hasta %(limit_value)d caracteres."},
        }
        widgets = {
            "name": forms.TextInput(attrs={"autocomplete": "off", "autofocus": True}),
            "barcode": forms.TextInput(attrs={"autocomplete": "off"}),
            "sale_price": forms.NumberInput(attrs={"min": "0.01", "max": "9999999.99", "step": "0.01", "inputmode": "decimal"}),
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
                message="El precio no puede superar S/ 9 999 999,99.",
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
        if Product.objects.filter(search_name=Product.normalize_search_name(value)).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("Ya existe un producto registrado con este nombre.")
        return value

    def clean_sale_price(self):
        return _clean_price_input(
            self.data.get(self.add_prefix("sale_price"), ""), self.cleaned_data["sale_price"]
        )

    def clean_minimum_stock(self) -> int:
        value = self.cleaned_data.get("minimum_stock")
        return 10 if value is None else value

    def clean_barcode(self) -> str:
        value = (self.cleaned_data.get("barcode") or "").strip()
        if not BARCODE_PATTERN.fullmatch(value):
            raise forms.ValidationError(
                "El código de barras solo puede contener letras, números, espacios o guiones."
            )
        return value


class ProductEditForm(forms.ModelForm):
    edit_snapshot = forms.CharField(widget=forms.HiddenInput, required=False)

    class Meta:
        model = Product
        fields = ("name", "barcode_type", "barcode", "category", "sale_price", "minimum_stock")
        labels = {
            "name": "Nombre del producto",
            "barcode": "Código de barras",
            "barcode_type": "Tipo de código",
            "category": "Categoría",
            "sale_price": "Precio final con IGV (S/)",
            "minimum_stock": "Existencia mínima",
        }
        error_messages = ProductRegistrationForm.Meta.error_messages
        help_texts = {
            "name": "Nombre único. Distinga marca, contenido o presentación; se ignoran mayúsculas y espacios redundantes.",
            "barcode": ProductRegistrationForm.Meta.help_texts["barcode"],
            "barcode_type": "Los registros anteriores permanecen sin clasificar hasta que confirme si son internos o GTIN.",
            "sale_price": ProductRegistrationForm.Meta.help_texts["sale_price"],
            "minimum_stock": "Entero de 0 a 999 999.",
            "category": "Si deja el campo vacío, se conserva la categoría actual.",
        }
        widgets = {
            "name": forms.TextInput(attrs={"autofocus": True, "autocomplete": "off"}),
            "barcode": forms.TextInput(attrs={"autocomplete": "off"}),
            "sale_price": forms.NumberInput(attrs={"min": "0.01", "max": "9999999.99", "step": "0.01", "inputmode": "decimal"}),
            "minimum_stock": forms.NumberInput(attrs={"min": "0", "max": "999999", "step": "1", "inputmode": "numeric"}),
        }

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        if not self.is_bound and self.instance and self.instance.pk:
            from .services import product_edit_snapshot
            self.initial["edit_snapshot"] = signing.dumps(
                product_edit_snapshot(self.instance), salt="catalog.product-edit"
            )
        self.fields["barcode_type"].required = False
        if self.instance.barcode_type != Product.BarcodeType.UNCLASSIFIED:
            self.fields["barcode_type"].choices = [(key, label) for key, label in Product.BarcodeType.choices
                                                   if key != Product.BarcodeType.UNCLASSIFIED]
        self.fields["category"].required = False
        qs = Category.objects.filter(is_active=True)
        if self.instance and self.instance.pk and self.instance.category_id:
            qs = Category.objects.filter(pk=self.instance.category_id) | qs
        self.fields["category"].queryset = qs.order_by("name_normalized").distinct()
        self.fields["sale_price"].validators.append(
            MaxValueValidator(
                Decimal("9999999.99"),
                message="El precio no puede superar S/ 9 999 999,99.",
            )
        )
        self.fields["minimum_stock"].validators.append(
            MaxValueValidator(999999, message="Asegúrese de que este valor sea menor o igual a 999999.")
        )

    def clean_barcode_type(self):
        return self.cleaned_data.get("barcode_type") or self.instance.barcode_type

    def clean_edit_snapshot(self):
        from .services import STALE_PRODUCT_MESSAGE

        try:
            snapshot = signing.loads(self.cleaned_data.get("edit_snapshot", ""), salt="catalog.product-edit")
        except signing.BadSignature:
            raise forms.ValidationError(STALE_PRODUCT_MESSAGE, code="stale_product") from None
        if not isinstance(snapshot, dict) or snapshot.get("id") != str(self.instance.pk):
            raise forms.ValidationError(STALE_PRODUCT_MESSAGE, code="stale_product")
        return snapshot

    def clean_category(self):
        return self.cleaned_data.get("category") or self.instance.category

    def clean_name(self) -> str:
        value = " ".join(self.cleaned_data["name"].split())
        if not any(ch.isalnum() for ch in value):
            raise forms.ValidationError("El nombre del producto debe contener letras o números.")
        if Product.objects.filter(search_name=Product.normalize_search_name(value)).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("Ya existe un producto registrado con este nombre.")
        return value

    def clean_sale_price(self):
        return _clean_price_input(
            self.data.get(self.add_prefix("sale_price"), ""), self.cleaned_data["sale_price"]
        )

    def clean_barcode(self) -> str:
        value = (self.cleaned_data.get("barcode") or "").strip()
        if value != self.instance.barcode and not BARCODE_PATTERN.fullmatch(value):
            raise forms.ValidationError(
                "El código de barras solo puede contener letras, números, espacios o guiones."
            )
        return value

