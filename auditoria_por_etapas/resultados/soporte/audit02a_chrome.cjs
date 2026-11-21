/* AUTH03: real Chrome UI + direct requests + read-only ORM; ephemeral test identities only. */
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const {execFileSync} = require('child_process');
const {chromium} = require(path.join(require('os').homedir(), '.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright-core'));
const run = process.env.AUDIT02A_RUN_DIR;
const out = process.env.AUDIT02A_EVIDENCE;
const base = `http://127.0.0.1:${process.env.AUDIT02A_PORT}`;
const credentials = JSON.parse(fs.readFileSync(path.join(run,'.credentials.json'),'utf8'));
const fixture = JSON.parse(fs.readFileSync(path.join(run,'fixture.json'),'utf8'));
const report = {date_utc: new Date().toISOString(), run: path.basename(run), viewport:{width:1366,height:768}, engine:'installed Google Chrome headless', cases:[], page_errors:[]};
function snapshot() {return JSON.parse(execFileSync(process.env.AUDIT02A_PYTHON,[path.join(__dirname,'audit02a_run.py'),'snapshot'],{encoding:'utf8',env:process.env}));}
function record(id,ok,details) {report.cases.push({id,ok:!!ok,details});}
function same(a,b) {return JSON.stringify(a)===JSON.stringify(b);}
function commercial(s) {return {shifts:s.shifts,closes:s.closes,lots:s.lots,sales_count:s.sales_count,sale_lines_count:s.sale_lines_count};}
async function shot(page,id) {
  await page.screenshot({path:path.join(out,id+'.png'),fullPage:true,mask:[page.locator('input[type="password"]')]});
  const text = await page.locator('body').innerText();
  fs.writeFileSync(path.join(out,id+'.txt'),text);
  return {screenshot:id+'.png',text:id+'.txt',url:page.url()};
}
async function click(page,locator) {await Promise.all([page.waitForNavigation({waitUntil:'networkidle'}),locator.click()]);}
async function login(page,alias) {
  await page.goto(base+'/',{waitUntil:'networkidle'});
  await page.locator('[name=email]').fill(credentials[alias].email);
  await page.locator('[name=password]').fill(credentials[alias].password);
  await click(page,page.locator('button[type=submit]'));
  if(!page.url().endsWith('/inicio/')) throw new Error('Login fixture failed: '+alias);
}
async function logoutMenu(page) {await click(page,page.locator('a.sidebar-logout'));}
async function confirm(page) {await click(page,page.getByRole('button',{name:'Cerrar sesión',exact:true}));}
async function checkBack(page,id) {
  await page.goBack({waitUntil:'networkidle'});
  const text = await page.locator('body').innerText();
  const privateVisible = await page.locator('.sidebar-account,.topbar-user,.draft-lines').count()>0;
  record(id,!privateVisible,{...await shot(page,id),privateVisible,loginVisible:await page.locator('[name=email]').count()===1});
}
(async()=>{
  const browser=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true});
  report.browser_version=browser.version();
  const a=await browser.newContext({viewport:report.viewport}), b=await browser.newContext({viewport:report.viewport});
  const p=await a.newPage(), q=await b.newPage();
  for(const page of [p,q]) page.on('pageerror',e=>report.page_errors.push(e.name));
  try {
    const nonce=crypto.randomBytes(32).toString('hex');
    const proof=await a.request.get(base+'/',{headers:{'X-Audit02a-Challenge':nonce}});
    const expected=crypto.createHmac('sha256',fs.readFileSync(path.join(run,'.django-key'),'utf8')).update(nonce).digest('hex');
    if(proof.headers()['x-audit02a-proof']!==expected || proof.headers()['x-audit02a-run']!==path.basename(run)) throw new Error('Server proof mismatch');
    record('A00-PROOF',true,{authenticated_server:true,run:path.basename(run),status:proof.status()});
    await login(p,'seller');
    await click(p,p.getByRole('link',{name:'Apertura de caja',exact:true}));
    await p.locator('[name=opening_amount]').fill('50.00');
    await click(p,p.getByRole('button',{name:'Abrir turno',exact:true}));
    const before=snapshot();
    const staleCookies=await a.cookies();
    await logoutMenu(p);
    const csrf=await p.locator('[name=csrfmiddlewaretoken]').inputValue();
    const text=await p.locator('main').innerText();
    record('A01-CA01-ADVERTENCIA',text.includes('turno')&&text.includes('seguirá ligado a tu cuenta')&&before.drafts.length===0,{...await shot(p,'A01-sin-borrador'),before});
    await confirm(p);
    const after=snapshot();
    record('A02-CA01-CONFIRMAR',p.url()===base+'/'&&same(commercial(before),commercial(after))&&after.sessions_by_user[credentials.seller.email]===0,{...await shot(p,'A02-salida'),after,commercial_unchanged:same(commercial(before),commercial(after))});
    await checkBack(p,'A03-ATRAS-SALIR');
    await checkBack(p,'A04-ATRAS-TURNO');
    const replay=await browser.newContext();
    await replay.addCookies(staleCookies);
    const replayGet=await replay.request.get(base+'/inicio/',{maxRedirects:0});
    const replayPost=await replay.request.post(base+'/ventas/',{maxRedirects:0,form:{csrfmiddlewaretoken:csrf,product_id:fixture.product_id,quantity:'1'}});
    record('A05-COOKIE-REVOCADA',replayGet.status()===302&&replayPost.status()===302&&same(commercial(after),commercial(snapshot())),{get_status:replayGet.status(),post_status:replayPost.status(),no_mutation:same(after.drafts,snapshot().drafts)});
    await replay.close();
    for(const route of ['/inicio/','/ventas/','/caja/abrir/','/caja/cerrar/','/empleados/','/salir/']) {
      const r=await a.request.get(base+route,{maxRedirects:0});
      record('A06-ANON-'+route,r.status()===302,{status:r.status(),location:r.headers().location});
    }
    await login(p,'seller');
    await click(p,p.getByRole('link',{name:'Preparar venta',exact:true}));
    record('A07-REINGRESO-SIN-BORRADOR',(await p.locator('main').innerText()).includes('Aún no agregaste productos')&&same(before.shifts,snapshot().shifts),{...await shot(p,'A07-turno-recuperado')});
    await p.locator('[name=query]').fill('775000000202');
    await click(p,p.getByRole('button',{name:'Buscar',exact:true}));
    await p.locator('.line-add-form [name=quantity]').fill('2');
    await click(p,p.locator('.line-add-form button'));
    const withDraft=snapshot();
    await logoutMenu(p);
    record('A08-CA02-ADVERTENCIA',(await p.locator('main').innerText()).includes('La venta en preparación se descartará.'),{...await shot(p,'A08-con-borrador'),before:withDraft});
    await click(p,p.getByRole('link',{name:'Cancelar',exact:true}));
    record('A09-CA02-CANCELAR',p.url()===base+'/inicio/'&&same(withDraft,snapshot()),{orm_unchanged:same(withDraft,snapshot()),url:p.url()});
    await click(p,p.getByRole('link',{name:'Preparar venta',exact:true}));
    record('A10-BORRADOR-CONSERVADO',await p.locator('.draft-line').count()===1,{...await shot(p,'A10-cancelar-conserva')});
    await logoutMenu(p);
    const missing=await a.request.post(base+'/salir/',{maxRedirects:0,form:{}});
    const token=await p.locator('[name=csrfmiddlewaretoken]').inputValue();
    const badmethod=await a.request.fetch(base+'/salir/',{method:'PUT',headers:{'X-CSRFToken':token},maxRedirects:0});
    record('A11-CSRF-Y-METODO',missing.status()===403&&badmethod.status()===405&&same(withDraft,snapshot()),{missing_csrf:missing.status(),put:badmethod.status(),orm_unchanged:same(withDraft,snapshot())});
    await confirm(p);
    const discarded=snapshot();
    record('A12-CA02-CONFIRMAR',same(commercial(withDraft),commercial(discarded))&&discarded.drafts.length===1&&discarded.drafts[0].status==='DISCARDED'&&discarded.drafts[0].lines.length===0&&!!discarded.drafts[0].discarded_at&&discarded.sessions_by_user[credentials.seller.email]===0,{...await shot(p,'A12-salida-borrador'),after:discarded});
    await checkBack(p,'A13-ATRAS-CON-BORRADOR');
    await checkBack(p,'A14-ATRAS-VENTA');
    await login(q,'seller2');
    await click(q,q.getByRole('link',{name:'Apertura de caja',exact:true}));
    record('A15-OTRO-VENDEDOR-TURNO',(await q.locator('main').innerText()).includes('AUD02A Vendedor Uno'),{...await shot(q,'A15-turno-ajeno')});
    await click(q,q.getByRole('link',{name:'Preparar venta',exact:true}));
    record('A16-OTRO-VENDEDOR-VENTA',(await q.locator('main').innerText()).includes('Abre tu turno para preparar una venta'),{...await shot(q,'A16-venta-ajena')});
    await click(q,q.getByRole('link',{name:'Cerrar turno',exact:true}));
    record('A17-OTRO-VENDEDOR-CIERRE',(await q.locator('main').innerText()).includes('No tienes un turno abierto'),{...await shot(q,'A17-cierre-ajeno')});
    await logoutMenu(q);
    const token2=await q.locator('[name=csrfmiddlewaretoken]').inputValue();
    for(const [route,data] of [['/caja/abrir/',{opening_amount:'2.00'}],['/ventas/',{product_id:fixture.product_id,quantity:'1'}],['/caja/cerrar/',{counted_amount:'50.00'}]]) {
      const pre=snapshot();
      const r=await b.request.post(base+route,{maxRedirects:0,form:{csrfmiddlewaretoken:token2,...data}});
      const post=snapshot();
      record('A18-POST-AJENO-'+route,r.status()===200&&same(commercial(pre),commercial(post))&&same(pre.drafts,post.drafts),{status:r.status(),no_mutation:same(pre,post)});
    }
    await login(p,'seller');
    await click(p,p.getByRole('link',{name:'Preparar venta',exact:true}));
    record('A19-CA03-REINGRESO',(await p.locator('main').innerText()).includes('Aún no agregaste productos')&&same(before.shifts,snapshot().shifts),{...await shot(p,'A19-reingreso')});
    await click(p,p.getByRole('link',{name:'Cerrar turno',exact:true}));
    await p.locator('[name=counted_amount]').fill('50.00');
    await click(p,p.getByRole('button',{name:/Cerrar turno|Confirmar cierre/}));
    const closed=snapshot();
    await logoutMenu(p);
    record('A20-SIN-TURNO-ADVERTENCIA',closed.shifts.filter(x=>x.status==='OPEN').length===0,{...await shot(p,'A20-sin-turno'),open_shifts:closed.shifts.filter(x=>x.status==='OPEN').length});
    await confirm(p);
    record('A21-SIN-TURNO-SALIDA',same(commercial(closed),commercial(snapshot()))&&snapshot().sessions_by_user[credentials.seller.email]===0,{after:snapshot()});
    await confirm(q);
    for(const alias of ['admin','warehouse']) {
      await login(p,alias);
      await logoutMenu(p);
      const pre=snapshot();
      const text=await p.locator('main').innerText();
      const shotInfo=await shot(p,'A22-'+alias+'-salida');
      await confirm(p);
      record('A22-SALIDA-'+alias,p.url()===base+'/'&&same(commercial(pre),commercial(snapshot()))&&snapshot().sessions_by_user[credentials[alias].email]===0,{...shotInfo,conditional_warning:text.includes('Si tienes un turno abierto')});
    }
    await login(p,'admin');
    await login(q,'admin');
    const r1=await a.request.get(base+'/inicio/',{maxRedirects:0}),r2=await b.request.get(base+'/inicio/',{maxRedirects:0});
    record('A23-AUTH04A-FUTURO',r1.status()===200&&r2.status()===200,{classification:'PREVISTO/FUTURO',both_sessions_active:true,statuses:[r1.status(),r2.status()]});
    await logoutMenu(p);await confirm(p);await logoutMenu(q);await confirm(q);
  } catch(e) {
    report.error={name:e.name,message:String(e.message).slice(0,1800)};
    try {await shot(p,'ERROR-current');} catch {}
  } finally {
    await browser.close();
    report.completed_utc=new Date().toISOString();
    report.passed=report.cases.filter(x=>x.ok).length;
    report.failed=report.cases.filter(x=>!x.ok).length;
    fs.writeFileSync(path.join(out,'browser.json'),JSON.stringify(report,null,2));
  }
  console.log(JSON.stringify({cases:report.cases.length,passed:report.passed,failed:report.failed,error:report.error}));
  if(report.error||report.failed||report.page_errors.length) process.exitCode=1;
})();
