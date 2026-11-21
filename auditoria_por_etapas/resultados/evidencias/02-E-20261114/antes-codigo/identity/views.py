from __future__ import annotations

from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.debug import sensitive_post_parameters, sensitive_variables
from django.views.decorators.http import require_GET, require_http_methods

from identity.authorization import roles_required

from .forms import EmployeeCreationForm, EmployeeEditForm, LoginForm
from .models import Account, Role
from .services import (
    INVALID_CREDENTIALS_MESSAGE,
    authenticate_active_account,
    create_employee,
    create_server_session,
    deactivate_employee,
    reactivate_employee,
    update_employee,
)


@sensitive_post_parameters()
@sensitive_variables()
@never_cache
@require_http_methods(["GET", "POST"])
def login_view(request):
    from django.utils.http import url_has_allowed_host_and_scheme

    if request.user.is_authenticated:
        if request.user.is_active:
            return redirect("dashboard")
        logout(request)
    next_url = request.POST.get("next") or request.GET.get("next") or ""
    form = LoginForm(request.POST if request.method == "POST" else None)
    if request.method == "POST":
        if form.is_valid():
            result = authenticate_active_account(form.cleaned_data["email"], form.cleaned_data["password"])
            if result.authenticated:
                create_server_session(request, result.account)
                if next_url and url_has_allowed_host_and_scheme(
                    url=next_url,
                    allowed_hosts={request.get_host()},
                    require_https=request.is_secure(),
                ):
                    return redirect(next_url)
                return redirect("dashboard")
            if result.locked_minutes:
                form.add_error(None, f"Demasiados intentos fallidos consecutivos. Inténtelo nuevamente en {result.locked_minutes} minuto(s).")
            else:
                form.add_error(None, INVALID_CREDENTIALS_MESSAGE)
    return render(request, "identity/login.html", {"form": form, "next": next_url})


@login_required
@require_GET
@never_cache
def dashboard(request):
    if not request.user.is_active:
        logout(request)
        return redirect("login")
    role = request.user.role.code
    if role not in Role.Code.values:
        raise PermissionDenied
    today = timezone.localdate()
    return render(request, "identity/dashboard.html", {
        "summary": _dashboard_summary(role, today),
        "summary_date": today,
    })


@login_required
@require_http_methods(["GET", "POST"])
@never_cache
def logout_view(request):
    from cash.models import CashShift
    from sales.services import active_draft_for_actor, discard_active_draft

    if request.method == "POST":
        # The draft discard and database-backed session revocation must either
        # both commit or both roll back if logout fails.
        with transaction.atomic():
            if active_draft_for_actor(actor=request.user) is not None:
                discard_active_draft(actor=request.user)
            logout(request)
        return redirect("login")
    draft = active_draft_for_actor(actor=request.user)
    has_active_draft = bool(draft is not None and draft.lines.exists())
    has_open_shift = (
        request.user.role.code == Role.Code.SELLER
        and CashShift.objects.filter(seller=request.user, status=CashShift.Status.OPEN).exists()
    )
    return render(
        request,
        "identity/logout_confirm.html",
        {"has_active_draft": has_active_draft, "has_open_shift": has_open_shift},
    )


# ── HU-USR-01 · Lista de empleados ───────────────────────────────────────────

@roles_required(Role.Code.ADMIN)
@require_GET
@never_cache
def employee_list(request):
    """Lista de todos los empleados del minimarket registrados en el sistema."""
    from django.db.models import Q
    from django.db.models.functions import Lower

    query = request.GET.get("q", "").strip()
    accounts = Account.objects.select_related("role").filter(role__code__in=Role.Code.values)
    if query:
        normalized_query = Account.normalize_email(query)
        accounts = accounts.filter(
            Q(display_name__icontains=query)
            | Q(email__icontains=query)
            | Q(email_normalized__icontains=normalized_query)
        )
    accounts = accounts.order_by(Lower("display_name"), "email_normalized")
    return render(
        request,
        "identity/employee_list.html",
        {"accounts": accounts, "employees": accounts, "query": query},
    )


# ── HU-USR-02 · Crear nuevo empleado ─────────────────────────────────────────

@roles_required(Role.Code.ADMIN)
@require_http_methods(["GET", "POST"])
@sensitive_post_parameters("password")
@sensitive_variables("form")
@never_cache
def employee_create(request):
    """Formulario para crear una nueva cuenta de empleado."""
    form = EmployeeCreationForm(request.POST if request.method == "POST" else None)
    if request.method == "POST" and form.is_valid():
        try:
            account = create_employee(
                actor=request.user,
                display_name=form.cleaned_data["display_name"],
                email=form.cleaned_data["email"],
                password=form.cleaned_data["password"],
                role=form.cleaned_data["role"],
            )
        except ValidationError as error:
            if hasattr(error, "error_dict"):
                for field, errors in error.error_dict.items():
                    target = (
                        "email"
                        if field == "email_normalized"
                        else (field if field in form.fields else None)
                    )
                    for item in errors:
                        form.add_error(target, item)
            else:
                for item in error.error_list:
                    form.add_error(None, item)
        else:
            messages.success(request, f"Empleado «{account.display_name}» creado correctamente.")
            return redirect("employee-list")
    return render(request, "identity/employee_form.html", {"form": form})


# ── HU-USR-03 · Editar datos y rol de un empleado ────────────────────────────

@roles_required(Role.Code.ADMIN)
@require_http_methods(["GET", "POST"])
@sensitive_post_parameters("new_password")
@sensitive_variables("form")
@never_cache
def employee_edit(request, account_id):
    """Formulario para editar nombre, correo y rol de un empleado."""
    account = get_object_or_404(Account.objects.select_related("role"), pk=account_id, role__code__in=Role.Code.values)
    initial = {
        "display_name": account.display_name,
        "email": account.email,
        "role": account.role,
    }
    form = EmployeeEditForm(request.POST if request.method == "POST" else None, initial=initial)
    if request.method == "POST" and form.is_valid():
        try:
            update_employee(
                actor=request.user,
                account=account,
                display_name=form.cleaned_data["display_name"],
                email=form.cleaned_data["email"],
                role=form.cleaned_data["role"],
                new_password=form.cleaned_data.get("new_password", ""),
            )
        except ValidationError as error:
            if hasattr(error, "error_dict"):
                for field, errors in error.error_dict.items():
                    target = (
                        "email"
                        if field == "email_normalized"
                        else (field if field in form.fields else None)
                    )
                    for item in errors:
                        form.add_error(target, item)
            else:
                for item in error.error_list:
                    form.add_error(None, item)
        else:
            messages.success(request, f"Empleado «{account.display_name}» actualizado.")
            return redirect("employee-list")
    return render(request, "identity/employee_edit.html", {"form": form, "account": account})


# ── HU-USR-04 · Desactivar / reactivar cuenta de empleado ────────────────────

@roles_required(Role.Code.ADMIN)
@require_http_methods(["POST"])
@never_cache
def employee_deactivate(request, account_id):
    """Apply the explicit requested state; never toggle on a repeated POST."""
    actions = request.POST.getlist("action")
    if len(actions) != 1 or actions[0] not in ("desactivar", "reactivar"):
        return HttpResponseBadRequest("Seleccione una acción de estado válida.")
    account = get_object_or_404(Account, pk=account_id, role__code__in=Role.Code.values)
    try:
        if actions[0] == "desactivar" and account.is_active:
            deactivate_employee(actor=request.user, account=account)
            messages.success(request, f"Cuenta de «{account.display_name}» desactivada.")
        elif actions[0] == "reactivar" and not account.is_active:
            reactivate_employee(actor=request.user, account=account)
            messages.success(request, f"Cuenta de «{account.display_name}» reactivada.")
        else:
            messages.info(request, f"La cuenta de «{account.display_name}» ya tiene el estado solicitado.")
    except ValidationError as error:
        messages.error(request, error.messages[0])
    return redirect("employee-list")



def _dashboard_summary(role, today):
    """DEC-07-VENCIDOS-FILTRO: one statement snapshot, one day, data by role."""
    from datetime import timedelta

    from django.db import connection
    from django.db.models import Case, F, IntegerField, Q, Sum, Value, When

    from cash.models import CashShift
    from catalog.models import Product
    from inventory.models import Lot
    from sales.models import Sale

    if role not in (Role.Code.ADMIN, Role.Code.WAREHOUSE):
        return None
    active = Product.objects.filter(is_active=True, category__is_active=True)
    critical = active.annotate(available=Sum(
        "lots__available_quantity", filter=Q(lots__expiration_date__gt=today), default=0,
    )).filter(available__lte=F("minimum_stock"))
    # Compose only ORM-generated SELECTs and fixed SQL; values stay bound params.
    # Separate aggregate calls can mix commits even inside atomic() under
    # PostgreSQL READ COMMITTED. A single SELECT uses one statement snapshot.
    lots = Lot.objects.filter(available_quantity__gt=0).order_by().annotate(
        is_expiring=Case(When(expiration_date__gt=today,
                             expiration_date__lte=today + timedelta(days=30), then=Value(1)),
                         default=Value(0), output_field=IntegerField()),
        is_expired=Case(When(expiration_date__lte=today, then=Value(1)),
                        default=Value(0), output_field=IntegerField()),
    ).values("is_expiring", "is_expired")
    lot_sql, lot_params = lots.query.sql_with_params()
    critical_sql, critical_params = critical.order_by().values("pk").query.sql_with_params()
    parts = [
        f"(SELECT COALESCE(SUM(is_expiring), 0) AS expiring, "
        f"COALESCE(SUM(is_expired), 0) AS expired FROM ({lot_sql}) AS lot_rows) AS lot_totals",
        f"(SELECT COUNT(*) AS low_stock FROM ({critical_sql}) AS critical_rows) AS critical_totals",
    ]
    params = [*lot_params, *critical_params]
    columns = ["expiring", "expired", "low_stock"]
    if role == Role.Code.ADMIN:
        sales = Sale.objects.filter(confirmed_at__date=today).order_by().values("total_amount", "discount_amount")
        sales_sql, sales_params = sales.query.sql_with_params()
        shifts_sql, shifts_params = CashShift.objects.filter(status=CashShift.Status.OPEN).order_by().values("pk").query.sql_with_params()
        parts.extend([
            f"(SELECT COUNT(*) AS sales_count, COALESCE(SUM(total_amount), 0) AS sales_total, "
            f"COALESCE(SUM(discount_amount), 0) AS discount_total FROM ({sales_sql}) AS sale_rows) AS sale_totals",
            f"(SELECT COUNT(*) AS open_shifts FROM ({shifts_sql}) AS shift_rows) AS shift_totals",
        ])
        params.extend([*sales_params, *shifts_params])
        columns.extend(["sales_count", "sales_total", "discount_total", "open_shifts"])
    with connection.cursor() as cursor:
        cursor.execute("SELECT " + ", ".join(columns) + " FROM " + " CROSS JOIN ".join(parts), params)
        summary = dict(zip(columns, cursor.fetchone()))
    if role == Role.Code.ADMIN:
        # Use the same backend/Decimal conversion as ORM Sum (not float math).
        for key, field in [("sales_total", "total_amount"), ("discount_total", "discount_amount")]:
            expression = Sum(field, default=0).resolve_expression(Sale.objects.all().query)
            for converter in connection.ops.get_db_converters(expression) + expression.get_db_converters(connection):
                summary[key] = converter(summary[key], expression, connection)
    return summary
