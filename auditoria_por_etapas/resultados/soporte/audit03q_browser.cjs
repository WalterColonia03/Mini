const fs=require('fs'),path=require('path'),os=require('os'),crypto=require('crypto');
const {execFileSync}=require('child_process');
const {chromium}=require(path.join(os.homedir(),'.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright-core'));
const run=process.env.AUDIT03_RUN_DIR,out=process.env.AUDIT03_OUT,base='http://127.0.0.1:'+process.env.AUDIT03_PORT;
const creds=JSON.parse(fs.readFileSync(path.join(run,'.credentials.json'),'utf8')),fx=JSON.parse(fs.readFileSync(path.join(out,'fixture.json'),'utf8'));
const report={mode:'Chrome sequential cross-reclassification with a multiproduct draft; no concurrency claim',cases:[],posts:[]};
function record(id,ok,detail={}){report.cases.push({id,ok,...detail});if(!ok) throw Error('case-'+id);}
function snapshot(){return JSON.parse(execFileSync(process.env.AUDIT03_PYTHON,[path.join(__dirname,'audit03q_browser_run.py'),'snapshot'],{encoding:'utf8',env:{...process.env,PYTHONIOENCODING:'utf-8'}}));}
function write(n,d){fs.writeFileSync(path.join(out,n),JSON.stringify(d,null,2));}
async function role(browser,role,menu){const page=await(await browser.newContext({viewport:{width:1366,height:900},locale:'es-PE'})).newPage();await page.goto(base);await page.locator('[name=email]').fill(creds[role].email);await page.locator('[name=password]').fill(creds[role].password);await page.locator('button[type=submit]').click();await page.getByRole('link',{name:menu,exact:true}).click();page.on('request',r=>{if(r.method()==='POST')report.posts.push({role,path:new URL(r.url()).pathname});});return page;}
async function edit(p,code){if(new URL(p.url()).pathname!='/productos/')await p.getByRole('link',{name:'Productos',exact:true}).click();await p.getByRole('row').filter({has:p.getByRole('cell',{name:code,exact:true})}).getByRole('link',{name:'Editar',exact:true}).click();}
const prod=(s,id)=>s['catalog.Product'].find(x=>x.id===id), stock=(s,id)=>s['inventory.Lot'].filter(x=>x.product_id===id).reduce((a,x)=>a+x.available_quantity,0),same=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
(async()=>{const browser=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true});try{
 report.browser=browser.version();const probe=await browser.newPage(),nonce=crypto.randomBytes(32).toString('hex');const res=await probe.request.get(base,{headers:{'X-Audit03-Challenge':nonce}});record('isolation',res.headers()['x-audit03-proof']===crypto.createHmac('sha256',fs.readFileSync(path.join(run,'.django-key'))).update(nonce).digest('hex'));await probe.close();
 const a=await role(browser,'admin','Productos'),s=await role(browser,'seller','Preparar venta'),w=await role(browser,'warehouse','Catálogo de productos');
 const before=snapshot(),p=fx.product_id,q=fx.empty_product_id;
 record('initial-categories',prod(before,p).category_id===fx.category_id&&prod(before,q).category_id===fx.category_b_id);
 record('initial-stocks',stock(before,p)===20&&stock(before,q)===6);
 record('draft-two-products',before['sales.SaleDraftLine'].filter(x=>x.draft_id===before['sales.SaleDraft'].find(d=>d.status==='ACTIVE').id).length===2);
 const receipt=await s.context().newPage();await receipt.goto(base+'/ventas/constancia/'+fx.sale_id+'/');const historical=await receipt.locator('#constancia-interna').innerText();
 await s.getByRole('link',{name:'Cobrar venta →',exact:true}).click();await s.locator('[name=cash_received]').fill('30.00');
 await edit(a,'AUD03-BEBIDA');const valid=await a.locator('form[method=post]').evaluate(f=>Object.fromEntries(new FormData(f)));valid.category=fx.category_b_id;
 for(const [name,page] of [['warehouse',w],['seller',s]]){let url=base+'/productos/'+p+'/editar/';record(name+'-get-denied',(await page.request.get(url)).status()===403);const c=(await page.context().cookies()).find(c=>c.name.includes('csrf'));record(name+'-post-denied',(await page.request.post(url,{form:{...valid,csrfmiddlewaretoken:c.value},headers:{Referer:base}})).status()===403);}
 record('denials-no-change',same(snapshot(),before));
 await a.locator('[name=category]').selectOption(fx.category_b_id);await a.getByRole('button',{name:'Guardar cambios',exact:true}).click();await a.waitForURL(base+'/productos/');
 await edit(a,'AUD03-EMPTY');await a.locator('[name=category]').selectOption(fx.category_id);await a.getByRole('button',{name:'Guardar cambios',exact:true}).click();await a.waitForURL(base+'/productos/');
 const moved=snapshot();record('cross-moved',same({...prod(before,p),category_id:fx.category_b_id},prod(moved,p))&&same({...prod(before,q),category_id:fx.category_id},prod(moved,q)));
 for(const key of Object.keys(before).filter(k=>!['catalog.Product'].includes(k)))record('preserve-'+key,same(before[key],moved[key]));
 await w.reload();for(const [code,cat,n] of [['AUD03-BEBIDA','Alimentos','20'],['AUD03-EMPTY','Higiene','6']]){let cells=await w.getByRole('row').filter({has:w.getByRole('cell',{name:code,exact:true})}).getByRole('cell').allInnerTexts();record('warehouse-'+code,cells.includes(cat)&&cells.some(c=>c===n||c.startsWith(n+' '))&&cells.includes('Disponible'),{cells});}
 await w.screenshot({path:path.join(out,'01-crossed.png'),fullPage:true});await receipt.reload();record('receipt-preserved-before-sale',historical===await receipt.locator('#constancia-interna').innerText());
 await s.getByRole('button',{name:'Confirmar cobro',exact:true}).click();await s.waitForURL(/\/constancia\//);
 const sold=snapshot();record('one-new-sale',sold['sales.Sale'].length===before['sales.Sale'].length+1);record('stock-after',stock(sold,p)===18&&stock(sold,q)===5);record('categories-after',prod(sold,p).category_id===fx.category_b_id&&prod(sold,q).category_id===fx.category_id);record('new-sale-two-lines',sold['sales.SaleLine'].length===before['sales.SaleLine'].length+2);await receipt.reload();record('receipt-preserved-after-sale',historical===await receipt.locator('#constancia-interna').innerText());
 await s.screenshot({path:path.join(out,'02-receipt.png'),fullPage:true});write('checkpoints.json',{before,moved,sold});
 }catch(e){report.error=e.message;process.exitCode=1;}finally{write('browser.json',report);await browser.close();}})().catch(e=>{console.error(e.message);process.exitCode=1});
