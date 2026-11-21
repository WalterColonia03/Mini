from __future__ import annotations

import hashlib
import json
import uuid

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q
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
    StockEntryProductForm,
    StockWriteOffForm,
    SupplierForm,
)
from .models import InitialInventoryLoad, Lot, Supplier
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
    return get_object_or_404(Lot.objects.select_related("product"), pk=lot_id)


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
            "lots__adjustments", "lots__supplier", "lots__responsible"
        ),
        pk=load_id,
    )
    all_lots = list(load.lots.all())
    for lot in all_lots:
        positive_adj = sum(adj.delta for adj in lot.adjustments.all() if adj.delta > 0)
        lot.original_initial_quantity = max(0, lot.initial_quantity - positive_adj)
    initial_lots = [lot for lot in all_lots if lot.is_initial]
    subsequent_lots = [lot for lot in all_lots if not lot.is_initial]
    return render(
        request,
        "inventory/initial_load_created.html",
        {
            "load": load,
            "lots": initial_lots,
            "subsequent_lots": subsequent_lots,
        },
    )


# ── HU-INV-01b · Entrada posterior de mercadería por lotes ────────────────────

@roles_required(Role.Code.WAREHOUSE)
@never_cache
@require_http_methods(["GET", "POST"])
def stock_entry_create(request):
    bound_data = request.POST if request.method == "POST" else None
    product_form = StockEntryProductForm(bound_data)
    lot_formset = LotInputFormSet(bound_data, prefix="lots")
    if request.method == "POST" and product_form.is_valid() and lot_formset.is_valid():
        lot_inputs = [LotInput(**form.cleaned_data) for form in lot_formset if form.cleaned_data]
        try:
            load = register_stock_entry(
                actor=request.user,
                product=product_form.cleaned_data["product"],
                lots=lot_inputs,
                supplier=product_form.cleaned_data.get("supplier"),
            )
        except ValidationError as error:
            for message in error.messages:
                product_form.add_error(None, message)
        else:
            messages.success(
                request,
                f"Entrada de lotes registrada para «{load.product.name}». Costo promedio actualizado.",
            )
            return redirect("inventory-load-created", load_id=load.pk)
    return render(
        request,
        "inventory/stock_entry_form.html",
        {"product_form": product_form, "lot_formset": lot_formset},
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
        .select_related("product")
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
            signature = _inventory_payload_signature(
                action="writeoff",
                lot_id=selected_lot.pk,
                quantity=form.cleaned_data["quantity"],
                reason=form.cleaned_data["reason"],
                notes=form.cleaned_data.get("notes", ""),
            )
            idem_key = _resolve_inventory_idempotency_key(
                request,
                form.cleaned_data.get("idempotency_key"),
                action="writeoff",
                lot_id=selected_lot.pk,
                value=signature,
            )
            duplicate_replay = False
            key_conflict = False
            wo = None
            with transaction.atomic():
                _lock_writeoff_actor(
                    request.user, "No tiene permiso para registrar bajas de inventario."
                )
                session_store, is_db_store = _load_locked_inventory_session(request)
                key_state = _inventory_key_status(session_store, idem_key, signature)
                if key_state == "replay":
                    duplicate_replay = True
                elif key_state == "conflict":
                    key_conflict = True
                else:
                    try:
                        wo = write_off_stock(
                            actor=request.user,
                            lot=selected_lot,
                            quantity=form.cleaned_data["quantity"],
                            reason=form.cleaned_data["reason"],
                            notes=form.cleaned_data.get("notes", ""),
                        )
                    except ValidationError as error:
                        transaction.set_rollback(True)
                        _attach_validation_error(form, error)
                    else:
                        _save_inventory_key(
                            session_store,
                            is_db_store=is_db_store,
                            key_str=idem_key,
                            signature=signature,
                        )
            if duplicate_replay:
                messages.info(request, "Esta baja ya fue registrada anteriormente.")
                return redirect("stock-writeoff")
            if key_conflict:
                form.add_error(
                    None,
                    "La clave de operación ya fue utilizada para otra solicitud. Recargue el formulario e inténtelo nuevamente.",
                )
            elif wo is not None:
                messages.success(request, f"Baja {wo.correlativo} registrada correctamente.")
                return redirect("stock-writeoff")
    return render(request, "inventory/writeoff_form.html", {
        "form": form,
        "lots": lots,
        "selected_lot": selected_lot,
    })


# ── HU-INV-03 · Ajuste por conteo físico ─────────────────────────────────────

@roles_required(Role.Code.ADMIN)
@never_cache
@require_http_methods(["GET", "POST"])
def physical_adjustment_create(request):
    """Formulario de ajuste físico de inventario."""
    lots = (
        Lot.objects.select_related("product")
        .order_by("product__name", "expiration_date")
    )
    if request.method == "POST":
        lot_id = request.POST.get("lot_id") or request.GET.get("lote")
    else:
        lot_id = request.GET.get("lote")
    selected_lot = _get_lot_or_404(lot_id)

    initial_data = {"lot_id": lot_id, "idempotency_key": uuid.uuid4()} if lot_id else None
    form = PhysicalAdjustmentForm(request.POST if request.method == "POST" else None, initial=initial_data)
    if request.method == "POST":
        if not selected_lot:
            form.is_valid()
            form.add_error(None, "Seleccione un lote válido para ajustar.")
        elif form.is_valid():
            signature = _inventory_payload_signature(
                action="adjustment",
                lot_id=selected_lot.pk,
                delta=form.cleaned_data["delta"],
                reason=form.cleaned_data["reason"],
            )
            idem_key = _resolve_inventory_idempotency_key(
                request,
                form.cleaned_data.get("idempotency_key"),
                action="adjustment",
                lot_id=selected_lot.pk,
                value=signature,
            )
            duplicate_replay = False
            key_conflict = False
            adjustment = None
            with transaction.atomic():
                _lock_admin_actor(
                    request.user, "Solo el administrador puede registrar ajustes físicos."
                )
                session_store, is_db_store = _load_locked_inventory_session(request)
                key_state = _inventory_key_status(session_store, idem_key, signature)
                if key_state == "replay":
                    duplicate_replay = True
                elif key_state == "conflict":
                    key_conflict = True
                else:
                    try:
                        adjustment = register_physical_adjustment(
                            actor=request.user,
                            lot=selected_lot,
                            delta=form.cleaned_data["delta"],
                            reason=form.cleaned_data["reason"],
                        )
                    except ValidationError as error:
                        transaction.set_rollback(True)
                        _attach_validation_error(form, error)
                    else:
                        _save_inventory_key(
                            session_store,
                            is_db_store=is_db_store,
                            key_str=idem_key,
                            signature=signature,
                        )
            if duplicate_replay:
                messages.info(request, "Este ajuste físico ya fue registrado anteriormente.")
                return redirect("physical-adjustment")
            if key_conflict:
                form.add_error(
                    None,
                    "La clave de operación ya fue utilizada para otra solicitud. Recargue el formulario e inténtelo nuevamente.",
                )
            elif adjustment is not None:
                messages.success(request, "Ajuste físico registrado correctamente.")
                return redirect("physical-adjustment")
    return render(request, "inventory/adjustment_form.html", {
        "form": form,
        "lots": lots,
        "selected_lot": selected_lot,
    })


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


# ── HUECO-03 · HU-INV-06 · Historial de movimientos por producto ─────────────

@roles_required(Role.Code.ADMIN, Role.Code.WAREHOUSE)
@never_cache
@require_GET
def product_movements(request, product_id):
    """Historial unificado de movimientos de un producto (entradas, ventas, mermas, ajustes)."""
    from django.db.models import Q
    from catalog.models import Product
    from sales.models import SaleLine
    from .models import StockWriteOff, PhysicalAdjustment

    product = get_object_or_404(
        Product.objects.prefetch_related(
            "lots__initial_load__responsible",
            "lots__responsible",
            "lots__adjustments",
            "lots__supplier",
        ),
        pk=product_id,
    )

    # Recopilar todos los eventos en listas unificadas
    events = []

    # Carga inicial y entradas posteriores (restando ajustes positivos posteriores para preservar la cantidad original)
    for lot in product.lots.all():
        positive_adj = sum(adj.delta for adj in lot.adjustments.all() if adj.delta > 0)
        original_initial_qty = max(0, lot.initial_quantity - positive_adj)
        if getattr(lot, "responsible", None):
            responsible_name = lot.responsible.display_name
        elif getattr(lot, "initial_load", None) and getattr(lot.initial_load, "responsible", None):
            responsible_name = lot.initial_load.responsible.display_name
        else:
            responsible_name = "Sistema"
        lot_number = lot.number_normalized or lot.number
        supplier_suffix = f" ({lot.supplier.name})" if lot.supplier else ""
        if lot.is_initial:
            desc = f"Carga inicial — Lote {lot_number}{supplier_suffix}"
        else:
            desc = f"Entrada de mercadería — Lote {lot_number}{supplier_suffix}"
        events.append({
            "tipo": "entrada",
            "icono": "\u25b2",
            "fecha": lot.received_at,
            "orden_tipo": 0,
            "orden_id": str(lot.pk),
            "descripcion": desc,
            "cantidad": f"+{original_initial_qty}",
            "responsable": responsible_name,
        })

    # Ventas registradas (por FK directa o líneas heredadas sin FK y mismo código histórico)
    sale_lines = (
        SaleLine.objects
        .filter(Q(product=product) | Q(product__isnull=True, product_snapshot_barcode=product.barcode))
        .select_related("sale__seller")
        .order_by("-sale__confirmed_at")
        .distinct()
    )
    for sl in sale_lines:
        seller = sl.sale.seller
        events.append({
            "tipo": "venta",
            "icono": "\u25bc",
            "fecha": sl.sale.confirmed_at,
            "orden_tipo": 1,
            "orden_id": (sl.sale.correlative, str(sl.pk)),
            "descripcion": f"Venta {sl.sale.correlative}",
            "cantidad": f"-{sl.quantity}",
            "responsable": seller.display_name if hasattr(seller, "display_name") else str(seller),
        })

    # Mermas
    writeoffs = (
        StockWriteOff.objects
        .filter(lot__product=product)
        .select_related("responsible", "lot")
        .order_by("-created_at")
    )
    for wo in writeoffs:
        wo_lot_num = wo.lot.number_normalized or wo.lot.number
        notes_suffix = f". {wo.notes}" if wo.notes else ""
        events.append({
            "tipo": "merma",
            "icono": "\u25bc",
            "fecha": wo.created_at,
            "orden_tipo": 2,
            "orden_id": (wo.correlativo, str(wo.pk)),
            "descripcion": f"Merma ({wo.get_reason_display()}) · {wo.correlativo} — Lote {wo_lot_num}{notes_suffix}",
            "cantidad": f"-{wo.quantity}",
            "responsable": wo.responsible.display_name if hasattr(wo.responsible, "display_name") else str(wo.responsible),
        })

    # Ajustes físicos
    adjustments = (
        PhysicalAdjustment.objects
        .filter(lot__product=product)
        .select_related("responsible", "lot")
        .order_by("-created_at")
    )
    for adj in adjustments:
        signo = "+" if adj.delta > 0 else ""
        adj_lot_num = adj.lot.number_normalized or adj.lot.number
        reason_suffix = f". {adj.reason}" if adj.reason else ""
        events.append({
            "tipo": "ajuste",
            "icono": "\u21c5",
            "fecha": adj.created_at,
            "orden_tipo": 3,
            "orden_id": str(adj.pk),
            "descripcion": f"Ajuste f\u00edsico — Lote {adj_lot_num}{reason_suffix}",
            "cantidad": f"{signo}{adj.delta}",
            "responsable": adj.responsible.display_name if hasattr(adj.responsible, "display_name") else str(adj.responsible),
        })

    events.sort(
        key=lambda e: (e["fecha"], e["orden_tipo"], str(e["orden_id"])),
        reverse=True,
    )

    return render(request, "inventory/product_movements.html", {
        "product": product,
        "events": events,
    })