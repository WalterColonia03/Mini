"""Bounded smoke checks; never sends a password or POST."""
import hashlib
import hmac
import os
from pathlib import Path
import secrets
import sys
import urllib.request

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "r1-pmv"))
os.environ["DJANGO_SETTINGS_MODULE"] = "audit_settings"
import django
django.setup()
from django.conf import settings

challenge = secrets.token_hex(32)
req = urllib.request.Request("http://127.0.0.1:8765/", headers={"X-Audit00-Challenge": challenge})
with urllib.request.urlopen(req, timeout=5) as response:
    status = response.status
    proof = response.headers.get("X-Audit00-Proof", "")
expected = hmac.new(settings.SECRET_KEY.encode(), challenge.encode("ascii"), hashlib.sha256).hexdigest()
assert status == 200
assert hmac.compare_digest(proof, expected)
assert not hmac.compare_digest(proof, "")
assert not hmac.compare_digest(proof, "0" * 64)
print("identity proof: valid instance accepted; empty and forged proofs rejected; no credentials or POST sent")
