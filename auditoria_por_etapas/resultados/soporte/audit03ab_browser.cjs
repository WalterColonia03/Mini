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
async function rejected(page,data,path,previous,id) {
  const res=await page.request.post(base+path,{form:data,maxRedirects:0});
  check(id+' status',res.status(),200);
  check(id+' error',/role="alert"/.test(await res.text()),true);
  check(id+' atomicidad',state(),previous);
}
async function test(browser) {
  const proof=await browser.newPage(),nonce=crypto.randomBytes(32).toString('hex');
  const response=await proof.request.get(base,{headers:{'X-Audit03-Challenge':nonce}});
  check('servidor aislado',response.headers()['x-audit03-proof'],
    crypto.createHmac('sha256',fs.readFileSync(path.join(run,'.django-key'))).update(nonce).digest('hex'));
  await proof.close();
  const page=await login(browser,'warehouse');
  const initial=state();
  await menu(page,'inventory-load-link');
  await fill(page,fixture.products[0],[lot('cancelado',12,'2.0000')]);
  await page.getByRole('link',{name:'Cancelar',exact:true}).click();
  check('cancelar conserva toda la base comercial',state(),initial);

  await menu(page,'inventory-load-link');
  await fill(page,fixture.products[0],[lot('A-1',12,'2.0000'),lot('A-2',6,'5.0000',fixture.today)]);
  await button(page,'Confirmar existencias').click();
  await page.getByRole('alert').filter({hasText:'vencimiento debe ser posterior'}).waitFor();
  check('lote vencido revierte carga completa',state(),initial);
  await page.locator('[name="lots-1-expiration_date"]').fill(fixture.later);
  await page.locator('[name="lots-1-number"]').fill(' a-1 ');
  await button(page,'Confirmar existencias').click();
  await page.getByRole('alert').filter({hasText:'repetido'}).waitFor();
  check('duplicado normalizado revierte carga completa',state(),initial);
  await page.locator('[name="lots-1-number"]').fill('a-2');
  const firstPayload=await payload(page);
  for (const [field,value] of [['quantity','0'],['quantity','1.5'],['quantity','1000000'],
                               ['unit_cost','1e2'],['unit_cost','0.00001'],['number','N'.repeat(65)]]) {
    await rejected(page,{...firstPayload,['lots-0-'+field]:value},'/inventario/carga-inicial/',initial,
                   'HTTP límite '+field+' '+value);
  }
  await button(page,'Confirmar existencias').click();
  await page.waitForURL(/\/inventario\/cargas\//);
  const receiptUrl=page.url();
  const first=state();
  check('una cabecera inicial',first.receipt_loads.length,1);
  check('dos lotes iniciales',first.receipt_lots.length,2);
  check('18 unidades A',first.receipt_lots.reduce((sum,l)=>sum+l.available_quantity,0),18);
  check('costo ponderado A',first.commerce.find(p=>p.id===fixture.products[0].id).average_cost,'3.0000');
  check('constancia con proveedor',(await page.locator('main').innerText()).includes('Proveedor ficticio AB'),true);
  check('constancia con UND',(await page.locator('main').innerText()).includes('18 UND'),true);
  await page.screenshot({path:path.join(out,'carga-inicial.png'),fullPage:true});
  await page.reload();
  check('recarga sin duplicación',state(),first);
  await rejected(page,firstPayload,'/inventario/carga-inicial/',first,'reenvío inicial');

  for (const product of fixture.products.slice(1)) {
    await menu(page,'inventory-load-link');
    await fill(page,product,[lot(' a-1 ',4,'1.0000'),lot('A-2',2,'4.0000',fixture.later)]);
    await button(page,'Confirmar existencias').click();
    await page.waitForURL(/\/inventario\/cargas\//);
    const current=state();
    const lots=current.receipt_lots.filter(l=>l.product_id===product.id);
    check(product.name+' lotes propios',lots.length,2);
    check(product.name+' cantidad',lots.reduce((sum,l)=>sum+l.available_quantity,0),6);
    check(product.name+' costo',current.commerce.find(p=>p.id===product.id).average_cost,'2.0000');
  }
  const three=state();
  check('tres cargas',three.receipt_loads.length,3);
  for (const row of three.receipt_lots) {
    check('proveedor '+row.number+' '+row.product_id,row.supplier_id,fixture.supplier_id);
    check('responsable '+row.number+' '+row.product_id,row.responsible_id,fixture.warehouse_id);
  }
  await menu(page,'stock-entry-link');
  await fill(page,fixture.products[0],[lot('CANCELAR',2,'6.0000')]);
  await page.getByRole('link',{name:'Cancelar',exact:true}).click();
  check('cancelar reposición',state(),three);
  await menu(page,'stock-entry-link');
  await fill(page,fixture.products[0],[lot('R-1',2,'6.0000'),lot(' a-1 ',1,'1.0000')]);
  await button(page,'Confirmar entrada').click();
  await page.getByRole('alert').filter({hasText:'ya existe'}).waitFor();
  check('mezcla nuevo y existente revierte reposición',state(),three);
  for(const field of ['number','quantity','unit_cost','expiration_date']) await page.locator('[name="lots-1-'+field+'"]').fill('');
  const entryPayload=await payload(page);
  await button(page,'Confirmar entrada').click();
  await page.waitForURL(/\/inventario\/cargas\//);
  check('constancia posterior usa referencia inicial',page.url(),receiptUrl);
  const after=state();
  check('constancia identifica el responsable inicial',(await page.locator('main').innerText()).includes('Responsable de carga inicial'),true);
  check('constancia distingue entradas posteriores',(await page.locator('main').innerText()).includes('Cada entrada conserva sus lotes y responsable.'),true);
  check('sin cabecera inicial adicional',after.receipt_loads,three.receipt_loads);
  check('solo un lote posterior',after.receipt_lots.filter(l=>!l.is_initial).length,1);
  check('20 unidades A',after.receipt_lots.filter(l=>l.product_id===fixture.products[0].id).reduce((n,l)=>n+l.available_quantity,0),20);
  check('nuevo costo promedio',after.commerce.find(p=>p.id===fixture.products[0].id).average_cost,'3.3000');
  check('lotes anteriores sin sobreescritura',after.receipt_lots.filter(l=>l.is_initial),three.receipt_lots);
  await rejected(page,entryPayload,'/inventario/entrada/',after,'reenvío reposición');
  await page.screenshot({path:path.join(out,'reposicion.png'),fullPage:true});
  for(const role of ['admin','seller']) {
    const other=await login(browser,role);
    const cookies=await other.context().cookies();
    const csrf=cookies.find(c=>c.name==='audit03k_csrftoken').value;
    for(const route of ['/inventario/carga-inicial/','/inventario/entrada/']) {
      check(role+' GET '+route,(await other.request.get(base+route)).status(),403);
      check(role+' POST '+route,(await other.request.post(base+route,{form:{...entryPayload,csrfmiddlewaretoken:csrf}})).status(),403);
    }
    if(role==='seller') {
      await other.getByRole('link',{name:'Preparar venta',exact:true}).click();
      for (const [index,product] of fixture.products.entries()) {
        await other.locator('[name=query]').fill(product.barcode);
        await button(other,'Buscar').click();
        const row=other.locator('.sales-search-panel tbody tr');
        check('vendedor ficha '+product.name,await row.count(),1);
        check('vendedor saldo '+product.name,await row.getByRole('cell').nth(2).innerText(),index===0?'20':'6');
      }
    }
  }
  check('consultas y roles conservan estado',state(),after);
}
(async()=>{
  const browser=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true});
  try {report.chrome=browser.version();await test(browser);}
  catch(error){report.error=error.message;process.exitCode=1;}
  finally{fs.writeFileSync(path.join(out,'browser.json'),JSON.stringify(report,null,2));await browser.close();}
})();
