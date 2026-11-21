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

async function sell(seller,product){
  await seller.goto(base);await seller.getByRole('link',{name:'Preparar venta',exact:true}).click();
  await seller.locator('[name=query]').fill(product.barcode);await button(seller,'Buscar').click();
  const row=seller.locator('.sales-search-panel tbody tr');
  await row.locator('[name=quantity]').fill('2');await row.getByRole('button',{name:'Agregar',exact:true}).click();
  await seller.getByRole('link',{name:'Cobrar venta',exact:false}).click();
  await seller.locator('[name=cash_received]').fill('20');
  await button(seller,'Confirmar cobro').click();await seller.waitForURL(/\/ventas\/constancia\//);
  return {url:seller.url(),text:await seller.locator('main').innerText()};
}

async function test(browser){
  const probe=await browser.newPage(),nonce=crypto.randomBytes(32).toString('hex');
  const res=await probe.request.get(base,{headers:{'X-Audit03-Challenge':nonce}});
  check('aislamiento',res.headers()['x-audit03-proof'],crypto.createHmac('sha256',fs.readFileSync(path.join(run,'.django-key'))).update(nonce).digest('hex'));await probe.close();
  const warehouse=await login(browser,'warehouse'),seller=await login(browser,'seller'),admin=await login(browser,'admin');
  const product=fixture.products[0];
  const cost=s=>s.commerce.find(p=>p.id===product.id).average_cost;
  const quantities=s=>Object.fromEntries(s.receipt_lots.map(l=>[l.number,l.available_quantity]));
  report.states={};
  await menu(warehouse,'inventory-load-link');
  await fill(warehouse,product,[lot('AH-A',10,'2.0000'),lot('AH-B',10,'4.0000',fixture.later)]);
  await button(warehouse,'Confirmar existencias').click();await warehouse.waitForURL(/\/inventario\/cargas\//);
  const loadUrl=warehouse.url();
  const receipt=await sell(seller,product),before=state(),lines=before['sales.SaleLine'];
  check('costo previo 3',cost(before),'3.0000');
  check('FEFO retira dos del barato',quantities(before),{'AH-A':8,'AH-B':10});
  report.states.before=before;
  report.clock=JSON.parse(execFileSync(process.env.AUDIT03_PYTHON,[path.join(__dirname,'audit03y_browser_run.py'),'ah-advance'],{encoding:'utf8'}));
  check('avanzar fecha no cambia datos',state(),before);
  await warehouse.goto(base);await warehouse.getByRole('link',{name:'Ver inventario y alertas',exact:true}).first().click();
  const stock=warehouse.getByRole('row').filter({hasText:product.barcode});
  check('fisico 18',await stock.getByRole('cell').nth(2).innerText(),'18');
  check('vigente 10',await stock.getByRole('cell').nth(3).innerText(),'10');
  await warehouse.screenshot({path:path.join(out,'01-vencido.png'),fullPage:true});
  await menu(warehouse,'stock-entry-link');
  await fill(warehouse,product,[lot('AH-C',10,'6.0000',fixture.later)]);
  await button(warehouse,'Confirmar entrada').click();await warehouse.waitForURL(/\/inventario\/cargas\//);
  const received=state();report.states.received=received;
  check('promedio observado mezcla stock vigente y promedio anterior',cost(received),'4.5000');
  check('entrada no consume vencido',quantities(received),{'AH-A':8,'AH-B':10,'AH-C':10});
  check('entrada conserva venta',received['sales.SaleLine'],lines);
  check('promedio visible',await warehouse.locator('dt').filter({hasText:'Costo promedio'}).locator('..').locator('dd').innerText(),'S/ 4,50');
  await warehouse.screenshot({path:path.join(out,'02-reposicion.png'),fullPage:true});
  await menu(warehouse,'stock-writeoff-link');
  await warehouse.getByRole('row').filter({hasText:'AH-A'}).getByRole('link',{name:'Dar de baja',exact:true}).click();
  await warehouse.locator('[name=quantity]').fill('1');
  await warehouse.locator('[name=reason]').selectOption({label:'Daño o rotura'});
  await warehouse.locator('[name=notes]').fill('Caso ficticio de auditoria');
  await button(warehouse,'Confirmar baja').click();
  check('exige causa vencimiento',(await warehouse.locator('main').innerText()).includes('el motivo debe ser'),true);
  check('rechazo conserva estado',state(),received);
  await warehouse.locator('[name=reason]').selectOption('VENCIMIENTO');
  await button(warehouse,'Confirmar baja').click();
  await warehouse.waitForURL(base+'/inventario/bajas/nueva/');
  const written=state();report.states.written=written;
  check('baja parcial vencida 1',quantities(written),{'AH-A':7,'AH-B':10,'AH-C':10});
  check('baja vencida revalora vigentes sin cambiarlos',cost(written),'5.0000');
  check('baja conserva venta',written['sales.SaleLine'],lines);
  check('baja conserva responsable',written.writeoffs[0].responsible_id,fixture.warehouse_id);
  await warehouse.goto(loadUrl);
  check('costo revalorado visible',await warehouse.locator('dt').filter({hasText:'Costo promedio'}).locator('..').locator('dd').innerText(),'S/ 5,00');
  await warehouse.screenshot({path:path.join(out,'03-baja-revalora.png'),fullPage:true});
  await admin.goto(base);await admin.locator('a[href="/inventario/ajustes/nuevo/"]').first().click();
  for(const [delta,expected] of [['2','4.9091'],['-2','5.0000']]){
    await admin.getByRole('row').filter({hasText:'AH-B'}).getByRole('link',{name:'Ajustar',exact:true}).click();
    await admin.locator('[name=delta]').fill(delta);await admin.locator('[name=reason]').fill('Conteo ficticio AH');
    await button(admin,'Confirmar ajuste').click();await admin.waitForURL(base+'/inventario/ajustes/nuevo/');
    const adjusted=state();report.states['adjust'+delta]=adjusted;
    check('costo ajuste '+delta,cost(adjusted),expected);
    check('ajuste conserva venta '+delta,adjusted['sales.SaleLine'],lines);
  }
  for(const [page,route,label] of [[seller,'bajas/nueva','seller writeoff'],[seller,'ajustes/nuevo','seller adjustment'],[warehouse,'ajustes/nuevo','warehouse adjustment']]){
    const previous=state();const response=await page.request.post(base+'/inventario/'+route+'/',{form:{}});
    check('denegado '+label,response.status(),403);check('sin cambios '+label,state(),previous);
  }
  await seller.goto(receipt.url);check('constancia original igual',await seller.locator('main').innerText(),receipt.text);
  await sell(seller,product);const final=state();report.states.final=final;
  check('costos historicos separados',final['sales.SaleLine'].map(l=>l.unit_cost).sort(),['3.0000','5.0000']);
  check('venta no toca vencido',quantities(final),{'AH-A':7,'AH-B':8,'AH-C':10});
}
(async()=>{
  const browser=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true});
  try{report.chrome=browser.version();await test(browser);}
  catch(error){report.error=error.message;process.exitCode=1;}
  finally{fs.writeFileSync(path.join(out,'browser.json'),JSON.stringify(report,null,2));await browser.close();}
})();
