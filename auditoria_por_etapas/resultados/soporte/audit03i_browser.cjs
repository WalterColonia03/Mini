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
const report = { stage: '03-I', started: new Date().toISOString(), cases: [], errors: [] };

function record(id, ok, details = {}) {
  report.cases.push({ id, ok: Boolean(ok), ...details });
}
function snapshot() {
  return JSON.parse(execFileSync(process.env.AUDIT03_PYTHON, [path.join(__dirname, 'audit03i_run.py'), 'snapshot'], {
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
  const cookie = (await page.context().cookies(base)).find(c=>c.name==='audit03i_csrftoken');
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
  const browser=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true});
  report.browser=browser.version();
  const pages=[];
  for(let i=0;i<4;i++)pages.push(await (await browser.newContext({viewport:{width:1366,height:900},locale:'es-PE'})).newPage());
  const [a,w,s,v]=pages;
  const equal=(x,y)=>JSON.stringify(x)===JSON.stringify(y);
  try {
    const nonce=crypto.randomBytes(32).toString('hex');
    const probe=await a.request.get(base,{headers:{'X-Audit03-Challenge':nonce}});
    if(probe.headers()['x-audit03-proof']!==crypto.createHmac('sha256',fs.readFileSync(path.join(run,'.django-key'))).update(nonce).digest('hex'))throw Error('Isolation mismatch');
    await login(a,'admin');await login(w,'warehouse');await login(s,'seller');
    await follow(a,a.getByRole('link',{name:'Registrar producto',exact:true}));
    const before=snapshot();
    const cat=before['catalog.Category'].find(c=>c.name==='Higiene').id;
    const field=a.locator('[name=minimum_stock]');
    record('H01-initial',await field.inputValue()==='10' && await field.getAttribute('min')==='0' &&
      await field.getAttribute('max')==='999999',{screenshot:await screenshot(a,'01-minimo')});
    const normal={name:'Mínimo normal',barcode:'H-NORMAL',category:cat,unit:'UND',sale_price:'8.50'};
    for(const [label,value] of [['vacio',''],['cero','0'],['maximo','999999']]){
      await a.goto(entry);await fill(a,{...normal,name:'Mínimo '+label,barcode:'H-'+label,minimum_stock:value});
      await follow(a,a.getByTestId('product-submit'));
      const product=snapshot()['catalog.Product'].find(p=>p.barcode==='H-'+label);
      record('H02-create-'+label,product?.minimum_stock===(value===''?10:Number(value)) && product.unit==='UND',
        {stored:product?.minimum_stock});
    }
    const omit=await submit(a,{...normal,name:'Mínimo omitido',barcode:'H-OMIT'});
    record('H03-omitted',omit.status()===302 && snapshot()['catalog.Product'].find(p=>p.barcode==='H-OMIT')?.minimum_stock===10);
    const baseline=snapshot();
    async function invalid(url,data,label){
      const response=await submit(a,data,url);
      const html=await response.text();
      record(label,response.status()===200 && html.includes('id_minimum_stock_error') && equal(baseline,snapshot()),{status:response.status()});
    }
    for(const val of ['-1','0.5','NaN','1e6','1000000','texto']){
      await invalid(entry,{...normal,barcode:'H-REJECT',minimum_stock:val},'H04-create-reject-'+val);
    }
    await follow(w,w.getByRole('link',{name:'Catálogo de productos',exact:true}));
    const row=w.getByRole('row').filter({has:w.getByRole('cell',{name:'H-maximo',exact:true})});
    const rowText=await row.innerText();
    record('H05-warehouse',rowText.includes('999999') && rowText.includes('Sin stock vigente') &&
      !await w.getByRole('link',{name:'Editar',exact:true}).count(),{row:rowText,screenshot:await screenshot(w,'05-almacen')});
    await follow(s,s.getByRole('link',{name:'Preparar venta',exact:true}));
    await s.locator('[name=query]').fill('H-maximo');await follow(s,s.getByRole('button',{name:'Buscar',exact:true}));
    record('H06-seller',!await s.getByRole('button',{name:'Agregar',exact:true}).count());
    const product=baseline['catalog.Product'].find(p=>p.barcode==='H-maximo');
    const edit=base+'/productos/'+product.id+'/editar/';
    for(const value of ['0','999999']){
      await a.goto(edit);await a.locator('[name=minimum_stock]').fill(value);
      await follow(a,a.getByRole('button',{name:'Guardar cambios',exact:true}));
      record('H07-edit-'+value,snapshot()['catalog.Product'].find(p=>p.id===product.id).minimum_stock===Number(value));
    }
    for(const val of ['', '-1','0.5','NaN','1e6','1000000','texto']){
      await invalid(edit,{name:product.name,barcode:product.barcode,category:cat,sale_price:'8.50',minimum_stock:val},'H08-edit-reject-'+val);
    }
    await a.goto(edit);await a.locator('[name=minimum_stock]').fill('0.5');
    await follow(a,a.getByRole('button',{name:'Guardar cambios',exact:true}));
    record('H09-error-visible',await a.locator('#id_minimum_stock_error').isVisible() && equal(baseline,snapshot()),
      {screenshot:await screenshot(a,'09-error-edicion')});
    for(const [role,page] of [['warehouse',w],['seller',s]]){
      const create=await submit(page,{...normal,minimum_stock:'10'});
      const change=await submit(page,{...normal,minimum_stock:'10'},edit);
      record('H10-role-'+role,create.status()===403 && change.status()===403 && equal(baseline,snapshot()));
    }
    const guest=await v.request.get(edit,{maxRedirects:0});
    record('H11-guest',guest.status()===302);
    const final=snapshot();
    record('H12-final',equal(baseline,final) && final['catalog.Product'].length===4 && !final['inventory.Lot'].length &&
      !final['sales.Sale'].length && equal(before['cash.CashShift'],final['cash.CashShift']));

    // Accepted name policy: real form errors, persistence and cross-role reads.
    const nameData={...normal,name:'  Leche   Gloria  400 g ',barcode:'I-MILK-400',minimum_stock:'10'};
    await a.goto(entry);await fill(a,nameData);await follow(a,a.getByTestId('product-submit'));
    let milk=snapshot()['catalog.Product'].find(p=>p.barcode==='I-MILK-400');
    record('I01-normalized-name',milk?.name==='Leche Gloria 400 g');
    const afterMilk=snapshot();
    await a.goto(entry);await fill(a,{...nameData,name:'LECHE GLORIA 400 G',barcode:'I-DUP'});
    await follow(a,a.getByTestId('product-submit'));
    record('I02-duplicate-visible',await a.locator('#id_name_error').isVisible() &&
      await a.locator('#id_name_error').innerText()==='Ya existe un producto registrado con este nombre.' &&
      await a.locator('[name=name]').evaluate(el=>el===document.activeElement) && equal(afterMilk,snapshot()),
      {screenshot:await screenshot(a,'i02-duplicate')});
    await a.goto(entry);await fill(a,{...nameData,name:'Leche Gloria 170 g',barcode:'I-MILK-170'});
    await follow(a,a.getByTestId('product-submit'));
    const small=snapshot()['catalog.Product'].find(p=>p.barcode==='I-MILK-170');
    record('I03-presentation',!!small && snapshot()['catalog.Product'].length===6);
    const beforeEdit=snapshot();
    const smallEdit=base+'/productos/'+small.id+'/editar/';
    await a.goto(smallEdit);await fill(a,{name:'  leche   gloria 400 g',barcode:'I-NOT-SAVED',sale_price:'9.20',minimum_stock:'0'});
    await follow(a,a.getByRole('button',{name:'Guardar cambios',exact:true}));
    record('I04-edit-duplicate-rollback',await a.locator('#id_name_error').isVisible() && equal(beforeEdit,snapshot()),
      {screenshot:await screenshot(a,'i04-edit-duplicate')});
    await a.goto(smallEdit);await fill(a,{name:' LECHE  GLORIA 170 g ',minimum_stock:'999999'});
    await follow(a,a.getByRole('button',{name:'Guardar cambios',exact:true}));
    record('I05-self-edit',snapshot()['catalog.Product'].find(p=>p.id===small.id)?.name==='LECHE GLORIA 170 g');
    await a.goto(base+'/productos/');
    const milkRow=a.getByRole('row').filter({has:a.getByRole('cell',{name:'I-MILK-400',exact:true})});
    await follow(a,milkRow.getByRole('button'));
    const afterInactive=snapshot();
    const duplicated=await submit(a,{...nameData,name:'LECHE GLORIA 400 g',barcode:'I-DUP-INACTIVE'});
    record('I06-inactive-reserves-name',!afterInactive['catalog.Product'].find(p=>p.id===milk.id).is_active &&
      duplicated.status()===200 && (await duplicated.text()).includes('Ya existe un producto registrado con este nombre.') &&
      equal(afterInactive,snapshot()));
    await w.goto(base+'/productos/?q=leche');
    record('I07-warehouse-names',await w.getByRole('cell',{name:'Leche Gloria 400 g',exact:true}).count()===1 &&
      await w.getByRole('cell',{name:'LECHE GLORIA 170 g',exact:true}).count()===1 &&
      !await w.getByRole('link',{name:'Editar',exact:true}).count(),{screenshot:await screenshot(w,'i07-warehouse')});
    await s.locator('[name=query]').fill('LECHE GLORIA 170');await follow(s,s.getByRole('button',{name:'Buscar',exact:true}));
    record('I08-seller-no-stock',!await s.getByRole('button',{name:'Agregar',exact:true}).count());
    const finalNames=snapshot();
    record('I09-final',equal(afterInactive,finalNames) && finalNames['catalog.Product'].length===6 &&
      equal(before['cash.CashShift'],finalNames['cash.CashShift']) && !finalNames['sales.Sale'].length && !finalNames['inventory.Lot'].length);
  }catch(error){report.errors.push({type:error.name,message:error.message.split('\n').slice(0,3).join(' ')});}
  finally{
    report.finished=new Date().toISOString();fs.writeFileSync(path.join(out,'browser.json'),JSON.stringify(report,null,2));await browser.close();
  }
  console.log(JSON.stringify({cases:report.cases.length,passed:report.cases.filter(c=>c.ok).length,failed:report.cases.filter(c=>!c.ok).map(c=>c.id),errors:report.errors}));
  if(report.errors.length || report.cases.some(c=>!c.ok))process.exitCode=1;
})();
