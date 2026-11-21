"""Read-only inventory ledger from persisted origins; no inferred opening stock."""
from collections import defaultdict
from zoneinfo import ZoneInfo

from django.db.models import Prefetch, Q
from django.utils import timezone

from sales.models import SaleLine, SaleLotAllocation
from .models import PhysicalAdjustment, StockWriteOff

LIMA = ZoneInfo("America/Lima")


def _event(kind, identity, when, description, delta, responsible, changes, **extra):
    return dict(tipo=kind, orden_id=f"{identity}:{kind}", fecha=when,
        descripcion=description, delta=delta,
        cantidad=f"{delta:+d}" if delta is not None else "No disponible",
        responsable=responsible, lot_changes=changes,
        icono="▲" if kind == "entrada" else "⇅" if kind == "ajuste" else "▼", **extra)


def build_ledger(product):
    """Product must have lots prefetched with their source lines and headers."""
    events, issues = [], set()
    lots = list(product.lots.all())
    by_id = {lot.pk: lot for lot in lots}
    known_codes = {product.barcode}
    for lot in lots:
        receipt_line = getattr(lot, "receipt_line", None)
        initial_line = getattr(lot, "initial_line", None)
        adjustment_origin = getattr(lot, "adjustment_origin", None)
        if sum(bool(origin) for origin in (receipt_line, initial_line, adjustment_origin)) > 1:
            issues.add("Un lote tiene más de un origen registrado.")
        if adjustment_origin:
            if adjustment_origin.lot_id != lot.pk or adjustment_origin.delta <= 0 or not adjustment_origin.has_snapshot:
                issues.add("Hay una relación de origen inconsistente.")
            known_codes.add(adjustment_origin.product_snapshot_barcode)
            # The originating adjustment below is the entry; never count a second receipt.
        elif receipt_line:
            line, receipt = receipt_line, receipt_line.receipt
            if receipt.product_id != product.pk:
                issues.add("Hay una relación de origen inconsistente.")
            known_codes.add(receipt.product_snapshot_barcode)
            supplier = receipt.supplier_snapshot_name or "Sin proveedor asignado"
            events.append(_event("entrada", line.pk, receipt.confirmed_at,
                f"Recepción {receipt.correlative} — Lote {line.number} ({supplier})",
                line.quantity, receipt.responsible_snapshot_name, {lot.pk: line.quantity},
                receipt_id=receipt.pk))
        elif initial_line:
            line, load = initial_line, initial_line.load
            if load.product_id != product.pk or line.load_id != lot.initial_load_id:
                issues.add("Hay una relación de origen inconsistente.")
            known_codes.add(load.product_snapshot_barcode)
            if load.responsible_snapshot_name is None or load.supplier_snapshot_name is None:
                issues.add("La cabecera de una carga está incompleta.")
            supplier = f" ({load.supplier_snapshot_name})" if load.supplier_snapshot_name else ""
            events.append(_event("entrada", line.pk, line.received_at,
                f"Carga inicial — Lote {line.number}{supplier}", line.quantity,
                load.responsible_snapshot_name or "No disponible (registro anterior)",
                {lot.pk: line.quantity}, load_id=load.pk))
        else:
            issues.add("Sin fotografía de entrada para uno o más lotes.")
            supplier = f" ({lot.supplier.name})" if lot.supplier else ""
            # Old is_initial flags are not evidence of the kind of entry.
            events.append(_event("entrada", lot.pk, lot.received_at,
                f"Entrada de origen no confirmado — Lote {lot.number_normalized or lot.number}{supplier}",
                None, lot.responsible.display_name if lot.responsible else "No disponible",
                {}, legacy_origin=True))

    known_codes.discard(None)
    sale_lines = (SaleLine.objects.filter(Q(product=product) | Q(product__isnull=True,
        product_snapshot_barcode__in=known_codes)).select_related("sale")
        .prefetch_related(Prefetch("lot_allocations", queryset=SaleLotAllocation.objects.select_related(
            "lot__receipt_line__receipt"))))
    for line in sale_lines:
        allocations = list(line.lot_allocations.all())
        complete = (bool(allocations) and sum(a.quantity for a in allocations) == line.quantity
            and all(a.quantity > 0 and a.lot_id in by_id for a in allocations))
        if not complete:
            issues.add("Una venta tiene asignaciones de lote ausentes o incompletas.")
        if line.product_id is None:
            issues.add("La identidad de un producto vendido no está confirmada.")
        events.append(_event("venta", line.pk, line.sale.confirmed_at,
            f"Venta {line.sale.correlative}", -line.quantity if line.product_id is not None else None,
            line.sale.seller_snapshot_name or "No disponible (registro anterior)",
            {a.lot_id: -a.quantity for a in allocations}, allocations=allocations,
            allocation_complete=complete, product_identity_unknown=line.product_id is None,
            unit_cost=line.unit_cost))

    for item in StockWriteOff.objects.filter(lot__product=product).select_related("responsible", "lot__receipt_line__receipt"):
        lot = by_id.get(item.lot_id)
        if lot is None:
            issues.add("El inventario cambió durante la consulta. Vuelva a consultar.")
            lot = item.lot
        line = getattr(lot, "receipt_line", None)
        notes = f". {item.notes}" if item.notes else ""
        events.append(_event("merma", item.pk, item.created_at,
            f"Merma ({item.get_reason_display()}) · {item.correlativo} — Lote {item.lot_snapshot_number or 'No disponible (registro anterior)'}{notes}",
            -item.quantity, item.responsible_snapshot_name or "No disponible (registro anterior)", {lot.pk: -item.quantity},
            receipt_id=line.receipt_id if line else None, writeoff_id=item.pk,
            writeoff_legacy=not item.has_snapshot, unit_cost=item.unit_cost))
    for item in PhysicalAdjustment.objects.filter(lot__product=product).select_related("responsible", "lot__receipt_line__receipt"):
        lot = by_id.get(item.lot_id)
        if lot is None:
            issues.add("El inventario cambió durante la consulta. Vuelva a consultar.")
            lot = item.lot
        line = getattr(lot, "receipt_line", None)
        reason = f". {item.reason}" if item.reason else ""
        events.append(_event("ajuste", item.pk, item.created_at,
            f"Ajuste físico — Lote {item.lot_snapshot_number or 'No disponible (registro anterior)'}{reason}",
            item.delta, item.responsible_snapshot_name or "No disponible (registro anterior)", {lot.pk: item.delta},
            receipt_id=line.receipt_id if line else None, adjustment_id=item.pk,
            adjustment_legacy=not item.has_snapshot, unit_cost=item.unit_cost))

    events.sort(key=lambda e: (e["fecha"], e["orden_id"]))
    quantities = defaultdict(int)
    balance = 0
    for event in events:
        for lot_id, delta in event["lot_changes"].items():
            if lot_id not in by_id:
                issues.add("Hay una relación de origen inconsistente.")
            quantities[lot_id] += delta
            if quantities[lot_id] < 0:
                issues.add("La secuencia registrada produce una cantidad negativa por lote.")
        if event["delta"] is not None:
            balance += event["delta"]
        event["balance"] = balance
    if any(quantities[lot.pk] != lot.available_quantity for lot in lots):
        issues.add("Las cantidades por lote no concilian con el stock físico actual.")
    if balance != sum(lot.available_quantity for lot in lots):
        issues.add("La variación registrada no concilia con el stock físico actual.")
    if issues:
        for event in events:
            event["balance"] = None
    return events, sorted(issues)


def select_period(events, *, start=None, end=None, kind="", reliable=True):
    """Balances are established before selecting rows; end minute is inclusive."""
    opening = closing = 0
    period = []
    for event in events:
        minute = timezone.localtime(event["fecha"], LIMA).replace(tzinfo=None, second=0, microsecond=0)
        if start is not None and minute < start:
            opening = event["balance"]
        if end is None or minute <= end:
            closing = event["balance"]
        if (start is None or minute >= start) and (end is None or minute <= end):
            period.append(event)
    def matches(event):
        if kind == "salidas":
            return event["tipo"] in ("venta", "merma") or (event["tipo"] == "ajuste" and event["delta"] < 0)
        return not kind or event["tipo"] == kind
    filtered = [event for event in period if matches(event)]
    total = sum(event["delta"] for event in filtered) if all(event["delta"] is not None for event in filtered) else None
    return filtered, dict(opening_balance=opening if reliable else None,
        closing_balance=closing if reliable else None, filtered_delta=total,
        filtered_delta_display=f"{total:+d}" if total else "0" if total == 0 else "No disponible",
        filtered_count=len(filtered))
