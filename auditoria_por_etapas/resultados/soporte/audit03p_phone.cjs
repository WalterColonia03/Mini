// Physical test. Never fill, type, paste, or synthesize input on either barcode field.
// Use only via audit03k_run.py with keyboard_fixture() on a fresh marked instance.
const fs = require('fs');
const os = require('os');
const path = require('path');
const crypto = require('crypto');
const {execFileSync} = require('child_process');
const {chromium} = require(path.join(os.homedir(), '.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright-core'));
const output = process.env.AUDIT03_OUT;
const runDir = process.env.AUDIT03_RUN_DIR;
const base = 'http://127.0.0.1:' + process.env.AUDIT03_PORT;
const label = {A: '00CAT03K-A', B: '00CAT03K-B'};
const report = {test: '03-P', inputSource: 'operator with connected phone, operator attestation at each step',
  codeType: 'Code 128', started: new Date().toISOString(), status: 'preparing', stages: [], posts: [], checks: []};
function write(name, data) { fs.writeFileSync(path.join(output, name), JSON.stringify(data, null, 2)); }
function snapshot() {
  return JSON.parse(execFileSync(process.env.AUDIT03_PYTHON, [path.join(__dirname,'audit03k_run.py'),'snapshot'],
    {encoding:'utf8', timeout:12000, env:{...process.env,PYTHONIOENCODING:'utf-8'}}));
}
const same = (a, b) => JSON.stringify(a) === JSON.stringify(b);
class Stop extends Error {}
function check(id, success) {
  report.checks.push({id, success});
  if (!success) throw new Stop(id);
}
async function values(page) {
  return page.locator('form').filter({has:page.locator('[name=barcode]')})
    .locator('input:not([type=hidden])[name], select[name]').evaluateAll(fields =>
      Object.fromEntries(fields.map(field=>[field.name, field.value])));
}
async function edit(page, code) {
  if(new URL(page.url()).pathname!=='/productos/')
    await page.getByRole('link',{name:'Productos',exact:true}).click();
  await page.getByRole('row').filter({has:page.getByRole('cell',{name:code,exact:true})})
    .getByRole('link',{name:'Editar',exact:true}).click();
}

// This panel only observes the actual application input. It changes the displayed specimen
// and collects consent. Only the application's actual buttons transfer or submit the value.
function showSpecimen({symbol, code, action, title}) {
  const dialog = document.getElementById('barcode-capture-dialog');
  const field = document.getElementById('barcode-capture-input');
  if (!dialog?.open || !field) return false;
  if(window.k9Cleanup) window.k9Cleanup();
  const panel = document.createElement('section');
  panel.style.cssText='max-width:100%;margin:0 0 1em;padding:.5em;border:2px solid #15786d;background:white;color:#192f39;text-align:center;';
  const caption = document.createElement('strong');
  caption.textContent = title;
  const image = document.createElement('img');
  image.src = symbol;
  image.alt = 'Etiqueta de prueba ' + code;
  image.style.cssText='display:block;max-width:100%;width:490px;height:auto;margin:.25em auto;';
  const legend = document.createElement('p');
  legend.textContent = code + ' · Escanee con el teléfono, retire la cámara y confirme aquí.';
  const confirm = document.createElement('button');
  confirm.type = 'button';
  confirm.className = 'button button-secondary';
  confirm.textContent = action;
  confirm.disabled = true;
  panel.append(caption,image,legend,confirm);
  dialog.insertBefore(panel, field.closest('.field'));
  const state = {events:0, trustedInputs:0, exactReadings:0, maxLength:0, controlA:0,
    enter:0, tab:0, otherFieldInputs:0, confirmed:false, cancelled:false};
  const onInput = event => {
    if (event.target !== field) { state.otherFieldInputs++; return; }
    state.events++;
    if(event.isTrusted) state.trustedInputs++;
    if(event.isTrusted && field.value === code) state.exactReadings++;
    state.maxLength=Math.max(state.maxLength,field.value.length);
    confirm.disabled=field.value!==code || !state.exactReadings;
  };
  const onKey = event => {
    if(event.ctrlKey && event.key.toLowerCase()==='a') state.controlA++;
    if(event.key==='Enter') state.enter++;
    if(event.key==='Tab') state.tab++;
  };
  const onClose = () => {state.cancelled=true;};
  document.addEventListener('input',onInput,true);
  dialog.addEventListener('keydown',onKey,true);
  dialog.addEventListener('close',onClose);
  confirm.addEventListener('click',event=>{
    if(event.isTrusted && field.value===code && state.exactReadings && !confirm.disabled) {
      state.confirmed=true;
      confirm.disabled=true;
    }
  });
  const focusKind = () => {
    const active=document.activeElement;
    if (active === field) return 'temporary-input';
    if (active === confirm) return 'operator-confirm';
    return dialog.contains(active) ? 'other-in-dialog' : 'outside-dialog';
  };
  window.k9Status = () => ({...state, exact:field.value===code, length:field.value.length,
    focus:focusKind(), dialogOpen:dialog.open, documentFocused:document.hasFocus()});
  window.k9Cleanup = () => {
    document.removeEventListener('input',onInput,true);
    dialog.removeEventListener('keydown',onKey,true);
    dialog.removeEventListener('close',onClose);
    panel.remove();
    delete window.k9Cleanup;
    delete window.k9Status;
  };
  field.focus();
  return true;
}

async function physicalTest(browser) {
  const accounts=JSON.parse(fs.readFileSync(path.join(runDir,'.credentials.json'),'utf8'));
  const fixture=JSON.parse(fs.readFileSync(path.join(output,'fixture.json'),'utf8'));
  const context=await browser.newContext({viewport:null,locale:'es-PE'});
  context.setDefaultTimeout(8000);
  const page=await context.newPage();
  const nonce=crypto.randomBytes(32).toString('hex');
  const proof=await page.request.get(base,{headers:{'X-Audit03-Challenge':nonce}});
  check('isolated-instance',proof.headers()['x-audit03-proof']===crypto.createHmac('sha256',fs.readFileSync(path.join(runDir,'.django-key'))).update(nonce).digest('hex'));
  const initial=snapshot();
  const original=initial['catalog.Product'].find(p=>p.id===fixture.product_id);
  check('A-inactive-existing',original.barcode===label.A && !original.is_active);
  check('B-available',!initial['catalog.Product'].some(p=>p.barcode===label.B));
  async function login(p,role) {
    await p.goto(base);
    await p.locator('[name=email]').fill(accounts[role].email);
    await p.locator('[name=password]').fill(accounts[role].password);
    await p.locator('button[type=submit]').click();
  }
  await login(page,'admin');
  await page.getByRole('link',{name:'Registrar producto',exact:true}).click();
  page.on('request',req=>{
    if(req.method()==='POST' && new URL(req.url()).origin===base)
      report.posts.push({path:new URL(req.url()).pathname,time:new Date().toISOString()});
  });
  await page.locator('[name=name]').fill('AUD03 P lectura física');
  await page.locator('[name=category]').selectOption({label:'Higiene'});
  await page.locator('[name=sale_price]').fill('8.50');
  await page.bringToFront();
  const deadline=Date.now()+720000;
  report.deadline=new Date(deadline).toISOString();
  report.status='waiting-for-operator';
  async function readStage(id,letter,duplicate,minReads,action) {
    const before=snapshot(), form=await values(page), posts=report.posts.length;
    const stage={id,expected:label[letter],duplicate,minReads,status:'waiting'};
    report.stages.push(stage);
    const svg=fs.readFileSync(path.join(__dirname,'audit03k9_'+letter+'.svg')).toString('base64');
    check('P'+id+'-dialog',await page.evaluate(showSpecimen,{symbol:'data:image/svg+xml;base64,'+svg,
      code:stage.expected,title:'Fase '+id+' de 5: '+(duplicate?'código existente':'código permitido')+' · lea '+minReads+' vez/veces',action}));
    if(id===1)write('ready.json',{firstCode:stage.expected,deadline:report.deadline});
    let last='';
    for(;;) {
      if(Date.now()>=deadline)throw new Stop('operator-timeout');
      const s=await page.evaluate(()=>window.k9Status?.());
      if(!s?.dialogOpen || s.cancelled)throw new Stop('dialog-closed-before-confirmation');
      stage.observed=s;
      if(last!==JSON.stringify(s)){write('progress.json',report);last=JSON.stringify(s);}
      if(s.confirmed)break;
      await new Promise(r=>setTimeout(r,250));
    }
    check('P'+id+'-physical-exact',stage.observed.exact && stage.observed.exactReadings>=minReads && stage.observed.trustedInputs>0);
    check('P'+id+'-no-other-fields-or-post',stage.observed.otherFieldInputs===0 && report.posts.length===posts && same(await values(page),form));
    check('P'+id+'-database-unchanged',same(snapshot(),before));
    const expected=duplicate?'El código de barras ya está registrado':'Sin duplicados en esta consulta. Se volverá a comprobar al guardar.';
    await page.locator('#barcode-capture-status').filter({hasText:expected}).waitFor();
    stage.message=await page.locator('#barcode-capture-status').innerText();
    check('P'+id+'-exact-message',stage.message===expected);
    check('P'+id+'-copy-state',(await page.locator('#barcode-capture-apply').isDisabled())===duplicate);
    await page.screenshot({path:path.join(output,'P'+id+'.png')});
    stage.status='verified';stage.finished=new Date().toISOString();write('progress.json',report);
    await page.evaluate(()=>window.k9Cleanup());
  }
  const open=()=>page.getByRole('button',{name:'Escanear código',exact:true}).click();
  const cancel=()=>page.locator('#barcode-capture-cancel').click();
  await open();
  await readStage(1,'A',true,2,'Confirmar dos lecturas de A y continuar');
  await readStage(2,'B',false,1,'Confirmar B y guardar una ficha de prueba');
  await page.getByRole('button',{name:'Usar código',exact:true}).click();
  check('B-copied-exact',await page.locator('[name=barcode]').inputValue()===label.B && report.posts.length===0);
  await page.getByRole('button',{name:'Registrar producto',exact:true}).click();
  await page.waitForURL(/\/registrado\/$/);
  const created=snapshot();
  const newProduct=created['catalog.Product'].find(p=>p.barcode===label.B);
  check('one-explicit-create',!!newProduct && created['catalog.Product'].length===initial['catalog.Product'].length+1 && report.posts.length===1);
  check('existing-products-unchanged',same(created['catalog.Product'].filter(p=>p.id!==newProduct.id),initial['catalog.Product']));
  await page.getByRole('link',{name:'Registrar producto',exact:true}).first().click();
  await open();
  await readStage(3,'B',true,2,'Confirmar dos lecturas de B registrado');
  await cancel();
  await edit(page,label.A);
  await open();
  await readStage(4,'A',false,1,'Confirmar código propio y probar código ajeno');
  await readStage(5,'B',true,1,'Confirmar bloqueo del código ajeno y terminar');
  await cancel();
  check('no-automatic-or-edit-post',report.posts.length===1);
  check('final-business-state',same(snapshot(),created));
  for(const key of Object.keys(initial).filter(k=>!['catalog.Product','commerce'].includes(k)))
    check('preserved-'+key,same(initial[key],created[key]));
  // Observe other roles through menus and direct requests. These are software checks.
  for(const role of ['warehouse','seller']) {
    const c=await browser.newContext({locale:'es-PE'}),p=await c.newPage();
    await login(p,role);
    if(role==='warehouse') {
      await p.getByRole('link',{name:'Catálogo de productos',exact:true}).click();
      check('warehouse-sees-B',await p.getByRole('cell',{name:label.B,exact:true}).count()===1);
      check('warehouse-no-edit',await p.getByRole('link',{name:'Editar',exact:true}).count()===0);
    } else {
      await p.getByRole('link',{name:'Preparar venta',exact:true}).click();
      // Catalog administrative surface remains forbidden to this role.
      check('seller-catalog-forbidden',(await p.request.get(base+'/productos/')).status()===403);
    }
    check(role+'-code-check-forbidden',(await p.request.get(base+'/productos/codigos/comprobar/?barcode='+label.B)).status()===403);
    await c.close();
  }
  check('roles-no-commercial-changes',same(snapshot(),created));
  report.status='completed';
}
(async()=>{
  let browser;
  try {
    browser=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:false,args:['--start-maximized'],timeout:10000});
    report.browser=browser.version();await physicalTest(browser);
  } catch(error) {
    report.status='partial';report.stop=error instanceof Stop?error.message:'browser-or-harness-error-'+error.name;process.exitCode=1;
  } finally {
    report.finished=new Date().toISOString();write('phone.json',report);if(browser)await browser.close();
  }
})();