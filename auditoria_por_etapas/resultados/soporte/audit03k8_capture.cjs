// Exercise the optional scan dialog through Chrome. Keyboard emulation, no phone.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const crypto = require('node:crypto');
const {execFileSync} = require('node:child_process');
const {chromium} = require(path.join(os.homedir(), '.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright-core'));
const run = process.env.AUDIT03_RUN_DIR;
const out = process.env.AUDIT03_OUT;
const base = 'http://127.0.0.1:' + process.env.AUDIT03_PORT;
const load = pathname => JSON.parse(fs.readFileSync(pathname, 'utf8'));
const report = {source:'Chrome keyboard, Ctrl+A and text', cases:[], productPosts:[]};
const initial = load(path.join(out, 'orm-initial.json'));
const credentials = load(path.join(run, '.credentials.json'));
const fixture = load(path.join(out, 'fixture.json'));
function snapshot() {
  return JSON.parse(execFileSync(process.env.AUDIT03_PYTHON, [path.join(__dirname,'audit03k_run.py'),'snapshot'], {
    encoding:'utf8', env:{...process.env, PYTHONIOENCODING:'utf-8'}
  }));
}
function check(id,condition,detail={}) {
  report.cases.push({id, ok:!!condition, ...detail});
  assert.ok(condition,id);
}
async function session(browser, role, menu, options={}) {
  const context = await browser.newContext({locale:'es-PE',viewport:{width:1280,height:900},...options});
  const page = await context.newPage();
  await page.goto(base);
  await page.locator('[name=email]').fill(credentials[role].email);
  await page.locator('[name=password]').fill(credentials[role].password);
  await page.locator('button[type=submit]').click();
  await page.getByRole('link',{name:menu,exact:true}).click();
  page.on('request', request => {
    const {pathname} = new URL(request.url());
    if (request.method()==='POST' && pathname.startsWith('/productos/')) report.productPosts.push({role,pathname});
  });
  return page;
}
async function readCode(page, code) {
  await page.keyboard.press('Control+a');
  await page.keyboard.type(code);
}
function businessValues(page) {
  return page.locator('form[method=post] :is(input,select)[name]:not([type=hidden])').evaluateAll(nodes =>
    Object.fromEntries(nodes.map(node=>[node.name,node.value])));
}
async function goEdit(page,code) {
  await page.getByRole('link',{name:'Productos',exact:true}).click();
  await page.getByRole('row').filter({has:page.getByRole('cell',{name:code,exact:true})})
    .getByRole('link',{name:'Editar',exact:true}).click();
}
async function capture(page,mode,finalCode) {
  const startValues=await businessValues(page);
  const posts=report.productPosts.length;
  const button=page.getByRole('button',{name:'Escanear código',exact:true});
  const dialog=page.getByRole('dialog',{name:'Escanear código',exact:true});
  const draft=dialog.getByRole('textbox',{name:'Código leído',exact:true});
  const apply=dialog.getByRole('button',{name:'Usar código',exact:true});
  const cancel=dialog.getByRole('button',{name:'Cancelar',exact:true});
  await button.click();
  check(mode+'-inicio',await draft.inputValue()==='' && await apply.isDisabled() &&
    await draft.evaluate(e=>e===document.activeElement) && await dialog.evaluate(e=>e.matches(':modal')));
  await page.locator('[name=name]').evaluate(e=>e.focus());
  check(mode+'-foco-externo-bloqueado',!await page.locator('[name=name]').evaluate(e=>e===document.activeElement));
  await readCode(page,'00CAT03K-A');
  for (const [i,code] of ['00CAT03K-B','00CAT03K-A','00CAT03K-A'].entries()) {
    await cancel.focus();
    await readCode(page,code);
    check(mode+'-lectura-'+i,await draft.inputValue()===code && await draft.evaluate(e=>e===document.activeElement));
  }
  await page.keyboard.press('Enter');
  check(mode+'-enter',await dialog.isVisible() && report.productPosts.length===posts);
  await page.keyboard.press('Escape');
  check(mode+'-escape',!await dialog.isVisible() && await button.evaluate(e=>e===document.activeElement));
  assert.deepEqual(await businessValues(page),startValues);check(mode+'-escape-conserva-ficha',true);
  await button.click();
  await readCode(page,'PARCIAL');
  await cancel.click();
  assert.deepEqual(await businessValues(page),startValues);check(mode+'-cancelar-conserva-ficha',true);
  await button.click();
  await readCode(page,'X'.repeat(65));
  check(mode+'-desborde',await apply.isDisabled() && (await dialog.getByRole('alert').innerText()).includes('64'));
  await readCode(page,'Y'.repeat(64));
  check(mode+'-limite',await draft.inputValue()==='Y'.repeat(64) && await apply.isEnabled());
  await readCode(page,finalCode);
  await page.screenshot({path:path.join(out,mode+'-revision.png')});
  await apply.click();
  const expected={...startValues,barcode:finalCode};
  assert.deepEqual(await businessValues(page),expected);
  check(mode+'-solo-codigo',!await dialog.isVisible() && report.productPosts.length===posts,{barcode:finalCode});
}
(async()=>{
  const browser=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true});
  try {
    report.browser=browser.version();
    const probe=await browser.newPage();
    const nonce=crypto.randomBytes(32).toString('hex');
    const response=await probe.request.get(base,{headers:{'X-Audit03-Challenge':nonce}});
    assert.equal(response.headers()['x-audit03-proof'],crypto.createHmac('sha256',fs.readFileSync(path.join(run,'.django-key'))).update(nonce).digest('hex'),'Isolation mismatch');
    await probe.close();
    const admin=await session(browser,'admin','Registrar producto');
    await admin.locator('[name=name]').fill('AUD03 K8 jabón por unidad');
    await admin.locator('[name=category]').selectOption({label:'Higiene'});
    await admin.locator('[name=sale_price]').fill('7.30');
    const repeat='AB12AB12';
    await capture(admin,'alta',repeat);
    assert.deepEqual(snapshot(),initial);check('alta-sin-escrituras',true);
    await admin.getByRole('button',{name:'Registrar producto',exact:true}).click();
    await admin.waitForURL(/\/registrado\/$/);
    const saved=snapshot();
    const added=saved['catalog.Product'].filter(p=>p.barcode===repeat);
    check('alta-expresa',added.length===1 && added[0].sale_price==='7.30' && saved['catalog.Product'].length===initial['catalog.Product'].length+1);
    await goEdit(admin,'AUD03-BEBIDA');
    await capture(admin,'edicion',repeat);
    await admin.getByRole('button',{name:'Guardar cambios',exact:true}).click();
    check('duplicado-servidor',await admin.getByText('Ya existe un producto con este código de barras.',{exact:true}).isVisible());
    assert.deepEqual(snapshot(),saved);check('duplicado-sin-escrituras',true);
    const newCode='00CAT03K-C';
    await admin.getByRole('button',{name:'Escanear código',exact:true}).click();
    await readCode(admin,newCode);
    await admin.getByRole('button',{name:'Usar código',exact:true}).click();
    await admin.getByRole('button',{name:'Guardar cambios',exact:true}).click();
    await admin.waitForURL(base+'/productos/');
    const final=snapshot();
    check('edicion-identidad',final['catalog.Product'].find(p=>p.id===fixture.product_id)?.barcode===newCode);
    for(const key of Object.keys(saved).filter(k=>!['catalog.Product','commerce'].includes(k))) {
      assert.deepEqual(final[key],saved[key]);check('conservado-'+key,true);
    }
    const warehouse=await session(browser,'warehouse','Catálogo de productos');
    const whRow=warehouse.getByRole('row').filter({has:warehouse.getByRole('cell',{name:newCode,exact:true})});
    const whCells=await whRow.getByRole('cell').allInnerTexts();
    check('almacen-ficha-correcta',whCells[0]==='AUD03 Bebida de prueba' && whCells[3]==='8,50' && whCells[4]==='19' && !await whRow.getByRole('link',{name:'Editar',exact:true}).count(),{cells:whCells});
    const seller=await session(browser,'seller','Preparar venta');
    await seller.locator('[name=query]').fill(newCode);
    await seller.getByRole('button',{name:'Buscar',exact:true}).click();
    const sellRow=seller.getByRole('row').filter({has:seller.getByRole('cell',{name:newCode,exact:true})});
    check('mostrador',await sellRow.getByRole('button',{name:'Agregar',exact:true}).isVisible());
    const manual=await session(browser,'admin','Registrar producto',{javaScriptEnabled:false});
    check('sin-js-control-oculto',!await manual.locator('#barcode-capture-open').isVisible());
    await manual.locator('[name=name]').fill('AUD03 K8 manual');
    await manual.locator('[name=barcode]').fill('00-MANUAL');
    await manual.locator('[name=category]').selectOption({label:'Higiene'});
    await manual.locator('[name=sale_price]').fill('1.75');
    await manual.getByRole('button',{name:'Registrar producto',exact:true}).click();
    await manual.waitForURL(/\/registrado\/$/);
    check('sin-js-alta-manual',snapshot()['catalog.Product'].filter(p=>p.barcode==='00-MANUAL').length===1);
  } catch(error) {report.error=error.message;process.exitCode=1;}
  finally {fs.writeFileSync(path.join(out,'capture.json'),JSON.stringify(report,null,2));await browser.close();}
})().catch(error=>{console.error(error.message);process.exitCode=1;});
