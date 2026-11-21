/* Real Chrome + HTTP + ORM. Synthetic data only. Never save credentials/tokens. */
const fs=require('fs'),path=require('path'),os=require('os'),crypto=require('crypto');
const {execFileSync}=require('child_process');
const {chromium}=require(path.join(os.homedir(),'.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright-core'));
const run=process.env.AUDIT03_RUN_DIR,out=process.env.AUDIT03_OUT,base=`http://127.0.0.1:${process.env.AUDIT03_PORT}`;
const creds=JSON.parse(fs.readFileSync(path.join(run,'.credentials.json'),'utf8'));
const py=(action,...args)=>JSON.parse(execFileSync(process.env.AUDIT03_PYTHON,[path.join(__dirname,'audit03_run.py'),action,...args],{encoding:'utf8',env:process.env}));
const snap=()=>py('snapshot');
const report={stage:'03-A',started_utc:new Date().toISOString(),cases:[],errors:[],viewport:{width:1366,height:900}};
const rec=(id,ok,details={})=>report.cases.push({id,ok:!!ok,...details});
const equal=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
const click=async(p,l)=>Promise.all([p.waitForNavigation({waitUntil:'domcontentloaded'}),l.click()]);
async function save(p,id){await p.screenshot({path:path.join(out,id+'.png'),fullPage:true,mask:[p.locator('input[type=password]')]});fs.writeFileSync(path.join(out,id+'.txt'),await p.locator('body').innerText());return id+'.png';}
async function login(p,alias){await p.goto(base+'/');await p.locator('[name=email]').fill(creds[alias].email);await p.locator('[name=password]').fill(creds[alias].password);await click(p,p.locator('button[type=submit]'));}
async function create(p,name){await p.goto(base+'/productos/categorias/nueva/');await p.locator('[name=name]').fill(name);await click(p,p.getByRole('button',{name:'Guardar',exact:true}));}
async function csrf(p){return p.locator('[name=csrfmiddlewaretoken]').first().inputValue();}
(async()=>{
 const browser=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true});report.browser=browser.version();
 const contexts=await Promise.all(Array.from({length:4},()=>browser.newContext({viewport:report.viewport})));
 const [a,w,s,v]=await Promise.all(contexts.map(c=>c.newPage()));for(const p of [a,w,s,v])p.setDefaultTimeout(12000);
 try{
  const nonce=crypto.randomBytes(32).toString('hex'),probe=await contexts[0].request.get(base+'/',{headers:{'X-Audit03-Challenge':nonce}});
  const expected=crypto.createHmac('sha256',fs.readFileSync(path.join(run,'.django-key'),'utf8')).update(nonce).digest('hex');
  if(probe.headers()['x-audit03-proof']!==expected||probe.headers()['x-audit03-run']!==path.basename(run))throw Error('Isolated instance proof mismatch');
  rec('B00-isolation',true);
  await login(a,'admin');await click(a,a.getByRole('link',{name:'Categorías',exact:true}));
  rec('B01-CAT01-empty', (await a.locator('main').innerText()).includes('No hay categorías registradas.'),{screenshot:await save(a,'B01-empty')});
  await click(a,a.getByRole('link',{name:'+ Nueva categoría',exact:true}));
  rec('B02-field-default',await a.locator('[name=name]').inputValue()==='',{attributes:await a.locator('[name=name]').evaluate(el=>({label:document.querySelector('label[for="'+el.id+'"]').innerText,required:el.required,maxLength:el.maxLength,type:el.type,autofocus:el.autofocus}))});
  await a.locator('[name=name]').fill('   AUD03   Bebidas   y jugos   ');await click(a,a.getByRole('button',{name:'Guardar',exact:true}));
  let state=snap(),category=state['catalog.Category'][0];
  rec('B03-create-normalized',category.name==='AUD03 Bebidas y jugos'&&category.is_active,{persisted:category,screenshot:await save(a,'B03-created')});
  const originalCount=state['catalog.Category'].length;
  await create(a,'aud03 bebidas y jugos');
  rec('B04-duplicate',snap()['catalog.Category'].length===originalCount&&(await a.locator('main').innerText()).includes('La categoría ya existe'),{screenshot:await save(a,'B04-duplicate')});
  await create(a,'   ');
  const errorAria=await a.locator('[name=name]').evaluate(el=>({invalid:el.getAttribute('aria-invalid'),describedby:el.getAttribute('aria-describedby'),targets:(el.getAttribute('aria-describedby')||'').split(/\s+/).filter(Boolean).map(id=>({id,exists:!!document.getElementById(id),role:document.getElementById(id)?.getAttribute('role')}))}));
  rec('B05-empty-message',(await a.locator('main').innerText()).includes('El nombre es obligatorio'),{aria:errorAria,screenshot:await save(a,'B05-empty-error')});
  rec('B06-error-accessibility',errorAria.invalid==='true'&&errorAria.targets.length>0&&errorAria.targets.every(x=>x.exists)&&errorAria.targets.some(x=>x.role==='alert'));
  await create(a,'A'.repeat(120));
  rec('B07-length120',snap()['catalog.Category'].some(c=>c.name.length===120));
  await a.goto(base+'/productos/categorias/nueva/');
  const before=snap(),token=await csrf(a);
  const over=await a.request.post(base+'/productos/categorias/nueva/',{form:{name:'B'.repeat(121),csrfmiddlewaretoken:token}});
  rec('B08-http121',over.status()===200&&equal(before,snap()),{status:over.status()});
  const missing=await a.request.post(base+'/productos/categorias/nueva/',{form:{csrfmiddlewaretoken:token}});
  rec('B09-http-missing',missing.status()===200&&(await missing.text()).includes('El nombre es obligatorio')&&equal(before,snap()));
  await a.locator('[name=name]').fill('AUD03 Cancelada');await click(a,a.getByRole('link',{name:'Cancelar',exact:true}));
  await a.reload();rec('B10-cancel-reload',equal(before,snap()));
  await create(a,'<script>AUD03</script>');await a.goto(base+'/productos/categorias/');
  rec('B11-escaped',await a.locator('main script').count()===0&&(await a.locator('main').innerText()).includes('<script>AUD03</script>'));
  await login(w,'warehouse');await click(w,w.getByRole('link',{name:'Catálogo de productos',exact:true}));
  await login(s,'seller');
  for(const [p,role] of [[w,'warehouse'],[s,'seller'],[v,'visitor']]){
   const pre=snap();let status=[];
   if(role!=='visitor'){await p.goto(base+'/salir/');}
   const tk=role==='visitor'?'':await csrf(p);
   for(const route of ['/productos/categorias/','/productos/categorias/nueva/',`/productos/categorias/${category.id}/estado/`]){
    const r=await p.request.get(base+route,{maxRedirects:0});status.push(r.status());
    if(role!=='visitor'){const post=await p.request.post(base+route,{form:{name:'DENIED',csrfmiddlewaretoken:tk},maxRedirects:0});status.push(post.status());}
   }
   await p.goto(base+'/productos/categorias/');
   rec('B12-denied-'+role,status.every(x=>x===(role==='visitor'?302:403))&&equal(pre,snap()),{status,screenshot:await save(p,'B12-'+role)});
  }
  await a.goto(base+'/productos/categorias/');
  const row=a.locator('tbody tr').filter({has:a.locator(`form[action="/productos/categorias/${category.id}/estado/"]`)});
  await click(a,row.getByRole('button',{name:'Desactivar',exact:true}));
  rec('B13-inactive-visible',snap()['catalog.Category'].find(c=>c.id===category.id).is_active===false&&(await row.innerText()).includes('Inactiva'));
  await create(a,category.name.toUpperCase());
  rec('B14-inactive-duplicate',(await a.locator('main').innerText()).includes('La categoría ya existe'));
  await a.goto(base+'/productos/categorias/');await click(a,row.getByRole('button',{name:'Activar',exact:true}));
  await click(a,a.getByRole('link',{name:'Registrar producto',exact:true}));
  const productHeading=await a.locator('main h2').innerText();
  await a.locator('[name=name]').fill('AUD03 Jabón de prueba');
  await a.locator('[name=barcode]').fill('AUD03-JABON');
  await a.locator('[name=category]').selectOption(category.id);
  await a.locator('[name=unit]').selectOption('UND');
  await a.locator('[name=sale_price]').fill('3.50');
  await a.locator('[name=minimum_stock]').fill('');
  await click(a,a.getByRole('button',{name:'Registrar producto',exact:true}));
  const nonCanned=snap()['catalog.Product'].find(p=>p.barcode==='AUD03-JABON');
  rec('B14b-category-usable-noncanned',nonCanned?.category_id===category.id&&nonCanned?.controls_expiration===true&&nonCanned?.unit==='UND',
      {heading:productHeading,product:nonCanned,screenshot:await save(a,'B14b-noncanned')});
  await a.goBack();rec('B14c-back-no-write',snap()['catalog.Product'].filter(p=>p.barcode==='AUD03-JABON').length===1);
  // Fixture is setup, not evidence of a complete inventory/cash/sales audit.
  const fixture=py('effects',category.id);fs.writeFileSync(path.join(out,'fixture.json'),JSON.stringify(fixture,null,2));
  await s.goto(base+'/inicio/');await click(s,s.locator('a[href="/ventas/"]').first());
  await s.locator('[name=query]').fill('AUD03-BEBIDA');await click(s,s.getByRole('button',{name:'Buscar',exact:true}));
  rec('B15-sale-search-active',await s.getByRole('button',{name:'Agregar',exact:true}).count()===1);
  await s.goto(base+`/ventas/constancia/${fixture.sale_id}/`);const receiptBefore=await s.locator('main').innerText();
  const effectsBefore=snap();
  await a.goto(base+'/productos/categorias/');await click(a,row.getByRole('button',{name:'Desactivar',exact:true}));
  await s.goto(base+'/ventas/');await s.locator('[name=query]').fill('AUD03-BEBIDA');await click(s,s.getByRole('button',{name:'Buscar',exact:true}));
  rec('B16-sale-search-inactive',await s.getByRole('button',{name:'Agregar',exact:true}).count()===0&&(await s.locator('main').innerText()).includes('No se encontraron productos con existencias vendibles.'),{screenshot:await save(s,'B16-inactive-sale')});
  await s.locator('.draft-line-actions [name=quantity]').fill('3');await click(s,s.getByRole('button',{name:'Actualizar',exact:true}));
  const updateText=await s.locator('main').innerText();
  rec('B17-draft-reject',equal(effectsBefore['sales.SaleDraftLine'],snap()['sales.SaleDraftLine']),{message:updateText.match(/[^\n]*(?:inactiv|disponib)[^\n]*/gi)});
  await s.goto(base+'/ventas/cobrar/');
  if(await s.locator('[name=cash_received]').count()){
    await s.locator('[name=cash_received]').fill('30.00');await click(s,s.locator('form button[type=submit]').last());
  }
  const afterCheckout=snap();
  rec('B18-checkout-no-mutation',(await s.locator('main').innerText()).includes('ya no está disponible para la venta')&&['sales.Sale','sales.SaleLine','sales.SaleDraft','sales.SaleDraftLine','inventory.Lot','cash.CashShift'].every(k=>equal(effectsBefore[k],afterCheckout[k])),{screenshot:await save(s,'B18-checkout')});
  await w.goto(base+'/inventario/carga-inicial/');const initialChoices=await w.locator('[name=product] option').evaluateAll(es=>es.map(e=>e.value));
  await w.goto(base+'/inventario/entrada/');const entryChoices=await w.locator('[name=product] option').evaluateAll(es=>es.map(e=>e.value));
  rec('B19-inventory-selectors',!initialChoices.includes(fixture.empty_product_id)&&!entryChoices.includes(fixture.product_id),{screenshot:await save(w,'B19-entry')});
  await w.goto(base+'/productos/');rec('B20-warehouse-state',(await w.locator('main').innerText()).includes('Categoría desactivada'),{screenshot:await save(w,'B20-catalog')});
  await s.goto(base+`/ventas/constancia/${fixture.sale_id}/`);rec('B21-historical-receipt',(await s.locator('main').innerText())===receiptBefore,{screenshot:await save(s,'B21-receipt')});
  await a.goto(base+'/productos/categorias/');await click(a,row.getByRole('button',{name:'Activar',exact:true}));
  await s.goto(base+'/ventas/?query=AUD03-BEBIDA');
  await w.goto(base+'/inventario/entrada/');
  rec('B22-reactivation',await s.getByRole('button',{name:'Agregar',exact:true}).count()===1&&(await w.locator('[name=product] option').evaluateAll(es=>es.map(e=>e.value))).includes(fixture.product_id)&&equal(effectsBefore,snap()));
  await a.goto(base+'/productos/categorias/');await a.setViewportSize({width:390,height:844});
  rec('B23-mobile-observation',true,{horizontalOverflow:await a.evaluate(()=>document.documentElement.scrollWidth>innerWidth),screenshot:await save(a,'B23-mobile')});
 }catch(error){report.errors.push({name:error.name,message:error.message.split('\n')[0]});}
 finally{report.finished_utc=new Date().toISOString();fs.writeFileSync(path.join(out,'browser.json'),JSON.stringify(report,null,2));await browser.close();console.log(JSON.stringify({cases:report.cases.length,passed:report.cases.filter(x=>x.ok).length,failed:report.cases.filter(x=>!x.ok).map(x=>x.id),errors:report.errors}));if(report.errors.length||report.cases.some(x=>!x.ok))process.exitCode=1;}
})();
