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
async function fill(p,product){
  await p.locator('[name=product]').selectOption(product.id);
  for(const [field,value] of Object.entries({number:'AE-LOT',quantity:'3',unit_cost:'2.00',expiration_date:fixture.future})){
    await p.locator('[name="lots-0-'+field+'"]').fill(value);
  }
}
async function test(browser){
  const probe=await browser.newPage(),nonce=crypto.randomBytes(32).toString('hex');
  const res=await probe.request.get(base,{headers:{'X-Audit03-Challenge':nonce}});
  check('aislamiento',res.headers()['x-audit03-proof'],crypto.createHmac('sha256',fs.readFileSync(path.join(run,'.django-key'))).update(nonce).digest('hex'));
  await probe.close();
  const warehouse=await login(browser,'warehouse'),admin=await login(browser,'admin'),seller=await login(browser,'seller');
  for(const [index,target] of ['product','category'].entries()){
    const product=fixture.products[index];
    await warehouse.goto(base);await warehouse.getByTestId('inventory-load-link').click();
    await fill(warehouse,product);
    const url=warehouse.url();
    const payload=await warehouse.locator('form[data-testid]').evaluate(f=>Object.fromEntries(new FormData(f)));
    await admin.goto(base);
    if(target==='product'){
      await admin.getByRole('link',{name:'Productos',exact:true}).click();
      await admin.getByRole('row').filter({has:admin.getByRole('cell',{name:product.barcode,exact:true})})
        .getByRole('button',{name:'Deshabilitar',exact:true}).click();
    }else{
      await admin.getByRole('link',{name:'Categorías',exact:true}).click();
      await admin.getByRole('row').filter({has:admin.getByRole('cell',{name:'Higiene',exact:true})})
        .getByRole('button',{name:'Desactivar',exact:true}).click();
      await button(admin,'Confirmar desactivación').click();
    }
    const before=state();
    await button(warehouse,'Confirmar existencias').click();
    await warehouse.getByRole('alert').filter({hasText:'no está disponible'}).waitFor();
    check(target+' rechazo sin escrituras',state(),before);
    check(target+' producto excluido',await warehouse.locator('[name=product] option[value="'+product.id+'"]').count(),0);
    check(target+' conserva cantidad para corregir',await warehouse.locator('[name="lots-0-quantity"]').inputValue(),'3');
    check(target+' conserva lote',await warehouse.locator('[name="lots-0-number"]').inputValue(),'AE-LOT');
    const direct=await warehouse.request.post(url,{form:payload,maxRedirects:0});
    check(target+' POST antiguo rechazado',direct.status(),200);
    check(target+' POST muestra motivo',(await direct.text()).includes('no está disponible'),true);
    check(target+' POST sin cambios',state(),before);
    await warehouse.screenshot({path:path.join(out,target+'-rechazo.png'),fullPage:true});
    await seller.goto(base);await seller.getByRole('link',{name:'Preparar venta',exact:true}).click();
    await seller.locator('[name=query]').fill(fixture.products[0].barcode);
    await button(seller,'Buscar').click();
    check(target+' vendedor no ofrece producto afectado',await seller.locator('.sales-search-panel tbody tr').count(),0);
    if(target==='product'){
      await admin.getByRole('row').filter({has:admin.getByRole('cell',{name:product.barcode,exact:true})})
        .getByRole('button',{name:'Habilitar',exact:true}).click();
    }else{
      await admin.getByRole('row').filter({has:admin.getByRole('cell',{name:'Higiene',exact:true})})
        .getByRole('button',{name:'Activar',exact:true}).click();
      await button(admin,'Confirmar activación').click();
    }
    await warehouse.goto(url);await fill(warehouse,product);
    await button(warehouse,'Confirmar existencias').click();await warehouse.waitForURL(/\/inventario\/cargas\//);
    const after=state();
    check(target+' una carga',after.receipt_loads.filter(l=>l.product_id===product.id).length,1);
    check(target+' tres unidades',after.receipt_lots.filter(l=>l.product_id===product.id).reduce((n,l)=>n+l.available_quantity,0),3);
    check(target+' costo correcto',after.commerce.find(p=>p.id===product.id).average_cost,'2.0000');
    check(target+' otros lotes intactos',after.receipt_lots.filter(l=>l.product_id!==product.id),before.receipt_lots);
    await seller.locator('[name=query]').fill(product.barcode);await button(seller,'Buscar').click();
    check(target+' vendedor ve ficha reactivada',await seller.locator('.sales-search-panel tbody tr').count(),1);
    check(target+' vendedor ve saldo3',await seller.locator('.sales-search-panel tbody tr').getByRole('cell').nth(2).innerText(),'3');
  }
}
(async()=>{
  const browser=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true});
  try{report.chrome=browser.version();await test(browser);}
  catch(error){report.error=error.message;process.exitCode=1;}
  finally{fs.writeFileSync(path.join(out,'browser.json'),JSON.stringify(report,null,2));await browser.close();}
})();
