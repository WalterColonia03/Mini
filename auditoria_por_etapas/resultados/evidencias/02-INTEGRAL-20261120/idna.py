"""Count IDNA domain equivalences without exporting identities or changing accounts."""
import collections
import hashlib
import json
import sqlite3
import sys
from pathlib import Path

def summarize(rows):
    groups = collections.Counter()
    invalid = changed = count = 0
    for (value,) in rows:
        count += 1
        local, sep, domain = value.strip().casefold().rpartition("@")
        try:
            if not sep:
                raise ValueError()
            ascii_domain = domain.encode("idna").decode("ascii")
        except (ValueError, UnicodeError):
            invalid += 1
            continue
        changed += domain != ascii_domain
        groups[local, ascii_domain] += 1
    return dict(accounts=count, domain_changes=changed, invalid=invalid,
                collision_groups=sum(n > 1 for n in groups.values()))

if __name__ == "__main__":
    assert summarize([("a@bücher.example",), ("a@xn--bcher-kva.example",)])["collision_groups"] == 1
    path = Path(sys.argv[1]).resolve()
    before = hashlib.file_digest(path.open("rb"), "sha256").hexdigest()
    with sqlite3.connect(path.as_uri()+"?mode=ro", uri=True) as db:
        db.execute("PRAGMA query_only=ON")
        result = summarize(db.execute("SELECT email_normalized FROM identity_account"))
    result["sha256_before_after_equal"] = before == hashlib.file_digest(path.open("rb"), "sha256").hexdigest()
    print(json.dumps(result))
