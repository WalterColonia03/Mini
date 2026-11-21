// Product recategorization during checkout through Chrome.
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
const report = {mode:'Chrome product recategorization, stale destination and role boundaries',cases:[],findings:[],posts:[]};
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
  const admin=await rolePage(browser,'admin','Productos');
  const admin2=await rolePage(browser,'admin2','Categorías');
  const seller=await rolePage(browser,'seller','Preparar venta');
  const warehouse=await rolePage(browser,'warehouse','Catálogo de productos');
  const original=snapshot();
  const stock=state=>state['inventory.Lot'].filter(l=>l.product_id===fx.product_id).reduce((n,l)=>n+l.available_quantity,0);
  record('stock-inicial-20',stock(original)===20);
  const receipt=await seller.context().newPage();
  await receipt.goto(base+'/ventas/constancia/'+fx.sale_id+'/');
  const historical=await receipt.locator('#constancia-interna').innerText();
  await seller.getByRole('link',{name:'Cobrar venta →',exact:true}).click();
  await seller.locator('[name=cash_received]').fill('20.00');
  await edit(admin,'AUD03-BEBIDA');
  record('categoria-inicial',await admin.locator('[name=category]').inputValue()===fx.category_id);
  const editPath='/productos/'+fx.product_id+'/editar/';
  const validEdit=await admin.locator('form[method=post]').evaluate(form=>Object.fromEntries(new FormData(form)));
  validEdit.category=fx.category_b_id;
  for(const [role,page] of [['warehouse',warehouse],['seller',seller]]) {
    const deniedGet=await page.request.get(base+editPath);
    record(role+'-get-edicion-denegado',deniedGet.status()===403,{status:deniedGet.status()});
    const csrf=(await page.context().cookies()).find(c=>c.name.includes('csrf'));
    const deniedPost=await page.request.post(base+editPath,{form:{...validEdit,csrfmiddlewaretoken:csrf.value},headers:{Referer:base}});
    record(role+'-post-edicion-denegado',deniedPost.status()===403,{status:deniedPost.status()});
  }
  record('permisos-sin-mutacion',JSON.stringify(snapshot())===JSON.stringify(original));
  await admin.locator('[name=category]').selectOption(fx.category_b_id);
  await admin.getByRole('button',{name:'Guardar cambios',exact:true}).click();
  await admin.waitForURL(base+'/productos/');
  record('mensaje-reclasificacion',await admin.getByText('Producto «AUD03 Bebida de prueba» actualizado.',{exact:true}).isVisible());
  const moved=snapshot();
  record('ficha-solo-cambia-categoria',JSON.stringify({...row(original,fx.product_id),category_id:fx.category_b_id})===JSON.stringify(row(moved,fx.product_id)));
  for(const key of Object.keys(original).filter(k=>k!=='catalog.Product')) record('reclasificar-conserva-'+key,JSON.stringify(original[key])===JSON.stringify(moved[key]));
  record('vecino-integro',JSON.stringify(row(original,fx.empty_product_id))===JSON.stringify(row(moved,fx.empty_product_id)));
  await warehouse.reload();
  const cells=await warehouse.getByRole('row').filter({has:warehouse.getByRole('cell',{name:'AUD03-BEBIDA',exact:true})}).getByRole('cell').allInnerTexts();
  record('almacen-categoria-stock',cells.includes('Alimentos')&&cells.includes('20')&&cells.includes('Disponible'),{cells});
  await admin.screenshot({path:path.join(out,'01-reclasificado.png'),fullPage:true});
  await receipt.reload();record('historico-integro',historical===await receipt.locator('#constancia-interna').innerText());
  await seller.getByRole('button',{name:'Confirmar cobro',exact:true}).click();
  await seller.waitForURL(/\/constancia\//);
  const sold=snapshot();
  record('cobro-abierto-confirma',sold['sales.Sale'].length===2&&stock(sold)===18&&row(sold,fx.product_id).category_id===fx.category_b_id);
  await seller.screenshot({path:path.join(out,'02-cobro-confirmado.png'),fullPage:true});
  await edit(admin,'AUD03-BEBIDA');
  await admin.locator('[name=category]').selectOption(fx.category_id);
  await admin.locator('[name=sale_price]').fill('9.50');
  await admin.locator('[name=minimum_stock]').fill('11');
  const categoryRow=admin2.getByRole('row').filter({has:admin2.getByRole('cell',{name:'Higiene',exact:true})});
  await categoryRow.getByRole('button',{name:'Desactivar',exact:true}).click();
  await admin2.getByRole('button',{name:'Confirmar desactivación',exact:true}).click();
  const destinationDisabled=snapshot();
  record('destino-inactivo-antes-envio',destinationDisabled['catalog.Category'].find(c=>c.id===fx.category_id).is_active===false);
  await admin.getByRole('button',{name:'Guardar cambios',exact:true}).click();
  const errors=await admin.getByRole('alert').allInnerTexts();
  record('destino-antiguo-rechazado',errors.some(t=>t.includes('Escoja una opción válida')),{messages:errors});
  record('rechazo-atomico',JSON.stringify(snapshot())===JSON.stringify(destinationDisabled));
  record('otros-campos-retienen-intento',await admin.locator('[name=sale_price]').inputValue()==='9.50'&&await admin.locator('[name=minimum_stock]').inputValue()==='11');
  await admin.screenshot({path:path.join(out,'03-destino-inactivo.png'),fullPage:true});
  await receipt.reload();record('historico-final-integro',historical===await receipt.locator('#constancia-interna').innerText());
  write('checkpoints.json',{original,moved,sold,destinationDisabled,final:snapshot()});
 } catch(error) {report.error=error.message;process.exitCode=1;}
 finally {write('browser.json',report);await browser.close();}
 if(report.cases.some(r=>!r.ok))process.exitCode=1;
})().catch(error=>{console.error(error.message);process.exitCode=1;});
