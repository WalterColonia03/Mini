const fs=require('node:fs'),path=require('node:path'),os=require('node:os'),assert=require('node:assert/strict');
const {chromium}=require(path.join(os.homedir(),'.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright-core'));
const root=path.resolve(__dirname,'../../..'),out=path.join(root,'auditoria_por_etapas/resultados/evidencias/01-K-20261115');
const before=JSON.parse(fs.readFileSync(path.join(out,'expiracion-real-antes.json'),'utf8'));
const creds=JSON.parse(fs.readFileSync(path.join(root,'auditoria_por_etapas/resultados/datos/01-K-20261115/.credentials.json'),'utf8'));
const base='http://127.0.0.1:8800';
(async()=>{
 assert(Date.now()>Date.parse(before.locked_until)+1000,'El plazo real aún no terminó');
 const browser=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true});
 try{
  const ctx=await browser.newContext(),page=await ctx.newPage();await page.goto(base);
  await page.locator('[name=email]').fill(creds.admin.email);await page.locator('[name=password]').fill(creds.admin.password);
  const [res]=await Promise.all([page.waitForResponse(r=>r.request().method()==='POST'&&r.url()===base+'/'),page.locator('button[type=submit]').click()]);
  await page.waitForURL(base+'/inicio/');assert.equal(res.status(),302);
  const stamp=new Date();
  const report={observado_utc:stamp.toISOString(),status:res.status(),destino:new URL(page.url()).pathname,chrome:browser.version(),espera_real_segundos:(stamp-Date.parse(before.quinto_fallo_inferido_de_plazo_15_min))/1000,reloj_controlado:false,ok:true};
  fs.writeFileSync(path.join(out,'expiracion-real-browser.json'),JSON.stringify(report,null,2));
  console.log(JSON.stringify(report));await ctx.close();
 }finally{await browser.close();}
})().catch(e=>{console.error(e.message);process.exitCode=1;});
