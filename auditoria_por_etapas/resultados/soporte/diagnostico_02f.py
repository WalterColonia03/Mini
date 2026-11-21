"""Snapshot pre-02-F + diagnóstico de límites, Unicode e IDNA (solo lectura / BD aislada)."""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import sqlite3
import sys
import tempfile
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "r1-pmv/manage.py").is_file())
PROJECT = ROOT / "r1-pmv"
RESULTS = ROOT / "auditoria_por_etapas/resultados"
EV_DIR = RESULTS / "evidencias/02-F-20261114"
EV_DIR.mkdir(parents=True, exist_ok=True)
SKIP_DIRS = {".venv", "__pycache__", ".pytest_cache", "node_modules", ".git"}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def collect_r1_manifest() -> dict:
    entries: list[dict] = []
    for dirpath, dirnames, filenames in os.walk(PROJECT):
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS)
        rel_dir = Path(dirpath).relative_to(PROJECT)
        for fname in sorted(filenames):
            fpath = Path(dirpath) / fname
            rel = (rel_dir / fname).as_posix()
            entries.append(
                {
                    "path": rel,
                    "size": fpath.stat().st_size,
                    "sha256": sha256_file(fpath),
                }
            )
    entries.sort(key=lambda item: item["path"])
    combined = hashlib.sha256(
        "\n".join(f"{e['path']}:{e['sha256']}" for e in entries).encode("utf-8")
    ).hexdigest()
    return {
        "captured_utc": datetime.now(timezone.utc).isoformat(),
        "file_count": len(entries),
        "r1_build_sha256": combined,
        "prod_db_sha256": sha256_file(PROJECT / "r1_pmv.sqlite3"),
        "files": entries,
    }


def save_snapshots() -> tuple[str, dict]:
    prod_db = PROJECT / "r1_pmv.sqlite3"
    db_hash = sha256_file(prod_db)
    manifest = collect_r1_manifest()
    (EV_DIR / "build-antes.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    for src, dst in [
        (ROOT / "08_Historias_de_Usuario.md", EV_DIR / "08-antes.md"),
        (RESULTS / "ESTADO_GENERAL.md", EV_DIR / "antes-ESTADO_GENERAL.md"),
        (RESULTS / "ETAPA-02.md", EV_DIR / "antes-ETAPA-02.md"),
    ]:
        if src.is_file() and not dst.exists():
            shutil.copy2(src, dst)
    return db_hash, manifest


def inspect_readonly_sqlite(prod_db: Path) -> dict:
    uri = prod_db.resolve().as_uri() + "?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            """
            SELECT a.id, a.email, a.email_normalized, a.display_name,
                   r.code AS role_code, a.is_active, a.is_staff, a.is_superuser
            FROM identity_account a
            JOIN identity_role r ON r.id = a.role_id
            ORDER BY a.email_normalized, a.id
            """
        ).fetchall()
        attempts = conn.execute(
            "SELECT COUNT(*) AS total, SUM(CASE WHEN locked_until IS NOT NULL THEN 1 ELSE 0 END) AS with_lockout FROM identity_loginattempt"
        ).fetchone()
    finally:
        conn.close()

    accounts = []
    norm_groups: dict[str, list[str]] = {}
    idna_groups: dict[str, list[str]] = {}
    for row in rows:
        email = row["email"]
        local, _, domain = email.partition("@")
        try:
            domain_idna = domain.strip().encode("idna").decode("ascii").lower()
        except Exception as exc:
            domain_idna = f"ERR:{exc}"
        idna_canon = f"{local.strip().casefold()}@{domain_idna}"
        nfkc_canon = f"{unicodedata.normalize('NFKC', local).strip().casefold()}@{domain_idna}"
        norm_groups.setdefault(row["email_normalized"], []).append(email)
        idna_groups.setdefault(idna_canon, []).append(email)
        accounts.append(
            {
                "id": row["id"],
                "email": email,
                "email_normalized": row["email_normalized"],
                "display_name": row["display_name"],
                "role_code": row["role_code"],
                "is_active": bool(row["is_active"]),
                "is_staff": bool(row["is_staff"]),
                "is_superuser": bool(row["is_superuser"]),
                "non_ascii_email": any(ord(ch) > 127 for ch in email),
                "idna_canonical": idna_canon,
                "nfkc_canonical": nfkc_canon,
            }
        )
    return {
        "account_count": len(accounts),
        "accounts": accounts,
        "login_attempts_total": attempts["total"],
        "login_attempts_with_lockout": attempts["with_lockout"] or 0,
        "non_ascii_accounts": [a for a in accounts if a["non_ascii_email"]],
        "idna_collisions": {k: v for k, v in idna_groups.items() if len(v) > 1},
        "normalized_collisions": {k: v for k, v in norm_groups.items() if len(v) > 1},
    }


def run_isolated_layer_probes() -> dict:
    with tempfile.TemporaryDirectory(prefix="diag02f-") as tmp:
        db_path = Path(tmp) / "isolated.sqlite3"
        sys.path.insert(0, str(PROJECT))
        os.environ.update(
            APP_ENV="test",
            DJANGO_DEBUG="false",
            DJANGO_SECRET_KEY="diag02f-secret-key-only-for-isolated-probes",
            DJANGO_SETTINGS_MODULE="config.settings",
        )
        from config import env as config_env

        config_env.load_dotenv = lambda path=None: None
        from django.conf import settings

        settings.DATABASES = {
            "default": {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": str(db_path),
            }
        }
        import django

        django.setup()
        from django.core.exceptions import ValidationError
        from django.core.management import call_command
        from django.db import IntegrityError, connections
        from django.test import Client

        try:
            return _run_isolated_probes_inner(
                Account=None,
                ValidationError=ValidationError,
                IntegrityError=IntegrityError,
                call_command=call_command,
                Client=Client,
            )
        finally:
            connections.close_all()


def _run_isolated_probes_inner(*, Account, ValidationError, IntegrityError, call_command, Client) -> dict:
    if True:

        call_command("migrate", verbosity=0)

        from identity.forms import EmployeeCreationForm, EmployeeEditForm, LoginForm
        from identity.models import Account, Role
        from identity.services import (
            authenticate_active_account,
            create_employee,
            update_employee,
        )

        admin_role, _ = Role.objects.get_or_create(
            code=Role.Code.ADMIN, defaults={"name": "Administrador"}
        )
        seller_role, _ = Role.objects.get_or_create(
            code=Role.Code.SELLER, defaults={"name": "Vendedor"}
        )
        warehouse_role, _ = Role.objects.get_or_create(
            code=Role.Code.WAREHOUSE, defaults={"name": "Almacenero"}
        )
        admin = Account.objects.create_user(
            "admin.diag02f@minimarket.local",
            "Admin1234",
            display_name="Admin Diag",
            role=admin_role,
        )

        # 1. IDNA / Unicode / NFKC / Whitespace matrix across normalize_email + Forms + Model + Services + Search
        matrix = []
        test_emails = [
            ("ascii_upper", "Ana.Lopez@Minimarket.Local"),
            ("unicode_domain", "usuaria@mañana.invalid"),
            ("punycode_domain", "usuaria@xn--maana-pta.invalid"),
            ("unicode_domain_upper", "USUARIA@MAÑANA.INVALID"),
            ("unicode_domain_nfd", "usuaria@man\u0303ana.invalid"),
            ("fullwidth_local_domain", "\uff55suaria@ma\u00f1ana.invalid"),
            ("accents_local", "josé.perez@minimarket.local"),
            ("german_sharp_s", "straße@minimarket.local"),
            ("internal_tab", "ana\tlopez@minimarket.local"),
            ("leading_trailing_nbsp", "\xa0ana.nbsp@minimarket.local\xa0"),
            ("zero_width_space", "ana\u200blopez@minimarket.local"),
            ("domain_254_ascii", f"{'a' * 239}@minimarket.com"),
            ("domain_255_ascii", f"{'a' * 240}@minimarket.com"),
            ("local_65_ascii", f"{'b' * 65}@t.co"),
            ("unicode_under_254_puny_over", "u@" + (("ñ" * 58) + ".") * 3 + "invalid"),
        ]
        for label, raw_email in test_emails:
            login_form = LoginForm(data={"email": raw_email, "password": "Password123"})
            create_form = EmployeeCreationForm(
                data={
                    "display_name": "Empleado Probe",
                    "email": raw_email,
                    "role": str(seller_role.pk),
                    "password": "Password123",
                }
            )
            edit_form = EmployeeEditForm(
                data={
                    "display_name": "Empleado Probe",
                    "email": raw_email,
                    "role": str(seller_role.pk),
                    "new_password": "",
                }
            )
            local, sep, domain = raw_email.strip().partition("@")
            try:
                domain_idna = domain.encode("idna").decode("ascii").lower() if sep else ""
            except Exception as exc:
                domain_idna = f"ERR:{type(exc).__name__}"
            model_acc = Account(
                display_name="Model Probe",
                email=raw_email,
                email_normalized=Account.normalize_email(raw_email),
                role=seller_role,
            )
            model_acc.set_password("Password123")
            try:
                model_acc.full_clean()
                model_valid = True
                model_err = None
            except ValidationError as exc:
                model_valid = False
                model_err = {k: list(v) for k, v in exc.message_dict.items()}
            matrix.append(
                {
                    "label": label,
                    "len_raw": len(raw_email),
                    "non_ascii": any(ord(c) > 127 for c in raw_email),
                    "normalize_email": Account.normalize_email(raw_email),
                    "idna_domain": domain_idna,
                    "len_idna_equivalent": len(f"{local}@{domain_idna}") if sep else len(raw_email),
                    "login_form_valid": login_form.is_valid(),
                    "login_form_errors": {k: list(v) for k, v in login_form.errors.items()},
                    "create_form_valid": create_form.is_valid(),
                    "create_form_errors": {k: list(v) for k, v in create_form.errors.items()},
                    "edit_form_valid": edit_form.is_valid(),
                    "model_valid": model_valid,
                    "model_errors": model_err,
                }
            )

        # 2. Collision & Login equivalence probe: unicode domain vs punycode domain vs NFD vs ß
        u_uni = create_employee(
            actor=admin,
            display_name="Usuaria Mañana NFC",
            email="usuaria@mañana.invalid",
            password="Password123",
            role=seller_role,
        )
        puny_res = {"created": False, "error": None}
        try:
            u_puny = create_employee(
                actor=admin,
                display_name="Usuaria Punycode",
                email="usuaria@xn--maana-pta.invalid",
                password="Password123",
                role=warehouse_role,
            )
            puny_res = {
                "created": True,
                "id": u_puny.pk,
                "email_normalized": u_puny.email_normalized,
            }
        except ValidationError as exc:
            puny_res = {"created": False, "error": exc.message_dict}

        nfd_res = {"created": False, "error": None}
        try:
            u_nfd = create_employee(
                actor=admin,
                display_name="Usuaria NFD",
                email="usuaria@man\u0303ana.invalid",
                password="Password123",
                role=warehouse_role,
            )
            nfd_res = {
                "created": True,
                "id": str(u_nfd.pk),
                "email_normalized": u_nfd.email_normalized,
            }
        except ValidationError as exc:
            nfd_res = {"created": False, "error": exc.message_dict}

        # Login with punycode against unicode account and vice-versa:
        auth_uni_by_uni = authenticate_active_account("usuaria@mañana.invalid", "Password123")
        auth_uni_by_puny = authenticate_active_account("usuaria@xn--maana-pta.invalid", "Password123")
        auth_uni_by_upper = authenticate_active_account("USUARIA@MAÑANA.INVALID", "Password123")

        # Sharp s casefold probe (local part and domain)
        sharp_domain_res = {"created": False}
        sharp_dup = {"created": False}
        auth_sharp_domain_pk = None
        try:
            u_sharp = create_employee(
                actor=admin,
                display_name="Ana Sharp Domain",
                email="ana@straße.invalid",
                password="Password123",
                role=seller_role,
            )
            sharp_domain_res = {
                "created": True,
                "id": str(u_sharp.pk),
                "email_normalized": u_sharp.email_normalized,
            }
            try:
                u_ss = create_employee(
                    actor=admin,
                    display_name="Ana Strasse Dos",
                    email="ANA@STRASSE.INVALID",
                    password="Password123",
                    role=seller_role,
                )
                sharp_dup = {"created": True, "id": str(u_ss.pk), "email_normalized": u_ss.email_normalized}
            except ValidationError as exc:
                sharp_dup = {"created": False, "error": exc.message_dict}
            auth_sharp_by_upper = authenticate_active_account("ANA@STRASSE.INVALID", "Password123")
            auth_sharp_domain_pk = str(auth_sharp_by_upper.account.pk) if auth_sharp_by_upper.account else None
        except ValidationError as exc:
            sharp_domain_res = {"created": False, "error": exc.message_dict}

        # 3. Display name boundaries & invisible chars & search `q`
        name_probes = []
        for label, dname in [
            ("name_120", "N" * 120),
            ("name_120_padded", "  " + ("N" * 120) + "  "),
            ("name_121", "N" * 121),
            ("name_only_spaces", "   "),
            ("name_nbsp", "\xa0\xa0"),
            ("name_zero_width", "\u200b"),
            ("name_emoji", "Cajera 🌟 Turno"),
            ("name_accents_nfd", "Jose\u0301 Ma\u0301rquez"),
        ]:
            f = EmployeeCreationForm(
                data={
                    "display_name": dname,
                    "email": f"nameprobe_{label}@minimarket.local",
                    "role": str(seller_role.pk),
                    "password": "Password123",
                }
            )
            svc_res = None
            try:
                acc_probe = create_employee(
                    actor=admin,
                    display_name=dname,
                    email=f"svc_{label}@minimarket.local",
                    password="Password123",
                    role=seller_role,
                )
                svc_res = {"ok": True, "stored": repr(acc_probe.display_name), "len": len(acc_probe.display_name)}
            except ValidationError as exc:
                svc_res = {"ok": False, "errors": exc.message_dict}
            name_probes.append(
                {
                    "label": label,
                    "form_valid": f.is_valid(),
                    "form_errors": {k: list(v) for k, v in f.errors.items()},
                    "cleaned_name": repr(f.cleaned_data.get("display_name")) if f.is_valid() else None,
                    "service_result": svc_res,
                }
            )

        # Search `?q=` behavior in employee_list view
        client = Client()
        client.force_login(admin)
        session = client.session
        session["role_code"] = Role.Code.ADMIN
        session.save()

        search_probes = []
        for q in [
            "",
            "   ",
            "mañana",
            "xn--maana-pta",
            "MAÑANA",
            "man\u0303ana",
            "STRASSE",
            "%",
            "_",
            "\\",
            "a" * 500,
            "<script>alert(1)</script>",
        ]:
            resp = client.get("/empleados/", {"q": q})
            body = resp.content.decode("utf-8", errors="replace")
            search_probes.append(
                {
                    "q_repr": repr(q[:80]) + ("..." if len(q) > 80 else ""),
                    "q_len": len(q),
                    "status": resp.status_code,
                    "matched_emails": [
                        a["email"]
                        for a in [
                            {"email": u_uni.email},
                            {"email": "usuaria@xn--maana-pta.invalid"},
                            {"email": "usuaria@man\u0303ana.invalid"},
                            {"email": "ana@straße.invalid"},
                            {"email": "ANA@STRASSE.INVALID"},
                        ]
                        if a["email"] in body
                    ],
                }
            )

        return {
            "matrix": matrix,
            "collision_unicode_vs_punycode": {
                "unicode_account": {"id": str(u_uni.pk), "email_normalized": u_uni.email_normalized},
                "punycode_create": puny_res,
                "nfd_create": nfd_res,
                "auth_unicode_with_unicode": auth_uni_by_uni.authenticated,
                "auth_unicode_with_punycode": str(auth_uni_by_puny.account.pk) if auth_uni_by_puny.account else None,
                "auth_unicode_with_upper": str(auth_uni_by_upper.account.pk) if auth_uni_by_upper.account else None,
            },
            "collision_sharp_s_casefold": {
                "sharp_s_domain_create": sharp_domain_res,
                "strasse_create": sharp_dup,
                "auth_sharp_by_upper_strasse": auth_sharp_domain_pk,
            },
            "display_name_probes": name_probes,
            "employee_list_search_probes": search_probes,
        }


def main() -> None:
    db_before, manifest = save_snapshots()
    ro_data = inspect_readonly_sqlite(PROJECT / "r1_pmv.sqlite3")
    layer_probes = run_isolated_layer_probes()
    db_after = sha256_file(PROJECT / "r1_pmv.sqlite3")
    report = {
        "captured_utc": datetime.now(timezone.utc).isoformat(),
        "r1_build_sha256_before": manifest["r1_build_sha256"],
        "file_count": manifest["file_count"],
        "prod_db_sha256_before": db_before,
        "prod_db_sha256_after": db_after,
        "prod_db_unchanged": db_before == db_after,
        "readonly_sqlite_inspection": ro_data,
        "isolated_layer_probes": layer_probes,
    }
    (EV_DIR / "diagnostico-antes.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False, default=str), encoding="utf-8"
    )
    print(json.dumps({k: report[k] for k in ("r1_build_sha256_before", "file_count", "prod_db_unchanged")}, indent=2))
    print("readonly accounts:", ro_data["account_count"], "non_ascii:", len(ro_data["non_ascii_accounts"]), "idna_collisions:", ro_data["idna_collisions"])
    print("unicode vs punycode:", json.dumps(layer_probes["collision_unicode_vs_punycode"], ensure_ascii=False, default=str))
    print("sharp_s:", json.dumps(layer_probes["collision_sharp_s_casefold"], ensure_ascii=False, default=str))
    print("zero_width / space display_names:", json.dumps([p for p in layer_probes["display_name_probes"] if p["label"] in {"name_only_spaces", "name_nbsp", "name_zero_width", "name_120_padded", "name_121"}], ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
