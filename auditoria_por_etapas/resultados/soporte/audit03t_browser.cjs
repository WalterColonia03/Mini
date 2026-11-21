const fs=require('fs'),path=require('path'),os=require('os'),crypto=require('crypto');
const {execFileSync}=require('child_process');
const {chromium}=require(path.join(os.homedir(),'.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright-core'));
const run=process.env.AUDIT03_RUN_DIR,out=process.env.AUDIT03_OUT,base='http://127.0.0.1:'+process.env.AUDIT03_PORT;
const creds=JSON.parse(fs.readFileSync(path.join(run,'.credentials.json'),'utf8')),fx=JSON.parse(fs.readFileSync(path.join(out,'fixture.json'),'utf8'));
const report={mode:'03-T sequential Chrome product rename/recode between visible checkout and submit, not concurrency',cases:[],posts:[]};
function record(id,ok,detail={}){report.cases.push({id,ok,...detail});if(!ok)throw Error('case-'+id)}
function snapshot(){return JSON.parse(execFileSync(process.env.AUDIT03_PYTHON,[path.join(__dirname,'audit03t_browser_run.py'),'snapshot'],{encoding:'utf8',env:{...process.env,PYTHONIOENCODING:'utf-8'}}));}
function write(n,d){fs.writeFileSync(path.join(out,n),JSON.stringify(d,null,2));}
async function role(browser,role,menu){const page=await(await browser.newContext({viewport:{width:1366,height:900},locale:'es-PE'})).newPage();await page.goto(base);await page.locator('[name=email]').fill(creds[role].email);await page.locator('[name=password]').fill(creds[role].password);await page.locator('button[type=submit]').click();await page.getByRole('link',{name:menu,exact:true}).click();page.on('request',r=>{if(r.method()==='POST')report.posts.push({role,path:new URL(r.url()).pathname});});return page;}
const prod=(s,id)=>s['catalog.Product'].find(x=>x.id===id),stock=(s,id)=>s['inventory.Lot'].filter(x=>x.product_id===id).reduce((a,x)=>a+x.available_quantity,0),same=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
(async()=>{const browser=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true});try{
 report.browser=browser.version();const probe=await browser.newPage(),nonce=crypto.randomBytes(32).toString('hex');const res=await probe.request.get(base,{headers:{'X-Audit03-Challenge':nonce}});record('isolation',res.headers()['x-audit03-proof']===crypto.createHmac('sha256',fs.readFileSync(path.join(run,'.django-key'))).update(nonce).digest('hex'));await probe.close();
 const a=await role(browser,'admin','Productos'),s=await role(browser,'seller','Preparar venta'),w=await role(browser,'warehouse','Catálogo de productos');
 const before=snapshot(),p=fx.product_id,q=fx.empty_product_id;const original=prod(before,p),draft=before['sales.SaleDraft'].find(d=>d.status==='ACTIVE');
 record('fixture-two-products',stock(before,p)===20&&stock(before,q)===6&&before['sales.SaleDraftLine'].filter(l=>l.draft_id===draft.id).length===2);
 const receipt=await s.context().newPage();await receipt.goto(base+'/ventas/constancia/'+fx.sale_id+'/');const historical=await receipt.locator('#constancia-interna').innerText();
 await s.getByRole('link',{name:'Cobrar venta →',exact:true}).click();await s.locator('[name=cash_received]').fill('50.00');
 const initialSignature=await s.locator('[name=draft_signature]').inputValue(),initialSubtotal=await s.locator('[name=expected_subtotal]').inputValue();
 record('seller-sees-original-name',(await s.locator('main').innerText()).includes(original.name));
 await a.getByRole('row').filter({has:a.getByRole('cell',{name:original.barcode,exact:true})}).getByRole('link',{name:'Editar',exact:true}).click();
 const valid=await a.locator('form[method=post]').evaluate(f=>Object.fromEntries(new FormData(f)));valid.name='AUD03 T Bebida nueva';valid.barcode='AUD03-T-NUEVO';
 for(const [name,page] of [['warehouse',w],['seller',s]]){const csrf=(await page.context().cookies()).find(c=>c.name==='audit03k_csrftoken')?.value;record(name+'-csrf',!!csrf);const endpoint=base+'/productos/'+p+'/editar/';record(name+'-get-denied',(await page.request.get(endpoint)).status()===403);record(name+'-post-denied',(await page.request.post(endpoint,{form:{...valid,csrfmiddlewaretoken:csrf},headers:{Referer:base+'/productos/'}})).status()===403);}
 record('denials-no-changes',same(snapshot(),before));
 await a.locator('[name=name]').fill(valid.name);await a.locator('[name=barcode]').fill(valid.barcode);await a.getByRole('button',{name:'Guardar cambios',exact:true}).click();await a.waitForURL(base+'/productos/');
 const edited=snapshot();record('admin-changes-name-code',prod(edited,p).name===valid.name&&prod(edited,p).barcode===valid.barcode&&prod(edited,p).sale_price===original.sale_price&&prod(edited,p).category_id===original.category_id);
 for(const key of ['inventory.Lot','sales.Sale','sales.SaleLine','sales.SaleDraft','sales.SaleDraftLine','cash.CashShift'])record('edit-preserves-'+key,same(before[key],edited[key]));
 await w.reload();const row=w.getByRole('row').filter({has:w.getByRole('cell',{name:valid.barcode,exact:true})});record('warehouse-sees-name-code-stock',(await row.innerText()).includes(valid.name)&&(await row.innerText()).includes('20'));
 await receipt.reload();record('history-before-checkout',historical===await receipt.locator('#constancia-interna').innerText());
 await s.getByRole('button',{name:'Confirmar cobro',exact:true}).click();await s.waitForLoadState('networkidle');const warned=snapshot(),main=await s.locator('main').innerText();
 record('stale-summary-rejected',main.includes('El resumen de la venta en preparación cambió')&&same(edited,warned));
 record('updated-name-shown',main.includes(valid.name));record('subtotal-same',Number(await s.locator('[name=expected_subtotal]').inputValue())===Number(initialSubtotal));record('signature-changed',(await s.locator('[name=draft_signature]').inputValue())!==initialSignature);
 await s.screenshot({path:path.join(out,'01-resumen-actualizado.png'),fullPage:true});
 await s.locator('[name=cash_received]').fill('50.00');await s.getByRole('button',{name:'Confirmar cobro',exact:true}).click();await s.waitForURL(/\/constancia\//);
 const sold=snapshot(),newSales=sold['sales.Sale'].filter(x=>!before['sales.Sale'].some(y=>y.id===x.id)),lines=sold['sales.SaleLine'].filter(x=>!before['sales.SaleLine'].some(y=>y.id===x.id));
 record('one-explicit-sale',newSales.length===1&&Number(newSales[0].total_amount)===Number(initialSubtotal));record('snapshot-current-name-code',lines.length===2&&lines.some(l=>l.product_id===p&&l.product_snapshot_name===valid.name&&l.product_snapshot_barcode===valid.barcode&&l.quantity===2));
 record('stock-once',stock(sold,p)===18&&stock(sold,q)===5);record('history-line-preserved',before['sales.SaleLine'].every(x=>same(x,sold['sales.SaleLine'].find(y=>y.id===x.id))));await receipt.reload();record('history-receipt-after',historical===await receipt.locator('#constancia-interna').innerText());
 await s.screenshot({path:path.join(out,'02-constancia-actual.png'),fullPage:true});write('checkpoints.json',{before,edited,warned,sold});
 }catch(e){report.error=e.message;process.exitCode=1;}finally{write('browser.json',report);await browser.close();}})().catch(e=>{console.error(e.message);process.exitCode=1});
