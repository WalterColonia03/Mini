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
const report = { stage: '03-J', started: new Date().toISOString(), cases: [], errors: [] };

function record(id, ok, details = {}) {
  report.cases.push({ id, ok: Boolean(ok), ...details });
}
function snapshot() {
  return JSON.parse(execFileSync(process.env.AUDIT03_PYTHON, [path.join(__dirname, 'audit03j_run.py'), 'snapshot'], {
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
  const cookie = (await page.context().cookies(base)).find(c=>c.name==='audit03j_csrftoken');
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
  for(let i=0;i<5;i++)pages.push(await (await browser.newContext({viewport:{width:1366,height:900},locale:'es-PE'})).newPage());
  const [a,b,w,s,v]=pages;for(const page of pages)page.setDefaultTimeout(12000);
  const fx=JSON.parse(fs.readFileSync(path.join(out,'fixture.json'),'utf8'));
  const initial=snapshot(),categoryId=fx.category_id,productId=fx.product_id;
  const list=base+'/productos/categorias/',commit=list+categoryId+'/estado/',confirm=commit+'confirmar/';
  const equal=(x,y)=>JSON.stringify(x)===JSON.stringify(y);
  const current=()=>snapshot()['catalog.Category'].find(c=>c.id===categoryId);
  const version=()=>snapshot().category_versions.find(c=>c.id===categoryId).state_version;
  const business=state=>Object.fromEntries(Object.entries(state).filter(([key])=>!['catalog.Category','category_versions'].includes(key)));
  const preserved=()=>equal(business(initial),business(snapshot()));
  function row(page){return page.getByRole('row').filter({has:page.getByRole('cell',{name:'Productos enlatados',exact:true})});}
  async function openConfirm(page){await page.goto(list);await follow(page,row(page).getByRole('button'));}
  async function data(page){return page.locator('main form').evaluate(f=>Object.fromEntries([...new FormData(f)].filter(([key])=>key!=='csrfmiddlewaretoken')));}
  async function search(code='AUD03-BEBIDA'){await s.goto(base+'/ventas/');await s.locator('[name=query]').fill(code);await follow(s,s.getByRole('button',{name:'Buscar',exact:true}));return s.getByRole('button',{name:'Agregar',exact:true}).count();}
  async function selector(route,pid,exists){await w.goto(base+route);return (await w.locator('[name=product] option').evaluateAll(xs=>xs.map(x=>x.value))).includes(pid)===exists;}
  try{
    const nonce=crypto.randomBytes(32).toString('hex');
    const probe=await a.request.get(base,{headers:{'X-Audit03-Challenge':nonce}});
    if(probe.headers()['x-audit03-proof']!==crypto.createHmac('sha256',fs.readFileSync(path.join(run,'.django-key'))).update(nonce).digest('hex'))throw Error('Isolation mismatch');
    await login(a,'admin');await login(b,'admin2');await login(w,'warehouse');await login(s,'seller');
    const receipt=base+'/ventas/constancia/'+fx.sale_id+'/';
    await s.goto(receipt);const history=await s.locator('#constancia-interna').innerText();
    await follow(a,a.getByRole('link',{name:'Categorías',exact:true}));
    const oldList={is_active:'false',state_version:await row(a).locator('[name=state_version]').inputValue()};
    record('J01-list-readonly',equal(initial,snapshot())&&oldList.state_version==='0');
    await follow(a,row(a).getByRole('button',{name:'Desactivar',exact:true}));
    const impact=await a.locator('dl').innerText();
    record('J02-impact-readonly',equal(initial,snapshot())&&impact.includes('3')&&impact.includes('1')&&impact.includes('23')&&
      (await a.locator('main').innerText()).includes('no podrán actualizarse ni cobrarse'),{impact,screenshot:await screenshot(a,'02-impacto')});
    await follow(a,a.getByRole('link',{name:'Cancelar',exact:true}));
    record('J03-cancel',a.url()===list&&equal(initial,snapshot()));
    await openConfirm(a);await openConfirm(b);
    const captured=await data(a);
    await follow(a,a.getByRole('button',{name:'Confirmar desactivación',exact:true}));
    record('J04-commit',!current().is_active&&version()===1&&preserved()&&(await a.locator('main').innerText()).includes('ahora está inactiva.'));
    const afterOff=snapshot();
    const replay=await submit(a,captured,commit);
    record('J05-replay',replay.status()===409&&equal(afterOff,snapshot()));
    await follow(b,b.getByRole('button',{name:'Confirmar desactivación',exact:true}));
    record('J06-second-admin-stale',(await b.locator('[role=alert]').innerText()).includes('La categoría cambió')&&
      !await b.locator('main form').count()&&equal(afterOff,snapshot()),{screenshot:await screenshot(b,'06-conflicto')});
    await follow(w,w.getByRole('link',{name:'Catálogo de productos',exact:true}));
    const productRow=w.getByRole('row').filter({has:w.getByRole('cell',{name:'AUD03-BEBIDA',exact:true})});
    record('J07-warehouse-state',(await productRow.innerText()).includes('Categoría desactivada')&&(await productRow.innerText()).includes('19'));
    record('J08-entry-exclusion',await selector('/inventario/entrada/',productId,false));
    record('J08-initial-exclusion',await selector('/inventario/carga-inicial/',fx.empty_product_id,false));
    record('J09-sale-search',await search()===0);
    await s.locator('.draft-line-actions [name=quantity]').fill('3');
    await follow(s,s.getByRole('button',{name:'Actualizar',exact:true}));
    record('J10-draft-reject',(await s.locator('main').innerText()).includes('no está disponible')&&preserved());
    await s.goto(base+'/ventas/cobrar/');await s.locator('[name=cash_received]').fill('30.00');
    await follow(s,s.getByRole('button',{name:'Confirmar cobro',exact:true}));
    record('J11-checkout-reject',(await s.locator('main').innerText()).includes('ya no está disponible para la venta')&&preserved());
    await s.goto(receipt);
    record('J12-history',(await s.locator('#constancia-interna').innerText())===history&&preserved());
    for(const [role,page] of [['warehouse',w],['seller',s]]){
      const get=await page.request.get(confirm),post=await submit(page,{is_active:'true',state_version:'1',confirm:'yes'},commit);
      record('J13-role-'+role,get.status()===403&&post.status()===403&&equal(afterOff,snapshot()));
    }
    record('J14-visitor',(await v.request.get(confirm,{maxRedirects:0})).status()===302);
    const getPost=await a.request.get(commit),postGet=await submit(a,captured,confirm);
    record('J15-methods',getPost.status()===405&&postGet.status()===405&&equal(afterOff,snapshot()));
    const csrf=await a.request.post(commit,{form:{is_active:'true',state_version:'1',confirm:'yes'},maxRedirects:0});
    record('J16-csrf',csrf.status()===403&&equal(afterOff,snapshot()));
    const missing=await a.request.get(list+'88888888-8888-4888-8888-888888888888/estado/confirmar/');
    record('J17-missing',missing.status()===404&&equal(afterOff,snapshot()));
    for(const [label,payload] of [
      ['legacy',{}],['version',{is_active:'true',confirm:'yes'}],
      ['invalid-version',{is_active:'true',state_version:'-1',confirm:'yes'}],
      ['state',{is_active:'2',state_version:'1',confirm:'yes'}],
      ['confirmation',{is_active:'true',state_version:'1'}]
    ]){
      const response=await submit(a,payload,commit);
      record('J18-invalid-'+label,response.status()===400&&equal(afterOff,snapshot()));
    }
    await follow(b,b.getByRole('link',{name:'Revisar categorías',exact:true}));
    await follow(b,row(b).getByRole('button',{name:'Activar',exact:true}));
    record('J19-activate-readonly',equal(afterOff,snapshot())&&
      (await b.locator('main').innerText()).includes('Los productos deshabilitados individualmente seguirán deshabilitados'));
    await follow(b,b.getByRole('button',{name:'Confirmar activación',exact:true}));
    record('J20-activate',current().is_active&&version()===2&&preserved()&&await search()===1&&
      !snapshot()['catalog.Product'].find(p=>p.id===fx.expired_product_id).is_active&&
      await selector('/inventario/carga-inicial/',fx.empty_product_id,true));
    const active=snapshot();
    const aba=await submit(a,captured,commit);
    record('J21-old-screen-after-cycle',aba.status()===409&&equal(active,snapshot()));
    const staleGet=await a.request.get(confirm+'?is_active=false&state_version=0');
    record('J22-old-list',staleGet.status()===409&&equal(active,snapshot()));
    await a.setViewportSize({width:390,height:844});await openConfirm(a);
    const button=await a.getByRole('button',{name:'Confirmar desactivación',exact:true}).boundingBox();
    const noOverflow=await a.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth);
    record('J23-mobile',noOverflow&&button&&button.x>=0&&button.x+button.width<=390&&equal(active,snapshot()),
      {screenshot:await screenshot(a,'23-movil')});
    await follow(a,a.getByRole('link',{name:'Cancelar',exact:true}));
    await a.goBack();await a.reload();
    record('J24-back-reload',equal(active,snapshot()));
    const nojs=await (await browser.newContext({javaScriptEnabled:false,viewport:{width:1366,height:900}})).newPage();
    await login(nojs,'admin');await openConfirm(nojs);
    record('J25-no-javascript',await nojs.getByRole('button',{name:'Confirmar desactivación',exact:true}).isVisible()&&equal(active,snapshot()));
    await follow(nojs,nojs.getByRole('link',{name:'Cancelar',exact:true}));
    record('J26-final',preserved()&&equal(initial['catalog.Category'],snapshot()['catalog.Category'])&&version()===2);
  }catch(error){report.errors.push({type:error.name,message:error.message.split('\n').slice(0,3).join(' ')});}
  finally{report.finished=new Date().toISOString();fs.writeFileSync(path.join(out,'browser.json'),JSON.stringify(report,null,2));await browser.close();}
  console.log(JSON.stringify({cases:report.cases.length,passed:report.cases.filter(c=>c.ok).length,failed:report.cases.filter(c=>!c.ok).map(c=>c.id),errors:report.errors}));
  if(report.errors.length||report.cases.some(c=>!c.ok))process.exitCode=1;
})();
