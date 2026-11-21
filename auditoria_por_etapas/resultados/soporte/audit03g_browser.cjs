/* Reproduce the edit flow in Chrome against the marked local instance. */
const fs = require('fs');
const path = require('path');
const os = require('os');
const crypto = require('crypto');
const { execFileSync } = require('child_process');
const { chromium } = require(path.join(os.homedir(), '.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright-core'));
const run = process.env.AUDIT03_RUN_DIR;
const out = process.env.AUDIT03_OUT;
const base = 'http://127.0.0.1:' + process.env.AUDIT03_PORT;
const entry = base + '/productos/nuevo/';
const accounts = JSON.parse(fs.readFileSync(path.join(run, '.credentials.json'), 'utf8'));
const report = { stage: '03-G', started: new Date().toISOString(), cases: [], errors: [] };

function record(id, ok, details = {}) {
  report.cases.push({ id, ok: Boolean(ok), ...details });
}
function snapshot() {
  return JSON.parse(execFileSync(process.env.AUDIT03_PYTHON, [path.join(__dirname, 'audit03g_run.py'), 'snapshot'], {
    encoding: 'utf8', env: { ...process.env, PYTHONIOENCODING: 'utf-8' }
  }));
}
async function follow(page, button) {
  await Promise.all([page.waitForNavigation({waitUntil: 'domcontentloaded'}), button.click()]);
}
async function screenshot(page, file) {
  await page.screenshot({path: path.join(out, file + '.png'), fullPage: true});
  return file + '.png';
}
async function login(page, role) {
  await page.goto(base);
  await page.locator('[name=email]').fill(accounts[role].email);
  await page.locator('[name=password]').fill(accounts[role].password);
  await follow(page, page.locator('button[type=submit]'));
}
async function fields(page) {
  return page.locator('form[data-testid=product-form] .field').evaluateAll(nodes => nodes.map(node => {
    const field = node.querySelector('input,select');
    const refs = (field.getAttribute('aria-describedby') || '').split(' ').filter(Boolean);
    return {name: field.name, label: node.querySelector('label').textContent, value: field.value,
      required: field.required, type: field.type, max: field.max, min: field.min, maxLength: field.maxLength,
      mode: field.inputMode, refs, linked: refs.every(id => Boolean(document.getElementById(id)))};
  }));
}
async function fill(page, data) {
  for (const [name, value] of Object.entries(data)) {
    const input = page.locator('[name=' + name + ']');
    if (['category','unit'].includes(name)) await input.selectOption(value);
    else await input.fill(value);
  }
}
async function submit(page, data, url=entry) {
  const cookie = (await page.context().cookies(base)).find(c=>c.name==='audit03g_csrftoken');
  if (!cookie) throw Error('Missing CSRF cookie in the authenticated test context');
  const token = cookie.value;
  return page.request.post(url, {form: data, headers:{'X-CSRFToken': token}, maxRedirects:0});
}
async function disagreements(page, response) {
  if (response.status() !== 200) return {};
  return page.evaluate(html => {
    const doc = new DOMParser().parseFromString(html, 'text/html');
    return Object.fromEntries([...doc.querySelectorAll('[aria-invalid=true]')].map(input =>
      [input.name, input.parentElement.querySelector('.text-danger')?.textContent.trim() || '']));
  }, await response.text());
}
(async () => {
  const browser = await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true});
  report.browser=browser.version();
  const opts={viewport:{width:1366,height:900},locale:'es-PE'};
  const pages=[];
  for(let i=0;i<4;i++)pages.push(await (await browser.newContext(opts)).newPage());
  const [a,w,s,v]=pages;
  for(const page of pages)page.setDefaultTimeout(12000);
  const equal=(x,y)=>JSON.stringify(x)===JSON.stringify(y);
  const before=snapshot();
  const fixture=JSON.parse(fs.readFileSync(path.join(out,'fixture.json'),'utf8'));
  const id=fixture.product_id;
  const edit=base+'/productos/'+id+'/editar/';
  const current=()=>snapshot()['catalog.Product'].find(p=>p.id===id);
  const cats=Object.fromEntries(before['catalog.Category'].map(c=>[c.name,c.id]));
  const original=before['catalog.Product'].find(p=>p.id===id);
  const data=()=>{const p=current();return {name:p.name,barcode:p.barcode,category:p.category_id,sale_price:p.sale_price,minimum_stock:String(p.minimum_stock)}};
  const receipt=base+'/ventas/constancia/'+fixture.sale_id+'/';
  async function change(values) {
    await a.goto(edit);await fill(a,values);await follow(a,a.getByRole('button',{name:'Guardar cambios',exact:true}));
  }
  async function query(value) {
    await s.goto(base+'/ventas/');await s.locator('[name=query]').fill(value);
    await follow(s,s.getByRole('button',{name:'Buscar',exact:true}));
  }
  async function catalogueRow(page,code) {
    await page.goto(base+'/productos/');
    return page.locator('tbody tr').filter({has:page.getByRole('cell',{name:code,exact:true})}).innerText();
  }
  try {
    const nonce=crypto.randomBytes(32).toString('hex');
    const probe=await a.request.get(base,{headers:{'X-Audit03-Challenge':nonce}});
    if(probe.headers()['x-audit03-proof']!==crypto.createHmac('sha256',fs.readFileSync(path.join(run,'.django-key'))).update(nonce).digest('hex'))throw Error('Isolated identity mismatch');
    await login(a,'admin');await login(w,'warehouse');await login(s,'seller');
    // Keyboard input only: this does not connect a phone or Barcode to PC Server.
    await follow(a,a.getByRole('link',{name:'Registrar producto',exact:true}));
    const capture=a.locator('[name=barcode]');
    await capture.focus();
    await capture.pressSequentially('0012345678905');
    await capture.press('Tab');
    record('G01-keyboard-leading-zero',await capture.inputValue()==='0012345678905' && equal(before,snapshot()),
      {mode:'simulated keyboard; no physical reader',screenshot:await screenshot(a,'G01-captura-teclado')});
    await capture.fill('');await capture.pressSequentially('DUPLICADO');await capture.press('Tab');
    const liveDuplicate=await a.locator('#id_barcode_error').count();
    record('G02-duplicate-observation',liveDuplicate===0 && equal(before,snapshot()),
      {observation:'No immediate duplicate message after keyboard input and blur. HU-PROD-03 CA02 remains pending.',screenshot:await screenshot(a,'G02-duplicado-sin-aviso')});
    await follow(s,s.getByRole('link',{name:'Preparar venta',exact:true}));
    await s.goto(receipt);const receiptBefore=await s.locator('#constancia-interna').innerText();
    await follow(a,a.getByRole('link',{name:'Productos',exact:true}));
    const target=a.locator('tbody tr').filter({has:a.getByRole('cell',{name:original.barcode,exact:true})});
    await follow(a,target.getByRole('link',{name:'Editar',exact:true}));
    const inputs=await a.locator('main input:not([type=hidden]),main select').evaluateAll(nodes=>nodes.map(n=>({name:n.name,value:n.value,disabled:n.disabled,max:n.max,min:n.min,required:n.required})));
    record('D01-fields',inputs.length===5&&inputs.find(i=>i.name==='sale_price').value==='8.50'&&inputs.find(i=>i.name==='minimum_stock').value==='10',
      {inputs,barcodeEditable:!inputs.find(i=>i.name==='barcode').disabled,screenshot:await screenshot(a,'01-edicion')});
    await a.locator('[name=sale_price]').fill('11.00');await follow(a,a.getByRole('link',{name:'Cancelar',exact:true}));
    record('D02-cancel',a.url()===base+'/productos/'&&equal(before,snapshot()));
    await change({sale_price:'9.20'});
    record('D03-price-save',current().sale_price==='9.20'&&(await a.locator('main').innerText()).includes('Producto «'+original.name+'» actualizado.'),{screenshot:await screenshot(a,'03-precio')});
    const afterEdit=snapshot();
    record('D04-edit-only-product',['inventory.Lot','sales.Sale','sales.SaleLine','sales.SaleDraftLine','cash.CashShift'].every(k=>equal(before[k],afterEdit[k])));
    record('D05-warehouse-price',(await catalogueRow(w,original.barcode)).includes('9,20'));
    await query(original.barcode);
    const searchText=await s.locator('tbody tr').innerText(),draftText=await s.locator('.draft-lines').innerText();
    record('D06-search-and-old-draft',searchText.includes('9,20')&&draftText.includes('8,50'),{search:searchText,draft:draftText,screenshot:await screenshot(s,'06-borrador')});
    await follow(s,s.getByRole('link',{name:'Cobrar venta →',exact:true}));
    await s.locator('[name=cash_received]').fill('30.00');
    await follow(s,s.getByRole('button',{name:'Confirmar cobro',exact:true}));
    const warned=snapshot(),warning=await s.locator('main').innerText();
    record('D07-price-warning',warning.includes('cambió de S/ 8.50 a S/ 9.20')&&
      warned['sales.SaleDraftLine'].find(l=>l.product_id===id && l.draft_id===warned['sales.SaleDraft'].find(d=>d.status==='ACTIVE').id)?.unit_price==='9.20'&&
      ['sales.Sale','sales.SaleLine','inventory.Lot'].every(k=>equal(before[k],warned[k])),
      {message:warning.split('\n').filter(t=>t.includes('cambió')||t.includes('Verifica')),screenshot:await screenshot(s,'07-aviso-precio')});
    await s.locator('[name=cash_received]').fill('30.00');
    await follow(s,s.getByRole('button',{name:'Confirmar cobro',exact:true}));
    const sold=snapshot();
    const newSale=sold['sales.Sale'].find(p=>p.id!==fixture.sale_id);
    record('D08-new-sale',sold['sales.Sale'].length===2&&newSale?.total_amount==='18.40'&&newSale?.change_given==='11.60'&&
      sold['sales.SaleLine'].some(l=>l.unit_price==='9.20'&&l.quantity===2)&&sold['inventory.Lot'][0].available_quantity===17,
      {newSale,screenshot:await screenshot(s,'08-nueva-venta')});
    await s.goto(receipt);
    record('D09-history-price',(await s.locator('#constancia-interna').innerText())===receiptBefore&&
      equal(before['sales.SaleLine'][0],sold['sales.SaleLine'].find(l=>l.id===before['sales.SaleLine'][0].id)));
    await follow(s,s.getByRole('link',{name:'Nueva venta',exact:true}));
    await query(original.barcode);await follow(s,s.getByRole('button',{name:'Agregar',exact:true}));
    record('D10-new-draft',snapshot()['sales.SaleDraftLine'].some(l=>l.unit_price==='9.20'&&l.quantity===1));
    for(const minimum of ['17','16']) {
      await change({minimum_stock:minimum});
      const text=await catalogueRow(w,original.barcode);
      record('D11-minimum-'+minimum,text.includes('Stock bajo')===(minimum==='17')&&current().minimum_stock===Number(minimum),{row:text});
    }
    await change({name:'  AUD03D   Atún nuevo  '});
    const renamed=current();
    record('D12-name-save',renamed.name==='AUD03D Atún nuevo'&&snapshot().commerce.find(p=>p.id===id).search_name==='aud03d atún nuevo');
    await query('AUD03D Atún nuevo');
    record('D13-name-in-sale',(await s.locator('tbody tr').innerText()).includes(renamed.name)&&(await s.locator('.draft-lines').innerText()).includes(renamed.name));
    await s.goto(receipt);record('D14-name-history',(await s.locator('#constancia-interna').innerText())===receiptBefore);
    await change({barcode:'AUD03D-NUEVO'});
    const newCode=current().barcode;
    record('D15-code-edit',newCode==='AUD03D-NUEVO',{classification:'DOC03-02 accepted: administrative correction with unique code and preserved history'});
    await query(newCode);const newFound=await s.getByRole('button',{name:'Agregar',exact:true}).count();
    await query(original.barcode);const oldFound=await s.getByRole('button',{name:'Agregar',exact:true}).count();
    await s.goto(receipt);
    record('D16-code-history',newFound===1&&oldFound===0&&(await s.locator('#constancia-interna').innerText())===receiptBefore);
    await change({category:cats['Alternativa activa']});
    record('D17-category-save',current().category_id===cats['Alternativa activa']&&(await catalogueRow(w,newCode)).includes('Alternativa activa'));
    await a.goto(edit);
    const checks=[
      ['empty',{},['name','barcode','sale_price','minimum_stock']],
      ...['','0','-1','1.001','1e2','10000000.00','texto'].map((val,i)=>['price-'+i,{...data(),sale_price:val},['sale_price']]),
      ...['','-1','0.5','1000000','texto'].map((val,i)=>['minimum-'+i,{...data(),minimum_stock:val},['minimum_stock']]),
      ['name-empty',{...data(),name:''},['name']],['name-long',{...data(),name:'a'.repeat(161)},['name']],
      ['name-duplicate',{...data(),name:'ATÚN OCUPADO'},['name']],
      ['barcode-empty',{...data(),barcode:''},['barcode']],['barcode-long',{...data(),barcode:'a'.repeat(65)},['barcode']],
      ['barcode-duplicate',{...data(),barcode:'du pli cado'},['barcode']],
      ['category-inactive',{...data(),category:cats.Suspendida},['category']],
      ['category-absent',{...data(),category:'88888888-8888-4888-8888-888888888888'},['category']]
    ];
    const beforeRejected=snapshot();
    for(const [id,payload,expected] of checks) {
      const response=await submit(a,payload,edit),errors=await disagreements(a,response);
      record('D18-'+id,response.status()===200&&expected.every(f=>errors[f]),{status:response.status(),errors});
    }
    record('D19-rejections-preserve',equal(beforeRejected,snapshot()));
    await a.goto(edit);await a.locator('[name=sale_price]').fill('0');await follow(a,a.getByRole('button',{name:'Guardar cambios',exact:true}));
    const accessible=await a.locator('[name=sale_price]').evaluate(input=>({invalid:input.getAttribute('aria-invalid'),
      references:(input.getAttribute('aria-describedby')||'').split(' ').filter(Boolean).every(id=>Boolean(document.getElementById(id))),
      focused:document.activeElement===input}));
    record('D20-field-error',accessible.invalid==='true'&&accessible.references&&accessible.focused,{...accessible,screenshot:await screenshot(a,'20-error')});
    await change({category:''});
    record('D21-empty-category-retains',current().category_id===cats['Alternativa activa']);
    for(const [label,page] of [['warehouse',w],['seller',s]]) {
      const beforeRole=snapshot();
      const get=await page.request.get(edit),post=await submit(page,{...data(),sale_price:'1.00'},edit);
      record('D22-role-'+label,get.status()===403&&post.status()===403&&equal(beforeRole,snapshot()),{statuses:[get.status(),post.status()]});
    }
    const anon=await v.request.get(edit,{maxRedirects:0});
    record('D23-visitor',anon.status()===302);
    const missing=await a.request.get(base+'/productos/88888888-8888-4888-8888-888888888888/editar/');
    record('D24-missing',missing.status()===404);
    await a.goto(base+'/productos/categorias/');
    const catRow=a.getByRole('row').filter({has:a.getByRole('cell',{name:'Alternativa activa',exact:true})});
    await follow(a,catRow.getByRole('button',{name:'Desactivar',exact:true}));
    await change({sale_price:'9.30'});
    record('D25-retain-inactive-category',current().sale_price==='9.30'&&current().category_id===cats['Alternativa activa'],{screenshot:await screenshot(a,'25-categoria-inactiva')});
    await change({category:cats['Productos enlatados'],sale_price:'9.20'});
    record('D26-reclassify-active',current().category_id===cats['Productos enlatados']);
    const extreme=base+'/productos/'+fixture.empty_product_id+'/editar/';
    const result=await submit(a,{name:'X'.repeat(160),barcode:'Z'.repeat(64),category:cats['Productos enlatados'],sale_price:'9999999.99',minimum_stock:'999999'},extreme);
    const bound=snapshot()['catalog.Product'].find(p=>p.id===fixture.empty_product_id);
    record('D27-edit-bounds',result.status()===302&&bound.name.length===160&&bound.barcode.length===64&&bound.sale_price==='9999999.99'&&bound.minimum_stock===999999);
    await a.goto(edit);await a.setViewportSize({width:390,height:844});
    record('D28-mobile',await a.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),{screenshot:await screenshot(a,'28-movil')});
    await s.goto(receipt);
    record('D29-final-history',(await s.locator('#constancia-interna').innerText())===receiptBefore);
  }catch(error){report.errors.push({type:error.name,message:error.message.split('\n').slice(0,3).join(' ')});}
  finally{
    report.finished=new Date().toISOString();
    fs.writeFileSync(path.join(out,'browser.json'),JSON.stringify(report,null,2));
    await browser.close();
  }
  console.log(JSON.stringify({cases:report.cases.length,passed:report.cases.filter(c=>c.ok).length,failed:report.cases.filter(c=>!c.ok).map(c=>c.id),errors:report.errors}));
  if(report.errors.length||report.cases.some(c=>!c.ok))process.exitCode=1;
})();
