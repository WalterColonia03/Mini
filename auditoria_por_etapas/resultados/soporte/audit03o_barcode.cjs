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
async function waitCheck(page, value, duplicate=false) {
  await page.locator('#barcode-capture-input').fill(value);
  const msg=page.locator('#barcode-capture-status');
  await msg.filter({hasText: duplicate?'El código de barras ya está registrado':'Sin duplicados en esta consulta.'}).waitFor();
  check('consulta-'+value,duplicate?await page.locator('#barcode-capture-apply').isDisabled():await page.locator('#barcode-capture-apply').isEnabled());
}
(async()=>{
 const browser=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true});
 try {
  report.browser=browser.version();
  const probe=await browser.newPage(),nonce=crypto.randomBytes(32).toString('hex');
  const response=await probe.request.get(base,{headers:{'X-Audit03-Challenge':nonce}});
  assert.equal(response.headers()['x-audit03-proof'],crypto.createHmac('sha256',fs.readFileSync(path.join(run,'.django-key'))).update(nonce).digest('hex'));
  await probe.close();
  const page=await session(browser,'admin','Registrar producto');
  await page.locator('[name=name]').fill('AUD03 O jabón');
  await page.locator('[name=category]').selectOption({label:'Higiene'});
  await page.locator('[name=sale_price]').fill('7.30');
  const values=await businessValues(page);
  await page.getByRole('button',{name:'Escanear código',exact:true}).click();
  await waitCheck(page,'aud03- bebida',true);
  check('foco-no-cambia',await page.locator('#barcode-capture-input').evaluate(e=>e===document.activeElement));
  await page.keyboard.press('Enter');
  check('enter-sin-submit',report.productPosts.length===0 && await page.locator('#barcode-capture-dialog').isVisible());
  check('bloqueo-visible',await page.locator('#barcode-capture-apply').evaluate(e=>getComputedStyle(e).cursor==='not-allowed'));
  await page.screenshot({path:path.join(out,'01-duplicado.png')});
  // Rapid repeated scans replace the temporary input, preserve all commercial fields.
  for(let i=0;i<10;i++){await page.keyboard.press('Control+a');await page.keyboard.type('AUD03-BEBIDA');}
  await page.locator('#barcode-capture-status').filter({hasText:'ya está registrado'}).waitFor();
  check('relectura-no-concatena',await page.locator('#barcode-capture-input').inputValue()==='AUD03-BEBIDA');
  assert.deepEqual(await businessValues(page),values);check('relectura-no-cambia-ficha',true);
  await waitCheck(page,'AB12AB12');
  // Preserve max64 handling: no stale response may enable a truncated code.
  await page.keyboard.press('Control+a');await page.keyboard.type('X'.repeat(65));
  await page.waitForTimeout(400);
  check('max64-sigue-protegido',await page.locator('#barcode-capture-apply').isDisabled() && (await page.locator('#barcode-capture-error').innerText()).includes('64'));
  await waitCheck(page,'Y'.repeat(64));
  // Delayed stale response must not override a newer completed scan.
  await page.route('**/codigos/comprobar/**',async route=>{
    if(new URL(route.request().url()).searchParams.get('barcode')==='SLOW'){
      await new Promise(resolve=>setTimeout(resolve,700));
      await route.fulfill({status:200,contentType:'application/json',body:JSON.stringify({duplicate:true})}).catch(()=>{});
    } else await route.continue();
  });
  const sent=page.waitForRequest(req=>req.url().includes('barcode=SLOW'));
  await page.locator('#barcode-capture-input').fill('SLOW');await sent;
  await waitCheck(page,'00-NEW-O');await page.waitForTimeout(800);
  check('respuesta-antigua-descartada',await page.locator('#barcode-capture-apply').isEnabled() && (await page.locator('#barcode-capture-status').innerText()).includes('Sin duplicados'));
  await page.unroute('**/codigos/comprobar/**');
  await page.route('**/codigos/comprobar/**',route=>route.abort());
  await page.locator('#barcode-capture-input').fill('AUD03-BEBIDA');
  await page.locator('#barcode-capture-status').filter({hasText:'No se pudo comprobar'}).waitFor();
  check('red-falla-sin-falso-aprobado',await page.locator('#barcode-capture-apply').isEnabled());
  await page.locator('#barcode-capture-apply').click();
  await page.getByRole('button',{name:'Registrar producto',exact:true}).click();
  check('red-falla-servidor-bloquea',await page.getByText('Ya existe un producto con este código de barras.',{exact:true}).isVisible());
  assert.deepEqual(snapshot(),initial);check('consultas-rechazo-sin-escrituras',true);
  await page.unroute('**/codigos/comprobar/**');
  await page.locator('[name=barcode]').fill('AUD03-EMPTY');
  await page.locator('#id_barcode_barcode_check').filter({hasText:'ya está registrado'}).waitFor();
  check('manual-tambien-avisa',true);
  await page.getByRole('button',{name:'Escanear código',exact:true}).click();
  await waitCheck(page,'AB12AB12');await page.locator('#barcode-capture-apply').click();
  await page.getByRole('button',{name:'Registrar producto',exact:true}).click();
  await page.waitForURL(/\/registrado\/$/);
  const created=snapshot();check('alta-expresa-unica',created['catalog.Product'].filter(p=>p.barcode==='AB12AB12').length===1);
  await goEdit(page,'AUD03-BEBIDA');
  await page.getByRole('button',{name:'Escanear código',exact:true}).click();
  await waitCheck(page,'aud03-bebida');
  await waitCheck(page,'AB12AB12',true);
  await waitCheck(page,'00-EDIT-O');await page.locator('#barcode-capture-apply').click();
  await page.getByRole('button',{name:'Guardar cambios',exact:true}).click();await page.waitForURL(base+'/productos/');
  const edited=snapshot();check('edicion-identidad',edited['catalog.Product'].find(p=>p.id===fixture.product_id).barcode==='00-EDIT-O');
  for(const key of Object.keys(created).filter(k=>!['catalog.Product','commerce'].includes(k))){assert.deepEqual(edited[key],created[key]);check('conserva-'+key,true);}
  const manual=await session(browser,'admin','Registrar producto',{javaScriptEnabled:false});
  check('sin-js-manual-disponible',!await manual.locator('#barcode-capture-open').isVisible());
  await manual.locator('[name=name]').fill('AUD03 O sin JS');await manual.locator('[name=barcode]').fill('AB12AB12');
  await manual.locator('[name=category]').selectOption({label:'Higiene'});await manual.locator('[name=sale_price]').fill('2.00');
  await manual.getByRole('button',{name:'Registrar producto',exact:true}).click();
  check('sin-js-duplicado-bloqueado',await manual.getByText('Ya existe un producto con este código de barras.',{exact:true}).isVisible());
  assert.deepEqual(snapshot(),edited);check('sin-js-rechazo-integro',true);
  await manual.locator('[name=barcode]').fill('00-MANUAL-O');await manual.getByRole('button',{name:'Registrar producto',exact:true}).click();await manual.waitForURL(/\/registrado\/$/);
  check('sin-js-alta-unica',snapshot()['catalog.Product'].filter(p=>p.barcode==='00-MANUAL-O').length===1);
  await page.screenshot({path:path.join(out,'02-catalogo.png'),fullPage:true});
 } catch(error){report.error=error.message;process.exitCode=1;}
 finally {fs.writeFileSync(path.join(out,'barcode.json'),JSON.stringify(report,null,2));await browser.close();}
})().catch(error=>{console.error(error.message);process.exitCode=1;});
