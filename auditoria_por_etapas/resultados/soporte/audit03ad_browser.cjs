const fs=require('node:fs'),path=require('node:path'),os=require('node:os'),crypto=require('node:crypto');
const assert=require('node:assert/strict');
const {execFileSync}=require('node:child_process');
const {chromium}=require(path.join(os.homedir(),'.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright-core'));
const out=process.env.AUDIT03_OUT,run=process.env.AUDIT03_RUN_DIR,base='http://127.0.0.1:'+process.env.AUDIT03_PORT;
const fixture=JSON.parse(fs.readFileSync(path.join(out,'fixture.json')));
const accounts=JSON.parse(fs.readFileSync(path.join(run,'.credentials.json')));
const report={checks:[],states:[],input:'Automated Chrome seller checkout; mocked receipt times only during fixture creation'};
function check(id,a,b){assert.deepEqual(a,b,id);report.checks.push(id);}
function state(){return JSON.parse(execFileSync(process.env.AUDIT03_PYTHON,[path.join(__dirname,'audit03y_browser_run.py'),'snapshot'],{encoding:'utf8'}));}
async function login(browser,role){
  const p=await browser.newPage({locale:'es-PE',viewport:{width:1366,height:900}});
  await p.goto(base);await p.locator('[name=email]').fill(accounts[role].email);
  await p.locator('[name=password]').fill(accounts[role].password);
  await p.locator('button[type=submit]').click();return p;
}
async function test(browser){
  const probe=await browser.newPage(),nonce=crypto.randomBytes(32).toString('hex');
  const res=await probe.request.get(base,{headers:{'X-Audit03-Challenge':nonce}});
  check('aislamiento',res.headers()['x-audit03-proof'],crypto.createHmac('sha256',fs.readFileSync(path.join(run,'.django-key'))).update(nonce).digest('hex'));
  await probe.close();
  const seller=await login(browser,'seller');
  const initial=state();
  check('cinco lotes preparados',initial.receipt_lots.length,5);
  const expectedAmounts=[[0,1,2,2],[0,0,1,2],[0,0,0,0]];
  for(const [index,quantity] of fixture.quantities.entries()){
    await seller.goto(base);await seller.getByRole('link',{name:'Preparar venta',exact:true}).click();
    await seller.locator('[name=query]').fill(fixture.code);
    await seller.getByRole('button',{name:'Buscar',exact:true}).click();
    const row=seller.locator('.sales-search-panel tbody tr');
    const stock=[8,5,3][index];
    check('existencias vigentes '+index,await row.getByRole('cell').nth(2).innerText(),String(stock));
    await row.locator('[name=quantity]').fill(String(quantity));
    await row.getByRole('button',{name:'Agregar',exact:true}).click();
    await seller.getByRole('link',{name:'Cobrar venta',exact:false}).click();
    await seller.locator('[name=cash_received]').fill(String(quantity*3));
    const payload=await seller.locator('form[method=post]').evaluate(f=>Object.fromEntries(new FormData(f)));
    const checkoutUrl=seller.url();
    const before=state();
    await seller.getByRole('button',{name:'Confirmar cobro',exact:true}).click();
    await seller.waitForURL(/\/ventas\/constancia\//);
    const current=state();
    report.states.push(current);
    check('FEFO cantidades por UUID '+index,fixture.order.map(id=>current.receipt_lots.find(l=>l.id===id).available_quantity),expectedAmounts[index]);
    check('vencido conserva cinco '+index,current.receipt_lots.find(l=>l.id===fixture.expired).available_quantity,5);
    const withoutQty=lots=>lots.map(({available_quantity,...rest})=>rest);
    check('identidad y fechas intactas '+index,withoutQty(current.receipt_lots),withoutQty(initial.receipt_lots));
    check('una venta confirmada '+index,current['sales.Sale'].length,before['sales.Sale'].length+1);
    const response=await seller.request.post(checkoutUrl,{form:payload,maxRedirects:0});
    check('reenvío resuelto '+index,[200,302].includes(response.status()),true);
    check('reenvío no descuenta otra vez '+index,state(),current);
    if(index===0)await seller.screenshot({path:path.join(out,'primera-venta.png'),fullPage:true});
  }
  const warehouse=await login(browser,'warehouse');
  await warehouse.getByRole('link',{name:'Ver inventario y alertas',exact:true}).first().click();
  const row=warehouse.getByRole('row').filter({hasText:fixture.code});
  check('almacenero observa físico y vendible',(await row.innerText()).includes('Sin stock vendible'),true);
  await warehouse.screenshot({path:path.join(out,'inventario-final.png'),fullPage:true});
}
(async()=>{
  const browser=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true});
  try{report.chrome=browser.version();await test(browser);}
  catch(error){report.error=error.message;process.exitCode=1;}
  finally{fs.writeFileSync(path.join(out,'browser.json'),JSON.stringify(report,null,2));await browser.close();}
})();
