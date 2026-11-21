// Characterization in real Chrome. Text is automated; no physical scan claimed.
const fs=require('fs'),path=require('path'),os=require('os'),crypto=require('crypto');
const {execFileSync}=require('child_process');
const {chromium}=require(path.join(os.homedir(),'.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright-core'));
const out=process.env.AUDIT03_OUT,run=process.env.AUDIT03_RUN_DIR,base='http://127.0.0.1:'+process.env.AUDIT03_PORT;
const E='0012345678905',U='012345678905',report={mode:'Chrome headless, automated input; not physical',cases:[],searches:[]};
const creds=JSON.parse(fs.readFileSync(path.join(run,'.credentials.json'),'utf8'));
function invoke(action){return execFileSync(process.env.AUDIT03_PYTHON,[path.join(__dirname,'audit03y_browser_run.py'),action],{encoding:'utf8',env:{...process.env,PYTHONIOENCODING:'utf-8'}});}
const snapshot=()=>JSON.parse(invoke('snapshot')),same=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
function check(id,ok,detail={}){report.cases.push({id,ok:!!ok,...detail});if(!ok)throw Error(id);}
async function role(browser,key,menu){const page=await(await browser.newContext({locale:'es-PE',viewport:{width:1366,height:900}})).newPage();await page.goto(base);await page.locator('[name=email]').fill(creds[key].email);await page.locator('[name=password]').fill(creds[key].password);await page.locator('button[type=submit]').click();await page.getByRole('link',{name:menu,exact:true}).click();return page;}
async function scan(page,code,duplicate){await page.getByRole('button',{name:'Escanear código',exact:true}).click();await page.locator('#barcode-capture-input').fill(code);const message=duplicate?'El código de barras ya está registrado':'Sin duplicados en esta consulta.';await page.locator('#barcode-capture-status').filter({hasText:message}).waitFor();check('capture-'+code+'-'+duplicate,(await page.locator('#barcode-capture-apply').isDisabled())===duplicate,{message:await page.locator('#barcode-capture-status').innerText()});}
async function search(page,role,code,expected){await page.locator(role==='seller'?'[name=query]':'[name=q]').fill(code);await page.getByRole('button',{name:'Buscar',exact:true}).click();const found=[];for(const value of [E,U])if(await page.getByRole('cell',{name:value,exact:true}).count())found.push(value);report.searches.push({role,query:code,found});check(role+'-search-'+code,same(found,expected));check(role+'-query-retained-'+code,await page.locator(role==='seller'?'[name=query]':'[name=q]').inputValue()===code);}
(async()=>{const browser=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true});let a;try{
report.browser=browser.version();const probe=await browser.newPage(),nonce=crypto.randomBytes(32).toString('hex');const response=await probe.request.get(base,{headers:{'X-Audit03-Challenge':nonce}});check('isolation',response.headers()['x-audit03-proof']===crypto.createHmac('sha256',fs.readFileSync(path.join(run,'.django-key'))).update(nonce).digest('hex'));await probe.close();
a=await role(browser,'admin','Registrar producto');
const type=a.locator('[name=barcode_type]'),code=a.locator('[name=barcode]');
const create=async()=>{await a.getByRole('button',{name:'Registrar producto',exact:true}).click();};
const fill=async(name,kind,value)=>{await a.locator('[name=name]').fill(name);await type.selectOption(kind);await code.fill(value);await a.locator('[name=category]').selectOption({label:'Higiene'});await a.locator('[name=sale_price]').fill('3.00');};
check('tipo-explicito',await type.inputValue()==='');await fill('GTIN Y','GTIN',E);await create();await a.waitForURL(/registrado/);
const seeded=JSON.parse(invoke('stock-history')),before=snapshot();check('tres-claves-un-uuid',before['catalog.ProductBarcodeKey'].length===3&&before['catalog.ProductBarcodeKey'].every(k=>k.product_id===seeded.product_id));
await a.getByRole('link',{name:'Registrar producto',exact:true}).first().click();
for(const [kind,value] of [['GTIN',U],['INTERNAL','00012345678905']]){
 await fill('Intento '+kind,kind,value);await scan(a,value,true);await a.screenshot({path:path.join(out,'duplicado-'+kind+'.png')});await a.locator('#barcode-capture-cancel').click();await create();check('rechazo-'+kind,(await a.locator('main').innerText()).includes('Ya existe un producto con este código de barras.'));check('sin-cambio-'+kind,same(before,snapshot()));
}
for (const copies of [2, 3]) {
 const joined = U.repeat(copies);
 await fill('Relectura GTIN', 'GTIN', joined);
 await a.getByRole('button', {name:'Escanear código', exact:true}).click();
 await a.locator('#barcode-capture-input').fill(joined);
 await a.locator('#barcode-capture-status').filter({hasText:'Ingrese un GTIN'}).waitFor();
 check('relectura-dialogo-'+copies, await a.locator('#barcode-capture-apply').isDisabled());
 await a.locator('#barcode-capture-cancel').click();
 await create();
 check('relectura-rechazada-'+copies, (await a.getByRole('alert').allInnerTexts()).join(' ').includes('Ingrese un GTIN'));
 check('relectura-sin-cambios-'+copies, same(before, snapshot()));
}
await fill('Interno Y','GTIN','0012345678906');await create();check('digito-invalido', (await a.getByRole('alert').allInnerTexts()).join(' ').includes('control válido'));await type.selectOption('INTERNAL');await create();await a.waitForURL(/registrado/);
check('interno-asignado',snapshot().identity.some(p=>p.barcode_type==='INTERNAL'));
await a.getByRole('link',{name:'Productos',exact:true}).click();await a.getByRole('row').filter({has:a.getByRole('cell',{name:E,exact:true})}).getByRole('link',{name:'Editar'}).click();await scan(a,U,false);await a.locator('#barcode-capture-apply').click();await a.getByRole('button',{name:'Guardar cambios'}).click();await a.waitForURL(base+'/productos/');const edited=snapshot();check('mismo-uuid',edited['catalog.Product'].find(p=>p.id===seeded.product_id).barcode===U);check('historico-conservado',same(before['sales.SaleLine'],edited['sales.SaleLine']));
for(const [key,menu] of [['warehouse','Catálogo de productos'],['seller','Preparar venta']]){
 const page=await role(browser,key,menu);
 for(const value of [U,E,'00012345678905','GTIN Y']){await search(page,key,value,[U]);const row=page.getByRole('row').filter({has:page.getByRole('cell',{name:U,exact:true})});check('stock-'+key+'-'+value,/\b6\b/.test(await row.innerText()));}
 check('consulta-gestion-denegada-'+key,(await page.request.get(base+'/productos/codigos/comprobar/?barcode='+U)).status()===403);
}
check('consulta-sin-efectos',same(edited,snapshot()));
}catch(error){report.error=error.message;process.exitCode=1;if(a)await a.screenshot({path:path.join(out,'failure.png'),fullPage:true}).catch(()=>{});}finally{fs.writeFileSync(path.join(out,'browser.json'),JSON.stringify(report,null,2));await browser.close();}})().catch(e=>{console.error(e.message);process.exitCode=1;});

