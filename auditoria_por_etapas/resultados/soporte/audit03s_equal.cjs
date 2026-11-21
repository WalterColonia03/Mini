const fs=require('fs'),path=require('path'),os=require('os'),crypto=require('crypto');
const {execFileSync}=require('child_process');
const {chromium}=require(path.join(os.homedir(),'.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright-core'));
const run=process.env.AUDIT03_RUN_DIR,out=process.env.AUDIT03_OUT,base='http://127.0.0.1:'+process.env.AUDIT03_PORT;
const creds=JSON.parse(fs.readFileSync(path.join(run,'.credentials.json'),'utf8')),fx=JSON.parse(fs.readFileSync(path.join(out,'fixture.json'),'utf8'));
const report={mode:'Chrome separate tabs, same subtotal, stale and altered HTTP requests; sequential, no concurrency claim',cases:[],posts:[]};
function check(id,ok,detail={}){report.cases.push({id,ok,...detail});if(!ok) throw Error('case-'+id);}
function snapshot(){return JSON.parse(execFileSync(process.env.AUDIT03_PYTHON,[path.join(__dirname,'audit03s_equal_run.py'),'snapshot'],{encoding:'utf8',env:{...process.env,PYTHONIOENCODING:'utf-8'}}));}
function write(n,d){fs.writeFileSync(path.join(out,n),JSON.stringify(d,null,2));}
async function role(browser,role,menu){const page=await(await browser.newContext({viewport:{width:1366,height:900},locale:'es-PE'})).newPage();await page.goto(base);await page.locator('[name=email]').fill(creds[role].email);await page.locator('[name=password]').fill(creds[role].password);await page.locator('button[type=submit]').click();await page.getByRole('link',{name:menu,exact:true}).click();page.on('request',r=>{if(r.method()==='POST')report.posts.push({role,path:new URL(r.url()).pathname});});return page;}
const stock=(s,id)=>s['inventory.Lot'].filter(x=>x.product_id===id).reduce((a,x)=>a+x.available_quantity,0),same=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
(async()=>{const browser=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true});try{
 const probe=await browser.newPage(),nonce=crypto.randomBytes(32).toString('hex');const res=await probe.request.get(base,{headers:{'X-Audit03-Challenge':nonce}});check('isolation',res.headers()['x-audit03-proof']===crypto.createHmac('sha256',fs.readFileSync(path.join(run,'.django-key'))).update(nonce).digest('hex'));await probe.close();
 const s=await role(browser,'seller','Preparar venta');const w=await role(browser,'warehouse','Catálogo de productos');const before=snapshot(),p=fx.product_id,q=fx.empty_product_id;
 const draft=before['sales.SaleDraft'].find(d=>d.status==='ACTIVE'),pl=before['sales.SaleDraftLine'].find(l=>l.draft_id===draft.id&&l.product_id===p),ql=before['sales.SaleDraftLine'].find(l=>l.draft_id===draft.id&&l.product_id===q);
 check('fixture-equal-price',pl.quantity===2&&ql.quantity===1&&pl.unit_price===ql.unit_price);
 check('warehouse-sees-both',await w.getByRole('cell',{name:before['catalog.Product'].find(z=>z.id===p).barcode,exact:true}).count()===1&&await w.getByRole('cell',{name:before['catalog.Product'].find(z=>z.id===q).barcode,exact:true}).count()===1);
 for(const [who,page] of [['seller',s],['warehouse',w]]){const cookies=await page.context().cookies();const csrf=cookies.find(c=>c.name==='audit03k_csrftoken')?.value;check(who+'-csrf-present',!!csrf);const endpoint=base+'/productos/'+p+'/editar/';check(who+'-get-403',(await page.request.get(endpoint)).status()===403);check(who+'-post-403',(await page.request.post(endpoint,{form:{csrfmiddlewaretoken:csrf},headers:{Referer:base+'/productos/'}})).status()===403);}
 check('denials-no-changes',same(snapshot(),before));
 await s.getByRole('link',{name:'Cobrar venta →',exact:true}).click();const form=await s.locator('form[method=post]').evaluate(f=>Object.fromEntries(new FormData(f)));form.cash_received='50.00';const originalSubtotal=form.expected_subtotal,originalSig=form.draft_signature;
 const tab=await s.context().newPage();await tab.goto(base+'/ventas/');
 async function quantity(line,qty){const f=tab.locator('form.draft-line-actions').filter({has:tab.locator('input[id="draft-quantity-'+line.id+'"]')});await f.locator('[name=quantity]').fill(String(qty));await f.getByRole('button',{name:'Actualizar',exact:true}).click();await tab.waitForLoadState('networkidle');}
 await quantity(pl,1);await quantity(ql,2);
 const changed=snapshot(),p2=changed['sales.SaleDraftLine'].find(l=>l.id===pl.id),q2=changed['sales.SaleDraftLine'].find(l=>l.id===ql.id);
 check('second-tab-swapped-quantities',p2.quantity===1&&q2.quantity===2);
 check('same-total',Number(originalSubtotal)===Number(p2.unit_price)*p2.quantity+Number(q2.unit_price)*q2.quantity);
 check('stocks-and-sales-unchanged',same(before['inventory.Lot'],changed['inventory.Lot'])&&same(before['sales.Sale'],changed['sales.Sale']));
 const fresh=await s.context().newPage();await fresh.goto(base+'/ventas/cobrar/');check('signature-changed',(await fresh.locator('[name=draft_signature]').inputValue())!==originalSig);check('subtotal-still-equal',Number(await fresh.locator('[name=expected_subtotal]').inputValue())===Number(originalSubtotal));await fresh.close();
 const headers={Referer:base+'/ventas/cobrar/'};
 const baseline=await s.request.post(base+'/ventas/cobrar/',{form,headers,maxRedirects:0});const text=await baseline.text();check('intact-stale-same-subtotal-rejected',baseline.status()===200&&text.includes('modificados en otra pestaña')&&same(snapshot(),changed),{status:baseline.status()});
 const altered={...form};delete altered.draft_signature;
 const response=await s.request.post(base+'/ventas/cobrar/',{form:altered,headers,maxRedirects:0});const after=snapshot(),html=await response.text();
 check('omitted-signature-rejected',response.status()===200&&html.includes('No se pudo verificar el resumen de la venta')&&same(after,changed),{status:response.status()});
 await s.setContent(html);await s.screenshot({path:path.join(out,'01-mismo-subtotal-revision.png'),fullPage:true});
 check('signature-replaced',(await s.locator('[name=draft_signature]').inputValue())!==originalSig);check('subtotal-preserved',Number(await s.locator('[name=expected_subtotal]').inputValue())===Number(originalSubtotal));
 await s.getByRole('button',{name:'Confirmar cobro',exact:true}).click();await s.waitForURL(/\/constancia\//);
 const completed=snapshot(),created=completed['sales.Sale'].filter(x=>!before['sales.Sale'].some(y=>y.id===x.id));
 check('explicit-retry-one-sale',created.length===1&&Number(created[0].total_amount)===Number(originalSubtotal));
 check('stock-matches-reviewed',stock(completed,p)===stock(before,p)-1&&stock(completed,q)===stock(before,q)-2);
 const sold=completed['sales.SaleLine'].filter(x=>!before['sales.SaleLine'].some(y=>y.id===x.id));check('sale-lines-match-reviewed',sold.length===2&&sold.find(x=>x.product_id===p).quantity===1&&sold.find(x=>x.product_id===q).quantity===2);
 check('history-preserved',before['sales.SaleLine'].every(x=>same(x,completed['sales.SaleLine'].find(y=>y.id===x.id))));
 write('checkpoints.json',{before,changed,after,completed});
 }catch(e){report.error=e.message;process.exitCode=1;}finally{write('browser.json',report);await browser.close();}})().catch(e=>{console.error(e.message);process.exitCode=1});
