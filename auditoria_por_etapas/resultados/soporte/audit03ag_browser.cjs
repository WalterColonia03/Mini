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
  await menu(warehouse,'inventory-load-link');
  await fill(warehouse,product,[lot('AG-A',10,'2.0000'),lot('AG-B',10,'4.0000',fixture.later)]);
  await button(warehouse,'Confirmar existencias').click();await warehouse.waitForURL(/\/inventario\/cargas\//);
  const receipt=await sell(seller,product),before=state();
  const lines=before['sales.SaleLine'];check('una venta previa',lines.length,1);
  report.before=before;
  await menu(warehouse,'stock-entry-link');
  await fill(warehouse,product,[lot('AG-C',10,'6.0000',fixture.later)]);
  await button(warehouse,'Confirmar entrada').click();await warehouse.waitForURL(/\/inventario\/cargas\//);
  const after=state();report.after=after;
  check('promedio mostrado a dos decimales', await warehouse.locator('dt').filter({hasText:'Costo promedio'}).locator('..').locator('dd').innerText(), process.argv[2]==='ag-before'?'S/ 4,14':'S/ 4,07');
  check('reposicion conserva detalle anterior',after['sales.SaleLine'],lines);
  await seller.goto(receipt.url);check('constancia no cambia',await seller.locator('main').innerText(),receipt.text);
  check('no expone costo',/costo/i.test(receipt.text),false);
  await seller.screenshot({path:path.join(out,'constancia-conservada.png'),fullPage:true});
  for(const [role,page] of [['admin',admin],['seller',seller]]){
    const prior=state();const response=await page.request.post(base+'/inventario/entrada/',{form:{product:product.id}});
    check('entrada denegada '+role,response.status(),403);check('denegacion sin cambios '+role,state(),prior);
  }
  await sell(seller,product);report.final=state();
  const costs=report.final['sales.SaleLine'].map(x=>x.unit_cost);
  const cost=report.final.commerce.find(x=>x.id===product.id).average_cost;
  if(process.argv[2]==='ag-before'){
    check('brecha reproducida falta costo',costs.every(x=>x===undefined),true);
    check('brecha formula tras FEFO',cost,'4.1429');
  }else{
    check('costos distintos conservados',costs.sort(),['3.0000','4.0714']);
    check('promedio conforme RN14',cost,'4.0714');
  }
  await warehouse.goto(base);await warehouse.getByRole('link',{name:'Ver inventario y alertas',exact:true}).first().click();
  report.stockRow=await warehouse.getByRole('row').filter({hasText:product.barcode}).innerText();
  await warehouse.screenshot({path:path.join(out,'inventario-repuesto.png'),fullPage:true});
}
(async()=>{
  const browser=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true});
  try{report.chrome=browser.version();await test(browser);}
  catch(error){report.error=error.message;process.exitCode=1;}
  finally{fs.writeFileSync(path.join(out,'browser.json'),JSON.stringify(report,null,2));await browser.close();}
})();
