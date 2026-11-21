const fs=require('fs'),path=require('path'),os=require('os'),crypto=require('crypto');
const {execFileSync}=require('child_process');
const {chromium}=require(path.join(os.homedir(),'.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright-core'));
const run=process.env.AUDIT03_RUN_DIR,out=process.env.AUDIT03_OUT,base='http://127.0.0.1:'+process.env.AUDIT03_PORT;
const creds=JSON.parse(fs.readFileSync(path.join(run,'.credentials.json'),'utf8')),fx=JSON.parse(fs.readFileSync(path.join(out,'fixture.json'),'utf8'));
const report={mode:'Chrome sequential cross-reclassification with a multiproduct draft; no concurrency claim',cases:[],posts:[]};
function record(id,ok,detail={}){report.cases.push({id,ok,...detail});if(!ok) throw Error('case-'+id);}
function snapshot(){return JSON.parse(execFileSync(process.env.AUDIT03_PYTHON,[path.join(__dirname,'audit03r_altered_run.py'),'snapshot'],{encoding:'utf8',env:{...process.env,PYTHONIOENCODING:'utf-8'}}));}
function write(n,d){fs.writeFileSync(path.join(out,n),JSON.stringify(d,null,2));}
async function role(browser,role,menu){const page=await(await browser.newContext({viewport:{width:1366,height:900},locale:'es-PE'})).newPage();await page.goto(base);await page.locator('[name=email]').fill(creds[role].email);await page.locator('[name=password]').fill(creds[role].password);await page.locator('button[type=submit]').click();await page.getByRole('link',{name:menu,exact:true}).click();page.on('request',r=>{if(r.method()==='POST')report.posts.push({role,path:new URL(r.url()).pathname});});return page;}
async function edit(p,code){if(new URL(p.url()).pathname!='/productos/')await p.getByRole('link',{name:'Productos',exact:true}).click();await p.getByRole('row').filter({has:p.getByRole('cell',{name:code,exact:true})}).getByRole('link',{name:'Editar',exact:true}).click();}
const prod=(s,id)=>s['catalog.Product'].find(x=>x.id===id), stock=(s,id)=>s['inventory.Lot'].filter(x=>x.product_id===id).reduce((a,x)=>a+x.available_quantity,0),same=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
(async()=>{const browser=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true});try{
 report.mode='Valid CSRF direct POST from an obsolete checkout with hidden inputs omitted';
 const probe=await browser.newPage(),nonce=crypto.randomBytes(32).toString('hex');const res=await probe.request.get(base,{headers:{'X-Audit03-Challenge':nonce}});record('isolation',res.headers()['x-audit03-proof']===crypto.createHmac('sha256',fs.readFileSync(path.join(run,'.django-key'))).update(nonce).digest('hex'));await probe.close();
 const s=await role(browser,'seller','Preparar venta');const before=snapshot(),p=fx.product_id,q=fx.empty_product_id;
 const draft=before['sales.SaleDraft'].find(d=>d.status==='ACTIVE'),line=before['sales.SaleDraftLine'].find(l=>l.draft_id===draft.id&&l.product_id===p);
 await s.getByRole('link',{name:'Cobrar venta →',exact:true}).click();
 const form=await s.locator('form[method=post]').evaluate(f=>Object.fromEntries(new FormData(f)));form.cash_received='50.00';
 const tab=await s.context().newPage();await tab.goto(base+'/ventas/');const f=tab.locator('form.draft-line-actions').filter({has:tab.locator('input[id="draft-quantity-'+line.id+'"]')});await f.locator('[name=quantity]').fill('3');await f.getByRole('button',{name:'Actualizar',exact:true}).click();await tab.waitForLoadState('networkidle');
 const changed=snapshot();record('second-tab-updated',changed['sales.SaleDraftLine'].find(l=>l.id===line.id).quantity===3);
 const headers={Referer:base+'/ventas/cobrar/'};
 const baseline=await s.request.post(base+'/ventas/cobrar/',{form,headers,maxRedirects:0});const text=await baseline.text();record('intact-stale-post-rejected',baseline.status()===200&&text.includes('modificados en otra pestaña')&&same(snapshot(),changed),{status:baseline.status()});
 delete form.expected_subtotal;delete form.draft_signature;
 const altered=await s.request.post(base+'/ventas/cobrar/',{form,headers,maxRedirects:0});const after=snapshot();
 const created=after['sales.Sale'].filter(x=>!before['sales.Sale'].some(y=>y.id===x.id));
 report.observed={status:altered.status(),location:altered.headers().location||null,newSales:created.length,stockP:stock(after,p),stockQ:stock(after,q),draft:after['sales.SaleDraft'].find(d=>d.id===draft.id)?.status};
 const html=await altered.text();record('altered-rejected-with-review',altered.status()===200&&html.includes('No se pudo verificar el resumen de la venta')&&same(after,changed));
 await s.setContent(html);await s.screenshot({path:path.join(out,'01-revision-requerida.png'),fullPage:true});
 record('current-summary-restored',!!(await s.locator('[name=draft_signature]').inputValue())&&(await s.locator('[name=expected_subtotal]').inputValue())==='29.50');
 await s.getByRole('button',{name:'Confirmar cobro',exact:true}).click();await s.waitForURL(/\/constancia\//);
 const completed=snapshot(),newSale=completed['sales.Sale'].find(x=>!before['sales.Sale'].some(y=>y.id===x.id));
 record('explicit-retry-one-sale',!!newSale&&newSale.total_amount==='29.50'&&completed['sales.Sale'].length===before['sales.Sale'].length+1&&stock(completed,p)===17&&stock(completed,q)===5);
 write('checkpoints.json',{before,changed,after,completed});
 }catch(e){report.error=e.message;process.exitCode=1;}finally{write('browser.json',report);await browser.close();}})().catch(e=>{console.error(e.message);process.exitCode=1});
