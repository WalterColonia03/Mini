/* Reproduce the registration flow in Chrome against the marked local instance. */
const fs = require('fs');
const path = require('path');
const os = require('os');
const crypto = require('crypto');
const { execFileSync } = require('child_process');
const { chromium } = require(path.join(os.homedir(), '.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright-core'));
const run = process.env.AUDIT03_RUN_DIR;
const out = process.env.AUDIT03_OUT;
const base = 'http://127.0.0.1:' + process.env.AUDIT03_PORT;
const entry = base + '/productos/nuevo/';
const accounts = JSON.parse(fs.readFileSync(path.join(run, '.credentials.json'), 'utf8'));
const report = { stage: '03-F', started: new Date().toISOString(), cases: [], errors: [] };

function record(id, ok, details = {}) {
  report.cases.push({ id, ok: Boolean(ok), ...details });
}
function snapshot() {
  return JSON.parse(execFileSync(process.env.AUDIT03_PYTHON, [path.join(__dirname, 'audit03f_run.py'), 'snapshot'], {
    encoding: 'utf8', env: { ...process.env, PYTHONIOENCODING: 'utf-8' }
  }));
}
async function follow(page, button) {
  await Promise.all([page.waitForNavigation({waitUntil: 'domcontentloaded'}), button.click()]);
}
async function screenshot(page, file) {
  await page.screenshot({path: path.join(out, file + '.png'), fullPage: true});
  return file + '.png';
}
async function login(page, role) {
  await page.goto(base);
  await page.locator('[name=email]').fill(accounts[role].email);
  await page.locator('[name=password]').fill(accounts[role].password);
  await follow(page, page.locator('button[type=submit]'));
}
async function fields(page) {
  return page.locator('form[data-testid=product-form] .field').evaluateAll(nodes => nodes.map(node => {
    const field = node.querySelector('input,select');
    const refs = (field.getAttribute('aria-describedby') || '').split(' ').filter(Boolean);
    return {name: field.name, label: node.querySelector('label').textContent, value: field.value,
      required: field.required, type: field.type, max: field.max, min: field.min, maxLength: field.maxLength,
      mode: field.inputMode, refs, linked: refs.every(id => Boolean(document.getElementById(id)))};
  }));
}
async function fill(page, data) {
  for (const [name, value] of Object.entries(data)) {
    const input = page.locator('[name=' + name + ']');
    if (['category','unit'].includes(name)) await input.selectOption(value);
    else await input.fill(value);
  }
}
async function submit(page, data, url=entry) {
  const cookie = (await page.context().cookies(base)).find(c=>c.name==='audit03f_csrftoken');
  if (!cookie) throw Error('Missing CSRF cookie in the authenticated test context');
  const token = cookie.value;
  return page.request.post(url, {form: data, headers:{'X-CSRFToken': token}, maxRedirects:0});
}
async function disagreements(page, response) {
  if (response.status() !== 200) return {};
  return page.evaluate(html => {
    const doc = new DOMParser().parseFromString(html, 'text/html');
    return Object.fromEntries([...doc.querySelectorAll('.field-error')].map(n =>
      [n.querySelector('input, select').name, n.querySelector('[role=alert]').textContent.trim()]));
  }, await response.text());
}

(async () => {
  const browser = await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe', headless:true});
  const opts = {viewport:{width:1366,height:768}, locale:'es-PE'};
  report.browser = browser.version();
  try {
    const pages = [];
    for (let i = 0; i < 4; i++) pages.push(await (await browser.newContext(opts)).newPage());
    const [admin, warehouse, seller, visitor] = pages;
    const nonce = crypto.randomBytes(32).toString('hex');
    const challenge = await admin.request.get(base, {headers:{'X-Audit03-Fhallenge':nonce}});
    const proof = crypto.createHmac('sha256',fs.readFileSync(path.join(run,'.django-key'))).update(nonce).digest('hex');
    if (challenge.headers()['x-audit03-proof'] !== proof || challenge.headers()['x-audit03-run'] !== path.basename(run)) throw Error('Isolated server identity mismatch');
    await login(admin,'admin');
    await follow(admin,admin.getByRole('link',{name:'Registrar producto',exact:true}));
    const initial = snapshot();
    const categories = Object.fromEntries(initial['catalog.Category'].map(x => [x.name,x.id]));
    const data = {name:'  Atún   de prueba  ',barcode:' Ac-12 34 ',category:categories['Productos enlatados'],unit:'UND',sale_price:'8.50',minimum_stock:''};
    const pristine = await fields(admin);
    const options = await admin.locator('[name=category] option').allTextContents();
    record('F01-current-scope-copy', (await admin.locator('.page-heading h2').innerText())==='Registrar producto' &&
      (await admin.locator('.lede').innerText()).includes('categoría activa') &&
      (await admin.locator('.lede').innerText()).includes('por unidad') &&
      (await admin.locator('.info-panel').innerText()).includes('Todos los productos registrados requieren fecha de vencimiento.') &&
      !await admin.locator('[name=controls_expiration]').count());
    record('C01-initial', admin.url() === entry && pristine.length === 6 && pristine.find(f=>f.name==='minimum_stock').value==='10' &&
      pristine.find(f=>f.name==='unit').value==='UND' && options.includes('Productos enlatados') && options.includes('Higiene') && !options.includes('Suspendida'),
      {fields:pristine, options, screenshot:await screenshot(admin,'01-alta')});
    record('C02-help-links', pristine.every(x=>x.linked) && pristine.filter(x=>x.refs.length).length>=3);
    await follow(admin,admin.getByRole('link',{name:'Cancelar',exact:true}));
    record('C03-cancel', admin.url().endsWith('/inicio/') && snapshot()['catalog.Product'].length===0);
    await admin.goBack();
    await fill(admin,data);
    await follow(admin,admin.getByTestId('product-submit'));
    const saved = snapshot();
    const p = saved['catalog.Product'][0];
    const confirmation = admin.url();
    const body = await admin.locator('[data-testid=product-created]').innerText();
    const key=saved.commerce[0];
    record('C04-persisted',saved['catalog.Product'].length===1 && p.name==='Atún de prueba' && p.barcode==='Ac-12 34' &&
      key.barcode_normalized==='ac-1234' && p.category_id===data.category && p.sale_price==='8.50' && p.minimum_stock===10 && p.unit==='UND' &&
      p.controls_expiration && p.is_active && key.average_cost==='0.0000' && saved['inventory.Lot'].length===0, {product:p,normalisedCode:key.barcode_normalized});
    record('C05-confirmation',confirmation.endsWith('/registrado/') && ['Atún de prueba','Ac-12 34','Productos enlatados','S/ 8,50','10 UND','0 UND','sin stock vigente'].every(t=>body.includes(t)),{text:body,screenshot:await screenshot(admin,'05-confirmacion')});
    await admin.reload();
    const alias = await admin.goto(confirmation.replace('/registrado/','/creado/'));
    record('C06-reload-alias',alias.status()===200 && (await admin.locator('[data-testid=product-created]').innerText())===body && snapshot()['catalog.Product'].length===1);
    await follow(admin,admin.getByRole('link',{name:'Registrar otro producto',exact:true}));
    await fill(admin,{...data, name:'Otro atún',barcode:'a C- 1234',sale_price:'0.00',minimum_stock:'-1'});
    await follow(admin,admin.getByTestId('product-submit'));
    const badFields=await fields(admin);
    const errors=await admin.locator('.field-error').allTextContents();
    record('C07-visible-errors',errors.length===3 && (await admin.locator('[name=name]').inputValue())==='Otro atún' &&
      errors.some(x=>x.includes('Ya existe un producto con este código de barras.')),{errors,screenshot:await screenshot(admin,'07-errores')});
    record('C08-errors-linked',badFields.every(f=>f.linked) && (await admin.locator('input[aria-invalid=true]').count())===3);
    record('C08-first-error-focus',await admin.evaluate(()=>document.activeElement?.name==='barcode'));
    const normal={...data,name:'Producto distinto',barcode:'UNIQUE-02'};
    const cases=[
      ['empty',{},['name','barcode','category','unit','sale_price']],
      ['name-empty',{...normal,name:''},['name']],['name-punctuation',{...normal,name:'--'},['name']],
      ['name-long',{...normal,name:'n'.repeat(161)},['name']],
      ['barcode-empty',{...normal,barcode:' '},['barcode']],['barcode-long',{...normal,barcode:'7'.repeat(65)},['barcode']],
      ['barcode-chars',{...normal,barcode:'A/1'},['barcode']],['barcode-duplicate',{...normal,barcode:'AC - 12 34'},['barcode']],
      ['category-empty',{...normal,category:''},['category']],['category-inactive',{...normal,category:categories.Suspendida},['category']],
      ['category-absent',{...normal,category:'88888888-8888-4888-8888-888888888888'},['category']],
      ['unit-wrong',{...normal,unit:'KG'},['unit']],
      ...['','0','-0.01','8.501','texto','1e2','10000000.00','8,50'].map((v,i)=>['price-'+i,{...normal,sale_price:v},['sale_price']]),
      ...['-1','0.5','texto','1000000'].map((v,i)=>['minimum-'+i,{...normal,minimum_stock:v},['minimum_stock']]),
      ['name-duplicate',{...normal,name:'atún   de prueba'},['name']],
      ['name-uppercase',{...normal,name:'ATÚN DE PRUEBA'},['name']]
    ];
    for (const [id, payload, expected] of cases) {
      const response = await submit(admin,payload);
      const found=await disagreements(admin,response);
      const lengthMessages = {'name-long':'El nombre admite hasta 160 caracteres.','barcode-long':'El código de barras admite hasta 64 caracteres.'};
      record('C09-'+id,response.status()===200 && expected.every(k=>found[k]) &&
        (!lengthMessages[id] || found[expected[0]]===lengthMessages[id]),{status:response.status(),observed:found});
    }
    record('C10-rejections-persistence',JSON.stringify(saved)===JSON.stringify(snapshot()));
    await login(warehouse,'warehouse');
    await follow(warehouse,warehouse.getByRole('link',{name:'Catálogo de productos',exact:true}));
    const row=warehouse.locator('tr').filter({has:warehouse.getByRole('cell',{name:'Ac-12 34',exact:true})});
    record('C11-warehouse-read',(await row.innerText()).includes('Sin stock vigente') && !(await warehouse.getByRole('link',{name:'Registrar producto',exact:true}).count()),{screenshot:await screenshot(warehouse,'11-consulta-almacen')});
    await login(seller,'seller');
    await follow(seller,seller.getByRole('link',{name:/Preparar venta/}).first());
    await seller.locator('[name=query]').fill('Ac-12 34');
    await follow(seller,seller.getByRole('button',{name:'Buscar',exact:true}));
    record('C12-sale-no-stock',(await seller.locator('main').innerText()).includes('No se encontraron productos con existencias vendibles.') && !(await seller.getByRole('button',{name:'Agregar'}).count()), {screenshot:await screenshot(seller,'12-consulta-venta')});
    const beforeRoles=snapshot();
    for (const [label,page] of [['almacenero',warehouse],['vendedor',seller]]) {
      const get=await page.request.get(entry), post=await submit(page,{...normal,name:'Acceso '+label,barcode:'ROLES-'+label});
      const confirm=await page.request.get(confirmation), alt=await page.request.get(confirmation.replace('/registrado/','/creado/'));
      record('C13-'+label,[get,post,confirm,alt].every(x=>x.status()===403),{statuses:[get.status(),post.status(),confirm.status(),alt.status()]});
    }
    const anonymous=await visitor.request.get(entry,{maxRedirects:0});
    record('C14-visitor',anonymous.status()===302,{location:anonymous.headers().location});
    record('C15-role-persistence',JSON.stringify(beforeRoles)===JSON.stringify(snapshot()));
    await admin.goto(entry);
    await fill(admin,{name:'Jabón neutro',barcode:'HIG-01',category:categories.Higiene,unit:'UND',sale_price:'0.01',minimum_stock:'0'});
    await follow(admin,admin.getByTestId('product-submit'));
    const custom=snapshot()['catalog.Product'].find(p=>p.barcode==='HIG-01');
    record('C16-other-category',custom?.category_id===categories.Higiene && custom?.controls_expiration && custom?.sale_price==='0.01' && custom?.minimum_stock===0,{product:custom,screenshot:await screenshot(admin,'16-otra-categoria')});
    const customBefore=snapshot();
    const invalidUnit=await submit(admin,{...normal,category:categories.Higiene,unit:'KG'});
    const unitErrors=await disagreements(admin,invalidUnit);
    record('F02-other-category-unit-guard',invalidUnit.status()===200 && Boolean(unitErrors.unit) &&
      JSON.stringify(customBefore)===JSON.stringify(snapshot()),{errors:unitErrors});
    await warehouse.goto(base+'/productos/');
    const hygieneRow=warehouse.getByRole('row').filter({has:warehouse.getByRole('cell',{name:'HIG-01',exact:true})});
    record('F03-warehouse-other-category',(await hygieneRow.innerText()).includes('Jabón neutro') &&
      (await hygieneRow.innerText()).includes('Higiene') && (await hygieneRow.innerText()).includes('Sin stock vigente'),
      {screenshot:await screenshot(warehouse,'F03-higiene-almacen')});
    await seller.goto(base+'/ventas/');
    await seller.locator('[name=query]').fill('HIG-01');
    await follow(seller,seller.getByRole('button',{name:'Buscar',exact:true}));
    const sellerCatalogue=await seller.request.get(base+'/productos/');
    record('F04-seller-other-category-query',!await seller.getByRole('button',{name:'Agregar'}).count() &&
      sellerCatalogue.status()===403 && JSON.stringify(customBefore)===JSON.stringify(snapshot()),
      {catalogueStatus:sellerCatalogue.status(),screenshot:await screenshot(seller,'F04-higiene-venta')});
    const last = await submit(admin,{...normal,category:categories.Higiene,name:'N'.repeat(160),barcode:'0'.repeat(64),sale_price:'9999999.99',minimum_stock:'999999',controls_expiration:'false',stock:'75',average_cost:'20'});
    const end=snapshot();
    const bound=end['catalog.Product'].find(x=>x.name.length===160);
    record('C17-bounds',last.status()===302 && bound?.category_id===categories.Higiene && bound?.unit==='UND' && bound?.barcode.length===64 && bound?.sale_price==='9999999.99' && bound?.minimum_stock===999999 && bound?.controls_expiration && end['inventory.Lot'].length===0 && end.commerce.find(x=>x.id===bound.id)?.average_cost==='0.0000',{status:last.status(),product:bound});
    const again=await submit(admin,{...data});
    record('C18-replay',again.status()===200 && JSON.stringify(end)===JSON.stringify(snapshot()));
    await follow(admin,admin.getByRole('link',{name:'Ver catálogo',exact:true}));
    record('C19-catalogue',admin.url()===base+'/productos/' && await admin.getByText('Jabón neutro',{exact:true}).count()===1);
    await admin.goto(entry);
    await admin.setViewportSize({width:390,height:844});
    const mobile=await admin.evaluate(()=>({width:innerWidth,page:document.documentElement.scrollWidth}));
    record('C20-mobile',mobile.page<=mobile.width,{...mobile,screenshot:await screenshot(admin,'20-movil')});
    await fill(admin,{...normal,name:'Selección antigua',barcode:'STALE',category:categories.Higiene});
    const categoryTab=await admin.context().newPage();
    await categoryTab.goto(base+'/productos/categorias/');
    const hygiene=categoryTab.getByRole('row').filter({has:categoryTab.getByRole('cell',{name:'Higiene',exact:true})});
    await follow(categoryTab,hygiene.getByRole('button',{name:'Desactivar',exact:true}));
    const suspended=snapshot();
    await follow(admin,admin.getByTestId('product-submit'));
    record('C21-stale-selection',await admin.locator('#id_category_error').count()===1 &&
      (await admin.locator('#id_category_error').innerText()).includes('Seleccione una categoría válida de la lista.') &&
      JSON.stringify(suspended)===JSON.stringify(snapshot()),{screenshot:await screenshot(admin,'21-categoria-suspendida')});
    await follow(admin,admin.getByRole('link',{name:'Volver al inicio',exact:true}));
    await admin.goto(confirmation);
    await follow(admin,admin.getByRole('link',{name:'Ir al inicio',exact:true}));
    record('C22-dashboard-links',admin.url()===base+'/inicio/' && !suspended['sales.Sale'].length && !suspended['sales.SaleDraft'].length);
  } catch(error) {
    report.errors.push({type:error.name,message:error.message.split('\n').slice(0,3).join(' ')});
  } finally {
    report.finished = new Date().toISOString();
    fs.writeFileSync(path.join(out,'browser.json'),JSON.stringify(report,null,2));
    await browser.close();
  }
  console.log(JSON.stringify({cases:report.cases.length,passed:report.cases.filter(c=>c.ok).length,failed:report.cases.filter(c=>!c.ok).map(c=>c.id),errors:report.errors}));
  if (report.errors.length || report.cases.some(c=>!c.ok)) process.exitCode=1;
})();
