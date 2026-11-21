/* Reproduce the availability flow in Chrome against the marked local instance. */
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
const report = { stage: '03-E', started: new Date().toISOString(), cases: [], errors: [] };

function record(id, ok, details = {}) {
  report.cases.push({ id, ok: Boolean(ok), ...details });
}
function snapshot() {
  return JSON.parse(execFileSync(process.env.AUDIT03_PYTHON, [path.join(__dirname, 'audit03e_run.py'), 'snapshot'], {
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
  const cookie = (await page.context().cookies(base)).find(c=>c.name==='audit03e_csrftoken');
  if (!cookie) throw Error('Missing CSRF cookie in the authenticated test context');
  const token = cookie.value;
  return page.request.post(url, {form: data, headers:{'X-CSRFToken': token}, maxRedirects:0});
}
async function disagreements(page, response) {
  if (response.status() !== 200) return {};
  return page.evaluate(html => {
    const doc = new DOMParser().parseFromString(html, 'text/html');
    return Object.fromEntries([...doc.querySelectorAll('[aria-invalid=true]')].map(input =>
      [input.name, input.parentElement.querySelector('.text-danger')?.textContent.trim() || '']));
  }, await response.text());
}
(async()=>{
  const browser=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true});
  report.browser=browser.version();
  const pages=[];
  for(let i=0;i<4;i++) pages.push(await (await browser.newContext({viewport:{width:1366,height:900},locale:'es-PE'})).newPage());
  const [a,w,s,v]=pages;for(const page of pages)page.setDefaultTimeout(12000);
  const fx=JSON.parse(fs.readFileSync(path.join(out,'fixture.json'),'utf8'));
  const initial=snapshot(),id=fx.product_id,empty=fx.empty_product_id,expired=fx.expired_product_id;
  const original=initial['catalog.Product'].find(p=>p.id===id);
  const route=base+'/productos/'+id+'/disponibilidad/';
  const equal=(x,y)=>JSON.stringify(x)===JSON.stringify(y);
  const current=(pid=id)=>snapshot()['catalog.Product'].find(p=>p.id===pid);
  const preserved=(state)=>['inventory.Lot','inventory.InitialInventoryLoad','sales.Sale','sales.SaleLine','sales.SaleDraft','sales.SaleDraftLine','cash.CashShift','commerce'].every(k=>equal(initial[k],state[k]));
  function row(page,pid=id){return page.locator('tbody tr').filter({has:page.locator('form[action="/productos/'+pid+'/disponibilidad/"]')});}
  async function toggle(pid=id){await a.goto(base+'/productos/');await follow(a,row(a,pid).getByRole('button'));}
  async function setCategory(){
    await a.goto(base+'/productos/categorias/');
    const categoryRow=a.getByRole('row').filter({has:a.getByRole('cell',{name:'Productos enlatados',exact:true})});
    const data=await categoryRow.locator('form').evaluate(form=>Object.fromEntries([...new FormData(form)].filter(([name])=>name!=='csrfmiddlewaretoken')));
    await follow(a,categoryRow.getByRole('button'));
    return data;
  }
  async function search(code=original.barcode){await s.goto(base+'/ventas/');await s.locator('[name=query]').fill(code);await follow(s,s.getByRole('button',{name:'Buscar',exact:true}));return s.getByRole('button',{name:'Agregar',exact:true}).count();}
  async function inventory(field, pid, shouldExist) {
    await w.goto(base+field);
    const ids=await w.locator('[name=product] option').evaluateAll(nodes=>nodes.map(n=>n.value));
    return ids.includes(pid)===shouldExist;
  }
  try {
    const nonce=crypto.randomBytes(32).toString('hex');
    const probe=await a.request.get(base,{headers:{'X-Audit03-Challenge':nonce}});
    if(probe.headers()['x-audit03-proof']!==crypto.createHmac('sha256',fs.readFileSync(path.join(run,'.django-key'))).update(nonce).digest('hex'))throw Error('Isolation mismatch');
    await login(a,'admin');await login(w,'warehouse');await login(s,'seller');
    await follow(s,s.getByRole('link',{name:'Preparar venta',exact:true}));
    const receipt=base+'/ventas/constancia/'+fx.sale_id+'/';
    await s.goto(receipt);const historic=await s.locator('#constancia-interna').innerText();
    await a.goto(receipt);const adminHistoric=await a.locator('#constancia-interna').innerText();
    await follow(a,a.getByRole('link',{name:'Productos',exact:true}));
    record('E01-active-visible',(await row(a).innerText()).includes('Disponible')&&await search()===1,{screenshot:await screenshot(a,'01-activo')});
    const form=row(a).locator('form');
    const captured=await form.evaluate(f=>Object.fromEntries([...new FormData(f)].filter(([name])=>name!=='csrfmiddlewaretoken')));
    await follow(a,row(a).getByRole('button',{name:'Deshabilitar',exact:true}));
    record('E02-disabled',current().is_active===false&&preserved(snapshot()),{screenshot:await screenshot(a,'02-inactivo')});
    const offText=await row(a).innerText();
    record('E03-inactive-label',offText.includes('Inactivo'),{row:offText});
    const replay=await submit(a,captured,route);
    record('E04-replay-disable',replay.status()===302&&!current().is_active,{requestState:captured.is_active??null,status:replay.status(),observed:current().is_active});
    if(current().is_active){await toggle();report.observations=[{id:'initial-replay-recovery',action:'disabled again to continue independent cases'}];}
    record('E05-seller-search',await search()===0,{screenshot:await screenshot(s,'05-sin-venta')});
    await s.locator('.draft-line-actions [name=quantity]').fill('3');await follow(s,s.getByRole('button',{name:'Actualizar',exact:true}));
    const updateText=await s.locator('main').innerText();
    record('E06-draft-reject',preserved(snapshot())&&updateText.includes('no está disponible'),{message:updateText.split('\n').filter(t=>t.includes('disponib'))});
    await s.goto(base+'/ventas/cobrar/');await s.locator('[name=cash_received]').fill('30.00');
    await follow(s,s.getByRole('button',{name:'Confirmar cobro',exact:true}));
    const checkout=await s.locator('main').innerText();
    record('E07-checkout-reject',checkout.includes('ya no está disponible para la venta')&&preserved(snapshot()),{screenshot:await screenshot(s,'07-cobro-denegado')});
    record('E08-warehouse-entry',await inventory('/inventario/entrada/',id,false));
    await toggle(empty);
    record('E09-warehouse-initial',await inventory('/inventario/carga-inicial/',empty,false));
    await w.goto(base+'/productos/');
    const wh=w.getByRole('row').filter({has:w.getByRole('cell',{name:original.barcode,exact:true})});
    record('E10-warehouse-state',(await wh.innerText()).includes('Inactivo')&&(await wh.innerText()).includes('19'),{row:await wh.innerText()});
    await s.goto(receipt);await a.goto(receipt);
    record('E11-receipts',(await s.locator('#constancia-interna').innerText())===historic&&(await a.locator('#constancia-interna').innerText())===adminHistoric);
    await toggle();
    const activeText=await a.locator('main').innerText();
    const restoredCount = await search();
    const restoredRow = await s.locator('tbody tr').innerText();
    record('E12-reactivation',current().is_active&&restoredCount===1&&preserved(snapshot())&&activeText.includes('ahora está activo.')&&
      restoredRow.includes('19')&&restoredRow.includes('S/ 8,50'),{row:restoredRow,screenshot:await screenshot(s,'12-reactivado')});
    await toggle(empty);
    record('E13-zero-stock-message',current(empty).is_active&&(await a.locator('main').innerText()).includes('ahora está activo.')&&
      (await row(a,empty).innerText()).includes('Sin stock vigente')&&await search('AUD03-EMPTY')===0,{screenshot:await screenshot(a,'13-activo-sin-stock')});
    await toggle(expired);await toggle(expired);
    record('E14-expired-only',current(expired).is_active&&await search('AUD03E-EXP')===0&&
      (await row(a,expired).innerText()).includes('Sin stock vigente'));
    // Each state combination is visited through normal administrator controls.
    const categoryRequest=await setCategory();
    record('E15-active-inactive-category',current().is_active&&await search()===0&&await inventory('/inventario/entrada/',id,false));
    const categoryReplay=await submit(a,categoryRequest,base+'/productos/categorias/'+fx.category_id+'/estado/');
    record('E15-category-replay',categoryReplay.status()===302&&!snapshot()['catalog.Category'][0].is_active&&preserved(snapshot()),
      {requestState:categoryRequest.is_active??null,observed:snapshot()['catalog.Category'][0].is_active});
    if(snapshot()['catalog.Category'][0].is_active)await setCategory();
    const beforeCategoryError=snapshot();
    const invalidCategory=await submit(a,{is_active:'2'},base+'/productos/categorias/'+fx.category_id+'/estado/');
    record('E15-category-invalid',invalidCategory.status()===302&&equal(beforeCategoryError,snapshot()));
    await toggle();
    record('E16-both-inactive',!current().is_active&&!snapshot()['catalog.Category'][0].is_active&&await search()===0);
    await toggle();
    record('E17-reactivate-under-suspension',current().is_active&&await search()===0&&
      (await row(a).innerText()).includes('Categoría desactivada')&&(await a.locator('main').innerText()).includes('ahora está activo.'));
    await toggle();
    await setCategory();
    record('E18-category-reactivation-keeps-product-off',!current().is_active&&await search()===0);
    await toggle();
    record('E19-both-active',await search()===1&&await inventory('/inventario/entrada/',id,true)&&
      await inventory('/inventario/carga-inicial/',empty,true)&&preserved(snapshot()));
    const allBefore=snapshot();
    for(const [name,page] of [['warehouse',w],['seller',s]]) {
      const get=await page.request.get(route),post=await submit(page,{is_active:'false'},route);
      record('E20-role-'+name,get.status()===403&&post.status()===403&&equal(allBefore,snapshot()),{statuses:[get.status(),post.status()]});
    }
    const guest=await v.request.get(route,{maxRedirects:0});
    record('E21-visitor',guest.status()===302&&equal(allBefore,snapshot()));
    const get=await a.request.get(route),put=await a.request.put(route,{headers:{'X-CSRFToken':(await a.context().cookies(base)).find(c=>c.name==='audit03e_csrftoken').value}});
    record('E22-methods',get.status()===405&&put.status()===405&&equal(allBefore,snapshot()),{statuses:[get.status(),put.status()]});
    const miss=await submit(a,{is_active:'false'},base+'/productos/88888888-8888-4888-8888-888888888888/disponibilidad/');
    record('E23-missing',miss.status()===404&&equal(allBefore,snapshot()));
    const noToken=await a.request.post(route,{form:{is_active:'false'},maxRedirects:0});
    record('E23-csrf',noToken.status()===403&&equal(allBefore,snapshot()));
    for(const invalid of ['','yes','2']) {
      const response=await submit(a,{is_active:invalid},route);
      record('E24-invalid-'+JSON.stringify(invalid),response.status()===302&&equal(allBefore,snapshot()));
    }
    // Restore the baseline if an old endpoint ignored the invalid fields.
    if(!current().is_active)await toggle();
    await a.goto(base+'/productos/');
    await a.setViewportSize({width:390,height:844});
    await a.locator('.table-responsive').evaluate(node=>node.scrollLeft=node.scrollWidth);
    const mobile=await row(a).getByRole('button').boundingBox();
    record('E25-mobile-button',mobile&&mobile.x>=0&&mobile.x+mobile.width<=390,{screenshot:await screenshot(a,'25-movil')});
    await follow(a,row(a).getByRole('button',{name:'Deshabilitar',exact:true}));
    await a.reload();record('E26-refresh',!current().is_active);
    await a.goBack();record('E27-back',!current().is_active);
    await toggle();
    await s.goto(receipt);
    record('E28-final-conservation',equal(initial,snapshot())&&(await s.locator('#constancia-interna').innerText())===historic);
  } catch(error) { report.errors.push({type:error.name,message:error.message.split('\n').slice(0,3).join(' ')}); }
  finally {
    report.finished=new Date().toISOString();fs.writeFileSync(path.join(out,'browser.json'),JSON.stringify(report,null,2));await browser.close();
  }
  console.log(JSON.stringify({cases:report.cases.length,passed:report.cases.filter(c=>c.ok).length,failed:report.cases.filter(c=>!c.ok).map(c=>c.id),errors:report.errors}));
  if(report.errors.length||report.cases.some(c=>!c.ok))process.exitCode=1;
})();
