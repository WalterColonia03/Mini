/* Chrome visual catalogue audit. Separate roles, fresh marked DB, no secrets logged. */
const fs=require('fs'),path=require('path'),os=require('os'),crypto=require('crypto');
const {execFileSync}=require('child_process');
const {chromium}=require(path.join(os.homedir(),'.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright-core'));
const run=process.env.AUDIT03_RUN_DIR,out=process.env.AUDIT03_OUT,base=`http://127.0.0.1:${process.env.AUDIT03_PORT}`;
const creds=JSON.parse(fs.readFileSync(path.join(run,'.credentials.json'),'utf8'));
const py=(action)=>JSON.parse(execFileSync(process.env.AUDIT03_PYTHON,[path.join(__dirname,'audit03b_run.py'),action],{encoding:'utf8',env:{...process.env,PYTHONIOENCODING:'utf-8'}}));
const snap=()=>py('snapshot'),equal=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
const report={stage:'03-B',started_utc:new Date().toISOString(),cases:[],observations:[],errors:[],viewport:{width:1366,height:768}};
const rec=(id,ok,details={})=>report.cases.push({id,ok:!!ok,...details});
const click=async(p,l)=>Promise.all([p.waitForNavigation({waitUntil:'domcontentloaded'}),l.click()]);
async function save(p,id){await p.screenshot({path:path.join(out,id+'.png'),fullPage:true,mask:[p.locator('input[type=password]')]});fs.writeFileSync(path.join(out,id+'.txt'),await p.locator('body').innerText());return id+'.png';}
async function login(p,role){await p.goto(base+'/');await p.locator('[name=email]').fill(creds[role].email);await p.locator('[name=password]').fill(creds[role].password);await click(p,p.locator('button[type=submit]'));}
async function table(p){return p.locator('main').evaluate(main=>{const headers=[...main.querySelectorAll('thead th')].map(e=>e.textContent.trim());return {headers,rows:[...main.querySelectorAll('tbody tr')].map(tr=>Object.fromEntries([...tr.querySelectorAll('td')].map((td,i)=>[headers[i],td.textContent.replace(/\s+/g,' ').trim()])))}});}
async function search(p,q){await p.locator('[name=q]').fill(q);await click(p,p.getByRole('button',{name:'Buscar',exact:true}));return table(p);}
(async()=>{
 const browser=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true});report.browser=browser.version();
 const contexts=await Promise.all(Array.from({length:4},()=>browser.newContext({viewport:report.viewport})));
 const [a,w,s,v]=await Promise.all(contexts.map(c=>c.newPage()));for(const p of [a,w,s,v])p.setDefaultTimeout(12000);
 try{
  const nonce=crypto.randomBytes(32).toString('hex'),probe=await a.request.get(base+'/',{headers:{'X-Audit03-Challenge':nonce}});
  const expected=crypto.createHmac('sha256',fs.readFileSync(path.join(run,'.django-key'),'utf8')).update(nonce).digest('hex');
  if(probe.headers()['x-audit03-proof']!==expected||probe.headers()['x-audit03-run']!==path.basename(run))throw Error('Isolated server proof mismatch');
  rec('C00-isolation',true);
  await login(a,'admin');await click(a,a.getByRole('link',{name:'Productos',exact:true}));
  rec('C01-empty',(await a.locator('main').innerText()).includes('No hay productos registrados.'),{screenshot:await save(a,'C01-empty')});
  const fx=py('fixtures');fs.writeFileSync(path.join(out,'fixture.json'),JSON.stringify(fx,null,2));
  const initial=snap();await a.reload();const admin=await table(a);
  rec('C02-full-list',admin.rows.length===fx.products.length,{headers:admin.headers,screenshot:await save(a,'C02-catalogue')});
  const desktop=await a.locator('.table-responsive').evaluate(el=>({width:el.clientWidth,contentWidth:el.scrollWidth}));
  rec('C02-desktop-columns',desktop.contentWidth<=desktop.width+1,desktop);
  for(const p of fx.products){const row=admin.rows.find(r=>r['Código de barras']===p.code),stock=String(p.current)+(p.current<=p.minimum?' Stock bajo':'');
   const availability=!p.active?'Producto deshabilitado':!p.category_active?'Categoría desactivada':p.current>0?'Disponible':'Sin stock vigente';
   rec('C03-row-'+p.code,!!row&&row.Nombre===p.name&&row.Categoría===p.category&&row['Precio (S/)']===p.price&&row['Stock mínimo']===String(p.minimum)&&row.Disponibilidad===availability&&row['Existencias vigentes (UND)']===stock,{expected:{current:p.current,physical:p.physical,minimum:p.minimum,availability},observed:row});
  }
  const cases=[['code-exact','AUD03B-HIGH',['AUD03B-HIGH']],['code-spaces',' a u d 0 3 b - h i g h ',['AUD03B-HIGH']],['name-partial','aud03b alto',['AUD03B-HIGH']],['name-accent','Atún',['AUD03B-ACCENT']],['no-match','ausente-03b',[]],['html','<script>alert(1)</script>',[]],['sql',"' OR 1=1 --",[]],['wildcard-percent','%',[]],['wildcard-underscore','_',[]],['long4096','X'.repeat(4096),[]],['spaces','   ',fx.products.map(x=>x.code)],['empty','',fx.products.map(x=>x.code)]];
  for(const [id,q,expectedCodes] of cases){const t=await search(a,q),codes=t.rows.map(r=>r['Código de barras']).sort();rec('C04-search-'+id,equal(codes,[...expectedCodes].sort()),{result_codes:codes,query_length:q.length});}
  const unicode=await search(a,'ATÚN');rec('C04-unicode-case',equal(unicode.rows.map(r=>r['Código de barras']),['AUD03B-ACCENT']));
  await search(a,'ninguno');rec('C05-no-match-message',(await a.locator('main').innerText()).includes('No se encontraron productos con «ninguno».'),{screenshot:await save(a,'C05-no-match')});
  await click(a,a.getByRole('link',{name:'Limpiar búsqueda',exact:true}));rec('C06-clear',(await table(a)).rows.length===11&&await a.locator('[name=q]').inputValue()==='');
  await a.locator('label[for=product-search]').click();const focus=await a.locator('[name=q]').evaluate(el=>el===document.activeElement);
  await a.locator('[name=q]').fill('AUD03B-MIX');await Promise.all([a.waitForNavigation({waitUntil:'domcontentloaded'}),a.locator('[name=q]').press('Enter')]);
  rec('C07-keyboard-label',focus&&(await table(a)).rows[0]?.['Código de barras']==='AUD03B-MIX');
  await a.reload();rec('C08-reload',await a.locator('[name=q]').inputValue()==='AUD03B-MIX'&&(await table(a)).rows.length===1);
  await search(a,'AUD03B-HIGH');await a.goBack();const backState={query:new URL(a.url()).searchParams.get('q'),input:await a.locator('[name=q]').inputValue(),first:(await table(a)).rows[0]?.['Código de barras']};rec('C09-back',Object.values(backState).every(value=>value==='AUD03B-MIX'),backState);
  await a.goto(base+'/productos/?q=%00');
  rec('C10-null-query',(await table(a)).rows.length===0&&(await a.locator('main').innerText()).includes('La búsqueda contiene un carácter no válido.'),{screenshot:await save(a,'C10-invalid')});
  await a.goto(base+'/productos/?q=AUD03B-HIGH&minimum_stock=0&is_active=false');rec('C11-tampered-get',equal(initial,snap()));
  const tk=await a.locator('[name=csrfmiddlewaretoken]').first().inputValue();const post=await a.request.post(base+'/productos/',{form:{csrfmiddlewaretoken:tk,name:'INJECTED'},maxRedirects:0});rec('C12-post-denied',post.status()===405&&equal(initial,snap()),{status:post.status()});
  await login(w,'warehouse');await click(w,w.getByRole('link',{name:'Catálogo de productos',exact:true}));const warehouse=await table(w);
  const strip=rows=>rows.map(({Acciones,...rest})=>rest);
  rec('C13-warehouse-data',equal(strip(admin.rows),warehouse.rows)&&!warehouse.headers.includes('Acciones')&&await w.locator('main a[href$="/editar/"],main form[action$="/disponibilidad/"]').count()===0,{screenshot:await save(w,'C13-warehouse')});
  const wr=await search(w,'AUD03B-MIX');rec('C14-warehouse-search',wr.rows.length===1&&wr.rows[0]['Código de barras']==='AUD03B-MIX');
  await login(s,'seller');await click(s,s.locator('a[href="/ventas/"]').first());await s.locator('[name=query]').fill('AUD03B-HIGH');await click(s,s.getByRole('button',{name:'Buscar',exact:true}));
  const st=await table(s);rec('C15-seller-sale-query',st.rows.length===1&&st.rows[0]['Disponible']==='11'&&st.rows[0]['Precio']==='S/ 8,50',{screenshot:await save(s,'C15-sale-query')});
  const denied=await s.goto(base+'/productos/');rec('C16-seller-denied',denied.status()===403&&(await s.locator('main').innerText()).includes('No tienes permiso'),{screenshot:await save(s,'C16-seller-denied')});
  const visitor=await v.request.get(base+'/productos/',{maxRedirects:0});rec('C17-visitor',visitor.status()===302,{location:visitor.headers().location});
  await a.goto(base+'/productos/?q=AUD03B-MIX');await a.setViewportSize({width:390,height:844});
  report.observations.push({id:'OBS03B-mobile',screenshot:await save(a,'C18-mobile'),layout:await a.evaluate(()=>({pageOverflow:document.documentElement.scrollWidth>innerWidth,tableOverflow:!!document.querySelector('.table-responsive')&&document.querySelector('.table-responsive').scrollWidth>document.querySelector('.table-responsive').clientWidth}))});
  const mobile=await a.locator('.table-responsive').evaluate(el=>{el.scrollLeft=el.scrollWidth;const right=el.getBoundingClientRect().right;const actions=el.querySelector('tbody td:last-child').getBoundingClientRect();return {moved:el.scrollLeft>0,actionsVisible:actions.left<right&&actions.right<=right+1}});
  rec('C18-mobile-actions',mobile.moved&&mobile.actionsVisible,{...mobile,screenshot:await save(a,'C18-mobile-actions')});
  rec('C19-no-business-mutation',equal(initial,snap()));
 }catch(error){report.errors.push({name:error.name,message:error.message.split('\n')[0]});}
 finally{report.finished_utc=new Date().toISOString();fs.writeFileSync(path.join(out,'browser.json'),JSON.stringify(report,null,2));await browser.close();console.log(JSON.stringify({cases:report.cases.length,passed:report.cases.filter(x=>x.ok).length,failed:report.cases.filter(x=>!x.ok).map(x=>x.id),errors:report.errors}));if(report.errors.length||report.cases.some(x=>!x.ok))process.exitCode=1;}
})();
