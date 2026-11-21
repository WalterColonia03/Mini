"""Fault injection only into audit04 marked isolated DB; emits no credentials/session keys."""
import json
import sys
from audit04_run import setup
setup()
from identity.models import Account, Role
from identity.services import deactivate_employee, reactivate_employee
from django.contrib.sessions.models import Session
target = Account.objects.get(email="admin@audit04.invalid")
action = sys.argv[1]
if action in ("service_off", "service_on"):
    operator, _ = Account.objects.get_or_create(email="operator@audit04.invalid", defaults={
        "email_normalized": "operator@audit04.invalid", "display_name": "Operador aislado",
        "role": Role.objects.get(code=Role.Code.ADMIN), "is_active": True})
    (deactivate_employee if action == "service_off" else reactivate_employee)(actor=operator, account=target)
elif action in ("raw_off", "raw_on"):
    Account.objects.filter(pk=target.pk).update(is_active=action == "raw_on")
elif action != "status":
    raise ValueError("Unsupported action")
target.refresh_from_db()
count = sum(str(s.get_decoded().get("_auth_user_id")) == str(target.pk) for s in Session.objects.all())
print(json.dumps({"active": target.is_active, "account_sessions": count}))
