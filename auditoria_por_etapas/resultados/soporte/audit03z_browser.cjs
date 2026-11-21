const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const crypto = require('node:crypto');
const assert = require('node:assert/strict');
const {execFileSync} = require('node:child_process');
const {chromium} = require(path.join(os.homedir(), '.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright-core'));
const out = process.env.AUDIT03_OUT;
const run = process.env.AUDIT03_RUN_DIR;
const base = 'http://127.0.0.1:' + process.env.AUDIT03_PORT;
const beforeFix = process.argv[2] === 'z-before';
const report = {phase: process.argv[2], input: 'Chrome keyboard; selection loss deliberately simulated', checks: [], captures: []};
const accounts = JSON.parse(fs.readFileSync(path.join(run, '.credentials.json')));
function check(id, observed, expected) {
  assert.deepEqual(observed, expected, id);
  report.checks.push(id);
}
function state() {
  return JSON.parse(execFileSync(process.env.AUDIT03_PYTHON, [path.join(__dirname, 'audit03y_browser_run.py'), 'snapshot'], {encoding:'utf8'}));
}
const button = (page, name) => page.getByRole('button', {name, exact:true});
const link = (page, name) => page.getByRole('link', {name, exact:true});
async function login(browser, alias, menu) {
  const page = await browser.newPage({locale:'es-PE'});
  await page.goto(base);
  await page.locator('[name=email]').fill(accounts[alias].email);
  await page.locator('[name=password]').fill(accounts[alias].password);
  await page.locator('button[type=submit]').click();
  await link(page, menu).click();
  return page;
}
async function test(browser) {
  const probe = await browser.newPage();
  const nonce = crypto.randomBytes(32).toString('hex');
  const response = await probe.request.get(base, {headers:{'X-Audit03-Challenge':nonce}});
  check('entorno aislado', response.headers()['x-audit03-proof'],
        crypto.createHmac('sha256', fs.readFileSync(path.join(run,'.django-key'))).update(nonce).digest('hex'));
  await probe.close();
  if (process.argv[2]==='aa-box') {
    await testPackage(browser);
    return;
  }
  const admin = await login(browser,'admin','Registrar producto');
  const posts = [];
  admin.on('request', r => {if (r.method()==='POST') posts.push(new URL(r.url()).pathname);});
  const kind = admin.locator('[name=barcode_type]');
  const final = admin.locator('[name=barcode]');
  const field = admin.locator('#barcode-capture-input');
  const status = admin.locator('#barcode-capture-status');
  const initial = state();
  check('históricos preparados',initial['sales.SaleLine'].length,3);
  await kind.selectOption('INTERNAL');
  await admin.locator('[name=name]').fill('Interno Z');
  await admin.locator('[name=category]').selectOption({label:'Higiene'});
  await admin.locator('[name=sale_price]').fill('4.00');
  if (!beforeFix) {
    await button(admin,'Escanear código').click();
    await admin.keyboard.type('00AB');
    await admin.keyboard.press('Control+a');
    await admin.keyboard.press('End');
    await admin.keyboard.type('AB');
    check('edición manual conserva el movimiento intencional del cursor',await field.inputValue(),'00ABAB');
    await button(admin,'Cancelar').click();
    check('cancelar conserva el campo definitivo',await final.inputValue(),'');
    await button(admin,'Escanear código').click();
    await admin.keyboard.type('123');
    await admin.keyboard.press('Control+a');
    await field.evaluate(f=>f.setSelectionRange(f.value.length,f.value.length));
    const limit = 'X'.repeat(64);
    await admin.keyboard.insertText(limit);
    await status.filter({hasText:'Sin duplicados'}).waitFor();
    check('reemplazo de 64 caracteres sin recorte',await field.inputValue(),limit);
    await button(admin,'Cancelar').click();
  }
  for (const [first,second] of [['Z01','Z01'],['Z01','NUEVO02'],['','ABAB']]) {
    await button(admin,'Escanear código').click();
    if (first) {
      await admin.keyboard.type(first);
      await admin.keyboard.press('Control+a');
      // Reproduce the lost selection without a user's navigation key or pointer action.
      await field.evaluate(f => f.setSelectionRange(f.value.length,f.value.length));
    }
    await admin.keyboard.type(second);
    await status.filter({hasText:'Sin duplicados'}).waitFor();
    const expected = beforeFix ? first+second : second;
    report.captures.push({first,second,temporary:await field.inputValue()});
    check('temporal '+second,await field.inputValue(),expected);
    const previous = await final.inputValue();
    await admin.keyboard.press('Enter');
    check('sin copia implícita '+second,await final.inputValue(),previous);
    await button(admin,'Usar código').click();
    check('copia expresa '+second,await final.inputValue(),expected);
    check('cero envíos por captura '+second,posts.length,0);
    if (beforeFix && first !== second && first) break;
  }
  check('captura sin escritura',state(),initial);
  await button(admin,'Registrar producto').click();
  await admin.waitForURL(/registrado/);
  const saved = state();
  const created = saved['catalog.Product'].find(p=>p.name==='Interno Z');
  check('valor guardado',created.barcode,beforeFix ? 'Z01NUEVO02' : 'ABAB');
  check('una ficha nueva',saved['catalog.Product'].length,4);
  check('un POST explícito',posts.length,1);
  if (beforeFix) return;
  await link(admin,'Productos').click();
  const row = (page,name) => page.getByRole('row').filter({has:page.getByRole('cell',{name,exact:true})});
  for (const name of ['Anterior Z1','Anterior Z2','Anterior Z3']) {
    if (!admin.url().endsWith('/productos/')) await link(admin,'Productos').first().click();
    await row(admin,name).getByRole('link',{name:'Editar'}).click();
    check('tipo anterior '+name,await kind.inputValue(),'UNCLASSIFIED');
    await kind.selectOption('GTIN');
    await button(admin,'Guardar cambios').click();
    if (name!=='Anterior Z3') {
      await admin.getByRole('alert').filter({hasText:'Ya existe un producto con este código de barras'}).waitFor();
      check('rechazo atómico '+name,state(),saved);
    } else {
      await admin.waitForURL(base+'/productos/');
    }
  }
  const updated = state();
  const third = saved['catalog.Product'].find(p=>p.name==='Anterior Z3');
  const expected = structuredClone(saved);
  expected.identity.find(p=>p.id===third.id).barcode_type='GTIN';
  expected['catalog.ProductBarcodeKey'].push({product_id:third.id,reading_key:'0'+third.barcode});
  expected['catalog.ProductBarcodeKey'].sort((a,b)=>a.reading_key.localeCompare(b.reading_key));
  check('sólo cambian el tipo y la reserva de la tercera ficha',updated,expected);
  for (const [alias,menu,query] of [['warehouse','Catálogo de productos','q'],['seller','Preparar venta','query']]) {
    const page = await login(browser,alias,menu);
    await page.locator('[name='+query+']').fill('0'+third.barcode);
    await button(page,'Buscar').click();
    check('consulta alias y seis unidades '+alias,/\b6\b/.test(await row(page,third.name).innerText()),true);
    const url = base+'/productos/'+third.id+'/editar/';
    check('GET edición denegado '+alias,(await page.request.get(url)).status(),403);
    const cookies = await page.context().cookies();
    const token = cookies.find(c=>c.name==='audit03k_csrftoken').value;
    check('POST edición denegado '+alias,(await page.request.post(url,{form:{csrfmiddlewaretoken:token,barcode_type:'INTERNAL',barcode:'INT-ALTERADO'}})).status(),403);
  }
  check('consultas y rechazos conservan los datos',state(),updated);
}
async function testPackage(browser) {
  const before = state();
  const outer = '14006381333938';
  check('tres fichas', before['catalog.Product'].length, 3);
  check('seis lotes', before['inventory.Lot'].length, 6);
  const admin = await login(browser, 'admin', 'Registrar producto');
  const codeCheck = await admin.request.get(base+'/productos/codigos/comprobar/', {params:{barcode_type:'GTIN', barcode:outer}});
  check('servidor rechaza caja como GTIN de unidad', codeCheck.status(), 400);
  check('motivo de rechazo', (await codeCheck.json()).error.includes('GTIN'), true);
  for (const [alias,menu,field,index] of [['warehouse','Catálogo de productos','q',4],['seller','Preparar venta','query',2]]) {
    const page = await login(browser,alias,menu);
    const posts=[];
    page.on('request',r=>{if(r.method()==='POST') posts.push(new URL(r.url()).pathname);});
    const table = alias==='seller' ? page.locator('.sales-search-panel') : page.locator('main');
    for (const [query,name,stock] of [['4006381333931','Unidad AA',6],['00-BB','Interno BB',7],
                                    ['04006381333931','Unidad AA',6],['012345678905','Unidad CC',8],[outer,null,0]]) {
      await page.locator('[name='+field+']').fill(query);
      await button(page,'Buscar').click();
      const rows = table.locator('tbody tr');
      check(alias+' filas '+query,await rows.count(), name ? 1 : 0);
      if (name) {
        const cells=rows.first().getByRole('cell');
        check(alias+' ficha '+query,await cells.first().innerText(),name);
        check(alias+' unidades '+query,Number.parseInt(await cells.nth(index).innerText(),10),stock);
      } else {
        check(alias+' caja sin coincidencia',(await table.innerText()).includes('No se encontraron productos'),true);
      }
    }
    check(alias+' consultas sin POST',posts,[]);
  }
  check('fichas, reservas, ventas, lotes y borradores intactos',state(),before);
}
(async () => {
  const browser=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true});
  try {report.chrome=browser.version();await test(browser);}
  catch (error) {report.error=error.message;process.exitCode=1;}
  finally {fs.writeFileSync(path.join(out,'browser.json'),JSON.stringify(report,null,2));await browser.close();}
})();
