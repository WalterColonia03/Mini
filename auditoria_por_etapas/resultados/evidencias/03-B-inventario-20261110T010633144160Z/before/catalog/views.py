from __future__ import annotations

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from identity.authorization import roles_required
from identity.models import Role

from .forms import CategoryForm, ProductEditForm, ProductRegistrationForm
from .models import Category, Product
from .services import (
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


# ── HU-CAT-01 · Ver lista de categorías ──────────────────────────────────────

@roles_required(Role.Code.ADMIN)
@require_GET
def category_list(request):
    categories = Category.objects.order_by("name_normalized")
    return render(request, "catalog/category_list.html", {"categories": categories})


# ── HU-CAT-02 · Crear nueva categoría ────────────────────────────────────────

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


@roles_required(Role.Code.ADMIN)
@require_POST
def category_toggle(request, category_id):
    category = get_object_or_404(Category, pk=category_id)
    try:
        toggle_category_status(actor=request.user, category=category)
    except ValidationError as error:
        messages.error(request, error.messages[0])
    else:
        estado = "activa" if category.is_active else "inactiva"
        messages.success(request, f"Categoría «{category.name}» ahora está {estado}.")
    return redirect("category-list")


# ── HU-PROD-01 · Ver catálogo completo de productos ──────────────────────────

@roles_required(Role.Code.ADMIN, Role.Code.WAREHOUSE)
@require_GET
def product_list(request):
    query = request.GET.get("q", "").strip()
    products = (
        Product.objects.select_related("category")
        .order_by("name")
    )
    if query:
        normalized_bc = Product.normalize_barcode(query)
        q_filter = Q(name__icontains=query)
        if normalized_bc:
            q_filter = q_filter | Q(barcode_normalized__icontains=normalized_bc)
        products = products.filter(q_filter)
    return render(request, "catalog/product_list.html", {"products": products, "query": query})


# ── HU-PROD-02 · Registrar producto enlatado (existente) ─────────────────────

@roles_required(Role.Code.ADMIN)
@require_http_methods(["GET", "POST"])
def product_create(request):
    form = ProductRegistrationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            product = register_canned_product(actor=request.user, **form.cleaned_data)
        except ValidationError as error:
            _attach_validation_error(form, error)
        else:
            return redirect("product-created", product_id=product.pk)
    return render(request, "catalog/product_form.html", {"form": form})


@roles_required(Role.Code.ADMIN)
@require_GET
def product_created(request, product_id):
    product = get_object_or_404(Product.objects.select_related("category"), pk=product_id)
    return render(request, "catalog/product_created.html", {"product": product})


# ── HU-PROD-04 · Editar datos de un producto ─────────────────────────────────

@roles_required(Role.Code.ADMIN)
@require_http_methods(["GET", "POST"])
def product_edit(request, product_id):
    product = get_object_or_404(Product.objects.select_related("category"), pk=product_id)
    form = ProductEditForm(request.POST or None, instance=product)
    if request.method == "POST" and form.is_valid():
        try:
            update_product(
                actor=request.user,
                product=product,
                name=form.cleaned_data["name"],
                barcode=form.cleaned_data["barcode"],
                sale_price=form.cleaned_data["sale_price"],
                minimum_stock=form.cleaned_data["minimum_stock"],
                category=form.cleaned_data.get("category"),
            )
        except ValidationError as error:
            _attach_validation_error(form, error)
        else:
            messages.success(request, f"Producto «{product.name}» actualizado.")
            return redirect("product-list")
    return render(request, "catalog/product_edit.html", {"form": form, "product": product})


# ── HU-PROD-05 · Gestionar estado de disponibilidad ──────────────────────────

@roles_required(Role.Code.ADMIN)
@require_POST
def product_toggle_availability(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    try:
        toggle_product_availability(actor=request.user, product=product)
    except ValidationError as error:
        messages.error(request, error.messages[0])
    else:
        estado = "disponible" if product.is_active else "no disponible"
        messages.success(request, f"«{product.name}» ahora está {estado}.")
    return redirect("product-list")


# ── HU-PROD-06 · Consultar vencimientos de productos ─────────────────────────

@roles_required(Role.Code.ADMIN, Role.Code.WAREHOUSE)
@require_GET
def product_expirations(request):
    from inventory.models import Lot
    today = timezone.localdate()
    raw_days = request.GET.get("dias", "30").strip()
    days = 30
    if raw_days:
        try:
            parsed = int(raw_days)
            if 1 <= parsed <= 3650:
                days = parsed
            else:
                messages.error(request, "Ingrese un número de días entre 1 y 3650. Se muestran 30 días por defecto.")
        except ValueError:
            messages.error(request, "Ingrese un número entero válido de días. Se muestran 30 días por defecto.")
    cutoff = today + timezone.timedelta(days=days)
    lots = (
        Lot.objects.filter(available_quantity__gt=0, expiration_date__lte=cutoff)
        .select_related("product__category", "supplier")
        .order_by("expiration_date", "product__name")
    )
    return render(request, "catalog/product_expirations.html", {
        "lots": lots,
        "today": today,
        "days": days,
        "cutoff": cutoff,
    })
