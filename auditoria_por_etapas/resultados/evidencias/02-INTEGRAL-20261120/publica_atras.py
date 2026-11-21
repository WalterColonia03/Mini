import json, os, sys
from pathlib import Path
stage=Path(os.environ["MMSTAGE"]); sys.path.insert(0,os.environ["MM_PLAYWRIGHT"])
from playwright.sync_api import sync_playwright
base="https://minimarket-academico-auditoria02.vercel.app"
creds=json.loads((stage/"fixtures.json").read_text())
with sync_playwright() as pw:
    br=pw.chromium.launch(executable_path=r"C:\Program Files\Google\Chrome\Application\chrome.exe",ignore_default_args=["--disable-back-forward-cache"])
    for role in ("ADMIN","VENDEDOR","ALMACENERO"):
        p=br.new_page(); p.goto(base); email,password=creds[role]
        p.locator("[name=email]").fill(email); p.locator("[name=password]").fill(password)
        p.get_by_role("button",name="Iniciar sesión").click();p.wait_for_url("**/inicio/")
        if role=="VENDEDOR":
            p.goto(base+"/caja/abrir/")
            assert "Ya abriste" in p.inner_text("main")
            print("VENDEDOR recupera turno propio tras ingreso",flush=True)
        p.goto(base+"/salir/")
        if role!="VENDEDOR": assert "Tu cuenta no opera turnos de caja." in p.inner_text("main")
        p.get_by_role("button",name="Cerrar sesión").click();p.wait_for_url(base+"/")
        p.go_back();p.wait_for_load_state("networkidle")
        assert p.locator("[name=password]").is_visible()
        assert email not in p.inner_text("body")
        print(role,"Atrás devuelve ingreso",flush=True)
        p.close()
    br.close()
