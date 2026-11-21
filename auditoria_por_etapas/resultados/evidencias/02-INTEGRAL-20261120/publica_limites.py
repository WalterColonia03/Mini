import json, os, secrets, sys
from pathlib import Path
stage=Path(os.environ["MMSTAGE"])
sys.path.insert(0,os.environ["MM_PLAYWRIGHT"])
from playwright.sync_api import sync_playwright
base="https://minimarket-academico-auditoria02.vercel.app"
creds=json.loads((stage/"fixtures.json").read_text())
def ok(case, condition):
    print(case, bool(condition),flush=True)
    assert condition, case
with sync_playwright() as pw:
    br=pw.chromium.launch(executable_path=r"C:\Program Files\Google\Chrome\Application\chrome.exe")
    p=br.new_page(viewport={"width":390,"height":844})
    def login(page, email, password):
        page.goto(base)
        page.locator("[name=email]").fill(email)
        page.locator("[name=password]").fill(password)
        page.get_by_role("button",name="Iniciar sesión").click()
    login(p,*creds["ADMIN"]); p.wait_for_url("**/inicio/")
    email="empleado-"+secrets.token_hex(4)+"@prueba.invalid"; password=secrets.token_urlsafe(24)+"Aa9"
    p.goto(base+"/empleados/"); p.get_by_text("+ Nuevo empleado",exact=True).click()
    def form(name, mail, pwd):
        p.locator("[name=display_name]").fill(name)
        p.locator("[name=email]").fill(mail)
        p.locator("[name=password]").fill(pwd)
        p.locator("select[name=role]").select_option(label="Almacenero")
        p.get_by_role("button",name="Crear empleado").click()
    form("Ana Ensayo",email,"abc")
    ok("alta rechaza clave insuficiente","La contraseña debe tener al menos 7 caracteres" in p.inner_text("main"))
    form("Ana Ensayo",email,password)
    ok("alta confirma nombre","Empleado «Ana Ensayo» creado correctamente." in p.inner_text("main"))
    p.get_by_text("+ Nuevo empleado",exact=True).click()
    form("Otra persona",email.upper(),password)
    ok("duplicado normalizado","El correo ya está registrado." in p.inner_text("main"))
    p.goto(base+"/empleados/"); p.locator("[name=q]").fill(email); p.get_by_role("button",name="Buscar").click()
    ok("busqueda una coincidencia",p.locator("tbody tr").count()==1)
    p.get_by_text("Editar",exact=True).click()
    p.locator("[name=display_name]").fill("Ana Editada")
    p.get_by_role("button",name="Guardar cambios").click()
    ok("edicion confirmada","Empleado «Ana Editada» actualizado." in p.inner_text("main"))
    def row(): return p.locator("tr").filter(has_text=email)
    row().get_by_text("Desactivar").click()
    ok("resumen movil sin desbordamiento", p.evaluate("document.documentElement.scrollWidth <= innerWidth"))
    p.get_by_text("Cancelar",exact=True).click()
    ok("cancelar deja activa","Activo" in row().inner_text())
    row().get_by_text("Desactivar").click()
    p.get_by_role("button",name="Confirmar desactivación").click()
    ok("estado inactivo en lista","Inactivo" in row().inner_text())
    other=br.new_page(); login(other,email,password)
    ok("ingreso inactivo con mensaje general","Correo o contraseña incorrectos" in other.inner_text("main"))
    row().get_by_text("Reactivar").click(); p.get_by_role("button",name="Confirmar reactivación").click()
    login(other,email,password); other.wait_for_url("**/inicio/")
    ok("reingreso con rol conservado","Almacenero" in other.inner_text("body"))
    p.goto(base+"/empleados/?q=ningunresultado12345")
    ok("promesa de busqueda vacia","No se encontraron empleados para el criterio ingresado." in p.inner_text("main"))
    from uuid import uuid4
    def email_at(n):
        domain="@example.invalid"
        return uuid4().hex.ljust(n-len(domain),"a")+domain
    valid=email_at(254)
    p.goto(base+"/empleados/nuevo/")
    for editing in (False,True):
        # Exercise the server's field limits with a test browser beyond native maxlength.
        for field in ("email","display_name"):
            p.locator(f"[name={field}]").evaluate("(el)=>el.removeAttribute('maxlength')")
        p.locator("[name=display_name]").fill("A"*121)
        p.locator("[name=email]").fill(email_at(255))
        if not editing:
            p.locator("[name=password]").fill(password)
            p.locator("[name=role]").select_option(label="Almacenero")
        p.locator("main form button[type=submit]").click()
        for upper in (120,254):
            msg=f"Asegúrese de que este valor tenga como máximo {upper} caracteres (tiene {upper+1})."
            ok(f"{editing=} limite {upper} literal exacto",msg in p.inner_text("main"))
        p.locator("[name=display_name]").fill(("B" if editing else "A")*120)
        p.locator("[name=email]").fill(valid)
        if not editing: p.locator("[name=password]").fill(password)
        p.locator("main form button[type=submit]").click()
        p.wait_for_url("**/empleados/")
        target=p.locator("tr").filter(has_text=valid)
        ok(f"{editing=} acepta 120/254",target.count()==1)
        if not editing:target.get_by_text("Editar").click()
    br.close()

