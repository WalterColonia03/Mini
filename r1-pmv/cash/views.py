from __future__ import annotations

import uuid
from datetime import timedelta
from decimal import Decimal

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db.models import DecimalField, OuterRef, Q, Subquery, Sum, Value
from django.db.models.functions import Coalesce, Lower
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_http_methods

from app_platform.history import (
    extract_history_params,
    lima_day_start,
    paginate_history,
    parse_date_range,
)
from identity.authorization import roles_required
from identity.models import Account, Role
from sales.models import Sale

from .forms import CashCloseForm, CashOpeningForm
from .models import CashShift, CashShiftClose
from .services import close_cash_shift, open_cash_shift


def _add_validation_error(form, error: ValidationError) -> None:
    if hasattr(error, "error_dict"):
        for field, errors in error.error_dict.items():
            target = field if field in form.fields else None
            for item in errors:
                form.add_error(target, item)
    else:
        for message in error.messages:
            form.add_error(None, message)


@roles_required(Role.Code.SELLER)
@never_cache
@require_http_methods(["GET", "POST"])
def cash_open(request):
    current_shift = CashShift.objects.select_related("cash_register", "seller").filter(
        status=CashShift.Status.OPEN
    ).first()
    form = CashOpeningForm(request.POST if request.method == "POST" else None)
    if request.method == "POST" and form.is_valid():
        try:
            shift = open_cash_shift(actor=request.user, **form.cleaned_data)
        except ValidationError as error:
            _add_validation_error(form, error)
            current_shift = CashShift.objects.select_related("cash_register", "seller").filter(
                status=CashShift.Status.OPEN
            ).first()
        else:
            return redirect("cash-shift-opened", shift_id=shift.pk)
    return render(
        request,
        "cash/cash_open.html",
        {
            "form": form,
            "current_shift": current_shift,
            "owns_shift": current_shift is not None and current_shift.seller_id == request.user.pk,
        },
    )


@roles_required(Role.Code.SELLER)
@never_cache
@require_GET
def cash_shift_opened(request, shift_id):
    shift = get_object_or_404(
        CashShift.objects.select_related("cash_register", "seller", "close"),
        pk=shift_id,
        seller=request.user,
    )
    try:
        close = shift.close
    except CashShiftClose.DoesNotExist:
        close = None
    return render(request, "cash/cash_shift_opened.html", {"shift": shift, "close": close})


def _close_context_for_seller(actor):
    from sales.services import active_draft_for_actor

    current_shift = (
        CashShift.objects.select_related("cash_register", "seller")
        .filter(seller=actor, status=CashShift.Status.OPEN)
        .first()
    )
    draft = active_draft_for_actor(actor=actor)
    has_active_draft = bool(
        current_shift is not None
        and draft is not None
        and draft.cash_shift_id == current_shift.pk
        and draft.lines.exists()
    )
    return current_shift, has_active_draft


@roles_required(Role.Code.SELLER)
@never_cache
@require_http_methods(["GET", "POST"])
def cash_close(request):
    """Cash shift closure form (GET) or confirm closure (POST)."""
    current_shift, has_active_draft = _close_context_for_seller(request.user)
    form = CashCloseForm(request.POST if request.method == "POST" else None)
    if request.method == "POST" and form.is_valid():
        try:
            close = close_cash_shift(actor=request.user, **form.cleaned_data)
        except ValidationError as error:
            _add_validation_error(form, error)
            current_shift, has_active_draft = _close_context_for_seller(request.user)
        else:
            return redirect("cash-shift-closed", shift_id=close.cash_shift_id)
    return render(
        request,
        "cash/cash_close.html",
        {
            "form": form,
            "current_shift": current_shift,
            "has_active_draft": has_active_draft,
        },
    )


@roles_required(Role.Code.SELLER, Role.Code.ADMIN)
@never_cache
@require_GET
def cash_shift_closed(request, shift_id):
    """Acta de cierre del turno."""
    qs = CashShift.objects.select_related("cash_register", "seller")
    if request.user.role.code == Role.Code.SELLER:
        shift = get_object_or_404(qs, pk=shift_id, seller=request.user)
    else:
        shift = get_object_or_404(qs, pk=shift_id)
    close = get_object_or_404(CashShiftClose, cash_shift=shift)
    sales_total = (
        Sale.objects.filter(cash_shift=shift).aggregate(total=Sum("total_amount"))["total"]
        or Decimal("0.00")
    )
    return render(
        request,
        "cash/cash_shift_closed.html",
        {"shift": shift, "close": close, "sales_total": sales_total},
    )


# ── HU-CAJA-05 · Historial de turnos de caja ─────────────────────────────────


@roles_required(Role.Code.ADMIN, Role.Code.SELLER)
@never_cache
@require_GET
def cash_shift_history(request):
    """Lista de turnos de caja con apertura, total cobrado, cierre, filtros y paginación estable."""
    is_admin = request.user.role.code == Role.Code.ADMIN
    sales_subtotal_sq = Subquery(
        Sale.objects.filter(cash_shift=OuterRef("pk"))
        .order_by()
        .values("cash_shift")
        .annotate(total=Sum("total_amount"))
        .values("total")[:1],
        output_field=DecimalField(max_digits=14, decimal_places=2),
    )
    shifts_qs = (
        CashShift.objects.select_related("cash_register", "seller", "close")
        .annotate(sales_collected=Coalesce(sales_subtotal_sq, Value(Decimal("0.00"))))
        .order_by("-opened_at", "-id")
    )
    if not is_admin:
        shifts_qs = shifts_qs.filter(seller=request.user)

    cleaned, raw_page, param_errors = extract_history_params(
        request, ("fecha_desde", "fecha_hasta", "vendedor")
    )
    fecha_desde = cleaned["fecha_desde"]
    fecha_hasta = cleaned["fecha_hasta"]
    vendedor = cleaned["vendedor"] if is_admin else ""

    invalid_filter = bool(param_errors)
    for err in param_errors:
        messages.error(request, err)

    parsed_desde = None
    parsed_hasta = None
    if not invalid_filter:
        parsed_desde, parsed_hasta, range_errors = parse_date_range(fecha_desde, fecha_hasta)
        for err in range_errors:
            messages.error(request, err)
            invalid_filter = True
        if not invalid_filter:
            if parsed_desde is not None:
                shifts_qs = shifts_qs.filter(opened_at__gte=lima_day_start(parsed_desde))
            if parsed_hasta is not None:
                shifts_qs = shifts_qs.filter(
                    opened_at__lt=lima_day_start(parsed_hasta + timedelta(days=1))
                )

    if not invalid_filter and is_admin and vendedor:
        try:
            seller_uuid = uuid.UUID(vendedor)
        except ValueError:
            messages.error(request, "El vendedor seleccionado no es válido.")
            invalid_filter = True
        else:
            shifts_qs = shifts_qs.filter(seller_id=seller_uuid)

    is_filtered = bool(fecha_desde or fecha_hasta or vendedor or invalid_filter)
    shifts_all = [] if invalid_filter else list(shifts_qs)

    sellers = []
    if is_admin:
        if is_filtered:
            sellers = list(
                Account.objects.filter(Q(role__code=Role.Code.SELLER) | Q(cash_shifts__isnull=False))
                .distinct()
                .order_by(Lower("display_name"), "id")
            )
        else:
            seller_map = {}
            for sh in shifts_all:
                seller_map.setdefault(sh.seller_id, sh.seller)
            sellers = sorted(
                seller_map.values(),
                key=lambda acc: ((acc.display_name or "").lower(), str(acc.pk)),
            )

    page_obj = None
    previous_url = None
    next_url = None
    total_shifts_count = 0
    if not invalid_filter:
        filter_params = {"fecha_desde": fecha_desde, "fecha_hasta": fecha_hasta}
        if is_admin and vendedor:
            filter_params["vendedor"] = vendedor
        page_obj, previous_url, next_url, page_error = paginate_history(
            shifts_all,
            raw_page=raw_page,
            per_page=25,
            filter_params=filter_params,
        )
        if page_error:
            messages.error(request, page_error)
            invalid_filter = True
        else:
            total_shifts_count = len(shifts_all)

    shifts = page_obj.object_list if page_obj is not None else []
    return render(
        request,
        "cash/cash_shift_history.html",
        {
            "shifts": shifts,
            "page_obj": page_obj,
            "total_shifts_count": total_shifts_count,
            "previous_url": previous_url,
            "next_url": next_url,
            "has_invalid_query": invalid_filter,
            "is_admin_view": is_admin,
            "is_filtered": is_filtered,
            "sellers": sellers,
            "fecha_desde": fecha_desde,
            "fecha_hasta": fecha_hasta,
            "vendedor": vendedor,
        },
    )
