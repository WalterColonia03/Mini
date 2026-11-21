// Independent 04-C review: actual keyboard/touch-emulated operations, not viewport-only approval.
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const crypto = require('node:crypto');
const assert = require('node:assert/strict');
const {execFileSync} = require('node:child_process');
const {chromium} = require(path.join(os.homedir(), '.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright-core'));
const out = process.env.AUDIT04_OUT, run = process.env.AUDIT04_RUN_DIR;
const base = 'http://127.0.0.1:' + process.env.AUDIT04_PORT;
const credentials = JSON.parse(fs.readFileSync(path.join(run, '.credentials.json')));
const fixture = JSON.parse(fs.readFileSync(path.join(out, 'fixture.json')));
const report = {checks: [], observations: [], screenshots: [], page_errors: []};
function check(id, actual, expected) { assert.deepEqual(actual, expected, id); report.checks.push(id); }
function state() { return JSON.parse(execFileSync(process.env.AUDIT04_PYTHON, ['-X', 'utf8', path.join(__dirname, 'audit04_run.py'), 'snapshot'], {encoding:'utf8'})); }
async function shot(page, file) {await page.screenshot({path:path.join(out,file),fullPage:true}); report.screenshots.push(file);}
async function tabUntil(page, selector) {
  for(let i=0; i<45; i++) {
    if(await page.evaluate(s=>document.activeElement?.matches(s),selector)) return;
    await page.keyboard.press('Tab');
  }
  throw Error('Keyboard did not reach '+selector);
}
async function login(browser, role) {
  const ctx=await browser.newContext({viewport:{width:390,height:844},hasTouch:true,locale:'es-PE'});
  const page=await ctx.newPage(); page.on('pageerror', e=>report.page_errors.push(e.message));
  await page.goto(base);
  await page.locator('[name=email]').fill(credentials[role].email);
  await page.locator('[name=password]').fill(credentials[role].password);
  await page.locator('button[type=submit]').tap(); await page.waitForURL(base+'/inicio/');
  return {ctx,page};
}
async function menu(page) {
  await tabUntil(page,'#sidebar-navigation a[href="/inventario/proveedores/"]');
  await page.waitForTimeout(350); // Wait for the page's smooth focus scrolling.
  const b=await page.locator('#sidebar-navigation a[href="/inventario/proveedores/"]').boundingBox();
  report.observations.push({case:'menu_focus',box:b});
  await shot(page,'04C-menu-'+report.checks.length+'.png');
  check('menu_keyboard_visible_'+report.checks.length,b.x>=0 && b.x+b.width<=391,true);
  await page.keyboard.press('Enter'); await page.waitForURL(base+'/inventario/proveedores/');
}
async function swipe(page, locator) {
  await locator.scrollIntoViewIfNeeded();
  const b=await locator.boundingBox(), y=Math.max(10,Math.min(800,b.y+Math.min(60,b.height/2)));
  const x=Math.min(370,b.x+b.width-15), end=Math.max(b.x+15,25);
  const cdp=await page.context().newCDPSession(page);
  await cdp.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[{x,y}]});
  for(let i=1;i<=12;i++) {
    await cdp.send('Input.dispatchTouchEvent',{type:'touchMove',touchPoints:[{x:x+(end-x)*i/12,y}]});
    await page.waitForTimeout(20);
  }
  await cdp.send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]});
  await page.waitForTimeout(250); await cdp.detach();
  return await locator.evaluate(e=>e.scrollLeft);
}
(async()=>{
 const browser=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true});
 try {
  report.chrome=browser.version();
  const probe=await browser.newContext(), nonce=crypto.randomBytes(32).toString('hex');
  const res=await probe.request.get(base,{headers:{'X-Audit04-Challenge':nonce}});
  check('isolated_server_proof',res.headers()['x-audit04-proof'],crypto.createHmac('sha256',fs.readFileSync(path.join(run,'.django-key'))).update(nonce).digest('hex'));
  await probe.close();
  const a=await login(browser,'admin'), w=await login(browser,'warehouse'), s=await login(browser,'seller');
  await menu(a.page);
  await a.page.getByRole('link',{name:'+ Nuevo proveedor',exact:true}).tap();
  const longName='Proveedor revisión '+ 'A'.repeat(141);
  check('name_length',longName.length,160);
  await a.page.locator('[name=name]').fill(longName);
  await a.page.keyboard.press('Tab'); await a.page.keyboard.type('00123456001');
  await a.page.keyboard.press('Tab'); await a.page.keyboard.type('+51 999-123-456');
  await a.page.keyboard.press('Tab'); await a.page.keyboard.press('Enter');
  await a.page.waitForURL(base+'/inventario/proveedores/');
  let sup=state().suppliers.find(x=>x.ruc==='00123456001');
  check('mobile_create_exact_name',sup.name,longName); check('mobile_create_active',sup.is_active,true);
  const toggle=base+`/inventario/proveedores/${sup.id}/estado/`;
  const before=state();
  const token=(await a.ctx.cookies()).find(c=>c.name==='audit04_csrftoken').value;
  for(const value of ['', 'quizas']) {
    const r=await a.page.request.post(toggle,{form:{csrfmiddlewaretoken:token,is_active:value},maxRedirects:0});
    check('invalid_target_redirect_'+value,r.status(),302); check('invalid_target_full_snapshot_'+value,state(),before);
  }
  await a.page.reload();
  await tabUntil(a.page,'tbody button');
  await a.page.waitForTimeout(350);
  const button=a.page.locator('tbody button');
  check('keyboard_target_visible',await button.evaluate(e=>{
    const r=e.getBoundingClientRect(),t=e.closest('.table-responsive').getBoundingClientRect();
    return r.left>=t.left && r.right<=t.right && r.top>=0 && r.bottom<=innerHeight;
  }),true);
  await shot(a.page,'04C-keyboard-action.png');
  await a.page.keyboard.press('Enter'); await a.page.waitForLoadState('networkidle');
  check('keyboard_deactivates',state().suppliers[0].is_active,false);
  check('badge_inactive',await a.page.locator('tbody .badge').innerText(),'Inactivo');
  await menu(w.page);
  check('warehouse_reads_name',await w.page.locator('tbody td').first().innerText(),longName);
  check('warehouse_no_actions',await w.page.locator('tbody button').count(),0);
  const wt=w.page.locator('.table-responsive');
  check('warehouse_touch_scroll',await swipe(w.page,wt)>0,true);
  await shot(w.page,'04C-warehouse-touch-right.png');
  check('seller_no_menu',await s.page.locator('#sidebar-navigation a[href="/inventario/proveedores/"]').count(),0);
  const baseline=state();
  for(const [role,session] of [['warehouse',w],['seller',s]]) {
    const csrf=(await session.ctx.cookies()).find(c=>c.name==='audit04_csrftoken').value;
    check(role+'_direct_write_403',(await session.page.request.post(toggle,{form:{csrfmiddlewaretoken:csrf,is_active:'true'},maxRedirects:0})).status(),403);
    check(role+'_denied_full_snapshot',state(),baseline);
  }
  check('seller_read_403',(await s.page.goto(base+'/inventario/proveedores/')).status(),403);
  // Touch reactivation after moving the table; persist and inspect from another role.
  await a.page.reload();
  const at=a.page.locator('.table-responsive');
  check('admin_touch_scroll',await swipe(a.page,at)>0,true);
  await a.page.getByRole('button',{name:'Activar',exact:true}).tap();
  await a.page.waitForLoadState('networkidle'); check('touch_reactivates',state().suppliers[0].is_active,true);
  await w.page.reload(); check('warehouse_sees_reactivation',await w.page.locator('tbody .badge').innerText(),'Activo');
  // A receipt through the real form supplies a historical table with the long supplier name.
  await w.page.goto(base+'/inventario/entrada/');
  await w.page.locator('[name=product]').selectOption(fixture.products.subsequent.id);
  await w.page.locator('[name=supplier]').selectOption(sup.id);
  for(const [f,v] of Object.entries({number:'REVIEW04C',quantity:'2',unit_cost:'3.50',expiration_date:fixture.future_date})) await w.page.locator(`[name="lots-0-${f}"]`).fill(v);
  await w.page.getByRole('button',{name:'Confirmar entrada',exact:true}).tap();
  await w.page.waitForURL(/\/inventario\/cargas\//);
  check('receipt_supplier_persisted',state().lots.find(l=>l.number_normalized==='REVIEW04C').supplier_id,sup.id);
  const tables=w.page.locator('.table-wrap');
  report.observations.push({case:'load_tables',tables:await tables.evaluateAll(es=>es.map(e=>({width:e.clientWidth,scrollWidth:e.scrollWidth,tabIndex:e.tabIndex})))});
  check('load_two_tables',await tables.count(),2);
  check('load_touch_scroll',await swipe(w.page,tables.last())>0,true);
  for(let i=0;i<14;i++) {
    const edge=await tables.last().evaluate(e=>e.scrollLeft+e.clientWidth>=e.scrollWidth-2);
    if(edge) break;
    await swipe(w.page,tables.last());
  }
  check('load_touch_reaches_right_edge',await tables.last().evaluate(e=>e.scrollLeft+e.clientWidth>=e.scrollWidth-2),true);
  await shot(w.page,'04C-load-touch.png');
  await w.page.reload();
  await tabUntil(w.page,'.table-wrap');
  // Chrome makes scroll containers keyboard-focusable even when tabIndex reports -1.
  await w.page.keyboard.press('Tab');
  check('second_table_keyboard_focus',await tables.last().evaluate(e=>e===document.activeElement),true);
  for(let i=0;i<80;i++) await w.page.keyboard.press('ArrowRight');
  await w.page.waitForTimeout(350);
  check('load_keyboard_reaches_right_edge',await tables.last().evaluate(e=>e.scrollLeft+e.clientWidth>=e.scrollWidth-2),true);
  await shot(a.page,'04C-final-admin.png');
  check('no_page_errors',report.page_errors,[]);
 } catch(e) {report.error=e.message; process.exitCode=1;}
 finally {fs.writeFileSync(path.join(out,'browser.json'),JSON.stringify(report,null,2));await browser.close();}
})();

