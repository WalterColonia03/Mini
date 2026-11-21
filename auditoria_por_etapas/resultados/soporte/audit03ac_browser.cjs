const fs=require('node:fs'), path=require('node:path'), os=require('node:os'), crypto=require('node:crypto');
const assert=require('node:assert/strict');
const {execFileSync}=require('node:child_process');
const {chromium}=require(path.join(os.homedir(),'.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright-core'));
const out=process.env.AUDIT03_OUT, run=process.env.AUDIT03_RUN_DIR, base='http://127.0.0.1:'+process.env.AUDIT03_PORT;
const accounts=JSON.parse(fs.readFileSync(path.join(run,'.credentials.json')));
const fixture=JSON.parse(fs.readFileSync(path.join(out,'fixture.json')));
const report={checks:[],input:'Chrome automated UI, independent admin and warehouse sessions'};
function check(id,a,b){assert.deepEqual(a,b,id);report.checks.push(id);}
function state(){return JSON.parse(execFileSync(process.env.AUDIT03_PYTHON,[path.join(__dirname,'audit03y_browser_run.py'),'snapshot'],{encoding:'utf8'}));}
const button=(p,name)=>p.getByRole('button',{name,exact:true});
async function login(browser,role){
  const p=await browser.newPage({locale:'es-PE',viewport:{width:1366,height:900}});
  await p.goto(base);await p.locator('[name=email]').fill(accounts[role].email);await p.locator('[name=password]').fill(accounts[role].password);
  await p.locator('button[type=submit]').click();return p;
}
async function test(browser){
  const probe=await browser.newPage(),nonce=crypto.randomBytes(32).toString('hex');
  const res=await probe.request.get(base,{headers:{'X-Audit03-Challenge':nonce}});
  check('aislamiento',res.headers()['x-audit03-proof'],crypto.createHmac('sha256',fs.readFileSync(path.join(run,'.django-key'))).update(nonce).digest('hex'));
  await probe.close();
  const warehouse=await login(browser,'warehouse'), admin=await login(browser,'admin');
  await admin.getByRole('link',{name:'Proveedores',exact:true}).click();
  const supplierRow=admin.getByRole('row').filter({has:admin.getByRole('cell',{name:'Proveedor ficticio AB',exact:true})});
  const product=fixture.products[0];
  for(const [menu,submit,lotName] of [['inventory-load-link','Confirmar existencias','INITIAL'],['stock-entry-link','Confirmar entrada','LATER']]){
    await warehouse.goto(base);await warehouse.getByTestId(menu).click();
    const before=state();
    await warehouse.locator('[name=product]').selectOption(product.id);
    await warehouse.locator('[name=supplier]').selectOption(fixture.supplier_id);
    for(const [field,value] of Object.entries({number:lotName,quantity:'2',unit_cost:'3.00',expiration_date:fixture.future})){
      await warehouse.locator('[name="lots-0-'+field+'"]').fill(value);
    }
    const oldPayload=await warehouse.locator('form[data-testid]').evaluate(f=>Object.fromEntries(new FormData(f)));
    const url=warehouse.url();
    await supplierRow.getByRole('button',{name:'Desactivar',exact:true}).click();
    check(menu+' proveedor inactivo visible',(await supplierRow.innerText()).includes('Inactivo'),true);
    await button(warehouse,submit).click();
    await warehouse.locator('.field-error').filter({has:warehouse.locator('[name=supplier]')}).getByRole('alert').waitFor();
    check(menu+' rechazo atómico',state(),before);
    check(menu+' proveedor desaparece de opciones',await warehouse.locator('[name=supplier] option[value="'+fixture.supplier_id+'"]').count(),0);
    check(menu+' lote conservado para corregir',await warehouse.locator('[name="lots-0-number"]').inputValue(),lotName);
    check(menu+' cantidad conservada',await warehouse.locator('[name="lots-0-quantity"]').inputValue(),'2');
    const direct=await warehouse.request.post(url,{form:oldPayload,maxRedirects:0});
    check(menu+' POST antiguo rechazado',direct.status(),200);
    check(menu+' error de selección en POST',(await direct.text()).includes('field-error'),true);
    check(menu+' POST sin efectos',state(),before);
    await warehouse.screenshot({path:path.join(out,menu+'-rechazo.png'),fullPage:true});
    await supplierRow.getByRole('button',{name:'Activar',exact:true}).click();
    await warehouse.goto(url);
    await warehouse.locator('[name=product]').selectOption(product.id);
    await warehouse.locator('[name=supplier]').selectOption(fixture.supplier_id);
    for(const [field,value] of Object.entries({number:lotName,quantity:'2',unit_cost:'3.00',expiration_date:fixture.future})){
      await warehouse.locator('[name="lots-0-'+field+'"]').fill(value);
    }
    await button(warehouse,submit).click();await warehouse.waitForURL(/\/inventario\/cargas\//);
    const after=state(),lots=after.receipt_lots.filter(l=>l.product_id===product.id);
    check(menu+' reactivación permite una recepción',lots.length,lotName==='INITIAL'?1:2);
    check(menu+' proveedor conservado en lote',lots.find(l=>l.number===lotName).supplier_id,fixture.supplier_id);
  }
  await warehouse.goto(base);await warehouse.getByTestId('inventory-load-link').click();
  await warehouse.locator('[name=product]').selectOption(fixture.products[1].id);
  check('proveedor opcional inicialmente vacío',await warehouse.locator('[name=supplier]').inputValue(),'');
  for(const [field,value] of Object.entries({number:'MAXDATE',quantity:'1',unit_cost:'1.00',expiration_date:fixture.over_ceiling})){
    await warehouse.locator('[name="lots-0-'+field+'"]').fill(value);
  }
  const unchanged=state();
  await button(warehouse,'Confirmar existencias').click();
  await warehouse.getByRole('alert').filter({hasText:'20 años'}).waitFor();
  check('fecha superior al aniversario rechaza toda carga',state(),unchanged);
  await warehouse.locator('[name="lots-0-expiration_date"]').fill(fixture.ceiling);
  await warehouse.locator('form[data-testid]').evaluate(form=>{
    const input=document.createElement('input');input.type='hidden';input.name='lots-0-received_at';
    input.value='2000-01-01T00:00:00Z';form.append(input);
  });
  await button(warehouse,'Confirmar existencias').click();await warehouse.waitForURL(/\/inventario\/cargas\//);
  const last=state().receipt_lots.find(l=>l.product_id===fixture.products[1].id);
  check('aniversario exacto guardado',last.expiration_date,fixture.ceiling);
  check('proveedor opcional mantiene null',last.supplier_id,null);
  check('fecha ingreso procede del servidor',last.received_at.startsWith('2000-01-01'),false);
  await warehouse.screenshot({path:path.join(out,'fecha-limite.png'),fullPage:true});
  const before=state();
  const cookies=await warehouse.context().cookies();
  const csrf=cookies.find(c=>c.name==='audit03k_csrftoken').value;
  const formAction=await supplierRow.locator('form').getAttribute('action');
  check('almacenero no puede cambiar proveedor',(await warehouse.request.post(base+formAction,{form:{csrfmiddlewaretoken:csrf}})).status(),403);
  const seller=await login(browser,'seller');
  const sellerCookies=await seller.context().cookies();
  check('vendedor no puede cambiar proveedor',(await seller.request.post(base+formAction,
    {form:{csrfmiddlewaretoken:sellerCookies.find(c=>c.name==='audit03k_csrftoken').value}})).status(),403);
  check('rechazos de permisos sin efectos',state(),before);
}
(async()=>{
  const browser=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true});
  try {report.chrome=browser.version();await test(browser);}
  catch(error){report.error=error.message;process.exitCode=1;}
  finally{fs.writeFileSync(path.join(out,'browser.json'),JSON.stringify(report,null,2));await browser.close();}
})();
