"""Modelos monetarios aislados. No importa producto, Django, DB ni red."""
from decimal import Decimal as D
from pathlib import Path
import json

results = []

# Cambiar el QR visible no implica que el proveedor haya invalidado el anterior.
total, old_qr, new_qr = D('15'), D('15'), D('10')
received = old_qr + new_qr
assert received - total == D('10')
results.append({'id': 'AUTO-M01', 'case': 'Dos QR con importes fijos pueden producir exceso',
                'total': str(total), 'recibido': str(received), 'exceso': str(received-total)})

# Un cargo fijo por cada abono cambia sustancialmente el costo de una demo pequeña.
rate, fixed = D('0.0349'), D('1')
fees = {str(n): str(D('10') * rate + fixed*n) for n in (1, 2, 6)}
assert fees == {'1': '1.3490', '2': '2.3490', '6': '6.3490'}
results.append({'id': 'AUTO-M02', 'case': 'Tarifa nominal antes de redondeo y condiciones de cuenta',
                'base_total': '10', 'fees_by_payments': fees})

# El neto cobrado puede no financiar el reintegro bruto, si la comisión se retiene.
net = D('10') - (D('10')*rate+fixed)
assert net < D('10')
results.append({'id': 'AUTO-M03', 'case': 'Saldo neto no garantiza reembolso bruto',
                'saldo_condicional': str(net), 'reembolso': '10',
                'limite': 'Hipótesis de comisión retenida, no comportamiento probado del proveedor'})

# Mixto: total15; digital10; billete10; efectivo aplicado5; vuelto5.
total, digital, tender = D('15'), D('10'), D('10')
cash = total-digital
change = tender-cash
assert cash == D('5') and change == D('5') and digital+tender-change == total
results.append({'id': 'AUTO-M04', 'case': 'Mixto con QR de aporte y vuelto',
                'total': str(total), 'qr': str(digital), 'efectivo_entregado': str(tender),
                'efectivo_aplicado': str(cash), 'vuelto': str(change)})

# Una devolución pendiente ya compromete saldo aunque no haya respuesta externa.
paid, executed, unknown, next_request = map(D, ('10', '0', '7', '7'))
naive = next_request <= paid-executed
correct = next_request <= paid-executed-unknown
assert naive and not correct
results.append({'id': 'AUTO-M05', 'case': 'Excluir reintegro incierto permite comprometer14 sobre10',
                'naive_accepts': naive, 'with_reservation_accepts': correct})

output = {'status': 'PROBADO: cinco modelos aislados, no banco ni producto',
          'network': False, 'database': False, 'django': False, 'results': results}
Path(__file__).with_name('contraejemplos.json').write_text(
    json.dumps(output, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
print('5 contraejemplos/modelos verificados; ninguna operación bancaria o de producto.')
