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
async function inspectTable(p, selector, label) {
  const box=p.locator(selector);
  const before=await box.evaluate(e=>({width:e.clientWidth,scroll:e.scrollWidth,left:e.scrollLeft,tabindex:e.getAttribute('tabindex'),label:e.getAttribute('aria-label')}));
  let reached=false;
  for(let i=0;i<65;i++) {
    if(await box.evaluate(e=>e===document.activeElement)){reached=true;break;}
    await p.keyboard.press('Tab');
  }
  const row={label,before,reached};
  report.observations.push(row);
  if(reached) {
    const visibleColumns = new Set();
    const columnCount = await box.locator('thead th').count();
    // Horizontal movement must come from keyboard, not scrollLeft assignments.
    for(let step=0;step<60;step++) {
      const visible=await box.evaluate(el=>{
        const viewport=el.getBoundingClientRect();
        return [...el.querySelectorAll('tbody tr:first-child td')].map((cell,index)=>{
          const rect=cell.getBoundingClientRect();
          return rect.left>=viewport.left-2 && rect.right<=viewport.right+2 ? index : -1;
        }).filter(index=>index>=0);
      });
      for(const index of visible) visibleColumns.add(index);
      await p.keyboard.press('ArrowRight');
      await p.waitForTimeout(25);
    }
    await p.waitForTimeout(200);
    row.after=await box.evaluate(e=>{
      const last=e.querySelector('tbody tr td:last-child'),r=e.getBoundingClientRect(),c=last?.getBoundingClientRect();
      return {left:e.scrollLeft,max:e.scrollWidth-e.clientWidth,last: last?.textContent.trim(),lastVisible:!!c&&c.right<=r.right+2&&c.left>=r.left-2,
        focus:e===document.activeElement,outline:getComputedStyle(e).outlineStyle};
    });
    row.cells=await box.evaluate(e=>[...e.querySelectorAll('tbody tr:first-child td')].map(c=>({text:c.textContent.trim(),width:c.getBoundingClientRect().width,scrollWidth:c.scrollWidth,clientWidth:c.clientWidth})));
    check(label+'_columns_visible_during_scroll',visibleColumns.size,columnCount);
    row.skipLink = await p.locator('.skip-link').evaluate(e => {
      const rect = e.getBoundingClientRect();
      const style = getComputedStyle(e);
      return {focused:e === document.activeElement, top:rect.top, bottom:rect.bottom,
        transform:style.transform, visibleInViewport:rect.bottom > 0 && rect.top < innerHeight,
        activeTag:document.activeElement.tagName};
    });
    await p.screenshot({path:path.join(out,label+'-viewport.png'),fullPage:false});
    await shot(p,label+'.png');
  }
  if(process.env.AUDIT05I_STRICT==='1') {
    check(label+'_reachable',reached,true);
    check(label+'_scrolled_end',row.after.left>=row.after.max-2,true);
    check(label+'_last_cell_visible',row.after.lastVisible,true);
    check(label+'_focus_retained',row.after.focus,true);
    check(label+'_named',!!before.label,true);
    check(label+'_each_cell_fits_viewport',row.cells.every(c=>c.width<=before.width),true);
    check(label+'_no_cell_content_overflow',row.cells.every(c=>c.scrollWidth<=c.clientWidth+1),true);
  }
}
(async()=>{
 const browser=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true});
 try {
  report.chrome=browser.version();
  const wh=await login(browser,'warehouse',{width:390,height:844});
  const nonce=crypto.randomBytes(32).toString('hex');
  const proof=await wh.p.request.get(base,{headers:{'X-Audit05-Challenge':nonce}});
  check('owned_server',proof.headers()['x-audit05-proof'],crypto.createHmac('sha256',fs.readFileSync(path.join(run,'.django-key'))).update(nonce).digest('hex'));
  await wh.p.goto(base+'/inventario/carga-inicial/');
  await wh.p.locator('[name=product]').selectOption(fixture.products.elig2.id);
  await wh.p.locator('[name=supplier]').selectOption(fixture.suppliers.long.id);
  for(const [k,v] of Object.entries({number:'L'.repeat(64),quantity:'5',unit_cost:'1.2345',expiration_date:fixture.tomorrow}))
    await wh.p.locator(`[name="lots-0-${k}"]`).fill(v);
  await wh.p.getByRole('button',{name:'Confirmar existencias',exact:true}).click();
  await wh.p.waitForURL(/\/inventario\/cargas\//);
  const longReceipt=wh.p.url(),baseline=state();
  check('long_supplier_length',fixture.suppliers.long.name.length,160);
  check('lot_length',baseline.lots.find(l=>l.product_id===fixture.products.elig2.id).number.length,64);
  await wh.ctx.close();
  for(const role of ['warehouse','admin']) {
    const {ctx,p}=await login(browser,role,{width:390,height:844});
    for(const [tag,url,selectors] of [
      ['long',longReceipt,['.load-detail-panel .table-wrap']],
      ['sub',base+`/inventario/cargas/${fixture.products.sub.load_id}/`,['.load-detail-panel .table-wrap']],
      ['mov',base+`/inventario/productos/${fixture.products.sub.id}/movimientos/`,['.table-wrap']],
      ['stock',base+'/inventario/stock/',['.table-wrap']],
      ['expiry',base+'/productos/vencimientos/',['.table-responsive']]
    ]) {
      const menuPath=tag==='expiry'?'/productos/vencimientos/':'/inventario/stock/';
      const [menuResponse]=await Promise.all([p.waitForNavigation(),p.locator(`#sidebar-navigation a[href="${menuPath}"]`).click()]);
      let res=menuResponse;
      if(tag==='long'||tag==='sub'||tag==='mov') {
        const link=p.locator(`.stock-overview-table a[href="${new URL(url).pathname}"]`);
        [res]=await Promise.all([p.waitForNavigation(),link.click()]);
      }
      check(role+'_'+tag+'_200',res.status(),200);
      await geometry(p,role+'_'+tag);
      for(let i=0;i<selectors.length;i++) await inspectTable(p,selectors[i],role+'_'+tag+'_'+i);
    }
    check(role+'_queries_no_mutation',state(),baseline);
    await ctx.close();
  }
  const seller=await login(browser,'seller',{width:390,height:844});
  for(const url of [longReceipt,base+'/inventario/stock/',base+'/productos/vencimientos/']) check('seller_denied_'+url.split('/').slice(-2,-1), (await seller.p.goto(url)).status(),403);
  check('denials_no_mutation',state(),baseline);await seller.ctx.close();
  check('no_page_errors',report.page_errors,[]);
 }catch(e){report.error=e.message;process.exitCode=1;}
 finally{await browser.close();fs.writeFileSync(path.join(out,'narrow.json'),JSON.stringify(report,null,2));}
})();
