from __future__ import annotations

import re
import uuid
from datetime import datetime
from decimal import Decimal

from django import forms
from django.forms import formset_factory
from django.utils import timezone

from catalog.models import Product
from .models import (
    SUPPLIER_PHONE_DIGIT_PATTERN,
    SUPPLIER_PHONE_PATTERN,
    SUPPLIER_RUC_PATTERN,
    Lot,
    Supplier,
)


class MovementFilterForm(forms.Form):
    desde = forms.CharField(label="Desde (Lima)", required=False, max_length=16,
        widget=forms.DateTimeInput(attrs={"type": "datetime-local", "step": "60"}))
    hasta = forms.CharField(label="Hasta (Lima)", required=False, max_length=16,
        widget=forms.DateTimeInput(attrs={"type": "datetime-local", "step": "60"}))
    tipo = forms.ChoiceField(label="Tipo", required=False, choices=(
        ("", "Todos"), ("entrada", "Entradas"), ("venta", "Ventas"),
        ("merma", "Mermas"), ("ajuste", "Ajustes"), ("salidas", "Todas las salidas")))
    page = forms.CharField(required=False, max_length=9, widget=forms.HiddenInput,
        error_messages={"max_length": "Página debe ser un entero positivo de hasta 9 dígitos."})

    def clean_page(self):
        value = self.cleaned_data["page"]
        if not value:
            return 1
        if not re.fullmatch(r"[1-9][0-9]{0,8}", value):
            raise forms.ValidationError("Página debe ser un entero positivo de hasta 9 dígitos.")
        return int(value)

    def clean(self):
        data = super().clean()
        for name in self.fields:
            if hasattr(self.data, "getlist") and len(self.data.getlist(name)) > 1:
                self.add_error(name, f"No repita el parámetro {name}.")
        for name in ("desde", "hasta"):
            value = data.get(name)
            if value:
                try:
                    if not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}", value):
                        raise ValueError
                    data[name] = datetime.fromisoformat(value)
                except ValueError:
                    self.add_error(name, "Ingrese una fecha y hora válida: AAAA-MM-DDTHH:MM (Lima).")
        if not self.errors.get("desde") and not self.errors.get("hasta"):
            start, end = data.get("desde"), data.get("hasta")
            if bool(start) != bool(end):
                self.add_error(None, "Complete Desde y Hasta, o deje ambos vacíos.")
            elif start and end and start > end:
                self.add_error("hasta", "Desde no puede ser posterior a Hasta.")
        return data


class ReceiptSupplierSelect(forms.Select):
    REJECTED_INACTIVE_PREFIX = "__inactive__:"
    REJECTED_MISSING_SENTINEL = "__unavailable__"
    REJECTED_INVALID_SENTINEL = "__invalid_supplier__"

    def optgroups(self, name, value, attrs=None):
        groups = super().optgroups(name, value, attrs)
        raw = str(value[0]) if value else ""
        if not raw:
            return groups
        known_values = {str(opt["value"]) for _, options, _ in groups for opt in options}
        if raw in known_values:
            return groups

        if raw == self.REJECTED_MISSING_SENTINEL:
            sentinel_val = self.REJECTED_MISSING_SENTINEL
            label = "Proveedor eliminado — No disponible (cambie la selección)"
        elif raw == self.REJECTED_INVALID_SENTINEL:
            sentinel_val = self.REJECTED_INVALID_SENTINEL
            label = "Selección no válida (cambie la selección)"
        else:
            lookup = raw[len(self.REJECTED_INACTIVE_PREFIX) :] if raw.startswith(self.REJECTED_INACTIVE_PREFIX) else raw
            supplier = None
            try:
                parsed = uuid.UUID(lookup)
            except (ValueError, TypeError, AttributeError):
                parsed = None
            if parsed is not None:
                supplier = Supplier.objects.filter(pk=parsed).first()
            if supplier is not None:
                sentinel_val = f"{self.REJECTED_INACTIVE_PREFIX}{supplier.pk}"
                if not supplier.is_active:
                    label = f"{supplier.name} ({supplier.ruc}) — Inactivo (cambie la selección)"
                else:
                    label = f"{supplier.name} ({supplier.ruc}) — Revalidar selección"
            elif parsed is not None:
                sentinel_val = self.REJECTED_MISSING_SENTINEL
                label = "Proveedor eliminado — No disponible (cambie la selección)"
            else:
                sentinel_val = self.REJECTED_INVALID_SENTINEL
                label = "Selección no válida (cambie la selección)"

        selected_opt = self.create_option(name, sentinel_val, label, True, len(groups), attrs=None)
        return [*groups, (None, [selected_opt], len(groups))]


class ReceiptSupplierChoiceField(forms.ModelChoiceField):
    widget = ReceiptSupplierSelect

    def to_python(self, value):
        if value in self.empty_values:
            return None
        raw = str(value)
        if "\x00" in raw or raw == ReceiptSupplierSelect.REJECTED_INVALID_SENTINEL:
            raise forms.ValidationError(
                "El proveedor seleccionado no es válido. Seleccione un proveedor activo o «Sin proveedor asignado».",
                code="invalid_choice",
            )
        if raw == ReceiptSupplierSelect.REJECTED_MISSING_SENTINEL:
            raise forms.ValidationError(
                "El proveedor seleccionado ya no existe. Seleccione un proveedor activo o «Sin proveedor asignado».",
                code="invalid_choice",
            )

        from_rejected = raw.startswith(ReceiptSupplierSelect.REJECTED_INACTIVE_PREFIX)
        lookup_raw = raw[len(ReceiptSupplierSelect.REJECTED_INACTIVE_PREFIX) :] if from_rejected else raw
        if not from_rejected:
            try:
                return super().to_python(value)
            except forms.ValidationError:
                pass

        try:
            parsed = uuid.UUID(str(lookup_raw))
        except (ValueError, TypeError, AttributeError):
            raise forms.ValidationError(
                "El proveedor seleccionado no es válido. Seleccione un proveedor activo o «Sin proveedor asignado».",
                code="invalid_choice",
            ) from None

        supplier = Supplier.objects.filter(pk=parsed).first()
        if supplier is not None:
            if not supplier.is_active:
                raise forms.ValidationError(
                    f"El proveedor «{supplier.name}» ({supplier.ruc}) está inactivo. "
                    "Seleccione un proveedor activo o «Sin proveedor asignado».",
                    code="invalid_choice",
                )
            raise forms.ValidationError(
                f"El proveedor «{supplier.name}» ({supplier.ruc}) fue rechazado antes; "
                "selecciónelo nuevamente de la lista o elija «Sin proveedor asignado».",
                code="invalid_choice",
            )
        raise forms.ValidationError(
            "El proveedor seleccionado ya no existe. Seleccione un proveedor activo o «Sin proveedor asignado».",
            code="invalid_choice",
        )


class InitialLoadProductForm(forms.Form):
    product = forms.ModelChoiceField(
        label="Producto",
        queryset=Product.objects.none(),
        empty_label="Seleccione un producto",
        error_messages={
            "invalid_choice": "Este producto ya tiene una carga inicial registrada o no está disponible.",
            "required": "Seleccione un producto.",
        },
    )
    supplier = ReceiptSupplierChoiceField(
        label="Proveedor (opcional)",
        queryset=Supplier.objects.none(),
        required=False,
        empty_label="Sin proveedor asignado",
    )

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.fields["product"].queryset = Product.objects.filter(
            is_active=True,
            category__is_active=True,
            controls_expiration=True,
            initial_load__isnull=True,
        ).select_related("category")
        self.fields["supplier"].queryset = Supplier.objects.filter(is_active=True).order_by("name", "ruc")


class StockEntryProductForm(forms.Form):
    idempotency_key = forms.UUIDField(initial=uuid.uuid4, widget=forms.HiddenInput,
        error_messages={"required": "Falta la clave de recepción. Vuelva a abrir el formulario.",
                        "invalid": "La clave de recepción no es válida. Vuelva a abrir el formulario."})
    product = forms.ModelChoiceField(
        label="Producto con carga inicial previa",
        queryset=Product.objects.none(),
        empty_label="Seleccione un producto",
        error_messages={
            "invalid_choice": "Seleccione un producto activo que ya tenga carga inicial.",
            "required": "Seleccione un producto.",
        },
    )
    supplier = ReceiptSupplierChoiceField(
        label="Proveedor (opcional)",
        queryset=Supplier.objects.none(),
        required=False,
        empty_label="Sin proveedor asignado",
    )

    def __init__(self, *args, historical=False, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.fields["product"].queryset = Product.objects.filter(
            is_active=True,
            category__is_active=True,
            controls_expiration=True,
            initial_load__isnull=False,
        ).select_related("category")
        self.fields["supplier"].queryset = Supplier.objects.filter(is_active=True).order_by("name", "ruc")
        if historical:
            self.fields["product"].queryset = Product.objects.all()
            self.fields["supplier"].queryset = Supplier.objects.all()


class LotInputForm(forms.Form):
    def __init__(self, *args, historical=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.historical = historical

    number = forms.CharField(label="Número de lote", max_length=64)
    quantity = forms.IntegerField(
        label="Cantidad",
        min_value=1,
        max_value=999999,
        widget=forms.NumberInput(attrs={"min": "1", "max": "999999", "step": "1", "inputmode": "numeric"}),
    )
    unit_cost = forms.DecimalField(
        label="Costo unitario (S/)",
        min_value=Decimal("0.0001"),
        max_value=Decimal("9999999.9999"),
        max_digits=14,
        decimal_places=4,
        widget=forms.NumberInput(
            attrs={"min": "0.0001", "max": "9999999.9999", "step": "0.0001", "inputmode": "decimal"}
        ),
    )
    expiration_date = forms.DateField(
        label="Vencimiento",
        widget=forms.DateInput(attrs={"type": "date"}),
    )

    def clean_number(self):
        value = (self.cleaned_data.get("number") or "").strip()
        if "\x00" in value:
            raise forms.ValidationError("El número de lote contiene un carácter no válido.")
        if not value:
            raise forms.ValidationError("Ingrese el número de lote.")
        return value

    def clean_quantity(self):
        raw = str(self.data.get(self.add_prefix("quantity"), "")).strip()
        if raw and not raw.isascii():
            raise forms.ValidationError("Introduzca un número entero usando dígitos ASCII.")
        return self.cleaned_data["quantity"]

    def clean_unit_cost(self):
        raw = str(self.data.get(self.add_prefix("unit_cost"), "")).strip()
        if raw and not raw.isascii():
            raise forms.ValidationError("Introduzca un costo decimal válido usando dígitos ASCII.")
        if "e" in raw.lower():
            raise forms.ValidationError("Introduzca un costo decimal válido sin notación científica.")
        return self.cleaned_data["unit_cost"]

    def clean_expiration_date(self):
        exp = self.cleaned_data["expiration_date"]
        today = timezone.localdate()
        if not self.historical and exp <= today:
            raise forms.ValidationError("El vencimiento debe ser posterior a hoy en Lima.")
        if not self.historical and exp > Lot.latest_expiration_date(today):
            raise forms.ValidationError("El vencimiento no puede superar 20 años en el futuro.")
        return exp


class BaseLotInputFormSet(forms.BaseFormSet):
    def clean(self) -> None:
        super().clean()
        seen: dict[str, int] = {}
        for index, form in enumerate(self.forms, start=1):
            if not hasattr(form, "cleaned_data") or not form.cleaned_data:
                continue
            raw_number = form.cleaned_data.get("number")
            if not raw_number:
                continue
            normalized = Lot.normalize_number(raw_number)
            if normalized in seen:
                form.add_error(
                    "number",
                    f"El número {normalized} está repetido (ya ingresado en el Lote {seen[normalized]}).",
                )
            else:
                seen[normalized] = index


LotInputFormSet = formset_factory(
    LotInputForm, extra=3, min_num=1, validate_min=True, formset=BaseLotInputFormSet
)


# ── HU-PROV-02 · Formulario de proveedor ─────────────────────────────────────

class SupplierForm(forms.Form):
    name = forms.CharField(
        label="Nombre comercial",
        max_length=160,
        error_messages={
            "required": "El nombre del proveedor es obligatorio.",
            "max_length": "El nombre admite hasta %(limit_value)d caracteres.",
        },
        widget=forms.TextInput(
            attrs={"class": "form-control", "autofocus": True, "maxlength": "160", "autocomplete": "organization"}
        ),
    )
    ruc = forms.CharField(
        label="RUC",
        max_length=11,
        help_text="11 dígitos numéricos (solo valida formato; no verifica existencia ni condición ante SUNAT).",
        error_messages={
            "required": "El RUC es obligatorio.",
            "max_length": "El RUC debe contener exactamente 11 dígitos numéricos.",
        },
        widget=forms.TextInput(
            attrs={"class": "form-control", "inputmode": "numeric", "maxlength": "11", "autocomplete": "off"}
        ),
    )
    phone = forms.CharField(
        label="Teléfono",
        max_length=20,
        required=False,
        help_text="Opcional. Hasta 20 caracteres: números, espacios y signos (+, -, paréntesis).",
        error_messages={
            "max_length": "El teléfono admite hasta %(limit_value)d caracteres.",
        },
        widget=forms.TextInput(
            attrs={"class": "form-control", "inputmode": "tel", "maxlength": "20", "autocomplete": "tel"}
        ),
    )

    def clean_name(self) -> str:
        raw = self.cleaned_data.get("name") or ""
        if "\x00" in raw:
            raise forms.ValidationError("El nombre contiene un carácter no válido.")
        value = Supplier.normalize_name(raw)
        if not value:
            raise forms.ValidationError("El nombre del proveedor es obligatorio.")
        if not any(ch.isalnum() for ch in value):
            raise forms.ValidationError("El nombre comercial debe contener letras o números.")
        return value

    def clean_ruc(self) -> str:
        raw = self.cleaned_data.get("ruc") or ""
        if "\x00" in raw:
            raise forms.ValidationError("El RUC contiene un carácter no válido.")
        value = raw.strip()
        if not SUPPLIER_RUC_PATTERN.fullmatch(value):
            raise forms.ValidationError("El RUC debe contener exactamente 11 dígitos numéricos.")
        if Supplier.objects.filter(ruc=value).exists():
            raise forms.ValidationError("El RUC ya está registrado.")
        return value

    def clean_phone(self) -> str:
        raw = self.cleaned_data.get("phone") or ""
        if "\x00" in raw:
            raise forms.ValidationError("El teléfono contiene un carácter no válido.")
        value = Supplier.normalize_phone(raw)
        if value and (
            not SUPPLIER_PHONE_PATTERN.fullmatch(value) or not SUPPLIER_PHONE_DIGIT_PATTERN.search(value)
        ):
            raise forms.ValidationError(
                "El teléfono debe incluir al menos un dígito y solo puede contener números, espacios y signos (+, -, paréntesis)."
            )
        return value


# ── HU-INV-02 · Formulario de baja por merma ─────────────────────────────────

ASCII_INTEGER_PATTERN = re.compile(r"^[+-]?[0-9]+$")


class StockWriteOffForm(forms.Form):
    from inventory.models import StockWriteOff as _SWO

    lot_id = forms.UUIDField(widget=forms.HiddenInput())
    idempotency_key = forms.UUIDField(widget=forms.HiddenInput())
    quantity = forms.IntegerField(
        label="Cantidad a dar de baja",
        min_value=1,
        max_value=999999,
        widget=forms.NumberInput(attrs={"class": "form-control", "min": "1", "max": "999999", "step": "1"}),
    )
    reason = forms.ChoiceField(
        label="Motivo",
        choices=_SWO.Reason.choices,
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    notes = forms.CharField(
        label="Detalle (obligatorio para Daño y Robo)",
        required=False,
        widget=forms.Textarea(attrs={"class": "form-control", "rows": "3"}),
    )

    def clean_quantity(self) -> int:
        raw = str(self.data.get(self.add_prefix("quantity"), "")).strip()
        if raw and not ASCII_INTEGER_PATTERN.fullmatch(raw):
            raise forms.ValidationError("Introduzca un número entero usando dígitos ASCII.")
        return self.cleaned_data["quantity"]

    def clean_notes(self) -> str:
        raw = self.cleaned_data.get("notes") or ""
        if "\x00" in raw:
            raise forms.ValidationError("El detalle contiene un carácter no válido.")
        return raw.strip()


# ── HU-INV-03 · Formulario de ajuste físico ──────────────────────────────────

class PhysicalAdjustmentForm(forms.Form):
    lot_id = forms.UUIDField(widget=forms.HiddenInput())
    idempotency_key = forms.UUIDField(widget=forms.HiddenInput())
    delta = forms.IntegerField(
        label="Ajuste (positivo=entrada, negativo=faltante)",
        min_value=-999999,
        max_value=999999,
        widget=forms.NumberInput(attrs={"class": "form-control", "min": "-999999", "max": "999999", "step": "1"}),
    )
    reason = forms.CharField(
        label="Motivo del ajuste",
        max_length=300,
        widget=forms.Textarea(attrs={"class": "form-control", "rows": "3"}),
    )
    unit_cost = forms.DecimalField(
        label="Costo unitario documentado (S/)", required=False, min_value=Decimal("0.0001"),
        max_value=Decimal("9999999.9999"), max_digits=11, decimal_places=4,
        help_text="Obligatorio si el stock físico del producto está en cero. Con existencias se usa el promedio vigente.",
        widget=forms.NumberInput(attrs={"class": "form-control", "step": "0.0001"}),
    )
    cost_source = forms.CharField(
        label="Fuente del costo", required=False, max_length=300,
        help_text="Documento o referencia que acredita el costo cuando no quedan existencias físicas.",
        widget=forms.Textarea(attrs={"class": "form-control", "rows": "2"}),
    )

    def clean_cost_source(self):
        value = self.cleaned_data.get("cost_source", "")
        if "\x00" in value:
            raise forms.ValidationError("La fuente del costo contiene un carácter no válido.")
        return value.strip()

    def clean_delta(self) -> int:
        raw = str(self.data.get(self.add_prefix("delta"), "")).strip()
        if raw and not ASCII_INTEGER_PATTERN.fullmatch(raw):
            raise forms.ValidationError("Introduzca un número entero usando dígitos ASCII.")
        value = self.cleaned_data["delta"]
        if value == 0:
            raise forms.ValidationError("El ajuste no puede ser cero.")
        return value

    def clean_reason(self) -> str:
        raw = self.cleaned_data.get("reason") or ""
        if "\x00" in raw:
            raise forms.ValidationError("El motivo del ajuste contiene un carácter no válido.")
        cleaned = raw.strip()
        if not cleaned:
            raise forms.ValidationError("El motivo del ajuste es obligatorio.")
        return cleaned


class NewLotAdjustmentForm(PhysicalAdjustmentForm):
    lot_id = None
    product_id = forms.UUIDField(widget=forms.HiddenInput())
    number = forms.CharField(label="Número del lote nuevo", max_length=64,
        widget=forms.TextInput(attrs={"class": "form-control"}))
    expiration_date = forms.DateField(label="Vencimiento fiable del lote", input_formats=["%Y-%m-%d"],
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}, format="%Y-%m-%d"),
        help_text="Un lote vencido se registra como físico no vendible. No se inventan fechas.")

    def clean_number(self):
        value = self.cleaned_data["number"]
        if "\x00" in value:
            raise forms.ValidationError("El número de lote contiene un carácter no válido.")
        return Lot.normalize_number(value)
