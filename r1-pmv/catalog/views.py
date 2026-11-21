from __future__ import annotations

from uuid import UUID

from django.contrib import messages
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import ValidationError
from django.db.models import Q, Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_GET, require_http_methods, require_POST
from django.views.decorators.cache import never_cache

from identity.authorization import roles_required
from identity.models import Role

from .forms import BARCODE_PATTERN, CategoryForm, ProductEditForm, ProductRegistrationForm
from .models import Category, Product, ProductBarcodeKey
from .barcodes import reading_keys
from .services import (
    STALE_CATEGORY_MESSAGE,
    create_category,
    register_canned_product,
    toggle_category_status,
    toggle_product_availability,
    update_product,
)


def _attach_validation_error(form, error: ValidationError) -> None:
    if hasattr(error, "error_dict"):
        for field, errors in error.error_dict.items():
            target = field if field in form.fields else None
            for item in errors:
                form.add_error(target, item)
    else:
        for item in error.error_list:
            form.add_error(None, item)


@never_cache
@require_GET
def product_barcode_check(request):
    """Read-only early feedback; saving still enforces uniqueness in the database."""
    if not request.user.is_authenticated:
        return redirect_to_login(request.get_full_path())
    if request.user.role.code != Role.Code.ADMIN:
        # Return a response here so never_cache also protects denied lookups.
        return JsonResponse({"error": "No tiene permiso para esta operación."}, status=403)
    try:
        value = ProductRegistrationForm.base_fields["barcode"].clean(request.GET.get("barcode"))
    except ValidationError as error:
        return JsonResponse({"error": error.messages[0]}, status=400)

    products = Product.objects.all()
    product = None
    if "product_id" in request.GET:
        try:
            product_id = UUID(request.GET["product_id"])
        except (ValueError, TypeError, AttributeError):
            return JsonResponse({"error": "La ficha indicada no es válida."}, status=400)
        product = products.filter(pk=product_id).first()
        if product is None:
            return JsonResponse({"error": "La ficha indicada no existe."}, status=404)
        products = products.exclude(pk=product_id)
    kind = request.GET.get("barcode_type", product.barcode_type if product else "INTERNAL")
    try:
        keys = reading_keys(value, kind)
    except ValidationError as error:
        return JsonResponse({"error": error.messages[0]}, status=400)
    duplicate = ProductBarcodeKey.objects.filter(reading_key__in=keys, product__in=products).exists()
    if not duplicate and not BARCODE_PATTERN.fullmatch(value) and not (product and product.barcode == value):
        return JsonResponse({"error": "El código de barras solo puede contener letras, números, espacios o guiones."}, status=400)
    return JsonResponse({"duplicate": duplicate})


# ── HU-CAT-01 · Ver lista de categorías ──────────────────────────────────────

@roles_required(Role.Code.ADMIN)
@require_GET
@never_cache
def category_list(request):
    categories = Category.objects.order_by("name_normalized")
    return render(request, "catalog/category_list.html", {"categories": categories})


# ── HU-CAT-02 · Crear nueva categoría ────────────────────────────────────────

@never_cache
@roles_required(Role.Code.ADMIN)
@require_http_methods(["GET", "POST"])
def category_create(request):
    form = CategoryForm(request.POST if request.method == "POST" else None)
    if request.method == "POST" and form.is_valid():
        try:
            cat = create_category(actor=request.user, name=form.cleaned_data["name"])
        except ValidationError as error:
            _attach_validation_error(form, error)
        else:
            messages.success(request, f"Categoría «{cat.name}» creada correctamente.")
            return redirect("category-list")
    return render(request, "catalog/category_form.html", {"form": form})


def _category_state_values(data):
    raw_state, raw_version = data.get("is_active"), data.get("state_version", "")
    if raw_state not in {"true", "false"}:
        raise ValidationError("Seleccione un estado válido para la categoría.")
    if (not raw_version or len(raw_version) > 19 or not raw_version.isascii()
            or not raw_version.isdecimal() or int(raw_version) > 9223372036854775807):
        raise ValidationError("Vuelva a abrir la confirmación desde Categorías.")
    return raw_state == "true", int(raw_version)


def _category_state_page(request, category, target=None, error=None, status=200):
    from inventory.models import Lot
    from sales.models import SaleDraftLine

    context = {
        "category": category, "target": target, "error": error,
        "product_count": category.products.count(),
        "draft_count": SaleDraftLine.objects.filter(
            product__category=category, draft__status="ACTIVE"
        ).values("draft_id").distinct().count(),
        "physical_units": Lot.objects.filter(product__category=category).aggregate(
            total=Sum("available_quantity", default=0)
        )["total"],
    }
    return render(request, "catalog/category_state_confirm.html", context, status=status)


@roles_required(Role.Code.ADMIN)
@require_GET
@never_cache
def category_state_confirm(request, category_id):
    category = get_object_or_404(Category, pk=category_id)
    try:
        if request.GET:
            target, version = _category_state_values(request.GET)
        else:
            target, version = not category.is_active, category.state_version
        if version != category.state_version:
            raise ValidationError(STALE_CATEGORY_MESSAGE, code="stale_category")
    except ValidationError as error:
        return _category_state_page(request, category, error=error.messages[0],
                                    status=409 if error.code == "stale_category" else 400)
    return _category_state_page(request, category, target)


@roles_required(Role.Code.ADMIN)
@require_POST
@never_cache
def category_toggle(request, category_id):
    category = get_object_or_404(Category, pk=category_id)
    try:
        target, version = _category_state_values(request.POST)
        if request.POST.get("confirm") != "yes":
            raise ValidationError("Vuelva a abrir la confirmación desde Categorías.")
        toggle_category_status(actor=request.user, category=category, is_active=target, expected_version=version)
    except ValidationError as error:
        category.refresh_from_db()
        return _category_state_page(request, category, error=error.messages[0],
                                    status=409 if error.code == "stale_category" else 400)
    else:
        estado = "activa" if category.is_active else "inactiva"
        messages.success(request, f"Categoría «{category.name}» ahora está {estado}.")
    return redirect("category-list")


# ── HU-PROD-01 · Ver catálogo completo de productos ──────────────────────────

@roles_required(Role.Code.ADMIN, Role.Code.WAREHOUSE)
@never_cache
@require_GET
def product_list(request):
    query = request.GET.get("q", "").strip()
    invalid_query = "\x00" in query
    products = (
        Product.objects.select_related("category")
        .annotate(current_stock=Sum(
            "lots__available_quantity",
            filter=Q(lots__expiration_date__gt=timezone.localdate()),
            default=0,
        ))
        .order_by("name")
    )
    if invalid_query:
        products = products.none()
    elif query:
        normalized_bc = Product.normalize_barcode(query)
        q_filter = Q(search_name__contains=Product.normalize_search_name(query))
        if normalized_bc:
            q_filter = q_filter | Q(barcode_normalized__icontains=normalized_bc) | Q(pk__in=ProductBarcodeKey.objects.filter(reading_key=normalized_bc).values("product_id"))
        products = products.filter(q_filter)
    return render(request, "catalog/product_list.html", {
        "products": products,
        "query": query.replace("\x00", "") if invalid_query else query,
        "invalid_query": invalid_query,
    })


# ── HU-PROD-02 · Registrar producto enlatado (existente) ─────────────────────

@never_cache
@roles_required(Role.Code.ADMIN)
@require_http_methods(["GET", "POST"])
def product_create(request):
    form = ProductRegistrationForm(request.POST if request.method == "POST" else None)
    if request.method == "POST" and form.is_valid():
        try:
            product = register_canned_product(actor=request.user, **form.cleaned_data)
        except ValidationError as error:
            _attach_validation_error(form, error)
        else:
            return redirect("product-created", product_id=product.pk)
    if form.is_bound and form.errors:
        form.fields["name"].widget.attrs.pop("autofocus", None)
        for name, field in form.fields.items():
            if name in form.errors:
                field.widget.attrs["autofocus"] = True
                break
    return render(request, "catalog/product_form.html", {"form": form})


@never_cache
@roles_required(Role.Code.ADMIN)
@require_GET
def product_created(request, product_id):
    product = get_object_or_404(Product.objects.select_related("category"), pk=product_id)
    return render(request, "catalog/product_created.html", {"product": product})


# ── HU-PROD-04 · Editar datos de un producto ─────────────────────────────────

@never_cache
@roles_required(Role.Code.ADMIN)
@require_http_methods(["GET", "POST"])
def product_edit(request, product_id):
    product = get_object_or_404(Product.objects.select_related("category"), pk=product_id)
    form = ProductEditForm(request.POST if request.method == "POST" else None, instance=product)
    stale_product = False
    if request.method == "POST" and form.is_valid():
        try:
            update_product(
                actor=request.user,
                product=product,
                name=form.cleaned_data["name"],
                barcode=form.cleaned_data["barcode"],
                barcode_type=form.cleaned_data["barcode_type"],
                sale_price=form.cleaned_data["sale_price"],
                minimum_stock=form.cleaned_data["minimum_stock"],
                category=form.cleaned_data.get("category"),
                expected_snapshot=form.cleaned_data["edit_snapshot"],
            )
        except ValidationError as error:
            stale_product = getattr(error, "code", None) == "stale_product"
            _attach_validation_error(form, error)
        else:
            messages.success(request, f"Producto «{product.name}» actualizado.")
            return redirect("product-list")
    if form.is_bound and form.errors:
        stale_product = stale_product or "edit_snapshot" in form.errors
        form.fields["name"].widget.attrs.pop("autofocus", None)
        for name, field in form.fields.items():
            if name in form.errors:
                field.widget.attrs["autofocus"] = True
                break
    return render(request, "catalog/product_edit.html", {
        "form": form, "product": product, "stale_product": stale_product,
    })


# ── HU-PROD-05 · Gestionar estado de disponibilidad ──────────────────────────

@never_cache
@roles_required(Role.Code.ADMIN)
@require_POST
def product_toggle_availability(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    raw_state = request.POST.get("is_active")
    if raw_state not in {"true", "false"}:
        messages.error(request, "Seleccione un estado válido para el producto.")
        return redirect("product-list")
    target = raw_state == "true"
    try:
        toggle_product_availability(actor=request.user, product=product, is_active=target,
                                    expected_version=request.POST.get("version", ""))
    except ValidationError as error:
        messages.error(request, error.messages[0])
    else:
        estado = "activo" if product.is_active else "inactivo"
        messages.success(request, f"«{product.name}» ahora está {estado}.")
    return redirect("product-list")


# ── HU-PROD-06 · Consultar vencimientos de productos ─────────────────────────

@roles_required(Role.Code.ADMIN, Role.Code.WAREHOUSE)
@never_cache
@require_GET
def product_expirations(request):
    from inventory.models import Lot
    today = timezone.localdate()
    raw_days = request.GET.get("dias", "30").strip()
    days = 30
    if raw_days:
        is_ascii_signed_int = raw_days.isascii() and (
            raw_days.isdecimal() or (raw_days.startswith("-") and raw_days[1:].isdecimal())
        )
        if not is_ascii_signed_int:
            messages.error(request, "Ingrese un número entero válido de días. Se muestran 30 días por defecto.")
        else:
            # Bound integer conversion to the supported horizon. Leading zeros
            # do not change a positive number; negative values are out of range.
            digits = raw_days.lstrip("0")
            if not raw_days.startswith("-") and 0 < len(digits) <= 4 and int(digits) <= 3650:
                days = int(digits)
            else:
                messages.error(request, "Ingrese un número de días entre 1 y 3650. Se muestran 30 días por defecto.")
    cutoff = today + timezone.timedelta(days=days)
    lots = list(
        Lot.objects.filter(available_quantity__gt=0, expiration_date__lte=cutoff)
        .select_related("product__category", "supplier")
        .order_by("expiration_date", "product__name", "received_at", "id")
    )
    expired_count = 0
    upcoming_count = 0
    for lot in lots:
        delta = (lot.expiration_date - today).days
        lot.days_remaining = delta
        lot.abs_days_remaining = abs(delta)
        if delta <= 0:
            expired_count += 1
        else:
            upcoming_count += 1
    return render(request, "catalog/product_expirations.html", {
        "lots": lots,
        "today": today,
        "days": days,
        "cutoff": cutoff,
        "expired_count": expired_count,
        "upcoming_count": upcoming_count,
    })
