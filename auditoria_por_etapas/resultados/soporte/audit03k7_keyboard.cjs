// Real Chrome/HTTP/ORM, keyboard emulation only: this is NOT a physical phone scan.
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
const report = {mode:'Chrome keyboard emulation, no physical phone',cases:[],findings:[],posts:[]};
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
  const initial=snapshot();
  const admin=await rolePage(browser,'admin','Registrar producto');
  const warehouse=await rolePage(browser,'warehouse','Catálogo de productos');
  const seller=await rolePage(browser,'seller','Preparar venta');
  const receipt=await seller.context().newPage();
  await receipt.goto(base+'/ventas/constancia/'+fx.sale_id+'/');
  const historical=await receipt.locator('#constancia-interna').innerText();
  await admin.locator('[name=name]').fill('AUD03 K7 ficha nueva');
  await admin.locator('[name=category]').selectOption({label:'Higiene'});
  await admin.locator('[name=sale_price]').fill('8.50');
  await admin.locator('[name=barcode]').focus();
  const noPost=report.posts.length;
  for(const [i,code] of [A,B,A,B,B].entries()) {
    await profile(admin,code);
    record('K7-ALTA-'+i,await admin.locator('[name=barcode]').inputValue()===code && report.posts.length===noPost,{code});
  }
  record('K7-ALTA-SIN-PERSISTIR',JSON.stringify(initial)===JSON.stringify(snapshot()));
  await admin.screenshot({path:path.join(out,'01-alta-dos-codigos.png'),fullPage:true});
  await save(admin,'Registrar producto');await admin.waitForURL(/\/registrado\/$/);
  const saved=snapshot(),created=products(saved).find(p=>p.barcode===B);
  record('K7-ALTA-GUARDADA',!!created && products(saved).length===products(initial).length+1);
  await admin.getByRole('link',{name:'Productos',exact:true}).click();
  await edit(admin,'AUD03-BEBIDA');
  const beforeEdit=snapshot(),noEditPost=report.posts.length;
  await admin.locator('[name=barcode]').focus();
  for(const [i,code] of [A,C,A].entries()) {
    await profile(admin,code);record('K7-EDIT-'+i,await admin.locator('[name=barcode]').inputValue()===code && report.posts.length===noEditPost,{code});
  }
  record('K7-EDIT-SIN-PERSISTIR',JSON.stringify(beforeEdit)===JSON.stringify(snapshot()));
  await save(admin,'Guardar cambios');await admin.waitForURL(base+'/productos/');
  record('K7-EDIT-UUID',row(snapshot(),fx.product_id).barcode===A);
  await edit(admin,A);
  await admin.locator('[name=barcode]').focus();await profile(admin,B);
  const beforeDuplicate=snapshot();
  await save(admin,'Guardar cambios');
  const error='Ya existe un producto con este código de barras.';
  record('K7-DUPLICADO-EDICION',await admin.getByText(error,{exact:true}).count()===1 && JSON.stringify(beforeDuplicate)===JSON.stringify(snapshot()));
  await admin.screenshot({path:path.join(out,'02-duplicado-rechazado.png'),fullPage:true});
  // Manual replacement remains a supported input; do not deduplicate substrings.
  await admin.locator('[name=barcode]').fill(C);
  await save(admin,'Guardar cambios');await admin.waitForURL(base+'/productos/');
  record('K7-MANUAL',row(snapshot(),fx.product_id).barcode===C);
  // Wrong focus is a separate observed safety finding, never an approved test.
  await edit(admin,C);const correctName=await admin.locator('[name=name]').inputValue();
  await admin.locator('[name=name]').focus();await profile(admin,A);
  const wrongFocus=await formValues(admin);
  report.findings.push({id:'K7-FOCO',status:'INCUMPLE objetivo de evitar sustitucion en otro campo',priorName:correctName,observedName:wrongFocus.name,barcode:wrongFocus.barcode,persisted:false,explanation:'Global Ctrl+A + BARCODE targets focused name; no save performed.'});
  record('K7-FOCO-REPRODUCIDO',wrongFocus.name===A && wrongFocus.barcode===C);
  await admin.screenshot({path:path.join(out,'03-foco-equivocado.png'),fullPage:true});
  await admin.getByRole('link',{name:'Cancelar',exact:true}).click();
  // Autofocus case: read immediately after opening the edit screen, without clicking any field.
  await edit(admin,C);
  const focusedOnOpen=await admin.evaluate(()=>document.activeElement&&document.activeElement.name);
  await profile(admin,A);
  const onOpen=await formValues(admin);
  report.findings.push({id:'K7-FOCO-AL-ABRIR',status:onOpen.name===A?'RIESGO REPRODUCIDO':'NO REPRODUCIDO',focusedOnOpen,observedName:onOpen.name,barcode:onOpen.barcode,persisted:false});
  record('K7-FOCO-AL-ABRIR-OBSERVADO',focusedOnOpen==='name'&&onOpen.name===A&&onOpen.barcode===C,{focusedOnOpen});
  await admin.getByRole('link',{name:'Cancelar',exact:true}).click();
  record('K7-FOCO-SIN-PERSISTIR',row(snapshot(),fx.product_id).name==='AUD03 Bebida de prueba');
  // Two distinct ADMIN accounts load the same version, then submit sequentially.
  const second=await rolePage(browser,'admin2','Productos');
  await edit(admin,C);await edit(second,C);
  await admin.locator('[name=sale_price]').fill('9.20');
  await save(admin,'Guardar cambios');await admin.waitForURL(base+'/productos/');
  const afterFirst=snapshot();
  await second.locator('[name=minimum_stock]').fill('17');
  await save(second,'Guardar cambios');
  const staleState=snapshot(),product=row(staleState,fx.product_id);
  const alerts=await second.getByRole('alert').allTextContents();
  const staleBlocked=new URL(second.url()).pathname.endsWith('/editar/') && product.sale_price==='9.20' && product.minimum_stock===10
    && alerts.some(t=>t.includes('El producto cambió desde que abrió esta pantalla.'));
  report.findings.push({id:'K7-PANTALLA-ANTIGUA',status:staleBlocked?'CUMPLE muestra':'INCUMPLE',firstSavedPrice:row(afterFirst,fx.product_id).sale_price,stalePostedPrice:'8.50',observedPrice:product.sale_price,observedMinimum:product.minimum_stock,message:alerts});
  record('K7-PANTALLA-ANTIGUA-RECHAZADA',staleBlocked);
  await second.screenshot({path:path.join(out,'04-segundo-admin.png'),fullPage:true});
  // Recovery: reopen the current version, re-apply only the intended change and save.
  await second.getByRole('link',{name:'Revisar ficha actual',exact:true}).click();
  const reopened=await formValues(second);
  record('K7-REABRIR-VERSION-ACTUAL',reopened.sale_price==='9.20'&&reopened.minimum_stock==='10',{reopened});
  await second.locator('[name=minimum_stock]').fill('17');
  await save(second,'Guardar cambios');await second.waitForURL(base+'/productos/');
  const recovered=row(snapshot(),fx.product_id);
  record('K7-RECUPERACION-SIN-PERDIDA',recovered.sale_price==='9.20'&&recovered.minimum_stock===17);
  // Double click on save: both requests carry the same version and identical values.
  await edit(admin,C);await admin.locator('[name=minimum_stock]').fill('18');
  const beforeDouble=report.posts.length;
  await admin.getByRole('button',{name:'Guardar cambios',exact:true}).dblclick();
  await admin.waitForURL(base+'/productos/');await admin.waitForLoadState('networkidle');
  const doubled=row(snapshot(),fx.product_id);
  const doubleAlerts=await admin.getByRole('alert').allTextContents();
  record('K7-DOBLE-CLIC',doubled.minimum_stock===18&&doubled.sale_price==='9.20'&&!doubleAlerts.some(t=>t.includes('cambió')),{posts:report.posts.length-beforeDouble,alerts:doubleAlerts});
  await admin.screenshot({path:path.join(out,'05-doble-clic.png'),fullPage:true});
  const current=row(snapshot(),fx.product_id);
  await warehouse.reload();const wh=warehouse.getByRole('row').filter({has:warehouse.getByRole('cell',{name:C,exact:true})});
  const cells=await wh.getByRole('cell').allInnerTexts();
  const whChecks={name:cells[0]===current.name,code:cells[2]===C,price:cells[3].replace(',','.')===current.sale_price,minimum:Number(cells[5])===current.minimum_stock,noEdit:(await wh.getByRole('link',{name:'Editar',exact:true}).count())===0};
  record('K7-ALMACEN',Object.values(whChecks).every(Boolean),{cells,checks:whChecks});
  await seller.locator('[name=query]').fill(C);await seller.getByRole('button',{name:'Buscar',exact:true}).click();
  const saleRow=seller.getByRole('row').filter({has:seller.getByRole('cell',{name:C,exact:true})});
  const saleCells=await saleRow.getByRole('cell').allInnerTexts();
  record('K7-VENTA-CONSULTA',await saleRow.getByRole('button',{name:'Agregar',exact:true}).count()===1&&saleCells.some(t=>t.includes('9,20')),{cells:saleCells});
  await receipt.reload();record('K7-CONSTANCIA',historical===await receipt.locator('#constancia-interna').innerText());
  const final=snapshot();
  for(const key of Object.keys(initial).filter(k=>!['catalog.Product','commerce'].includes(k)))record('K7-INMUTABLE-'+key,JSON.stringify(initial[key])===JSON.stringify(final[key]),{rows:initial[key].length});
  write('orm-checkpoints.json',{beforeEdit,beforeDuplicate,afterFirst,staleState});
 } catch(error) {report.error=error.message;process.exitCode=1;}
 finally {write('keyboard.json',report);await browser.close();}
 if(report.cases.some(row=>!row.ok))process.exitCode=1;
})().catch(error=>{console.error(error.message);process.exitCode=1;});
