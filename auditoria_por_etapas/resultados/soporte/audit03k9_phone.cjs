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
const report = {test: '03-K9', inputSource: 'operator with connected phone, operator attestation at each step',
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
  const accounts = JSON.parse(fs.readFileSync(path.join(runDir,'.credentials.json'),'utf8'));
  const fixture = JSON.parse(fs.readFileSync(path.join(output,'fixture.json'),'utf8'));
  const context = await browser.newContext({viewport:null,locale:'es-PE'});
  context.setDefaultTimeout(5000);
  context.setDefaultNavigationTimeout(8000);
  const page = await context.newPage();
  const nonce = crypto.randomBytes(32).toString('hex');
  const proof = await page.request.get(base,{headers:{'X-Audit03-Challenge':nonce}});
  check('isolated-instance',proof.headers()['x-audit03-proof']===crypto.createHmac('sha256',fs.readFileSync(path.join(runDir,'.django-key'))).update(nonce).digest('hex'));
  const initial = snapshot();
  const original = initial['catalog.Product'].find(p=>p.id===fixture.product_id);
  check('sold-product-and-history-exist',!!original && initial['sales.SaleLine'].some(line=>line.product_id===original.id));
  check('labels-available',!initial['catalog.Product'].some(p=>Object.values(label).includes(p.barcode)));
  await page.goto(base);
  await page.locator('[name=email]').fill(accounts.admin.email);
  await page.locator('[name=password]').fill(accounts.admin.password);
  await page.locator('button[type=submit]').click();
  await page.getByRole('link',{name:'Registrar producto',exact:true}).click();
  page.on('request', req=>{
    if(req.method()!=='POST' || new URL(req.url()).origin!==base) return;
    const route = new URL(req.url()).pathname;
    const code = new URLSearchParams(req.postData() || '').get('barcode') || '';
    report.posts.push({screen:route==='/productos/nuevo/'?'create':route==='/productos/'+original.id+'/editar/'?'edit':'other',
      observed:Object.keys(label).find(key=>label[key]===code)||'other',length:code.length});
  });
  await page.locator('[name=name]').fill('AUD03 K9 físico');
  await page.locator('[name=category]').selectOption({label:'Higiene'});
  await page.locator('[name=sale_price]').fill('8.50');
  await page.bringToFront();
  const deadline=Date.now()+240000;
  report.deadline=new Date(deadline).toISOString();
  report.status='waiting-for-operator';
  async function readStage(id, letter, action) {
    const stage={id,expected:label[letter],status:'waiting',beforePosts:report.posts.length};
    report.stages.push(stage);
    const svg=fs.readFileSync(path.join(__dirname,'audit03k9_'+letter+'.svg')).toString('base64');
    const ok=await page.evaluate(showSpecimen,{symbol:'data:image/svg+xml;base64,'+svg,code:stage.expected,
      title:'Prueba física '+id+' de 5',action});
    check('stage-'+id+'-dialog',ok);
    if(id===1) write('ready.json',{firstCode:stage.expected,deadline:report.deadline});
    let last='';
    for(;;) {
      if(Date.now()>=deadline) throw new Stop('operator-timeout');
      if(page.isClosed()) throw new Stop('operator-closed-browser');
      const status=await page.evaluate(()=>window.k9Status?.());
      if(!status || !status.dialogOpen || status.cancelled) throw new Stop('dialog-closed-before-confirmation');
      stage.observed=status;
      if(last!==JSON.stringify(status)) {write('progress.json',report);last=JSON.stringify(status);}
      if(status.confirmed) break;
      await new Promise(resolve=>setTimeout(resolve,250));
    }
    check('stage-'+id+'-exact-and-isolated',stage.observed.exact && stage.observed.exactReadings>0 &&
      stage.observed.otherFieldInputs===0 && stage.beforePosts===report.posts.length);
    stage.status='confirmed-by-operator';
    stage.confirmed=new Date().toISOString();
    write('progress.json',report);
  }
  async function applyAndSave(id,letter,submit,beforeValues,beforeState) {
    const n=report.posts.length;
    check(id+'-unchanged-while-reading',same(await values(page),beforeValues)&&same(snapshot(),beforeState));
    await page.evaluate(()=>window.k9Cleanup());
    await page.getByRole('button',{name:'Usar código',exact:true}).click();
    check(id+'-only-code-transferred',same(await values(page),{...beforeValues,barcode:label[letter]})&&report.posts.length===n);
    const [response] = await Promise.all([page.waitForResponse(r=>r.request().method()==='POST'&&new URL(r.url()).origin===base),
      page.getByRole('button',{name:submit,exact:true}).click()]);
    check(id+'-one-explicit-post',report.posts.length===n+1&&report.posts[n].observed===letter &&
      report.posts[n].screen===(id==='create'?'create':'edit'));
    return response.status();
  }
  const open = () => page.getByRole('button',{name:'Escanear código',exact:true}).click();
  const createValues=await values(page);
  await open();
  await readStage(1,'A','Confirmar lectura A y mostrar B');
  await readStage(2,'B','Confirmar B y autorizar el alta de prueba');
  check('created-http',await applyAndSave('create','B','Registrar producto',createValues,initial)===302);
  await page.waitForURL(/\/registrado\/$/);
  const created=snapshot();
  const newProduct=created['catalog.Product'].find(p=>p.barcode===label.B);
  check('created-one-B',!!newProduct && newProduct.name===createValues.name &&
    created['catalog.Product'].length===initial['catalog.Product'].length+1);
  await edit(page,original.barcode);
  const editValues=await values(page);
  await open();
  await readStage(3,'B','Confirmar lectura B y mostrar A');
  await readStage(4,'A','Confirmar A y autorizar el guardado de la ficha vendida');
  check('edited-http',await applyAndSave('edit','A','Guardar cambios',editValues,created)===302);
  await page.waitForURL(base+'/productos/');
  const edited=snapshot();
  check('sold-product-keeps-identity',same(edited['catalog.Product'].find(p=>p.id===original.id),{...original,barcode:label.A}));
  check('other-products-unchanged',same(edited['catalog.Product'].filter(p=>p.id!==original.id),
    created['catalog.Product'].filter(p=>p.id!==original.id)));
  for (const key of Object.keys(initial).filter(key=>!['catalog.Product','commerce'].includes(key)))
    check('preserved-'+key,same(initial[key],edited[key]));
  await edit(page,label.A);
  const duplicateValues=await values(page);
  await open();
  await readStage(5,'B','Confirmar B y probar el rechazo del duplicado');
  check('duplicate-http',await applyAndSave('duplicate','B','Guardar cambios',duplicateValues,edited)===200);
  check('duplicate-visible',await page.getByText('Ya existe un producto con este código de barras.',{exact:true}).count()===1);
  check('duplicate-no-writes',same(edited,snapshot()));
  report.status='completed';
}

(async()=>{
  let browser;
  try {
    browser=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:false,
      args:['--start-maximized'],timeout:10000});
    report.browser=browser.version();
    await physicalTest(browser);
  } catch(error) {
    report.status='partial';
    // Browser errors may print the live DOM. Retain only known safe failure codes.
    report.stop=error instanceof Stop ? error.message : 'browser-or-harness-error-'+error.name;
    process.exitCode=1;
  } finally {
    report.finished=new Date().toISOString();
    write('phone.json',report);
    if(browser) await browser.close();
  }
})();
