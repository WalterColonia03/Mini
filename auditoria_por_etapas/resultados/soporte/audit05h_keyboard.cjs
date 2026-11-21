// Independent continuation: real keyboard input, DOM reads, and persisted state.
// Login is setup via fill; from dashboard through confirmation, only keyboard APIs.
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const assert = require('node:assert/strict');
const crypto = require('node:crypto');
const {execFileSync} = require('node:child_process');
const {chromium} = require(path.join(os.homedir(), '.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright-core'));
const out = process.env.AUDIT05_OUT, run = process.env.AUDIT05_RUN_DIR;
const base = 'http://127.0.0.1:' + process.env.AUDIT05_PORT;
const accounts = JSON.parse(fs.readFileSync(path.join(run, '.credentials.json'), 'utf8'));
const fixture = JSON.parse(fs.readFileSync(path.join(out, 'fixture.json'), 'utf8'));
const report = {checks: [], observations: [], screenshots: [], page_errors: [], keyboard_trace: []};
function check(id, actual, expected) {
  const row = {id, actual, expected, ok: JSON.stringify(actual) === JSON.stringify(expected)};
  report.checks.push(row); assert.deepEqual(actual, expected, id);
}
function state() {
  return JSON.parse(execFileSync(process.env.AUDIT05_PYTHON, [path.join(__dirname, 'audit05_run.py'), 'snapshot'], {encoding: 'utf8'}));
}
async function shot(p, name) {
  await p.screenshot({path:path.join(out, name), fullPage:true}); report.screenshots.push(name);
}
async function tabTo(p, selector) {
  for (let i=0; i<100; i++) {
    if (await p.evaluate(s => document.activeElement === document.querySelector(s), selector)) {
      report.keyboard_trace.push({selector, tabs:i}); return;
    }
    await p.keyboard.press('Tab');
  }
  throw new Error('Keyboard cannot reach '+selector);
}
async function type(p, name, value) {
  const selector = `[name="${name}"]`;
  await tabTo(p, selector); await p.keyboard.press('Control+A'); await p.keyboard.type(value);
  check(name+'_typed_'+report.checks.length, await p.locator(selector).inputValue(), value);
}
async function select(p, name, value) {
  const selector = `[name="${name}"]`;
  await tabTo(p, selector);
  const index = await p.locator(selector).evaluate((e,v) => [...e.options].findIndex(o=>o.value===v), value);
  assert(index >= 0); await p.keyboard.press('Home');
  for (let i=0;i<index;i++) await p.keyboard.press('ArrowDown');
  await p.keyboard.press('Tab');
  check(name+'_selected_'+report.checks.length, await p.locator(selector).inputValue(), value);
}
async function date(p, name, value) {
  await tabTo(p, `[name="${name}"]`);
  // Chrome es-PE exposes day/month/year segments; no DOM writes or fill().
  await p.keyboard.press('ArrowLeft'); await p.keyboard.press('ArrowLeft'); await p.keyboard.press('ArrowLeft');
  const [y,m,d] = value.split('-');
  await p.keyboard.type(d);
  for(let i=0;i<3;i++) await p.keyboard.press('ArrowLeft');
  await p.keyboard.press('ArrowRight'); await p.keyboard.type(m);
  for(let i=0;i<3;i++) await p.keyboard.press('ArrowLeft');
  await p.keyboard.press('ArrowRight'); await p.keyboard.press('ArrowRight'); await p.keyboard.type(y);
  await p.keyboard.press('Tab');
  if(await p.locator(`[name="${name}"]`).inputValue()!==value) await shot(p,'date-driver-error.png');
  check(name+'_date_'+report.checks.length, await p.locator(`[name="${name}"]`).inputValue(), value);
}
async function login(browser, role, viewport) {
  const ctx = await browser.newContext({locale:'es-PE', viewport});
  const p = await ctx.newPage(); p.on('pageerror',e=>report.page_errors.push(e.message));
  await p.goto(base); await p.locator('[name=email]').fill(accounts[role].email);
  await p.locator('[name=password]').fill(accounts[role].password);
  await p.locator('button[type=submit]').click(); await p.waitForURL(base+'/inicio/');
  return {ctx,p};
}
async function geometry(p, label) {
  const data = await p.evaluate(()=>({width:innerWidth, scrollWidth:document.documentElement.scrollWidth,
    tables:[...document.querySelectorAll('table')].map(e=>({width:e.getBoundingClientRect().width, parentWidth:e.parentElement.clientWidth, overflow:getComputedStyle(e.parentElement).overflowX}))}));
  report.observations.push({label,...data});
  check(label+'_no_page_overflow', data.scrollWidth<=data.width, true);
}
async function exercise(browser, viewport, productKey) {
  const tag=String(viewport.width), {ctx,p}=await login(browser,'warehouse',viewport);
  await tabTo(p,'#sidebar-navigation a[href="/inventario/carga-inicial/"]');
  await p.keyboard.press('Enter'); await p.waitForURL(base+'/inventario/carga-inicial/');
  check(tag+'_fresh_form_without_error_summary',await p.locator('#initial-load-errors').count(),0);
  const before=state(), product=fixture.products[productKey];
  await select(p,'product',product.id);
  for (let i=0;i<2;i++) {
    await type(p,`lots-${i}-number`, `KEY-${tag}-${i}`);
    await type(p,`lots-${i}-quantity`,i===0?'2':'0');
    await type(p,`lots-${i}-unit_cost`, i===0?'1.2344':'1.2345');
    await date(p,`lots-${i}-expiration_date`,fixture.future_45);
  }
  await tabTo(p,'[data-testid=inventory-load-form] button[type=submit]');
  await Promise.all([p.waitForNavigation(),p.keyboard.press('Enter')]);
  check(tag+'_invalid_no_mutation',state(),before);
  check(tag+'_quantity_message',await p.locator('[name="lots-1-quantity"]').locator('..').innerText().then(t=>t.includes('mayor o igual a 1')),true);
  if(process.env.AUDIT05H_REQUIRE_FOCUS==='1') check(tag+'_summary_identifies_lot2',await p.locator('#initial-load-errors').innerText().then(t=>t.includes('Lote 2')),true);
  const errors = await p.evaluate(()=>({activeId:document.activeElement.id, activeTag:document.activeElement.tagName,
    invalid:[...document.querySelectorAll('[aria-invalid=true]')].map(e=>({id:e.id, describedby:e.getAttribute('aria-describedby'),
      missing:(e.getAttribute('aria-describedby')||'').split(/\s+/).filter(Boolean).filter(id=>!document.getElementById(id))}))}));
  report.observations.push({label:tag+'_errors',...errors});
  await shot(p,tag+'-errors.png');
  if(process.env.AUDIT05H_REQUIRE_FOCUS==='1') {
    check(tag+'_error_focus',errors.activeId,'initial-load-errors');
    check(tag+'_error_descriptions_resolve',errors.invalid.flatMap(e=>e.missing),[]);
    await p.keyboard.press('Tab');
    await p.keyboard.press('Enter');
    check(tag+'_error_link_focus',await p.evaluate(()=>document.activeElement.id),'id_lots-1-quantity');
  }
  await geometry(p,tag+'_form');
  await type(p,'lots-1-quantity','2');
  await tabTo(p,'[data-testid=inventory-load-form] button[type=submit]');
  await Promise.all([p.waitForNavigation(),p.keyboard.press('Enter')]);
  assert(p.url().includes('/inventario/cargas/'));
  const after=state(), load=after.loads.find(x=>x.product_id===product.id), lots=after.lots.filter(x=>x.product_id===product.id);
  check(tag+'_single_load',after.loads.filter(x=>x.product_id===product.id).length,1);
  check(tag+'_two_lots',lots.length,2);
  check(tag+'_sum_quantity',lots.reduce((s,l)=>s+l.available_quantity,0),4);
  check(tag+'_half_up',after.products.find(x=>x.id===product.id).average_cost,'1.2345');
  check(tag+'_lot_responsible',lots.every(x=>x.responsible_id===load.responsible_id),true);
  check(tag+'_receipt_4_units',(await p.locator('main').innerText()).includes('4 UND'),true);
  await shot(p,tag+'-receipt.png'); await geometry(p,tag+'_receipt');
  const receipt=p.url(); await p.reload(); check(tag+'_reload_no_mutation',state(),after);
  for(const role of ['admin','seller']) {
    const other=await login(browser,role,viewport);
    const res=await other.p.goto(receipt);
    check(tag+'_'+role+'_receipt_status',res.status(),role==='admin'?200:403);
    await other.ctx.close();
  }
  check(tag+'_read_roles_no_mutation',state(),after);
  // Direct forged POST through authenticated browser, with valid CSRF, stale product.
  await p.goto(base+'/inventario/carga-inicial/');
  const csrf=await p.locator('[name=csrfmiddlewaretoken]').inputValue();
  const response=await p.request.post(base+'/inventario/carga-inicial/',{form:{csrfmiddlewaretoken:csrf,product:product.id,
    'lots-TOTAL_FORMS':'1','lots-INITIAL_FORMS':'0','lots-MIN_NUM_FORMS':'1','lots-MAX_NUM_FORMS':'1000',
    'lots-0-number':'REPLAY','lots-0-quantity':'1','lots-0-unit_cost':'1','lots-0-expiration_date':fixture.future_45}});
  check(tag+'_replay_rejected',response.status(),200);
  check(tag+'_replay_no_mutation',state(),after);
  await ctx.close();
}
(async()=>{
  const browser=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true});
  try {
    report.chrome=browser.version();
    const ctx=await browser.newContext();
    const nonce=crypto.randomBytes(32).toString('hex');
    const r=await ctx.request.get(base,{headers:{'X-Audit05-Challenge':nonce}});
    check('owned_server',r.headers()['x-audit05-proof'],crypto.createHmac('sha256',fs.readFileSync(path.join(run,'.django-key'))).update(nonce).digest('hex'));
    await ctx.close();
    await exercise(browser,{width:1366,height:768},'elig1');
    await exercise(browser,{width:390,height:844},'elig2');
    check('no_page_errors',report.page_errors,[]);
  } catch(e) {report.error=e.message; process.exitCode=1;}
  finally {await browser.close(); fs.writeFileSync(path.join(out,'keyboard.json'),JSON.stringify(report,null,2));}
})();
