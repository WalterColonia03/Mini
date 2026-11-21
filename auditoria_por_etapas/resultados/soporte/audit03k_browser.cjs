// HU-PROD-05/CA02. The five records already exist, each initially inactive.
const fs = require('fs');
const path = require('path');
const os = require('os');
const crypto = require('crypto');
const {execFileSync} = require('child_process');
const {chromium} = require(path.join(os.homedir(),'.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright-core'));
const run = process.env.AUDIT03_RUN_DIR;
const out = process.env.AUDIT03_OUT;
const base = 'http://127.0.0.1:' + process.env.AUDIT03_PORT;
const creds = JSON.parse(fs.readFileSync(path.join(run,'.credentials.json'),'utf8'));
const fx = JSON.parse(fs.readFileSync(path.join(out,'fixture.json'),'utf8'));
const before = JSON.parse(fs.readFileSync(path.join(out,'orm-initial.json'),'utf8'));
const report = {cases:[], evidence:[]};

function record(id, ok, details={}) { report.cases.push({id,ok,...details}); }
async function search(page, code) {
  await page.locator('[name=query]').fill(code);
  await page.getByRole('button',{name:'Buscar',exact:true}).click();
  return page.locator('tr').filter({has:page.getByRole('button',{name:'Agregar',exact:true})}).allTextContents();
}
async function rolePage(browser,role,menu) {
  const page=await (await browser.newContext({viewport:{width:1366,height:900},locale:'es-PE'})).newPage();
  await page.goto(base);
  await page.locator('[name=email]').fill(creds[role].email);
  await page.locator('[name=password]').fill(creds[role].password);
  await page.locator('button[type=submit]').click();
  await page.getByRole('link',{name:menu,exact:true}).click();
  return page;
}
(async()=>{
  const browser=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true});
  try {
    report.browser=browser.version();
    const probePage=await browser.newPage();
    const nonce=crypto.randomBytes(32).toString('hex');
    const probe=await probePage.request.get(base,{headers:{'X-Audit03-Challenge':nonce}});
    if(probe.headers()['x-audit03-proof']!==crypto.createHmac('sha256',fs.readFileSync(path.join(run,'.django-key'))).update(nonce).digest('hex')) throw Error('Isolation mismatch');
    await probePage.close();
    const admin=await rolePage(browser,'admin','Productos');
    const warehouse=await rolePage(browser,'warehouse','Catálogo de productos');
    const seller=await rolePage(browser,'seller','Preparar venta');
    const receipt=await seller.context().newPage();
    await receipt.goto(base+'/ventas/constancia/'+fx.sale_id+'/');
    const historical=await receipt.locator('#constancia-interna').innerText();
    for(const sample of fx.cases) {
      const row=admin.getByRole('row').filter({has:admin.getByRole('cell',{name:sample.code,exact:true})});
      const prior=await search(seller,sample.code);
      record(sample.code+'-inactivo',prior.length===0 && await row.getByRole('button',{name:'Habilitar',exact:true}).count()===1);
      const endpoint='/productos/'+sample.id+'/disponibilidad/';
      const [change]=await Promise.all([
        admin.waitForResponse(r=>new URL(r.url()).pathname===endpoint && r.request().method()==='POST'),
        row.getByRole('button',{name:'Habilitar',exact:true}).click()
      ]);
      const message=await admin.getByText(/ahora está activo/).innerText();
      record(sample.code+'-estado',change.status()===302 && await row.getByRole('button',{name:'Deshabilitar',exact:true}).count()===1,
             {http:change.status(),message});
      await warehouse.reload();
      const stockRow=warehouse.getByRole('row').filter({has:warehouse.getByRole('cell',{name:sample.code,exact:true})});
      const cells=(await stockRow.getByRole('cell').allInnerTexts()).map(value=>value.trim());
      record(sample.code+'-almacen',cells[6]===sample.badge && Number.parseInt(cells[4],10)===sample.stock && await stockRow.getByRole('button').count()===0,
             {badge:cells[6],stock:cells[4],price:cells[3]});
      const offered=await search(seller,sample.code);
      const matches=seller.locator('tr').filter({has:seller.getByRole('button',{name:'Agregar',exact:true})});
      const values=offered.length===1?(await matches.getByRole('cell').allInnerTexts()).map(v=>v.trim()):[];
      record(sample.code+'-mostrador',sample.offered ?
        offered.length===1 && values[1]===sample.code && values[2]===String(sample.stock) && values[3].replace(',','.').includes(sample.price):
        offered.length===0,{offered:offered.length,values:values.slice(0,4)});
      if(sample.offered) await seller.screenshot({path:path.join(out,'01-mostrador.png')});
    }
    await warehouse.screenshot({path:path.join(out,'02-almacen.png'),fullPage:true});
    await receipt.reload();
    record('constancia',historical===await receipt.locator('#constancia-interna').innerText());
    const after=JSON.parse(execFileSync(process.env.AUDIT03_PYTHON,[path.join(__dirname,'audit03k_run.py'),'snapshot'],{encoding:'utf8',env:{...process.env,PYTHONIOENCODING:'utf-8'}}));
    for(const key of Object.keys(before)) {
      const expected=key==='catalog.Product'?before[key].map(item=>({...item,is_active:true})):before[key];
      record('persistencia-'+key,JSON.stringify(expected)===JSON.stringify(after[key]),{rows:expected.length});
    }
  } catch(error) {report.error=error.message;process.exitCode=1;}
  finally {
    fs.writeFileSync(path.join(out,'browser.json'),JSON.stringify(report,null,2));
    await browser.close();
  }
  if(report.cases.some(row=>!row.ok))process.exitCode=1;
})().catch(error=>{console.error(error.message);process.exitCode=1;});
