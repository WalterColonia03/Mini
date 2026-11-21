const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const crypto = require('node:crypto');
const assert = require('node:assert/strict');
const {execFileSync} = require('node:child_process');
const {chromium} = require(path.join(os.homedir(),'.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright-core'));
const out=process.env.AUDIT03_OUT, run=process.env.AUDIT03_RUN_DIR;
const base='http://127.0.0.1:'+process.env.AUDIT03_PORT;
const accounts=JSON.parse(fs.readFileSync(path.join(run,'.credentials.json')));
const fixture=JSON.parse(fs.readFileSync(path.join(out,'fixture.json')));
const report={checks:[], input:'Chrome automated forms; explicit unit counts; no physical scans'};
function check(id,actual,expected) {
  assert.deepEqual(actual,expected,id);
  report.checks.push(id);
}
function state() {
  return JSON.parse(execFileSync(process.env.AUDIT03_PYTHON,[path.join(__dirname,'audit03y_browser_run.py'),'snapshot'],{encoding:'utf8'}));
}
const button=(page,name)=>page.getByRole('button',{name,exact:true});
async function login(browser,alias) {
  const p=await browser.newPage({locale:'es-PE',viewport:{width:1366,height:900}});
  await p.goto(base);
  await p.locator('[name=email]').fill(accounts[alias].email);
  await p.locator('[name=password]').fill(accounts[alias].password);
  await p.locator('button[type=submit]').click();
  return p;
}
async function menu(page,testid) {
  await page.goto(base+'/');
  await page.getByTestId(testid).click();
}
async function fill(page,product,lots) {
  await page.locator('[name=product]').selectOption(product.id);
  await page.locator('[name=supplier]').selectOption(fixture.supplier_id);
  for (const [index,lot] of lots.entries()) {
    for (const [field,value] of Object.entries(lot)) await page.locator('[name="lots-'+index+'-'+field+'"]').fill(String(value));
  }
}
const lot=(number,quantity,unit_cost,date=fixture.future)=>({number,quantity,unit_cost,expiration_date:date});
async function payload(page) {
  return page.locator('form[data-testid]').evaluate(form=>Object.fromEntries(new FormData(form)));
}


function actor(action='aj-actor'){return JSON.parse(execFileSync(process.env.AUDIT03_PYTHON,[path.join(__dirname,'audit03y_browser_run.py'),action],{encoding:'utf8'}));}
async function authenticate(p,alias='warehouse'){await p.locator('[name=email]').fill(accounts[alias].email);await p.locator('[name=password]').fill(accounts[alias].password);await p.locator('button[type=submit]').click();}
async function logoutViaUi(p){await p.goto(base+'/salir/');await button(p,'Cerrar sesión').click();await p.waitForSelector('[name=email]');}
async function test(browser){
 const probe=await browser.newPage(),nonce=crypto.randomBytes(32).toString('hex');
 const res=await probe.request.get(base,{headers:{'X-Audit03-Challenge':nonce}});
 check('aislamiento',res.headers()['x-audit03-proof'],crypto.createHmac('sha256',fs.readFileSync(path.join(run,'.django-key'))).update(nonce).digest('hex'));await probe.close();
 const wh=await login(browser,'warehouse'),admin=await login(browser,'admin'),product=fixture.products[0];
 await menu(wh,'inventory-load-link');await fill(wh,product,[lot('AJ-BASE',10,'2.0000')]);
 await button(wh,'Confirmar existencias').click();await wh.waitForURL(/\/inventario\/cargas\//);const canonical=wh.url();
 const initial=state();report.states={initial};

 // 1. Session expired in DB while /inventario/entrada/ form is open.
 const entryGetRespPromise=wh.waitForResponse(r=>r.request().method()==='GET'&&r.url()===base+'/inventario/entrada/');
 await menu(wh,'stock-entry-link');
 const entryGetResp=await entryGetRespPromise;
 check('entrada no cacheable',entryGetResp.headers()['cache-control'].includes('no-store'),true);
 await fill(wh,product,[lot('AJ-R1',2,'5.0000')]);
 const oldPayload=await payload(wh);check('una sesion expirada',actor('aj-expire').sessions_expired,1);
 const expiredResponse=wh.waitForResponse(r=>r.request().method()==='POST'&&r.url()===base+'/inventario/entrada/');
 await button(wh,'Confirmar entrada').click();
 check('sesion expirada redirige',(await expiredResponse).status(),302);
 check('ingreso visible',await wh.locator('[name=email]').count(),1);
 check('next conserva ruta',new URL(wh.url()).searchParams.get('next'),'/inventario/entrada/');
 check('sesion expirada no escribe',state(),initial);

 // 1b. Logging in on ?next=/inventario/entrada/ as ADMIN must land on 403 without writing.
 await authenticate(wh,'admin');await wh.waitForURL(base+'/inventario/entrada/');await wh.waitForSelector('[data-testid="permission-denied"]');
 check('next con rol admin denegado',(await wh.locator('main').innerText()).includes('No tienes permiso'),true);
 check('next rol admin sin escritura',state(),initial);
 await logoutViaUi(wh);
 await wh.goto(base+'/?next=/inventario/entrada/');
 await authenticate(wh,'warehouse');await wh.waitForURL(base+'/inventario/entrada/');
 check('login no reenvia operacion',state(),initial);
 check('producto no recuperado automaticamente',await wh.locator('[name=product]').inputValue(),'');
 check('lote no recuperado automaticamente',await wh.locator('[name="lots-0-number"]').inputValue(),'');
 await wh.screenshot({path:path.join(out,'01-retorno-formulario.png'),fullPage:true});
 const replay=await wh.request.post(base+'/inventario/entrada/',{form:oldPayload,maxRedirects:0});
 check('payload antiguo tras login rechazado CSRF',replay.status(),403);check('csrf viejo sin cambios',state(),initial);

 // 2. Menu recovery checks canonical load without creating extra lots.
 await wh.goto(base);await wh.getByRole('link',{name:'Ver inventario y alertas',exact:true}).first().click();
 const loadGetPromise=wh.waitForResponse(r=>r.request().method()==='GET'&&r.url()===canonical);
 await wh.getByRole('row').filter({hasText:product.barcode}).getByRole('link',{name:'Ver carga',exact:true}).click();
 const loadGetResp=await loadGetPromise;
 check('constancia carga no cacheable',loadGetResp.headers()['cache-control'].includes('no-store'),true);
 check('consulta carga previa',wh.url(),canonical);check('consulta no crea lote pendiente',state(),initial);

 // Confirm AJ-R1 once cleanly.
 await menu(wh,'stock-entry-link');await fill(wh,product,[lot('AJ-R1',2,'5.0000')]);await button(wh,'Confirmar entrada').click();await wh.waitForURL(/\/inventario\/cargas\//);
 const saved=state();report.states.saved=saved;
 check('una entrada tras reautenticar',saved.receipt_lots.length,2);check('stock12',saved.receipt_lots.reduce((n,l)=>n+l.available_quantity,0),12);
 check('costo2.5',saved.commerce.find(p=>p.id===product.id).average_cost,'2.5000');

 // 3. Controlled logout in second tab sharing cookies -> old form redirects 302 without writes.
 await menu(wh,'stock-entry-link');await fill(wh,product,[lot('AJ-R2',1,'8.0000')]);
 const whTabLogout=await wh.context().newPage({locale:'es-PE',viewport:{width:1366,height:900}});
 await logoutViaUi(whTabLogout);
 await whTabLogout.close();
 const loggedOutPost=wh.waitForResponse(r=>r.request().method()==='POST'&&r.url()===base+'/inventario/entrada/');
 await button(wh,'Confirmar entrada').click();
 check('salir en otra pestana redirige POST antiguo',(await loggedOutPost).status(),302);
 await wh.waitForSelector('[name=email]');
 check('salir otra pestana preserva next',new URL(wh.url()).searchParams.get('next'),'/inventario/entrada/');
 check('salir otra pestana sin cambios',state(),saved);
 await authenticate(wh,'warehouse');await wh.waitForURL(base+'/inventario/entrada/');

 // 4. Tab 2 re-login rotates session/CSRF -> Tab 1 stale CSRF POST rejected with 403.
 await fill(wh,product,[lot('AJ-R2',1,'8.0000')]);
 const whTabRelogin=await wh.context().newPage({locale:'es-PE',viewport:{width:1366,height:900}});
 await logoutViaUi(whTabRelogin);
 await authenticate(whTabRelogin,'warehouse');await whTabRelogin.waitForURL(base+'/inicio/');
 await whTabRelogin.close();
 const staleTabPost=wh.waitForResponse(r=>r.request().method()==='POST'&&r.url()===base+'/inventario/entrada/');
 await button(wh,'Confirmar entrada').click();
 check('tab1 tras relogin tab2 rechazado 403 CSRF',(await staleTabPost).status(),403);
 check('relogin tab2 sin escrituras',state(),saved);

 // 5. Admin changes warehouse role to VENDEDOR while old form is filled on Tab 1.
 await menu(wh,'stock-entry-link');await fill(wh,product,[lot('AJ-R2',1,'8.0000')]);
 await admin.goto(base);await admin.locator('a[href="/empleados/"]').first().click();
 const employee=()=>admin.getByRole('row').filter({hasText:accounts.warehouse.email});
 await employee().getByRole('link',{name:'Editar',exact:true}).click();
 const warehouseRole=await admin.locator('[name=role]').inputValue();
 const sellerOption=admin.locator('[name=role] option').filter({hasText:'Vendedor'});await admin.locator('[name=role]').selectOption(await sellerOption.getAttribute('value'));
 await button(admin,'Guardar cambios').click();await admin.waitForURL(base+'/empleados/');check('rol cambiado persistido',actor().role,'VENDEDOR');
 const whGetTab=await wh.context().newPage({locale:'es-PE',viewport:{width:1366,height:900}});
 const revokedGet=await whGetTab.goto(base+'/inventario/entrada/');
 check('get directo denegado tras cambio rol',revokedGet.status(),403);
 await whGetTab.close();
 const denied=wh.waitForResponse(r=>r.request().method()==='POST'&&r.url()===base+'/inventario/entrada/');await button(wh,'Confirmar entrada').click();
 check('viejo formulario denegado tras cambio rol',(await denied).status(),403);
 check('denegacion de permiso no csrf',(await wh.locator('main').innerText()).includes('No tienes permiso'),true);check('rol nuevo no escribe',state(),saved);
 await wh.screenshot({path:path.join(out,'02-rol-revocado.png'),fullPage:true});

 // Restore warehouse role.
 await employee().getByRole('link',{name:'Editar',exact:true}).click();await admin.locator('[name=role]').selectOption(warehouseRole);await button(admin,'Guardar cambios').click();await admin.waitForURL(base+'/empleados/');check('rol restaurado',actor().role,'ALMACENERO');

 // 6. Admin deactivates warehouse while /inventario/entrada/ is filled AND another tab viewed canonical load.
 await menu(wh,'stock-entry-link');await fill(wh,product,[lot('AJ-R2',1,'8.0000')]);
 const whBackTab=await wh.context().newPage({locale:'es-PE',viewport:{width:1366,height:900}});
 await whBackTab.goto(canonical);
 await whBackTab.goto(base+'/inicio/');
 await employee().getByRole('button',{name:'Desactivar',exact:true}).click();await admin.waitForURL(base+'/empleados/');check('cuenta desactivada',actor().active,false);
 await whBackTab.goBack();
 await whBackTab.waitForSelector('[name=email]');
 check('atras tras desactivar no expone constancia',new URL(whBackTab.url()).pathname,'/');
 await whBackTab.close();
 const inactive=wh.waitForResponse(r=>r.request().method()==='POST'&&r.url()===base+'/inventario/entrada/');await button(wh,'Confirmar entrada').click();
 check('cuenta inactiva redirige',(await inactive).status(),302);await wh.waitForSelector('[name=email]');check('desactivacion sin entrada',state(),saved);
 await authenticate(wh);check('ingreso inactivo rechazado',(await wh.locator('body').innerText()).includes('Correo o contraseña incorrectos'),true);check('login inactivo sin escritura',state(),saved);

 // Reactivate and complete clean confirmation.
 await employee().getByRole('button',{name:'Reactivar',exact:true}).click();await admin.waitForURL(base+'/empleados/');check('cuenta reactivada',actor().active,true);
 await authenticate(wh);await wh.waitForURL(base+'/inventario/entrada/');check('reactivacion no confirma pendiente',state(),saved);
 await fill(wh,product,[lot('AJ-R2',1,'8.0000')]);await button(wh,'Confirmar entrada').click();await wh.waitForURL(/\/inventario\/cargas\//);
 const final=state();report.states.final=final;
 check('tres lotes finales',final.receipt_lots.length,3);check('stock13',final.receipt_lots.reduce((n,l)=>n+l.available_quantity,0),13);
 check('costo final cuatro decimales',final.commerce.find(p=>p.id===product.id).average_cost,'2.9231');
 check('responsable historico conservado',final.receipt_lots.every(l=>l.responsible_id===fixture.warehouse_id),true);

 // 7. Verify initial_load_created layout metrics (panel padding and zero horizontal clipping at 1366x900).
 const layoutMetrics=await wh.evaluate(()=>{
   const panel=document.querySelector('[data-testid="inventory-load-created"]');
   const style=getComputedStyle(panel);
   const wraps=[...panel.querySelectorAll('.table-wrap')];
   const allFit=wraps.every(w=>{const t=w.querySelector('table');return t&&t.scrollWidth<=w.clientWidth+1;});
   return {
     paddingLeft:parseFloat(style.paddingLeft),
     paddingRight:parseFloat(style.paddingRight),
     allTablesFit:allFit,
   };
 });
 report.layoutMetrics=layoutMetrics;
 check('panel detalle con relleno izquierdo>=24',layoutMetrics.paddingLeft>=24,true);
 check('panel detalle con relleno derecho>=24',layoutMetrics.paddingRight>=24,true);
 check('tablas detalle sin recorte horizontal',layoutMetrics.allTablesFit,true);
 await wh.screenshot({path:path.join(out,'03-recuperada.png'),fullPage:true});
}
(async()=>{
  const browser=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true});
  try{report.chrome=browser.version();await test(browser);}
  catch(error){report.error=error.message;process.exitCode=1;}
  finally{fs.writeFileSync(path.join(out,'browser.json'),JSON.stringify(report,null,2));await browser.close();}
})();
