from __future__ import annotations

import uuid
from datetime import timedelta
from decimal import Decimal
from urllib.parse import urlencode

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db.models import Count, Q, Sum
from django.db.models.functions import Lower
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from app_platform.history import (
    extract_history_params,
    lima_day_start,
    paginate_history,
    parse_date_range,
    parse_history_date,
)
from cash.models import CashShift
from catalog.models import Product, ProductBarcodeKey
from identity.authorization import roles_required
from identity.models import Account, Role

from .forms import AddDraftLineForm, CheckoutForm, ConfirmedCheckoutRetryForm, ProductSearchForm, UpdateDraftLineForm
from .models import Sale, SaleDraft, SaleDraftLine
from .services import (
    MONEY,
    active_draft_for_actor,
    add_product_to_draft,
    checkout_sale,
    discard_active_draft,
    draft_totals,
    draft_signature,
    remove_draft_line,
    update_draft_line,
)


def _draft_signature(draft) -> str:
    if draft is None:
        return ""
    return draft_signature(draft.pk, draft.lines.all())


def _add_validation_error(form, error: ValidationError) -> None:
    if hasattr(error, "error_dict"):
        for field, errors in error.error_dict.items():
            target = field if field in form.fields else None
            for item in errors:
                form.add_error(target, item)
    else:
        for message in error.messages:
            form.add_error(None, message)


def _search_products(query: str):
    cleaned = (query or "").strip()
    if not cleaned or "\x00" in (query or ""):
        return Product.objects.none()
    normalized_name = Product.normalize_search_name(cleaned)
    normalized_code = Product.normalize_barcode(cleaned)
    query_filter = Q()
    if normalized_name:
        query_filter |= Q(search_name__contains=normalized_name)
    if normalized_code:
        query_filter |= Q(barcode_normalized=normalized_code) | Q(
            pk__in=ProductBarcodeKey.objects.filter(reading_key=normalized_code).values("product_id")
        )
    if not query_filter:
        return Product.objects.none()
    return (
        Product.objects.filter(is_active=True, category__is_active=True)
        .filter(query_filter)
        .filter(lots__available_quantity__gt=0, lots__expiration_date__gt=timezone.localdate())
        .annotate(sellable_quantity=Sum("lots__available_quantity"))
        .order_by("name", "barcode_normalized")
        .distinct()
    )


@roles_required(Role.Code.SELLER)
@never_cache
@require_http_methods(["GET", "POST"])
def sales_draft(request):
    search_form = ProductSearchForm(request.GET if "query" in request.GET else None)
    query = ""
    products = Product.objects.none()
    if search_form.is_bound and search_form.is_valid():
        query = search_form.cleaned_data["query"].strip()
        products = _search_products(query)

    add_form = AddDraftLineForm(request.POST if request.method == "POST" else None)
    if request.method == "POST" and add_form.is_valid():
        existing_draft = active_draft_for_actor(actor=request.user)
        old_line = (
            existing_draft.lines.filter(product_id=add_form.cleaned_data["product_id"]).first()
            if existing_draft
            else None
        )
        old_price = old_line.unit_price if old_line else None
        try:
            updated_draft = add_product_to_draft(actor=request.user, **add_form.cleaned_data)
        except ValidationError as error:
            _add_validation_error(add_form, error)
        else:
            if old_price is not None:
                new_line = updated_draft.lines.select_related("product").filter(
                    product_id=add_form.cleaned_data["product_id"]
                ).first()
                if new_line and new_line.unit_price != old_price:
                    messages.warning(
                        request,
                        f"El precio unitario de «{new_line.product.name}» se actualizó de S/ {old_price:.2f} a S/ {new_line.unit_price:.2f}.",
                    )
            return redirect(f"{request.path}?{urlencode({'query': query})}")

    current_shift = CashShift.objects.filter(seller=request.user, status=CashShift.Status.OPEN).first()
    last_shift_sale = (
        Sale.objects.filter(cash_shift=current_shift, seller=request.user)
        .order_by("-confirmed_at", "-correlative", "-id")
        .first()
        if current_shift
        else None
    )
    draft = active_draft_for_actor(actor=request.user)
    return render(
        request,
        "sales/sales_draft.html",
        {
            "search_form": search_form,
            "add_form": add_form,
            "query": query,
            "products": products,
            "current_shift": current_shift,
            "last_shift_sale": last_shift_sale,
            "draft": draft,
            "totals": draft_totals(draft),
        },
    )


@roles_required(Role.Code.SELLER)
@never_cache
@require_POST
def sales_line_update(request, line_id):
    form = UpdateDraftLineForm(request.POST)
    if form.is_valid():
        old_line = SaleDraftLine.objects.select_related("product").filter(
            pk=line_id, draft__seller=request.user, draft__status=SaleDraft.Status.ACTIVE
        ).first()
        old_price = old_line.unit_price if old_line else None
        try:
            updated_draft = update_draft_line(actor=request.user, line_id=line_id, **form.cleaned_data)
        except ValidationError as error:
            messages.error(request, error.messages[0])
        else:
            if old_price is not None:
                new_line = (
                    updated_draft.lines.select_related("product")
                    .filter(pk=line_id)
                    .first()
                )
                if new_line and new_line.unit_price != old_price:
                    messages.warning(
                        request,
                        f"El precio unitario de «{new_line.product.name}» se actualizó de S/ {old_price:.2f} a S/ {new_line.unit_price:.2f}.",
                    )
    else:
        error_message = next(
            (err for errs in form.errors.values() for err in errs),
            "Ingresa una cantidad entera mayor que cero.",
        )
        messages.error(request, error_message)
    return redirect("sales-draft")


@roles_required(Role.Code.SELLER)
@never_cache
@require_POST
def sales_line_remove(request, line_id):
    try:
        remove_draft_line(actor=request.user, line_id=line_id)
    except ValidationError as error:
        messages.error(request, error.messages[0])
    return redirect("sales-draft")


@roles_required(Role.Code.SELLER)
@never_cache
@require_POST
def sales_draft_discard(request):
    if discard_active_draft(actor=request.user):
        messages.success(request, "La venta en preparación fue descartada.")
    return redirect("sales-draft")


@roles_required(Role.Code.SELLER)
@never_cache
@require_http_methods(["GET", "POST"])
def sales_checkout(request):
    """Cobro: show checkout form (GET) or confirm sale (POST)."""
    if request.method == "POST":
        raw_idem = (request.POST.get("idempotency_key") or "").strip()
        existing_sale = None
        if raw_idem and "\x00" not in raw_idem:
            try:
                parsed_idem = uuid.UUID(raw_idem)
            except (ValueError, AttributeError):
                parsed_idem = None
            if parsed_idem is not None:
                existing_sale = Sale.objects.filter(idempotency_key=parsed_idem).first()

        if existing_sale is not None and existing_sale.seller_id == request.user.pk:
            retry_form = ConfirmedCheckoutRetryForm(request.POST)
            if retry_form.is_valid():
                posted_sig = (retry_form.cleaned_data.get("draft_signature") or "").strip()
                sig_draft_prefix = posted_sig.split("|", 1)[0] if "|" in posted_sig else ""
                if existing_sale.draft_id is not None and sig_draft_prefix == str(existing_sale.draft_id):
                    posted_expected = retry_form.cleaned_data.get("expected_subtotal")
                    posted_cash = retry_form.cleaned_data["cash_received"]
                    posted_discount = (
                        retry_form.cleaned_data.get("discount_amount") or Decimal("0.00")
                    ).quantize(MONEY)
                    recorded_subtotal = (
                        existing_sale.total_amount + existing_sale.discount_amount
                    ).quantize(MONEY)
                    if (
                        posted_expected is not None
                        and posted_expected == recorded_subtotal
                        and posted_cash == existing_sale.cash_received
                        and posted_discount == existing_sale.discount_amount
                    ):
                        messages.info(
                            request,
                            f"Este cobro ya había sido confirmado ({existing_sale.correlative}); se muestra su constancia interna.",
                        )
                        return redirect("sales-receipt", sale_id=existing_sale.pk)

                    draft = active_draft_for_actor(actor=request.user)
                    if draft is None:
                        messages.error(request, "La clave de cobro ya fue usada con otros montos.")
                        return redirect("sales-draft")

                    totals = draft_totals(draft)
                    current_sig = _draft_signature(draft)
                    post_data = request.POST.copy()
                    post_data["expected_subtotal"] = str(totals.total)
                    post_data["draft_signature"] = current_sig
                    form = CheckoutForm(post_data)
                    form.is_valid()
                    form.add_error(None, "La clave de cobro ya fue usada con otros montos.")
                    return render(
                        request,
                        "sales/sales_checkout.html",
                        {
                            "form": form,
                            "draft": draft,
                            "totals": totals,
                            "subtotal": totals.total,
                        },
                    )

    draft = active_draft_for_actor(actor=request.user)
    if draft is None:
        messages.error(request, "No tienes una venta en preparación.")
        return redirect("sales-draft")

    totals = draft_totals(draft)
    current_sig = _draft_signature(draft)

    if request.method == "POST":
        post_data = request.POST.copy()
        if not post_data.get("idempotency_key"):
            post_data["idempotency_key"] = str(uuid.uuid4())
        form = CheckoutForm(post_data)
        if form.is_valid():
            expected_subtotal = form.cleaned_data.get("expected_subtotal")
            posted_sig = (form.cleaned_data.get("draft_signature") or "").strip()
            # Both values must be present: otherwise a modified request could
            # bypass the review of a draft changed in another tab. Redisplay
            # the current summary and require a new, explicit confirmation.
            subtotal_mismatch = expected_subtotal is None or expected_subtotal != totals.total
            sig_mismatch = not posted_sig or posted_sig != current_sig
            if subtotal_mismatch or sig_mismatch:
                post_data["expected_subtotal"] = str(totals.total)
                post_data["draft_signature"] = current_sig
                form = CheckoutForm(post_data)
                form.is_valid()
                message = (
                    f"No se pudo verificar el resumen de la venta. "
                    f"El subtotal actual es S/ {totals.total:.2f}; revisa el resumen antes de confirmar el cobro."
                    if expected_subtotal is None or not posted_sig else
                    f"El resumen de la venta en preparación cambió. "
                    f"El subtotal actual es S/ {totals.total:.2f}; revisa el resumen antes de confirmar el cobro."
                )
                form.add_error(
                    None,
                    message,
                )
            else:
                try:
                    sale = checkout_sale(
                        actor=request.user,
                        draft_id=draft.pk,
                        cash_received=form.cleaned_data["cash_received"],
                        idempotency_key=form.cleaned_data["idempotency_key"],
                        expected_subtotal=expected_subtotal,
                        expected_signature=posted_sig,
                    )
                except ValidationError as error:
                    draft = active_draft_for_actor(actor=request.user)
                    if draft is None:
                        for msg in error.messages:
                            messages.error(request, msg)
                        return redirect("sales-draft")
                    totals = draft_totals(draft)
                    current_sig = _draft_signature(draft)
                    post_data["expected_subtotal"] = str(totals.total)
                    post_data["draft_signature"] = current_sig
                    form = CheckoutForm(post_data)
                    form.is_valid()
                    for msg in error.messages:
                        form.add_error(None, msg)
                else:
                    return redirect("sales-receipt", sale_id=sale.pk)
    else:
        form = CheckoutForm(
            initial={
                "idempotency_key": uuid.uuid4(),
                "expected_subtotal": totals.total,
                "draft_signature": current_sig,
            }
        )

    return render(
        request,
        "sales/sales_checkout.html",
        {
            "form": form,
            "draft": draft,
            "totals": totals,
            "subtotal": totals.total,
        },
    )


@roles_required(Role.Code.SELLER, Role.Code.ADMIN)
@never_cache
@require_GET
def sales_receipt(request, sale_id):
    """Internal receipt for a confirmed sale."""
    qs = Sale.objects.select_related("seller", "cash_shift__cash_register").prefetch_related("lines")
    if request.user.role.code == Role.Code.SELLER:
        sale = get_object_or_404(qs, pk=sale_id, seller=request.user)
    else:
        sale = get_object_or_404(qs, pk=sale_id)
    pre_discount_subtotal = (sale.total_amount + sale.discount_amount).quantize(MONEY)
    open_shift = (
        CashShift.objects.filter(seller=request.user, status=CashShift.Status.OPEN).first()
        if request.user.role.code == Role.Code.SELLER
        else None
    )
    return render(
        request,
        "sales/sales_receipt.html",
        {
            "sale": sale,
            "pre_discount_subtotal": pre_discount_subtotal,
            "open_shift": open_shift,
        },
    )


# ── HU-VEN-05a · Historial de ventas del turno actual ────────────────────────

@roles_required(Role.Code.SELLER)
@never_cache
@require_GET
def sales_shift_history(request):
    """Ventas confirmadas del turno actualmente abierto del vendedor."""
    shift = (
        CashShift.objects.select_related("cash_register")
        .filter(seller=request.user, status=CashShift.Status.OPEN)
        .first()
    )
    sales = (
        Sale.objects.filter(cash_shift=shift)
        .select_related("seller")
        .order_by("-confirmed_at", "-correlative", "-id")
        if shift
        else Sale.objects.none()
    )
    shift_agg = sales.aggregate(total=Sum("total_amount"), discount=Sum("discount_amount"))
    shift_total = shift_agg["total"] or Decimal("0.00")
    shift_discount = shift_agg["discount"] or Decimal("0.00")
    return render(
        request,
        "sales/sales_shift_history.html",
        {"sales": sales, "shift": shift, "shift_total": shift_total, "shift_discount": shift_discount},
    )


# ── HU-VEN-05b · Historial completo de ventas (admin y vendedor) ─────────────


@roles_required(Role.Code.ADMIN, Role.Code.SELLER)
@never_cache
@require_GET
def sales_history(request):
    """Historial completo de ventas con filtros opcionales y paginación estable."""
    is_admin = request.user.role.code == Role.Code.ADMIN
    sales = Sale.objects.select_related("seller", "cash_shift__cash_register").order_by(
        "-confirmed_at", "-correlative", "-id"
    )
    if not is_admin:
        sales = sales.filter(seller=request.user)

    cleaned, raw_page, param_errors = extract_history_params(
        request, ("correlativo", "fecha", "fecha_desde", "fecha_hasta", "vendedor", "turno")
    )
    correlativo = cleaned["correlativo"]
    fecha = cleaned["fecha"]
    fecha_desde = cleaned["fecha_desde"]
    fecha_hasta = cleaned["fecha_hasta"]
    vendedor = cleaned["vendedor"] if is_admin else ""
    turno = cleaned["turno"]

    invalid_filter = bool(param_errors)
    for err in param_errors:
        messages.error(request, err)

    if not invalid_filter and correlativo:
        sales = sales.filter(correlative__icontains=correlativo)

    if not invalid_filter and fecha:
        parsed_date = parse_history_date(fecha, needs_next_day=True)
        if parsed_date is None:
            messages.error(request, "La fecha ingresada no es válida. Usa el formato AAAA-MM-DD.")
            invalid_filter = True
        else:
            start_dt = lima_day_start(parsed_date)
            end_dt = lima_day_start(parsed_date + timedelta(days=1))
            sales = sales.filter(confirmed_at__gte=start_dt, confirmed_at__lt=end_dt)

    if not invalid_filter:
        parsed_desde, parsed_hasta, range_errors = parse_date_range(fecha_desde, fecha_hasta)
        for err in range_errors:
            messages.error(request, err)
            invalid_filter = True
        if not invalid_filter:
            if parsed_desde is not None:
                sales = sales.filter(confirmed_at__gte=lima_day_start(parsed_desde))
            if parsed_hasta is not None:
                sales = sales.filter(confirmed_at__lt=lima_day_start(parsed_hasta + timedelta(days=1)))

    if not invalid_filter and is_admin and vendedor:
        try:
            seller_uuid = uuid.UUID(vendedor)
        except ValueError:
            messages.error(request, "El vendedor seleccionado no es válido.")
            invalid_filter = True
        else:
            sales = sales.filter(seller_id=seller_uuid)

    if not invalid_filter and turno:
        try:
            shift_uuid = uuid.UUID(turno)
        except ValueError:
            messages.error(request, "El turno seleccionado no es válido.")
            invalid_filter = True
        else:
            sales = sales.filter(cash_shift_id=shift_uuid)

    totals_agg = None
    total_sales_count = 0
    page_obj = None
    previous_url = None
    next_url = None
    if not invalid_filter:
        totals_agg = sales.aggregate(
            total=Sum("total_amount"), discount=Sum("discount_amount"), total_count=Count("id")
        )
        total_sales_count = totals_agg["total_count"] or 0
        filter_params = {
            "correlativo": correlativo,
            "fecha": fecha,
            "fecha_desde": fecha_desde,
            "fecha_hasta": fecha_hasta,
            "turno": turno,
        }
        if is_admin and vendedor:
            filter_params["vendedor"] = vendedor
        page_obj, previous_url, next_url, page_error = paginate_history(
            sales,
            raw_page=raw_page,
            per_page=25,
            total_count=total_sales_count,
            filter_params=filter_params,
        )
        if page_error:
            messages.error(request, page_error)
            invalid_filter = True

    if invalid_filter or page_obj is None:
        sales_page = Sale.objects.none()
        total_vendido = Decimal("0.00")
        total_descuentos = Decimal("0.00")
        total_sales_count = 0
        previous_url = None
        next_url = None
    else:
        sales_page = page_obj.object_list
        total_vendido = totals_agg["total"] or Decimal("0.00")
        total_descuentos = totals_agg["discount"] or Decimal("0.00")

    sellers = (
        Account.objects.filter(Q(role__code=Role.Code.SELLER) | Q(sales__isnull=False))
        .distinct()
        .order_by(Lower("display_name"), "id")
        if is_admin
        else Account.objects.none()
    )
    shifts_qs = CashShift.objects.select_related("cash_register", "seller").order_by("-opened_at", "-id")
    if not is_admin:
        shifts_qs = shifts_qs.filter(seller=request.user)

    return render(
        request,
        "sales/sales_history.html",
        {
            "sales": sales_page,
            "page_obj": page_obj,
            "total_sales_count": total_sales_count,
            "previous_url": previous_url,
            "next_url": next_url,
            "has_invalid_query": invalid_filter,
            "is_admin_view": is_admin,
            "sellers": sellers,
            "shifts": shifts_qs[:200],
            "correlativo": correlativo,
            "fecha": fecha,
            "fecha_desde": fecha_desde,
            "fecha_hasta": fecha_hasta,
            "vendedor": vendedor,
            "turno": turno,
            "total_vendido": total_vendido,
            "total_descuentos": total_descuentos,
        },
    )
