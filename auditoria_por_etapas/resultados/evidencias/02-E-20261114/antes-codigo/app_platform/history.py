"""Shared validation and pagination helpers for chronological history views."""
from __future__ import annotations

import re
from datetime import date, datetime, time
from urllib.parse import urlencode

from django.core.paginator import EmptyPage, Page, Paginator
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.utils.functional import cached_property

HISTORY_DATE_PATTERN = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$", re.ASCII)
HISTORY_PAGE_PATTERN = re.compile(r"^[1-9][0-9]{0,8}$", re.ASCII)
INVALID_PAGE_MESSAGE = "La página solicitada no existe para estos filtros."


class PrecountedPaginator(Paginator):
    """Paginator that reuses an already-computed total count when provided."""

    def __init__(self, object_list, per_page: int, *, total_count: int | None = None) -> None:
        self._total_count = total_count
        super().__init__(object_list, per_page)

    @cached_property
    def count(self) -> int:
        if self._total_count is not None:
            return self._total_count
        return super().count


def lima_day_start(day: date) -> datetime:
    """Return midnight in the active site timezone (America/Lima) for a calendar date."""
    return timezone.make_aware(datetime.combine(day, time.min), timezone.get_current_timezone())


def parse_history_date(value: str, *, needs_next_day: bool = False) -> date | None:
    """Reject malformed/impossible dates and date.max overflow before building Lima intervals."""
    if not HISTORY_DATE_PATTERN.fullmatch(value):
        return None
    try:
        parsed = parse_date(value)
    except ValueError:
        return None
    if parsed is None:
        return None
    if needs_next_day and parsed == date.max:
        return None
    return parsed


def extract_history_params(
    request,
    fields: tuple[str, ...],
) -> tuple[dict[str, str], str, list[str]]:
    """Extract stripped GET filter/page parameters, rejecting duplicates and NUL bytes."""
    cleaned: dict[str, str] = {}
    errors: list[str] = []
    all_fields = (*fields, "page")
    for name in all_fields:
        values = request.GET.getlist(name)
        if len(values) > 1 and not errors:
            errors.append(f"No repita el parámetro {name}.")
        raw_val = values[0] if values else ""
        if "\x00" in raw_val and not errors:
            errors.append("Los filtros contienen caracteres no válidos.")
        cleaned[name] = raw_val.replace("\x00", "").strip()
    raw_page = cleaned.pop("page", "")
    return cleaned, raw_page, errors


def parse_date_range(fecha_desde: str, fecha_hasta: str) -> tuple[date | None, date | None, list[str]]:
    """Parse an inclusive YYYY-MM-DD range with Lima end-of-day overflow protection."""
    errors: list[str] = []
    parsed_desde = None
    parsed_hasta = None
    if fecha_desde:
        parsed_desde = parse_history_date(fecha_desde)
        if parsed_desde is None:
            errors.append("La fecha inicial ingresada no es válida. Usa el formato AAAA-MM-DD.")
    if not errors and fecha_hasta:
        parsed_hasta = parse_history_date(fecha_hasta, needs_next_day=True)
        if parsed_hasta is None:
            errors.append("La fecha final ingresada no es válida. Usa el formato AAAA-MM-DD.")
    if not errors and parsed_desde and parsed_hasta and parsed_desde > parsed_hasta:
        errors.append("La fecha inicial no puede ser posterior a la fecha final.")
    return parsed_desde, parsed_hasta, errors


def paginate_history(
    items,
    *,
    raw_page: str,
    per_page: int = 25,
    total_count: int | None = None,
    filter_params: dict[str, str] | None = None,
) -> tuple[Page | None, str | None, str | None, str | None]:
    """Validate ASCII page number and paginate items while preserving non-empty filter params."""
    if not raw_page:
        page_num = 1
    elif HISTORY_PAGE_PATTERN.fullmatch(raw_page):
        page_num = int(raw_page)
    else:
        return None, None, None, INVALID_PAGE_MESSAGE

    paginator = PrecountedPaginator(items, per_page, total_count=total_count)
    try:
        page_obj = paginator.page(page_num)
    except EmptyPage:
        return None, None, None, INVALID_PAGE_MESSAGE

    clean_params = {key: value for key, value in (filter_params or {}).items() if value}
    previous_url = (
        f"?{urlencode({**clean_params, 'page': page_obj.previous_page_number()})}"
        if page_obj.has_previous()
        else None
    )
    next_url = (
        f"?{urlencode({**clean_params, 'page': page_obj.next_page_number()})}"
        if page_obj.has_next()
        else None
    )
    return page_obj, previous_url, next_url, None
