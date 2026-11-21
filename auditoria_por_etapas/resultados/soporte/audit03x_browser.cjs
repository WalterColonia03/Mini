// Characterization in real Chrome. Text is automated; no physical scan claimed.
const fs=require('fs'),path=require('path'),os=require('os'),crypto=require('crypto');
const {execFileSync}=require('child_process');
const {chromium}=require(path.join(os.homedir(),'.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright-core'));
const out=process.env.AUDIT03_OUT,run=process.env.AUDIT03_RUN_DIR,base='http://127.0.0.1:'+process.env.AUDIT03_PORT;
const E='0012345678905',U='012345678905',report={mode:'Chrome headless, automated input; not physical',cases:[],searches:[]};
const creds=JSON.parse(fs.readFileSync(path.join(run,'.credentials.json'),'utf8'));
function invoke(action){return execFileSync(process.env.AUDIT03_PYTHON,[path.join(__dirname,'audit03x_run.py'),action],{encoding:'utf8',env:{...process.env,PYTHONIOENCODING:'utf-8'}});}
const snapshot=()=>JSON.parse(invoke('snapshot')),same=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
function check(id,ok,detail={}){report.cases.push({id,ok:!!ok,...detail});if(!ok)throw Error(id);}
async function role(browser,key,menu){const page=await(await browser.newContext({locale:'es-PE',viewport:{width:1366,height:900}})).newPage();await page.goto(base);await page.locator('[name=email]').fill(creds[key].email);await page.locator('[name=password]').fill(creds[key].password);await page.locator('button[type=submit]').click();await page.getByRole('link',{name:menu,exact:true}).click();return page;}
async function scan(page,code,duplicate){await page.getByRole('button',{name:'Escanear código',exact:true}).click();await page.locator('#barcode-capture-input').fill(code);const message=duplicate?'El código de barras ya está registrado':'Sin duplicados en esta consulta.';await page.locator('#barcode-capture-status').filter({hasText:message}).waitFor();check('capture-'+code+'-'+duplicate,(await page.locator('#barcode-capture-apply').isDisabled())===duplicate,{message:await page.locator('#barcode-capture-status').innerText()});}
async function search(page,role,code,expected){await page.locator(role==='seller'?'[name=query]':'[name=q]').fill(code);await page.getByRole('button',{name:'Buscar',exact:true}).click();const found=[];for(const value of [E,U])if(await page.getByRole('cell',{name:value,exact:true}).count())found.push(value);report.searches.push({role,query:code,found});check(role+'-search-'+code,same(found,expected));check(role+'-query-retained-'+code,await page.locator(role==='seller'?'[name=query]':'[name=q]').inputValue()===code);}
(async()=>{const browser=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true});let a;try{
report.browser=browser.version();const probe=await browser.newPage(),nonce=crypto.randomBytes(32).toString('hex');const response=await probe.request.get(base,{headers:{'X-Audit03-Challenge':nonce}});check('isolation',response.headers()['x-audit03-proof']===crypto.createHmac('sha256',fs.readFileSync(path.join(run,'.django-key'))).update(nonce).digest('hex'));await probe.close();
a=await role(browser,'admin','Registrar producto');
const initial=snapshot();check('empty-products',initial['catalog.Product'].length===0);
for(const [i,code] of [E,U].entries()){
 if(i)await a.getByRole('link',{name:'Registrar producto',exact:true}).first().click();
 await a.locator('[name=name]').fill('AUD03 X '+(i?'UPC':'EAN'));await a.locator('[name=category]').selectOption({label:'Higiene'});await a.locator('[name=sale_price]').fill(i?'4.50':'3.00');
 const before=snapshot();await scan(a,code,false);check('capture-not-save-'+code,same(before,snapshot())&&await a.locator('[name=barcode]').inputValue()==='');
 await a.locator('#barcode-capture-apply').click();check('copy-exact-'+code,await a.locator('[name=barcode]').inputValue()===code);await a.getByRole('button',{name:'Registrar producto',exact:true}).click();await a.waitForURL(/\/registrado\/$/);
 check('persist-'+code,snapshot()['catalog.Product'].filter(p=>p.barcode===code).length===1);
}
const created=snapshot();check('distinct-keys',created.commerce.some(p=>p.barcode_normalized===E)&&created.commerce.some(p=>p.barcode_normalized===U));
await a.getByRole('link',{name:'Registrar producto',exact:true}).first().click();
for(const code of [E,U,'00 12345678905',' 012345678905 ']){
 await scan(a,code,true);await a.locator('#barcode-capture-cancel').click();
 await a.locator('[name=name]').fill('AUD03 X duplicado');await a.locator('[name=category]').selectOption({label:'Higiene'});await a.locator('[name=sale_price]').fill('5.00');await a.locator('[name=barcode]').fill(code);
 await a.getByRole('button',{name:'Registrar producto',exact:true}).click();check('server-duplicate-'+code,await a.getByText('Ya existe un producto con este código de barras.',{exact:true}).isVisible());check('reject-unchanged-'+code,same(created,snapshot()));
}
await a.getByRole('link',{name:'Productos',exact:true}).click();const eId=created['catalog.Product'].find(p=>p.barcode===E).id;
await a.getByRole('row').filter({has:a.getByRole('cell',{name:E,exact:true})}).getByRole('link',{name:'Editar',exact:true}).click();
await scan(a,E,false);await a.locator('#barcode-capture-cancel').click();await scan(a,U,true);await a.locator('#barcode-capture-cancel').click();await a.locator('[name=barcode]').fill(U);await a.getByRole('button',{name:'Guardar cambios',exact:true}).click();check('edit-collision-message',await a.getByText('Ya existe un producto con este código de barras.',{exact:true}).isVisible());check('edit-collision-unchanged',same(created,snapshot()));
const w=await role(browser,'warehouse','Catálogo de productos'),s=await role(browser,'seller','Preparar venta');
check('warehouse-no-management',await w.getByRole('link',{name:'Editar',exact:true}).count()===0);
await search(s,'seller',E,[]);await search(s,'seller',U,[]);
invoke('stock');const stocked=snapshot();check('stock-fixture-only',stocked['inventory.Lot'].length===2&&stocked['sales.Sale'].length===0);
await a.getByRole('link',{name:'Productos',exact:true}).click();
for(const [key,p] of [['admin',a],['warehouse',w],['seller',s]]){
 await search(p,key,E,[E]);await search(p,key,U,key==='seller'?[U]:[E,U]);await search(p,key,'00 12345678905',[E]);
 await p.screenshot({path:path.join(out,key+'-search.png'),fullPage:true});
}
for(const [key,p] of [['warehouse',w],['seller',s]]){
 const csrf=(await p.context().cookies()).find(c=>c.name==='audit03k_csrftoken')?.value;check(key+'-csrf',!!csrf);
 for(const endpoint of ['/productos/nuevo/','/productos/'+eId+'/editar/','/productos/codigos/comprobar/?barcode='+E]){
  check(key+'-GET-'+endpoint,(await p.request.get(base+endpoint)).status()===403);
 }
 for(const endpoint of ['/productos/nuevo/','/productos/'+eId+'/editar/']){
  const r=await p.request.post(base+endpoint,{form:{name:'AUD03 X intruso',barcode:'00-X-INTRUSO',category:created['catalog.Product'][0].category_id,unit:'UND',sale_price:'1.00',minimum_stock:'0',csrfmiddlewaretoken:csrf},headers:{Referer:base+endpoint}});check(key+'-POST-'+endpoint,r.status()===403);
 }
}
check('seller-catalog-denied',(await s.request.get(base+'/productos/')).status()===403);
const guest=await browser.newContext();for(const endpoint of ['/productos/nuevo/','/productos/codigos/comprobar/?barcode='+E]){const r=await guest.request.get(base+endpoint,{maxRedirects:0});check('guest-redirect-'+endpoint,r.status()===302);}
check('consultations-and-denials-preserved',same(stocked,snapshot()));
report.service=JSON.parse(invoke('service-checks'));check('service-all',report.service.every(c=>c.ok));check('final-preserved',same(stocked,snapshot()));
fs.writeFileSync(path.join(out,'checkpoints.json'),JSON.stringify({initial,created,stocked},null,2));
}catch(error){report.error=error.message;process.exitCode=1;if(a)await a.screenshot({path:path.join(out,'failure.png'),fullPage:true}).catch(()=>{});}finally{fs.writeFileSync(path.join(out,'browser.json'),JSON.stringify(report,null,2));await browser.close();}})().catch(e=>{console.error(e.message);process.exitCode=1;});

