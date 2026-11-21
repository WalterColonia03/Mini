// The operator supplies the only input to the barcode field using the phone.
const fs = require('fs');
const os = require('os');
const path = require('path');
const crypto = require('crypto');
const {execFileSync} = require('child_process');
const { chromium } = require(path.join(os.homedir(), '.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright-core'));
const run = process.env.AUDIT03_RUN_DIR;
const out = process.env.AUDIT03_OUT;
const base = 'http://127.0.0.1:' + process.env.AUDIT03_PORT;
const expected = process.env.AUDIT03_SPECIMEN || '0012345678905';
const save = (name, value) => fs.writeFileSync(path.join(out, name), JSON.stringify(value, null, 2));
const wait = ms => new Promise(resolve => setTimeout(resolve, ms));
const isTextSpecimen=expected==='00CAT03K';
const report = {expected, entry: '/productos/nuevo/', symbology:isTextSpecimen?'Code 128':'EAN-13', inputs:0, posts:0, enters:0, tabs:0};
report.events=[];
const trace=(kind,data)=>report.events.push({at:new Date().toISOString(),kind,data});

// EAN-13 with first digit zero uses the LLLLLL left parity pattern.
function specimen(value) {
  const digits = ['0001101','0011001','0010011','0111101','0100011','0110001','0101111','0111011','0110111','0001011'];
  const checksum = [...value.slice(0,12)].reduce((sum,n,i)=>sum+Number(n)*(i%2?3:1),0);
  if (value[0] !== '0' || (10-checksum%10)%10 !== Number(value[12])) throw Error('Invalid specimen');
  const left = [...value.slice(1,7)].map(n=>digits[n]).join('');
  const right = [...value.slice(7)].map(n=>[...digits[n]].map(bit=>bit==='1'?'0':'1').join('')).join('');
  const bars = [...('101'+left+'01010'+right+'101')].map((bit,i)=>bit==='1'?'<rect x="'+(12+i)+'" y="1" width="1" height="27"/>':'').join('');
  return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 119 30" width="357" height="90" style="max-width:100%;background:white" shape-rendering="crispEdges" aria-label="Etiqueta EAN-13">'+bars+'</svg>';
}

(async () => {
  const browser = await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:false,args:['--start-maximized']});
  try {
    const page = await (await browser.newContext({viewport:null, locale:'es-PE'})).newPage();
    const nonce = crypto.randomBytes(32).toString('hex');
    const proof = await page.request.get(base,{headers:{'X-Audit03-Challenge':nonce}});
    if (proof.headers()['x-audit03-proof'] !== crypto.createHmac('sha256',fs.readFileSync(path.join(run,'.django-key'))).update(nonce).digest('hex')) throw Error('Isolation mismatch');
    const {admin} = JSON.parse(fs.readFileSync(path.join(run,'.credentials.json'),'utf8'));
    await page.goto(base);
    await page.locator('[name=email]').fill(admin.email);
    await page.locator('[name=password]').fill(admin.password);
    await Promise.all([page.waitForNavigation(),page.locator('button[type=submit]').click()]);
    await page.getByRole('link',{name:'Registrar producto',exact:true}).click();
    const barcode = page.locator('[name=barcode]');
    await page.locator('[name=name]').fill('Lectura física 03-K');
    await page.locator('[name=category]').selectOption({label:'Higiene'});
    await page.locator('[name=sale_price]').fill('8.50');
    if (await barcode.inputValue() !== '') throw Error('The field must start empty');
    page.on('request',req=>{
      if (req.method()==='POST' && req.url() === base + report.entry) {
        report.posts++;
        const value=new URLSearchParams(req.postData()||'').get('barcode')||'';
        trace('POST',{length:value.length,exact:value===expected});
        save('progress.json',report);
      }
    });
    await page.exposeFunction('observeAuditK', (kind,data) => {
      if (kind==='input') {
        report.inputs++;
        report.field=data;
        if(data.exact) report.exactObserved=true;
        if(data.exact) report.exactOccurrences=(report.exactOccurrences||0)+1;
        report.maximumLength=Math.max(report.maximumLength||0,data.length);
        report.lastInput=new Date().toISOString();
      } else if (kind==='operator') {
        report.operatorConfirmed=true;
        report.operatorAt=new Date().toISOString();
      } else {
        if (kind==='Enter') report.enters++;
        if (kind==='Tab') report.tabs++;
        trace(kind,data);
      }
      save('progress.json',report);
    });
    const installPanel = ({expected,svg,isTextSpecimen})=>{
      document.title='Prueba física 03-K · Registrar producto';
      const field=document.querySelector('[name=barcode]');
      if(!field || document.getElementById('audit-scan')) return;
      const form=field.form;
      const where=el=>['barcode','name','minimum_stock','unit','sale_price','category'].includes(el?.name)?el.name:
        (el?.id==='audit-finish'?'audit-finish':el?.tagName);
      for(const event of ['focus','blur']) window.addEventListener(event,()=>window.observeAuditK('window-'+event,where(document.activeElement)));
      form.addEventListener('focusin',e=>window.observeAuditK('form-focus',where(e.target)));
      form.addEventListener('submit',e=>window.observeAuditK('submit',{trigger:where(e.submitter),focus:where(document.activeElement)}));
      document.addEventListener('keydown',event=>{
        if (['Enter','Tab'].includes(event.key)) window.observeAuditK(event.key,where(event.target));
        if (event.ctrlKey && event.key.toLowerCase()==='a') window.observeAuditK('Control+A',where(event.target));
      });
      field.addEventListener('input',event=>window.observeAuditK('input',{
        length:field.value.length, exact:field.value===expected, repeatedSpecimen:field.value.length>0 && field.value.length%expected.length===0 && field.value===expected.repeat(field.value.length/expected.length), upcEquivalent:!isTextSpecimen && field.value===expected.slice(1), trusted:event.isTrusted
      }));
      const box=document.createElement('section');
      box.id='audit-scan';
      box.style.cssText='margin:8px 0;padding:10px;background:white;color:black;border:2px solid #244354;text-align:center';
      box.innerHTML='<strong>Prueba física 03-K</strong><div>'+svg+'</div><div style="font:18px monospace">'+expected+'</div><p>Escanea una vez con el teléfono y después pulsa este botón.</p><button type="button">Ya escaneé con el teléfono</button>';
      box.querySelector('button').id='audit-finish';
      box.querySelector('button').onclick=()=>{window.observeAuditK('operator');box.querySelector('button').disabled=true;};
      field.insertAdjacentElement('afterend',box);
      box.scrollIntoView({block:'center'});
      field.focus({preventScroll:true});
    };
    const panel={expected,isTextSpecimen,svg:isTextSpecimen?fs.readFileSync(path.join(__dirname,'audit03k_code128.svg'),'utf8'):specimen(expected)};
    page.on('domcontentloaded',async()=>{
      if(page.url()===base+report.entry) await page.evaluate(installPanel,panel).catch(()=>{});
    });
    await page.evaluate(installPanel,panel);
    await page.bringToFront();
    report.browser=browser.version();
    report.ready=new Date().toISOString();
    report.focused=await barcode.evaluate(el=>el===document.activeElement);
    await page.screenshot({path:path.join(out,'01-etiqueta.png')});
    save('ready.json',report);
    const deadline=Date.now()+15*60*1000;
    while (Date.now()<deadline && !page.isClosed() && !report.operatorConfirmed && !(report.posts && new URL(page.url()).pathname!==report.entry)) await wait(500);
    if (!page.isClosed()) {
      await wait(3500);
      report.finalPath=new URL(page.url()).pathname;
      if (report.finalPath===report.entry && await barcode.count()) {
        const value=await barcode.inputValue();
        report.finalField={length:value.length,exact:value===expected,upcEquivalent:!isTextSpecimen && value===expected.slice(1)};
        if (!value || report.finalField.exact || report.finalField.upcEquivalent) await page.screenshot({path:path.join(out,'02-resultado.png')});
      }
    } else report.closedByOperator=true;
    if (process.env.AUDIT03_VERIFY_SAVE==='1' && report.operatorConfirmed && report.finalField?.exact && report.posts===0 && report.enters===0) {
      const snapshot=()=>JSON.parse(execFileSync(process.env.AUDIT03_PYTHON,[path.join(__dirname,'audit03k_run.py'),'snapshot'],{encoding:'utf8',env:{...process.env,PYTHONIOENCODING:'utf-8'}}));
      const before=snapshot();
      report.beforeExplicitSave={posts:report.posts,products:before['catalog.Product'].length,exact:true};
      await page.getByTestId('product-submit').click();
      await page.waitForURL(/\/registrado\/$/);
      const after=snapshot();
      const product=after['catalog.Product'].find(p=>p.barcode===expected);
      report.explicitSave={clickedBy:'audit automation after operator confirmed physical scan',products:after['catalog.Product'].length,exact:product?.barcode===expected,path:new URL(page.url()).pathname};
      await page.screenshot({path:path.join(out,'03-guardado-explicito.png')});
      const accounts=JSON.parse(fs.readFileSync(path.join(run,'.credentials.json'),'utf8'));
      report.roles=[];
      for(const [role,menu] of [['warehouse','Catálogo de productos'],['seller','Preparar venta']]) {
        const other=await (await browser.newContext({viewport:{width:1366,height:900},locale:'es-PE'})).newPage();
        await other.goto(base);
        await other.locator('[name=email]').fill(accounts[role].email);
        await other.locator('[name=password]').fill(accounts[role].password);
        await Promise.all([other.waitForNavigation(),other.locator('button[type=submit]').click()]);
        await other.getByRole('link',{name:menu,exact:true}).click();
        if(role==='warehouse') {
          const row=other.getByRole('row').filter({has:other.getByRole('cell',{name:expected,exact:true})});
          report.roles.push({role,cells:await row.getByRole('cell').allInnerTexts(),buttons:await row.getByRole('button').count()});
        } else {
          await other.locator('[name=query]').fill(expected);
          await other.getByRole('button',{name:'Buscar',exact:true}).click();
          report.roles.push({role,offered:await other.getByRole('button',{name:'Agregar',exact:true}).count()});
        }
        await other.screenshot({path:path.join(out,'04-'+role+'.png'),fullPage:true});
      }
      save('orm-after-explicit-save.json',snapshot());
    }
    report.finished=new Date().toISOString();
    save('physical.json',report);
  } finally { await browser.close(); }
})().catch(error=>{console.error(error.message);process.exitCode=1;});
