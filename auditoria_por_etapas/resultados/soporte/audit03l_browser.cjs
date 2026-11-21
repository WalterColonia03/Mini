// Category suspension across checkout and stock entry through Chrome.
const fs = require('fs');
const path = require('path');
const os = require('os');
const crypto = require('crypto');
const {execFileSync} = require('child_process');
const {chromium} = require(path.join(os.homedir(),'.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright-core'));
const run = process.env.AUDIT03_RUN_DIR, out = process.env.AUDIT03_OUT;
const base = 'http://127.0.0.1:' + process.env.AUDIT03_PORT;
const creds = JSON.parse(fs.readFileSync(path.join(run,'.credentials.json'),'utf8'));
const fx = JSON.parse(fs.readFileSync(path.join(out,'fixture.json'),'utf8'));
const report = {mode:'Chrome sequential category suspension, checkout and stock entry',cases:[],findings:[],posts:[]};
const A='00CAT03K-A', B='00CAT03K-B', C='00CAT03K-C';
function record(id,ok,details={}) {report.cases.push({id,ok,...details});}
function snapshot() {return JSON.parse(execFileSync(process.env.AUDIT03_PYTHON,[path.join(__dirname,'audit03k_run.py'),'snapshot'],{encoding:'utf8',env:{...process.env,PYTHONIOENCODING:'utf-8'}}));}
function write(name,data) {fs.writeFileSync(path.join(out,name),JSON.stringify(data,null,2));}
function row(state,id) {return state['catalog.Product'].find(p=>p.id===id);}
function products(state) {return state['catalog.Product'];}
async function profile(page,value) {await page.keyboard.press('Control+a');await page.keyboard.type(value);}
async function rolePage(browser,role,menu) {
  const page=await (await browser.newContext({viewport:{width:1366,height:900},locale:'es-PE'})).newPage();
  await page.goto(base);await page.locator('[name=email]').fill(creds[role].email);
  await page.locator('[name=password]').fill(creds[role].password);
  await page.locator('button[type=submit]').click();
  await page.getByRole('link',{name:menu,exact:true}).click();
  page.on('request',req=>{if(req.method()==='POST')report.posts.push({role,path:new URL(req.url()).pathname});});
  return page;
}
async function edit(page,barcode) {
  if(new URL(page.url()).pathname!=='/productos/') await page.getByRole('link',{name:'Productos',exact:true}).click();
  const entry=page.getByRole('row').filter({has:page.getByRole('cell',{name:barcode,exact:true})});
  await entry.getByRole('link',{name:'Editar',exact:true}).click();
}
async function save(page,label) {await page.getByRole('button',{name:label,exact:true}).click();}
async function formValues(page) {return page.locator('form input:not([type=hidden]), form select').evaluateAll(nodes=>Object.fromEntries(nodes.filter(n=>n.name).map(n=>[n.name,n.value])));}

(async()=>{
 const browser=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true});
 try {
  report.browser=browser.version();
  const probe=await browser.newPage(),nonce=crypto.randomBytes(32).toString('hex');
  const challenge=await probe.request.get(base,{headers:{'X-Audit03-Challenge':nonce}});
  if(challenge.headers()['x-audit03-proof']!==crypto.createHmac('sha256',fs.readFileSync(path.join(run,'.django-key'))).update(nonce).digest('hex'))throw Error('Isolation mismatch');
  await probe.close();
  const admin=await rolePage(browser,'admin','Categorías');
  const seller=await rolePage(browser,'seller','Preparar venta');
  const warehouse=await rolePage(browser,'warehouse','Entrada de mercadería');
  const original=snapshot();
  const receipt=await seller.context().newPage();
  await receipt.goto(base+'/ventas/constancia/'+fx.sale_id+'/');
  const historical=await receipt.locator('#constancia-interna').innerText();
  await seller.getByRole('link',{name:'Cobrar venta →',exact:true}).click();
  await seller.locator('[name=cash_received]').fill('20.00');
  await warehouse.locator('[name=product]').selectOption(fx.product_id);
  for(const [key,value] of Object.entries({number:'L-CHROME',quantity:'5',unit_cost:'4.00',expiration_date:'2027-01-31'}))
    await warehouse.locator('[name="lots-0-'+key+'"]').fill(value);
  await admin.getByRole('button',{name:'Desactivar',exact:true}).click();
  record('impacto', (await admin.locator('main').innerText()).includes('Ventas en preparación'));
  await admin.screenshot({path:path.join(out,'01-impacto.png'),fullPage:true});
  await admin.getByRole('button',{name:'Confirmar desactivación',exact:true}).click();
  const suspended=snapshot();
  const category=suspended['catalog.Category'].find(c=>c.id===fx.category_id);
  record('categoria-suspendida',category.is_active===false);
  await seller.getByRole('button',{name:'Confirmar cobro',exact:true}).click();
  const saleAlerts=await seller.getByRole('alert').allInnerTexts();
  record('cobro-antiguo-rechazado',saleAlerts.some(t=>/no está disponible|cambió/.test(t)),{messages:saleAlerts});
  await seller.screenshot({path:path.join(out,'02-cobro-rechazado.png'),fullPage:true});
  record('cobro-sin-efectos',JSON.stringify(snapshot())===JSON.stringify(suspended));
  await warehouse.getByRole('button',{name:'Confirmar entrada',exact:true}).click();
  const entryAlerts=await warehouse.getByRole('alert').allInnerTexts();
  record('entrada-antigua-rechazada',entryAlerts.some(t=>t.includes('Seleccione un producto activo')),{messages:entryAlerts});
  record('entrada-sin-efectos',JSON.stringify(snapshot())===JSON.stringify(suspended));
  await warehouse.screenshot({path:path.join(out,'03-entrada-rechazada.png'),fullPage:true});
  await receipt.reload();record('historico-integro',historical===await receipt.locator('#constancia-interna').innerText());
  await warehouse.getByRole('link',{name:'Catálogo de productos',exact:true}).click();
  const cells=await warehouse.getByRole('row').filter({has:warehouse.getByRole('cell',{name:'AUD03-BEBIDA',exact:true})}).getByRole('cell').allInnerTexts();
  record('almacen-motivo-stock',cells.includes('Categoría desactivada')&&cells.includes('19'),{cells});
  await seller.getByRole('link',{name:'Preparar venta',exact:true}).click();
  await seller.locator('[name=query]').fill('AUD03-BEBIDA');
  await seller.getByRole('button',{name:'Buscar',exact:true}).click();
  record('mostrador-excluye',await seller.getByRole('button',{name:'Agregar',exact:true}).count()===0);
  // Restore via the ordinary category confirmation before the second sequential order.
  await admin.getByRole('button',{name:'Activar',exact:true}).click();
  await admin.getByRole('button',{name:'Confirmar activación',exact:true}).click();
  await seller.getByRole('link',{name:'Cobrar venta →',exact:true}).click();
  await seller.locator('[name=cash_received]').fill('20.00');
  await seller.getByRole('button',{name:'Confirmar cobro',exact:true}).click();
  await seller.waitForURL(/\/constancia\//);
  const sold=snapshot();
  record('venta-primero',sold['sales.Sale'].length===2 && sold['inventory.Lot'][0].available_quantity===17);
  const newReceipt=await seller.locator('#constancia-interna').innerText();
  await admin.getByRole('button',{name:'Desactivar',exact:true}).click();
  await admin.getByRole('button',{name:'Confirmar desactivación',exact:true}).click();
  await seller.reload();
  record('constancia-tras-suspender',newReceipt===await seller.locator('#constancia-interna').innerText());
  const final=snapshot();
  for(const key of Object.keys(sold).filter(k=>k!=='catalog.Category'))
    record('suspension-conserva-'+key,JSON.stringify(sold[key])===JSON.stringify(final[key]));
  write('checkpoints.json',{original,suspended,sold,final});
 } catch(error) {report.error=error.message;process.exitCode=1;}
 finally {write('browser.json',report);await browser.close();}
 if(report.cases.some(r=>!r.ok))process.exitCode=1;
})().catch(error=>{console.error(error.message);process.exitCode=1;});
