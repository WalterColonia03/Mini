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
function control(action) { return JSON.parse(execFileSync(process.env.AUDIT04_PYTHON,['-X','utf8',path.join(__dirname,'audit04d_control.py'),action],{encoding:'utf8'})); }
(async()=>{
 const browser=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true});
 try {
  report.chrome=browser.version();
  const probe=await browser.newContext(), nonce=crypto.randomBytes(32).toString('hex');
  const proof=await probe.request.get(base,{headers:{'X-Audit04-Challenge':nonce}});
  check('isolated_server_proof',proof.headers()['x-audit04-proof'],crypto.createHmac('sha256',fs.readFileSync(path.join(run,'.django-key'))).update(nonce).digest('hex'));
  await probe.close();
  for(const mode of ['service','raw']) {
   const a=await login(browser,'admin');
   await a.page.goto(base+'/inventario/proveedores/nuevo/');
   await a.page.locator('[name=name]').fill('Proveedor sesión '+mode);
   await a.page.locator('[name=ruc]').fill(mode==='service'?'00123456011':'00123456012');
   await a.page.getByRole('button',{name:'Guardar',exact:true}).click();
   await a.page.waitForURL(base+'/inventario/proveedores/');
   const supplier=state().suppliers.find(x=>x.ruc===(mode==='service'?'00123456011':'00123456012'));
   const old=await a.ctx.cookies();
   const csrf=old.find(c=>c.name==='audit04_csrftoken').value;
   const initial=state();
   report.observations.push({mode,disabled:control(mode+'_off')});
   const response=await a.page.request.get(base+'/inventario/proveedores/',{maxRedirects:0});
   check(mode+'_disabled_read_302',response.status(),302);
   const post=await a.page.request.post(base+'/inventario/proveedores/nuevo/',{form:{csrfmiddlewaretoken:csrf,name:'No guardar',ruc:'00123456999'},maxRedirects:0});
   check(mode+'_disabled_write_302',post.status(),302);
   check(mode+'_disabled_toggle_302',(await a.page.request.post(base+`/inventario/proveedores/${supplier.id}/estado/`,{form:{csrfmiddlewaretoken:csrf,is_active:'false'},maxRedirects:0})).status(),302);
   check(mode+'_disabled_no_writes',state(),initial);
   report.observations.push({mode,after_denial:control('status')});
   control(mode+'_on');
   const replay=await browser.newContext(); await replay.addCookies(old);
   const r=await replay.request.get(base+'/inventario/proveedores/',{maxRedirects:0});
   report.observations.push({mode,replay_status:r.status()});
   check(mode+'_old_cookie_revoked_after_reactivation',r.status(),302);
   check(mode+'_replay_write_302',(await replay.request.post(base+`/inventario/proveedores/${supplier.id}/estado/`,{form:{csrfmiddlewaretoken:csrf,is_active:'false'},maxRedirects:0})).status(),302);
   check(mode+'_replay_no_writes',state(),initial);
   await a.page.goto(base+'/inventario/proveedores/');
   await shot(a.page,'04D-'+mode+'-login-required.png');
   await replay.close(); await a.ctx.close();
  }
  check('no_page_errors',report.page_errors,[]);
 } catch(e) {report.error=e.message;process.exitCode=1;}
 finally {fs.writeFileSync(path.join(out,'browser.json'),JSON.stringify(report,null,2));await browser.close();}
})();
