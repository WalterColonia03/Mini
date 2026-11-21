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

async function dropped(p,afterCommit){
  let forwardedStatus=null,routeFailure=null;
  const failed=p.waitForEvent('requestfailed',r=>r.method()==='POST' && r.url()===base+'/inventario/entrada/');
  await p.route('**/inventario/entrada/',async route=>{
    if(route.request().method()!=='POST')return route.continue();
    try{
      if(afterCommit){const res=await route.fetch({maxRedirects:0});forwardedStatus=res.status();}
      await route.abort('connectionreset');
    }catch(e){routeFailure=e.message;await route.abort().catch(()=>{});}
  });
  await button(p,'Confirmar entrada').click({noWaitAfter:true}).catch(e=>{
    if(!e.message.includes('ERR_CONNECTION_RESET'))throw e;
  });
  const req=await failed;
  await p.waitForLoadState('domcontentloaded').catch(()=>{});
  await p.unroute('**/inventario/entrada/');
  check('intercepción sin error '+afterCommit,routeFailure,null);
  check('fallo de conexión visible '+afterCommit,req.failure().errorText.includes('ERR_CONNECTION_RESET'),true);
  check('respuesta servidor '+afterCommit,forwardedStatus,afterCommit?302:null);
  report.transport=report.transport||[];
  report.transport.push({afterCommit,forwardedStatus,browserFailure:req.failure().errorText});
}

async function test(browser){
  const probe=await browser.newPage(),nonce=crypto.randomBytes(32).toString('hex');
  const res=await probe.request.get(base,{headers:{'X-Audit03-Challenge':nonce}});
  check('aislamiento',res.headers()['x-audit03-proof'],crypto.createHmac('sha256',fs.readFileSync(path.join(run,'.django-key'))).update(nonce).digest('hex'));await probe.close();
  const warehouse=await login(browser,'warehouse'),product=fixture.products[0];
  await menu(warehouse,'inventory-load-link');await fill(warehouse,product,[lot('AI-BASE',10,'2.0000')]);
  await button(warehouse,'Confirmar existencias').click();await warehouse.waitForURL(/\/inventario\/cargas\//);
  const original=state(),canonical=warehouse.url();report.states={original};
  await menu(warehouse,'stock-entry-link');await fill(warehouse,product,[lot('AI-B',3,'4.0000'),lot('AI-C',2,'5.0000')]);
  const first=await payload(warehouse);
  check('formulario no lleva clave de idempotencia','idempotency_key' in first,false);
  await dropped(warehouse,false);check('sin entrega no guarda',state(),original);
  const retry=await warehouse.request.post(base+'/inventario/entrada/',{form:first,maxRedirects:0});
  check('reintento de no entregado confirma',retry.status(),302);
  check('reintento apunta a referencia inicial',new URL(retry.headers().location,base).href,canonical);
  const once=state();report.states.once=once;
  check('tres lotes tras primer reintento',once.receipt_lots.length,3);
  check('15 unidades tras primer reintento',once.receipt_lots.reduce((n,l)=>n+l.available_quantity,0),15);
  check('costo2.8',once.commerce.find(p=>p.id===product.id).average_cost,'2.8000');
  await menu(warehouse,'stock-entry-link');await fill(warehouse,product,[lot('AI-D',2,'6.0000'),lot('AI-E',3,'7.0000')]);
  const second=await payload(warehouse);await dropped(warehouse,true);
  const saved=state();report.states.saved=saved;
  check('una carga tecnica',saved.receipt_loads.length,1);
  check('cinco lotes tras respuesta perdida',saved.receipt_lots.length,5);
  check('20 unidades',saved.receipt_lots.reduce((n,l)=>n+l.available_quantity,0),20);
  check('costo3.75',saved.commerce.find(p=>p.id===product.id).average_cost,'3.7500');
  check('lotes anteriores intactos',saved.receipt_lots.filter(l=>once.receipt_lots.some(x=>x.id===l.id)),once.receipt_lots);
  check('proveedor y autor preservados',saved.receipt_lots.every(l=>l.responsible_id===fixture.warehouse_id&&l.supplier_id===fixture.supplier_id),true);
  check('cuatro lotes posteriores',saved.receipt_lots.filter(l=>!l.is_initial).length,4);
  for(const [label,data] of [['exacto',second],['normalizado',{...second,'lots-0-number':' ai-d '}],['cantidad alterada',{...second,'lots-0-quantity':'9'}],['mezcla nuevo y existente',{...second,'lots-0-number':'AI-NUEVO'}]]){
    const response=await warehouse.request.post(base+'/inventario/entrada/',{form:data,maxRedirects:0});
    check('rechazo controlado '+label,response.status(),200);
    check('mensaje duplicado '+label,(await response.text()).includes('ya existe para este producto'),true);
    check('sin cambios '+label,state(),saved);
  }
  // Show the duplicate rejection through a real form submission too.
  await menu(warehouse,'stock-entry-link');await fill(warehouse,product,[lot('AI-D',2,'6.0000'),lot('AI-E',3,'7.0000')]);
  await button(warehouse,'Confirmar entrada').click();
  check('error visible de duplicado',(await warehouse.locator('main').innerText()).includes('ya existe para este producto'),true);
  check('formulario rechazado no escribe',state(),saved);
  await warehouse.screenshot({path:path.join(out,'01-reintento-rechazado.png'),fullPage:true});
  const recovered=await login(browser,'warehouse');
  await recovered.getByRole('link',{name:'Ver inventario y alertas',exact:true}).first().click();
  const stock=recovered.getByRole('row').filter({hasText:product.barcode});
  check('consulta fisica20',await stock.getByRole('cell').nth(2).innerText(),'20');
  await stock.getByRole('link',{name:'Ver carga',exact:true}).click();
  check('recupera misma referencia',recovered.url(),canonical);
  check('costo visible3.75',await recovered.locator('dt').filter({hasText:'Costo promedio'}).locator('..').locator('dd').innerText(),'S/ 3,75');
  for(const number of ['AI-B','AI-C','AI-D','AI-E'])check('lote recuperado '+number,(await recovered.locator('main').innerText()).includes(number),true);
  await recovered.screenshot({path:path.join(out,'02-recuperacion.png'),fullPage:true});
  await recovered.reload();check('recarga no escribe',state(),saved);
  const admin=await login(browser,'admin'),seller=await login(browser,'seller');
  check('admin consulta',(await admin.goto(canonical)).status(),200);
  check('vendedor no consulta constancia inventario',(await seller.goto(canonical)).status(),403);
  for(const [role,page,route] of [['admin',admin,'entrada'],['seller',seller,'entrada'],
      ['seller',seller,'bajas/nueva'],['seller',seller,'ajustes/nuevo'],['warehouse',recovered,'ajustes/nuevo']]){
    const token=(await page.context().cookies(base)).find(c=>c.name==='audit03k_csrftoken').value;
    const response=await page.request.post(base+'/inventario/'+route+'/',{form:{...second,csrfmiddlewaretoken:token}});
    check('POST denegado '+role+' '+route,response.status(),403);
    check('rechazo de autorizacion no CSRF '+role+' '+route,(await response.text()).includes('No tienes permiso para esta operación'),true);
  }
  await seller.goto(base);await seller.getByRole('link',{name:'Preparar venta',exact:true}).click();
  await seller.locator('[name=query]').fill(product.barcode);await button(seller,'Buscar').click();
  check('vendedor ve stock20',await seller.locator('.sales-search-panel tbody tr').getByRole('cell').nth(2).innerText(),'20');
  check('consultas y denegaciones no alteran comercio',state(),saved);
}
(async()=>{
  const browser=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true});
  try{report.chrome=browser.version();await test(browser);}
  catch(error){report.error=error.message;process.exitCode=1;}
  finally{fs.writeFileSync(path.join(out,'browser.json'),JSON.stringify(report,null,2));await browser.close();}
})();
