const fs=require('node:fs'),path=require('node:path'),os=require('node:os'),crypto=require('node:crypto');
const assert=require('node:assert/strict');
const {execFileSync}=require('node:child_process');
const {chromium}=require(path.join(os.homedir(),'.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright-core'));
const out=process.env.AUDIT03_OUT,run=process.env.AUDIT03_RUN_DIR,base='http://127.0.0.1:'+process.env.AUDIT03_PORT;
const accounts=JSON.parse(fs.readFileSync(path.join(run,'.credentials.json')));
const fixture=JSON.parse(fs.readFileSync(path.join(out,'fixture.json')));
const report={checks:[],input:'Chrome automation with independent roles'};
const button=(p,name)=>p.getByRole('button',{name,exact:true});
function check(id,a,b){assert.deepEqual(a,b,id);report.checks.push(id);}
function state(){return JSON.parse(execFileSync(process.env.AUDIT03_PYTHON,[path.join(__dirname,'audit03y_browser_run.py'),'snapshot'],{encoding:'utf8'}));}
async function login(browser,role){
  const p=await browser.newPage({locale:'es-PE',viewport:{width:1366,height:900}});
  await p.goto(base);await p.locator('[name=email]').fill(accounts[role].email);await p.locator('[name=password]').fill(accounts[role].password);
  await p.locator('button[type=submit]').click();return p;
}

async function fill(p,product,costs){
  await p.locator('[name=product]').selectOption(product.id);
  await p.locator('[name=supplier]').selectOption(fixture.supplier_id);
  for(const [i,cost] of costs.entries()){
    for(const [key,value] of Object.entries({number:'AF-'+i,quantity:'1',unit_cost:cost,expiration_date:fixture.future}))
      await p.locator('[name="lots-'+i+'-'+key+'"]').fill(value);
  }
}
async function dropped(p,afterCommit){
  let forwardedStatus=null,routeFailure=null;
  const failed=p.waitForEvent('requestfailed',r=>r.method()==='POST' && r.url()===base+'/inventario/carga-inicial/');
  await p.route('**/inventario/carga-inicial/',async route=>{
    if(route.request().method()!=='POST')return route.continue();
    try{
      if(afterCommit){const res=await route.fetch({maxRedirects:0});forwardedStatus=res.status();}
      await route.abort('connectionreset');
    }catch(e){routeFailure=e.message;await route.abort().catch(()=>{});}
  });
  await button(p,'Confirmar existencias').click({noWaitAfter:true}).catch(e=>{
    if(!e.message.includes('ERR_CONNECTION_RESET'))throw e;
  });
  const req=await failed;
  await p.waitForLoadState('domcontentloaded').catch(()=>{});
  await p.unroute('**/inventario/carga-inicial/');
  check('intercepción sin error '+afterCommit,routeFailure,null);
  check('fallo de conexión visible '+afterCommit,req.failure().errorText.includes('ERR_CONNECTION_RESET'),true);
  check('respuesta servidor '+afterCommit,forwardedStatus,afterCommit?302:null);
  report.transport=report.transport||[];
  report.transport.push({afterCommit,forwardedStatus,browserFailure:req.failure().errorText});
}
async function test(browser){
  const probe=await browser.newPage(),nonce=crypto.randomBytes(32).toString('hex');
  const res=await probe.request.get(base,{headers:{'X-Audit03-Challenge':nonce}});
  check('aislamiento',res.headers()['x-audit03-proof'],crypto.createHmac('sha256',fs.readFileSync(path.join(run,'.django-key'))).update(nonce).digest('hex'));
  await probe.close();
  const warehouse=await login(browser,'warehouse');
  const initial=state();
  await warehouse.getByTestId('inventory-load-link').click();
  await fill(warehouse,fixture.products[0],['1.2344','1.2345']);
  await dropped(warehouse,false);
  check('sin entrega conserva estado completo',state(),initial);
  await warehouse.goto(base);await warehouse.getByTestId('inventory-load-link').click();
  check('sin entrega producto sigue elegible',await warehouse.locator('[name=product] option[value="'+fixture.products[0].id+'"]').count(),1);
  await fill(warehouse,fixture.products[0],['1.2344','1.2345']);
  const payload=await warehouse.locator('form[data-testid]').evaluate(f=>Object.fromEntries(new FormData(f)));
  await dropped(warehouse,true);
  const saved=state(),product=fixture.products[0];
  check('una carga pese a respuesta perdida',saved.receipt_loads.length,1);
  check('dos lotes pese a respuesta perdida',saved.receipt_lots.length,2);
  check('cantidad exacta',saved.receipt_lots.reduce((n,l)=>n+l.available_quantity,0),2);
  check('empate HALF_UP cuatro decimales',saved.commerce.find(p=>p.id===product.id).average_cost,'1.2345');
  check('todos los lotes corresponden al producto',saved.receipt_lots.every(l=>l.product_id===product.id),true);
  check('proveedor conservado',saved.receipt_lots.every(l=>l.supplier_id===fixture.supplier_id),true);
  check('responsable conservado',saved.receipt_lots.every(l=>l.responsible_id===fixture.warehouse_id),true);
  const replay=await warehouse.request.post(base+'/inventario/carga-inicial/',{form:payload,maxRedirects:0});
  check('reintento con error controlado',replay.status(),200);
  check('reintento informa carga o disponibilidad',(await replay.text()).includes('ya tiene una carga inicial registrada'),true);
  check('reintento no duplica ni cambia',state(),saved);
  const recovered=await login(browser,'warehouse');
  await recovered.getByRole('link',{name:'Ver inventario y alertas',exact:true}).first().click();
  await recovered.getByRole('row').filter({hasText:product.name}).getByRole('link',{name:'Ver carga',exact:true}).click();
  const canonical=recovered.url(),id=saved.receipt_loads[0].id;
  check('recupera UUID existente desde menú',canonical,base+'/inventario/cargas/'+id+'/');
  check('constancia redondea a dos',await recovered.locator('dl > div').filter({hasText:'Costo promedio'}).locator('dd').innerText(),'S/ 1,23');
  check('constancia identifica responsable',(await recovered.locator('main').innerText()).includes('AUD03 ALMACENERO'),true);
  await recovered.screenshot({path:path.join(out,'constancia-recuperada.png'),fullPage:true});
  await recovered.reload();check('recarga conserva estado',state(),saved);
  await recovered.goto(base);await recovered.getByTestId('inventory-load-link').click();
  check('cargado no elegible',await recovered.locator('[name=product] option[value="'+product.id+'"]').count(),0);
  await fill(recovered,fixture.products[1],['1.0050']);
  await button(recovered,'Confirmar existencias').click();await recovered.waitForURL(/\/inventario\/cargas\//);
  check('empate visual dos decimales',await recovered.locator('dl > div').filter({hasText:'Costo promedio'}).locator('dd').innerText(),'S/ 1,01');
  const final=state();check('almacenamiento conserva cuatro decimales',final.commerce.find(p=>p.id===fixture.products[1].id).average_cost,'1.0050');
  check('primera carga y lotes intactos',final.receipt_lots.filter(l=>l.product_id===product.id),saved.receipt_lots);
  const alias=base+'/inventario/carga-inicial/'+id+'/creada/';
  for(const role of ['warehouse','admin','seller']){
    const page=await login(browser,role);
    for(const [label,url] of [['canónica',canonical],['alias',alias]]){
      const response=await page.goto(url);check(role+' '+label+' permiso',response.status(),role==='seller'?403:200);
      if(role!=='seller')check(role+' '+label+' misma ficha',await page.getByRole('heading',{name:product.name,exact:true}).count(),1);
    }
  }
  check('consultas finales sin escritura',state(),final);
}
(async()=>{
  const browser=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true});
  try{report.chrome=browser.version();await test(browser);}
  catch(error){report.error=error.message;process.exitCode=1;}
  finally{fs.writeFileSync(path.join(out,'browser.json'),JSON.stringify(report,null,2));await browser.close();}
})();
