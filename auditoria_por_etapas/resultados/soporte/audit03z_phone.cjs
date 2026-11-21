// Real phone only. Two Code 128 labels, one dialog, no keyboard automation.
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const crypto = require('node:crypto');
const assert = require('node:assert/strict');
const {chromium} = require(path.join(os.homedir(), '.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright-core'));
const out = process.env.AUDIT03_OUT, run = process.env.AUDIT03_RUN_DIR;
const base = 'http://127.0.0.1:'+process.env.AUDIT03_PORT;
const report = {status:'preparing', posts:[]};
const write = name => fs.writeFileSync(path.join(out,name),JSON.stringify(report,null,2));
function observe({images,codes}) {
  const dialog = document.querySelector('#barcode-capture-dialog');
  const input = document.querySelector('#barcode-capture-input');
  const box = document.createElement('section');
  const title = document.createElement('strong');
  box.append(title);
  for (const [i,src] of images.entries()) {
    const caption=document.createElement('div');
    caption.textContent=i===0?'ARRIBA · A':'ABAJO · B';
    const image=document.createElement('img');
    image.alt=codes[i];image.src=src;
    image.style.cssText='display:block;width:350px;max-width:100%;margin:0 auto 12px';
    box.append(caption,image);
  }
  dialog.prepend(box);
  const phases=[];
  let index=0, done=false, stage;
  function start(){
    stage={code:codes[index],exact:0,ctrlA:0,max:0,unexpected:[],inputs:0,other:0,enter:0,tab:0};
    phases.push(stage);
    title.textContent=index===0?'Escanee A dos veces, después B dos veces. No pulse botones en Chrome.':
      'A recibida. Apunte a B (etiqueta inferior) dos veces y retire la cámara.';
    input.focus();
  }
  document.addEventListener('input', e=>{
    if(e.target!==input){if(e.target.name!=='barcode')stage.other++;return;}
    if(!e.isTrusted)return;
    const v=input.value;
    stage.inputs++;stage.max=Math.max(stage.max,v.length);
    if(v===stage.code)stage.exact++;
    if(!codes.some(code=>code.startsWith(v))&&stage.unexpected.length<15)stage.unexpected.push({length:v.length});
    if(index===0 && stage.exact>=2){index++;start();}
    else if(index===1 && stage.exact>=2)done=true;
  },true);
  dialog.addEventListener('keydown',e=>{
    if(e.ctrlKey && e.key.toLowerCase()==='a')stage.ctrlA++;
    if(e.key==='Enter')stage.enter++;
    if(e.key==='Tab')stage.tab++;
  },true);
  window.phoneZ=()=>({done,phases,open:dialog.open,final:document.querySelector('[name=barcode]').value});
  start();
}
(async()=>{
  const browser=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:false,args:['--start-maximized']});
  try {
    const page=await browser.newPage({viewport:null,locale:'es-PE'});
    const nonce=crypto.randomBytes(32).toString('hex');
    const probe=await page.request.get(base,{headers:{'X-Audit03-Challenge':nonce}});
    assert.equal(probe.headers()['x-audit03-proof'],crypto.createHmac('sha256',fs.readFileSync(path.join(run,'.django-key'))).update(nonce).digest('hex'));
    const {admin}=JSON.parse(fs.readFileSync(path.join(run,'.credentials.json')));
    await page.goto(base);await page.locator('[name=email]').fill(admin.email);await page.locator('[name=password]').fill(admin.password);
    await page.locator('button[type=submit]').click();await page.getByRole('link',{name:'Registrar producto',exact:true}).click();
    page.on('request',r=>{if(r.method()==='POST')report.posts.push(new URL(r.url()).pathname);});
    await page.locator('[name=barcode_type]').selectOption('INTERNAL');
    await page.getByRole('button',{name:'Escanear código',exact:true}).click();
    const images=['A','B'].map(id=>'data:image/svg+xml;base64,'+fs.readFileSync(path.join(__dirname,'audit03k9_'+id+'.svg')).toString('base64'));
    await page.bringToFront();
    await page.evaluate(observe,{images,codes:['00CAT03K-A','00CAT03K-B']});
    report.status='waiting';write('ready.json');
    const deadline=Date.now()+240000;
    let previous='';
    do {
      report.observed=await page.evaluate(()=>window.phoneZ());
      const progress=JSON.stringify(report.observed);
      if(progress!==previous){write('progress.json');previous=progress;}
      if (report.observed.done || !report.observed.open)break;
      await page.waitForTimeout(500);
    } while(Date.now()<deadline);
    assert.ok(report.observed.done,'Falta completar ambas lecturas físicas');
    assert.equal(report.observed.final,'');assert.deepEqual(report.posts,[]);
    for(const stage of report.observed.phases){
      assert.ok(stage.exact>=2 && stage.ctrlA>=2);
      assert.deepEqual(stage.unexpected,[]);
      assert.equal(stage.other+stage.enter+stage.tab,0);
    }
    await page.getByRole('button',{name:'Usar código',exact:true}).click();
    assert.equal(await page.locator('[name=barcode]').inputValue(),'00CAT03K-B');
    assert.deepEqual(report.posts,[]);
    report.status='passed';
  }catch(error){report.error=error.message;report.status='incomplete-or-failed';process.exitCode=1;}
  finally{write('phone.json');await browser.close();}
})();
