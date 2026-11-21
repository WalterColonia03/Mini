import base64,json,os,sys,time
from pathlib import Path
from datetime import datetime,timezone
here=Path(__file__).resolve().parent
sys.path.insert(0,os.environ["MM_PLAYWRIGHT"])
from playwright.sync_api import sync_playwright
base="https://minimarket-academico-auditoria02.vercel.app"
auth=json.loads((Path(os.environ["MMSTAGE"])/"fixtures.json").read_text())
out=here/("lector-"+str(time.time_ns())+".json")
r={"inicio":datetime.now(timezone.utc).isoformat(),"controles":{}}
def save():
    out.write_text(json.dumps(r,indent=2,ensure_ascii=False),encoding="utf8")
def check(k,v):
    r["controles"][k]=v
    save()
    assert v,k
with sync_playwright() as pw:
    browser=pw.chromium.launch(executable_path=r"C:\Program Files\Google\Chrome\Application\chrome.exe",headless=False,args=["--start-maximized"])
    page=browser.new_context(no_viewport=True,locale="es-PE").new_page()
    page.goto(base)
    page.locator("[name=email]").fill(auth["ADMIN"][0])
    page.locator("[name=password]").fill(auth["ADMIN"][1])
    page.get_by_role("button",name="Iniciar sesión").click()
    page.wait_for_url("**/inicio/")
    page.goto(base+"/productos/nuevo/")
    page.locator("[name=barcode_type]").select_option("INTERNAL")
    page.locator("#barcode-capture-open").click()
    svg=(here.parent.parent/"soporte/audit03k_code128.svg").read_bytes()
    page.locator("dialog").evaluate("""(d, data) => {let i=document.createElement('img');i.src=data;i.alt='Etiqueta física de ensayo';i.style.cssText='display:block;width:300px;max-width:95%;background:white';d.prepend(i);}""","data:image/svg+xml;base64,"+base64.b64encode(svg).decode())
    page.locator("#barcode-capture-input").focus()
    page.bring_to_front()
    r["listo"]=True;save()
    count=[]
    page.on("request",lambda req: count.append(1) if req.method=="POST" else None)
    page.wait_for_function("document.querySelector('#barcode-capture-input').value === '00CAT03K'",timeout=900000)
    page.wait_for_function("!document.querySelector('#barcode-capture-apply').disabled",timeout=20000)
    check("lectura exacta y sin envio",not count and page.locator("#id_barcode").input_value()=="")
    page.locator("#barcode-capture-apply").click()
    check("copia conserva ceros sin envio",page.locator("#id_barcode").input_value()=="00CAT03K" and not count)
    page.locator("[name=name]").fill("Lectura física 03 "+str(time.time_ns()))
    page.locator("[name=category]").select_option(index=1)
    page.locator("[name=sale_price]").fill("5.00")
    page.locator("main form button[type=submit]").click()
    page.wait_for_url("**/registrado/")
    check("alta explícita",len(count)==1 and "00CAT03K" in page.inner_text("main"))
    page.goto(base+"/productos/nuevo/")
    page.locator("[name=barcode_type]").select_option("INTERNAL")
    page.locator("#barcode-capture-open").click()
    page.locator("#barcode-capture-input").fill("00CAT03K")
    page.wait_for_function("document.querySelector('#barcode-capture-status').textContent.includes('ya está registrado')")
    check("duplicado simulado tras alta",page.locator("#barcode-capture-apply").is_disabled())
    r["fin"]=datetime.now(timezone.utc).isoformat();save()
    browser.close()
