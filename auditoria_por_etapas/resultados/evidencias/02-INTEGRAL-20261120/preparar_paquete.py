"""Materialize the 150 public build inputs in a new directory and verify their hashes."""
from pathlib import Path
import hashlib
import json
import sys

here = Path(__file__).resolve().parent
root = next(p for p in here.parents if (p/"r1-pmv/manage.py").is_file())
dest = Path(sys.argv[1]).resolve()
dest.mkdir(parents=True, exist_ok=False)
for relative, expected in json.loads((here/"paquete-entrega.json").read_text()).items():
    target = (dest / relative).resolve()
    assert target.is_relative_to(dest)
    if relative == "vercel.json":
        data = json.dumps({"framework":"django"}).encode()
    elif relative == ".python-version":
        data = b"3.12\r\n"
        if hashlib.sha256(data).hexdigest() != expected: data = b"3.12\n"
    else:
        data = (root/"r1-pmv"/relative).read_bytes()
    assert hashlib.sha256(data).hexdigest() == expected, relative
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_bytes(data)
print("150 entradas de despliegue verificadas")
