"""Contraejemplos de la propuesta: no importa producto, no abre DB ni usa red."""
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from datetime import datetime, timezone
import json

D = Decimal
cases = []

# Reducir efectivo por recibir no borra efectivo ya recibido.
total, digital, cash_received = 1500, 1500, 500
pending_cash = max(0, total - digital)
liability = max(0, digital + cash_received - total)
assert pending_cash == 0 and liability == 500
cases.append(dict(id='A01', pending_cash_cents=pending_cash,
                  real_excess_cents=liability, passed=True))

# Vigilar un QR sustituido no limita lo que sigue siendo pagable externamente.
payable_attempts = [1500, 1000]
assert sum(payable_attempts) > total
cases.append(dict(id='A02', external_payable_cents=sum(payable_attempts),
                  order_cents=total, passed=True))

# Dos pagos diferentes pueden tener iguales atributos observados en ventana 15s.
a = dict(bank_id='real-A', amount=1000, name='Ana', code='123', second=0)
b = dict(bank_id='real-B', amount=1000, name='Ana', code='123', second=10)
heuristic_duplicate = all(a[k] == b[k] for k in ('amount', 'name', 'code')) and b['second']-a['second'] <= 15
assert heuristic_duplicate and a['bank_id'] != b['bank_id']
cases.append(dict(id='A03', heuristic_merges_two_distinct_payments=True, passed=True))

# La ventana local no es el plazo de identidad de un movimiento bancario.
cache_window_seconds, repeat_after_seconds = 180, 181
assert repeat_after_seconds > cache_window_seconds
cases.append(dict(id='A04', same_bank_payment_can_be_outside_local_window=True, passed=True))

# Hipotesis EXPLICITA de redondeo por operacion; no tarifa efectiva ensayada.
amounts = [D('1.67')]*5 + [D('1.65')]
fees = [x*D('0.0349')+D('1') for x in amounts]
per_operation = sum(x.quantize(D('0.01'), rounding=ROUND_HALF_UP) for x in fees)
aggregate = sum(fees).quantize(D('0.01'), rounding=ROUND_HALF_UP)
assert sum(amounts) == D('10') and per_operation == D('6.36') and aggregate == D('6.35')
cases.append(dict(id='A05', aggregate_rounding=str(aggregate),
                  per_operation_rounding=str(per_operation), passed=True))

# El saldo contable no mide la presencia de billetes.
book, physical, requested = 2000, 500, 1000
assert requested <= book and requested > physical
cases.append(dict(id='A06', book_allows=True, physical_cash_sufficient=False, passed=True))

# Una aplicacion a otra venta no es ademas un reembolso ejecutado.
gross, allocated_to_new_sale, mistakenly_counted_refund = 1000, 1000, 1000
assert allocated_to_new_sale + mistakenly_counted_refund > gross
cases.append(dict(id='A07', erroneous_double_classification_cents=2000,
                  received_cents=gross, passed=True))

result = dict(time_utc=datetime.now(timezone.utc).isoformat(),
              status='PROBADO solo para siete contraejemplos en memoria',
              cases=cases, django_imported=False, db_opened=False, network=False,
              limits='No ejecuta el algoritmo de Argon, Django, PostgreSQL ni billeteras. No estima frecuencia de colision, tarifa efectiva, fraude o rendimiento.')
Path(__file__).with_name('contraejemplos.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
print(json.dumps({'cases': len(cases), 'passed': all(c['passed'] for c in cases), 'scope': result['status']}, ensure_ascii=True))
