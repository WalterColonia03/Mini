from __future__ import annotations

import hashlib
import json
import uuid

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Prefetch, Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from identity.authorization import roles_required
from identity.models import Role

from .forms import (
    InitialLoadProductForm,
    LotInputFormSet,
    PhysicalAdjustmentForm,
    NewLotAdjustmentForm,
    StockEntryProductForm,
    StockWriteOffForm,
    SupplierForm,
)
from .models import InitialInventoryLoad, Lot, PhysicalAdjustment, StockReceipt, StockWriteOff, Supplier
from .services import (
    LotInput,
    _lock_admin_actor,
    _lock_writeoff_actor,
    confirm_initial_load,
    create_supplier,
    register_physical_adjustment,
    register_stock_entry,
    toggle_supplier_status,
    write_off_stock,
)


def _get_lot_or_404(lot_id):
    if not lot_id:
        return None
    try:
        uuid.UUID(str(lot_id))
    except (ValueError, TypeError, AttributeError) as exc:
        raise Http404("Identificador de lote no válido.") from exc
    return get_object_or_404(Lot.objects.select_related("product", "receipt_line__receipt"), pk=lot_id)


def _inventory_payload_signature(*, action: str, lot_id, **fields) -> str:
    payload = json.dumps(
        {"action": action, "lot_id": str(lot_id), **fields},
        sort_keys=True,
        ensure_ascii=False,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _resolve_inventory_idempotency_key(request, key_value, *, action: str, lot_id, value) -> str:
    """Obtiene la clave de idempotencia explícita o genera una huella temporal contra doble clic."""
    if key_value:
        return str(key_value)
    bucket = int(timezone.now().timestamp() // 2)
    return f"auto:{action}:{lot_id}:{value}:{bucket}"


def _load_locked_inventory_session(request):
    """Bloquea la sesión en BD después del actor para serializar dobles envíos."""
    from importlib import import_module
    from django.conf import settings as dj_settings
    from django.contrib.sessions.models import Session

    session = getattr(request, "session", None)
    session_key = getattr(session, "session_key", None)
    if session_key:
        locked_row = Session.objects.select_for_update().filter(session_key=session_key).first()
        if locked_row is not None:
            engine = import_module(dj_settings.SESSION_ENGINE)
            return engine.SessionStore(session_key=session_key), True
    return session, False


def _inventory_key_status(store, key_str: str, signature: str) -> str:
    if store is None or not key_str:
        return "new"
    processed = list(store.get("processed_inventory_keys", []))
    if key_str not in processed:
        return "new"
    meta = dict(store.get("processed_inventory_keys_meta", {}))
    prev_sig = meta.get(key_str)
    if prev_sig is None or prev_sig == signature:
        return "replay"
    return "conflict"


def _save_inventory_key(store, *, is_db_store: bool, key_str: str, signature: str) -> None:
    if store is None or not key_str:
        return
    processed = list(store.get("processed_inventory_keys", []))
    meta = dict(store.get("processed_inventory_keys_meta", {}))
    if key_str not in processed:
        processed.append(key_str)
    processed = processed[-50:]
    meta[key_str] = signature
    meta = {k: meta[k] for k in processed if k in meta}
    store["processed_inventory_keys"] = processed
    store["processed_inventory_keys_meta"] = meta
    if is_db_store:
        store.save()


# ── Carga inicial (Sprint 1) ──────────────────────────────────────────────────

@roles_required(Role.Code.WAREHOUSE)
@never_cache
@require_http_methods(["GET", "POST"])
def initial_load_create(request):
    bound_data = request.POST if request.method == "POST" else None
    product_form = InitialLoadProductForm(bound_data)
    lot_formset = LotInputFormSet(bound_data, prefix="lots")
    if request.method == "POST" and product_form.is_valid() and lot_formset.is_valid():
        lot_inputs = [LotInput(**form.cleaned_data) for form in lot_formset if form.cleaned_data]
        try:
            load = confirm_initial_load(
                actor=request.user,
                product=product_form.cleaned_data["product"],
                lots=lot_inputs,
                supplier=product_form.cleaned_data.get("supplier"),
            )
        except ValidationError as error:
            for message in error.messages:
                product_form.add_error(None, message)
        else:
            return redirect("inventory-load-created", load_id=load.pk)
    return render(
        request,
        "inventory/initial_load_form.html",
        {"product_form": product_form, "lot_formset": lot_formset},
    )


@roles_required(Role.Code.WAREHOUSE, Role.Code.ADMIN)
@never_cache
@require_GET
def initial_load_created(request, load_id):
    load = get_object_or_404(
        InitialInventoryLoad.objects.select_related("product", "responsible").prefetch_related(
            "lots__supplier", "lots__responsible", "lots__receipt_line", "lines__lot"
        ),
        pk=load_id,
    )
    all_lots = list(load.lots.all())
    lines = list(load.lines.all())
    has_snapshot = all(getattr(load, name) is not None for name in (
        "product_snapshot_name", "product_snapshot_barcode", "unit_snapshot",
        "responsible_snapshot_name", "supplier_snapshot_name", "supplier_snapshot_ruc", "average_cost_snapshot",
    )) and bool(lines)
    original_by_lot = {line.lot_id: line.quantity for line in lines} if has_snapshot else {}
    for lot in all_lots:
        lot.original_initial_quantity = original_by_lot.get(lot.pk)
    initial_lots = [lot for lot in all_lots if lot.is_initial]
    legacy_lots = [lot for lot in all_lots if lot.pk not in original_by_lot and not hasattr(lot, "receipt_line")]
    return render(
        request,
        "inventory/initial_load_created.html",
        {
            "load": load,
            "lots": initial_lots,
            "legacy_lots": legacy_lots,
            "has_snapshot": has_snapshot,
            "lines": lines if has_snapshot else [],
            "receipts": StockReceipt.objects.filter(product=load.product),
        },
    )


# ── HU-INV-01b · Entrada posterior de mercadería por lotes ────────────────────

@roles_required(Role.Code.WAREHOUSE)
@never_cache
@require_http_methods(["GET", "POST"])
def stock_entry_create(request):
    bound_data = request.POST if request.method == "POST" else None
    historical = False
    if bound_data:
        try:
            key = uuid.UUID(bound_data.get("idempotency_key", ""))
        except (ValueError, TypeError, AttributeError):
            pass
        else:
            historical = StockReceipt.objects.filter(idempotency_key=key, responsible=request.user).exists()
    product_form = StockEntryProductForm(bound_data, historical=historical)
    lot_formset = LotInputFormSet(bound_data, prefix="lots", form_kwargs={"historical": historical})
    if request.method == "POST" and product_form.is_valid() and lot_formset.is_valid():
        lot_inputs = [LotInput(**form.cleaned_data) for form in lot_formset if form.cleaned_data]
        try:
            receipt = register_stock_entry(
                actor=request.user,
                product=product_form.cleaned_data["product"],
                lots=lot_inputs,
                supplier=product_form.cleaned_data.get("supplier"),
                idempotency_key=product_form.cleaned_data["idempotency_key"],
            )
        except ValidationError as error:
            for message in error.messages:
                product_form.add_error(None, message)
        else:
            messages.success(
                request,
                f"Recepción {receipt.correlative} confirmada para «{receipt.product_snapshot_name}».",
            )
            return redirect("stock-receipt", receipt_id=receipt.pk)
    return render(
        request,
        "inventory/stock_entry_form.html",
        {"product_form": product_form, "lot_formset": lot_formset},
    )


@roles_required(Role.Code.WAREHOUSE, Role.Code.ADMIN)
@never_cache
@require_GET
def stock_receipt_detail(request, receipt_id):
    receipt = get_object_or_404(StockReceipt.objects.prefetch_related("lines"), pk=receipt_id)
    return render(request, "inventory/stock_receipt.html", {"receipt": receipt})


def _attach_validation_error(form, error: ValidationError) -> None:
    if hasattr(error, "error_dict"):
        for field, errors in error.error_dict.items():
            target = field if field in form.fields else None
            for item in errors:
                form.add_error(target, item)
    else:
        for item in error.error_list:
            form.add_error(None, item)


# ── HU-PROV-01 · Ver lista de proveedores ────────────────────────────────────

@roles_required(Role.Code.ADMIN, Role.Code.WAREHOUSE)
@never_cache
@require_GET
def supplier_list(request):
    raw_query = request.GET.get("q", "")
    invalid_query = "\x00" in raw_query
    query = "" if invalid_query else raw_query.strip()
    suppliers = Supplier.objects.order_by("name", "ruc")
    if invalid_query:
        suppliers = Supplier.objects.none()
    elif query:
        collapsed = Supplier.normalize_name(query)
        search_filter = Q(name__icontains=collapsed) | Q(ruc__icontains=collapsed)
        if collapsed != query:
            search_filter |= Q(name__icontains=query) | Q(ruc__icontains=query)
        suppliers = suppliers.filter(search_filter).order_by("name", "ruc")
    return render(
        request,
        "inventory/supplier_list.html",
        {"suppliers": suppliers, "query": query, "invalid_query": invalid_query},
    )


# ── HU-PROV-02 · Registrar nuevo proveedor ───────────────────────────────────

@roles_required(Role.Code.ADMIN)
@never_cache
@require_http_methods(["GET", "POST"])
def supplier_create(request):
    form = SupplierForm(request.POST if request.method == "POST" else None)
    if request.method == "POST" and form.is_valid():
        try:
            supplier = create_supplier(actor=request.user, **form.cleaned_data)
        except ValidationError as error:
            _attach_validation_error(form, error)
        else:
            messages.success(request, f"Proveedor «{supplier.name}» registrado.")
            return redirect("supplier-list")
    if form.is_bound and form.errors:
        for field in form.fields.values():
            field.widget.attrs.pop("autofocus", None)
        first_invalid = next((fname for fname in form.fields if fname in form.errors), None)
        if first_invalid:
            form.fields[first_invalid].widget.attrs["autofocus"] = True
    return render(request, "inventory/supplier_form.html", {"form": form})


# ── HU-PROV-04 · Gestionar estado del proveedor ──────────────────────────────

@roles_required(Role.Code.ADMIN)
@never_cache
@require_POST
def supplier_toggle(request, supplier_id):
    supplier = get_object_or_404(Supplier, pk=supplier_id)
    raw_target = request.POST.get("is_active")
    target = None
    if raw_target is not None:
        normalized = str(raw_target).strip().lower()
        if normalized == "true":
            target = True
        elif normalized == "false":
            target = False
        else:
            messages.error(request, "El estado solicitado para el proveedor no es válido.")
            return redirect("supplier-list")
    try:
        toggle_supplier_status(actor=request.user, supplier=supplier, is_active=target)
    except ValidationError as error:
        messages.error(request, error.messages[0])
    else:
        estado = "activo" if supplier.is_active else "inactivo"
        if getattr(supplier, "_state_changed", True):
            messages.success(request, f"Proveedor «{supplier.name}» ahora está {estado}.")
        else:
            messages.info(request, f"El proveedor «{supplier.name}» ya se encontraba {estado}.")
    return redirect("supplier-list")


# ── HU-INV-02 · Baja de inventario por merma ─────────────────────────────────

@roles_required(Role.Code.ADMIN, Role.Code.WAREHOUSE)
@never_cache
@require_http_methods(["GET", "POST"])
def stock_writeoff_create(request):
    """Formulario de baja de inventario. GET muestra selector de lote; POST confirma."""
    lots = (
        Lot.objects.filter(available_quantity__gt=0)
        .select_related("product", "receipt_line__receipt")
        .order_by("expiration_date", "product__name")
    )
    if request.method == "POST":
        lot_id = request.POST.get("lot_id") or request.GET.get("lote")
    else:
        lot_id = request.GET.get("lote")
    selected_lot = _get_lot_or_404(lot_id)

    initial_data = {"lot_id": lot_id, "idempotency_key": uuid.uuid4()} if lot_id else None
    form = StockWriteOffForm(request.POST if request.method == "POST" else None, initial=initial_data)
    if request.method == "POST":
        if not selected_lot:
            form.is_valid()
            form.add_error(None, "Seleccione un lote válido para dar de baja.")
        elif form.is_valid():
            try:
                wo = write_off_stock(
                    actor=request.user, lot=selected_lot,
                    quantity=form.cleaned_data["quantity"],
                    reason=form.cleaned_data["reason"],
                    notes=form.cleaned_data.get("notes", ""),
                    idempotency_key=form.cleaned_data["idempotency_key"],
                )
            except ValidationError as error:
                _attach_validation_error(form, error)
            else:
                if getattr(wo, "_replayed", False):
                    messages.info(request, "Esta baja ya fue registrada anteriormente.")
                else:
                    messages.success(request, f"Baja {wo.correlativo} registrada correctamente.")
                return redirect("stock-writeoff-receipt", writeoff_id=wo.pk)
    return render(request, "inventory/writeoff_form.html", {
        "form": form,
        "lots": lots,
        "selected_lot": selected_lot,
    })


@roles_required(Role.Code.ADMIN, Role.Code.WAREHOUSE)
@never_cache
@require_GET
def stock_writeoff_receipt(request, writeoff_id):
    writeoff = get_object_or_404(StockWriteOff.objects.select_related("lot"), pk=writeoff_id)
    return render(request, "inventory/writeoff_receipt.html", {"writeoff": writeoff})


# ── HU-INV-03 · Ajuste por conteo físico ─────────────────────────────────────

@roles_required(Role.Code.ADMIN)
@never_cache
@require_http_methods(["GET", "POST"])
def physical_adjustment_create(request):
    """Existing-lot count and documented new-lot origin, always ADMIN."""
    from catalog.models import Product
    lots = Lot.objects.select_related("product", "receipt_line__receipt").order_by("product__name", "expiration_date")
    product_id = request.POST.get("product_id") if request.method == "POST" else request.GET.get("producto")
    lot_id = (request.POST.get("lot_id") or request.GET.get("lote")) if request.method == "POST" else request.GET.get("lote")
    selected_lot = _get_lot_or_404(lot_id)
    selected_product = None
    if product_id:
        try:
            identifier = uuid.UUID(str(product_id))
        except (ValueError, TypeError, AttributeError) as exc:
            raise Http404("Identificador de producto no válido.") from exc
        selected_product = get_object_or_404(Product, pk=identifier)
    new_mode = selected_product is not None
    cls = NewLotAdjustmentForm if new_mode else PhysicalAdjustmentForm
    initial = {"idempotency_key": uuid.uuid4(), "product_id": product_id} if new_mode else {"lot_id": lot_id, "idempotency_key": uuid.uuid4()}
    form = cls(request.POST if request.method == "POST" else None, initial=initial)
    if request.method == "POST":
        valid = form.is_valid()
        if selected_lot is not None and new_mode:
            form.add_error(None, "Seleccione solo un lote existente o un producto para lote nuevo.")
        elif not selected_lot and not new_mode:
            form.add_error(None, "Seleccione un lote válido para ajustar.")
        elif valid:
            args = dict(actor=request.user, delta=form.cleaned_data["delta"], reason=form.cleaned_data["reason"],
                idempotency_key=form.cleaned_data["idempotency_key"], unit_cost=form.cleaned_data.get("unit_cost"),
                cost_source=form.cleaned_data.get("cost_source", ""))
            if new_mode:
                args.update(product=selected_product, number=form.cleaned_data["number"], expiration_date=form.cleaned_data["expiration_date"])
            else:
                args["lot"] = selected_lot
            try:
                adjustment = register_physical_adjustment(**args)
            except ValidationError as error:
                _attach_validation_error(form, error)
            else:
                if getattr(adjustment, "_replayed", False):
                    messages.info(request, "Este ajuste físico ya fue registrado anteriormente.")
                else:
                    messages.success(request, "Ajuste físico registrado correctamente.")
                return redirect("physical-adjustment-detail", adjustment_id=adjustment.pk)
    return render(request, "inventory/adjustment_form.html", {"form": form, "lots": lots,
        "selected_lot": selected_lot, "selected_product": selected_product,
        "products": Product.objects.filter(initial_load__isnull=False).order_by("name"),
        "new_mode": new_mode})


@roles_required(Role.Code.ADMIN, Role.Code.WAREHOUSE)
@never_cache
@require_GET
def physical_adjustment_detail(request, adjustment_id):
    adjustment = get_object_or_404(PhysicalAdjustment.objects.select_related("lot"), pk=adjustment_id)
    return render(request, "inventory/adjustment_detail.html", {"adjustment": adjustment})


# ── HUECO-01 · HU-INV-04 · Vista de stock actual ─────────────────────────────

@roles_required(Role.Code.ADMIN, Role.Code.WAREHOUSE)
@never_cache
@require_GET
def stock_overview(request):
    """Vista consolidada del inventario actual con alertas integradas (HUECO-01 + HUECO-02)."""
    from catalog.models import Product
    from datetime import timedelta

    today = timezone.localdate()
    soon = today + timedelta(days=30)

    products = list(
        Product.objects
        .select_related("category", "initial_load")
        .prefetch_related("lots")
        .order_by("name")
    )

    # Productos activos (con categoría activa) cuyo stock vendible es igual o inferior al umbral mínimo, o sin unidades vigentes
    low_stock = [
        p for p in products
        if p.is_active and p.category.is_active and (p.sellable_stock <= p.minimum_stock or p.sellable_stock == 0)
    ]

    # Lotes próximos a vencer (en los próximos 30 días, sin incluir ya vencidos) con unidades disponibles
    from .models import Lot as LotModel
    expiring_lots = (
        LotModel.objects
        .filter(expiration_date__gt=today, expiration_date__lte=soon, available_quantity__gt=0)
        .select_related("product__category")
        .order_by("expiration_date", "product__name", "received_at", "id")
    )
    expired_lots = (
        LotModel.objects
        .filter(expiration_date__lte=today, available_quantity__gt=0)
        .select_related("product__category")
        .order_by("expiration_date", "product__name", "received_at", "id")
    )

    return render(request, "inventory/stock_overview.html", {
        "products": products,
        "today": today,
        "low_stock": low_stock,
        "expiring_lots": expiring_lots,
        "expired_lots": expired_lots,
    })


# ── HU-INV-04 · Historial de movimientos por producto ──────────────────────

@roles_required(Role.Code.ADMIN, Role.Code.WAREHOUSE)
@never_cache
@require_GET
def product_movements(request, product_id):
    """Read-only ledger with validated period/type filters and stable pages."""
    from urllib.parse import urlencode
    from django.core.paginator import EmptyPage, Paginator
    from catalog.models import Product
    from .forms import MovementFilterForm
    from .ledger import build_ledger, select_period

    product = get_object_or_404(Product.objects.prefetch_related(Prefetch("lots",
        queryset=Lot.objects.select_related("responsible", "supplier", "initial_line__load", "receipt_line__receipt", "adjustment_origin"))),
        pk=product_id)
    form = MovementFilterForm(request.GET)
    context = {"product": product, "filter_form": form, "query_valid": False, "events": []}
    if form.is_valid():
        events, issues = build_ledger(product)
        data = form.cleaned_data
        filtered, summary = select_period(events, start=data.get("desde") or None,
            end=data.get("hasta") or None, kind=data["tipo"], reliable=not issues)
        paginator = Paginator(filtered, 25)
        try:
            page = paginator.page(data["page"])
        except EmptyPage:
            form.add_error("page", "La página solicitada no existe para estos filtros.")
        else:
            params = {name: value.isoformat(timespec="minutes") if name in ("desde", "hasta") else value
                for name in ("desde", "hasta", "tipo") if (value := data.get(name))}
            context.update(query_valid=True, events=page.object_list, page_obj=page,
                balance_issues=issues, **summary)
            if page.has_previous():
                context["previous_url"] = "?" + urlencode({**params, "page": page.previous_page_number()})
            if page.has_next():
                context["next_url"] = "?" + urlencode({**params, "page": page.next_page_number()})
    return render(request, "inventory/product_movements.html", context)
