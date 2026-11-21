/* 02-B browser audit: fictional accounts, isolated local server, sanitized reports. */
const fs=require('fs'),path=require('path'),os=require('os'),crypto=require('crypto');
const {execFileSync}=require('child_process');
const {chromium}=require(path.join(os.homedir(),'.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright-core'));
const run=process.env.AUDIT02A_RUN_DIR,out=process.env.AUDIT02A_EVIDENCE;
const base=`http://127.0.0.1:${process.env.AUDIT02A_PORT}`;
const creds=JSON.parse(fs.readFileSync(path.join(run,'.credentials.json'),'utf8'));
const snap=()=>JSON.parse(execFileSync(process.env.AUDIT02A_PYTHON,[path.join(__dirname,'audit02b_run.py'),'snapshot'],{encoding:'utf8',env:process.env}));
const report={stage:'02-B',started_utc:new Date().toISOString(),viewport:{width:1366,height:768},cases:[],errors:[]};
function rec(id,ok,details={}) {report.cases.push({id,ok:!!ok,...details});}
function eq(a,b){return JSON.stringify(a)===JSON.stringify(b)}
const byemail=(s,email)=>s.accounts.find(x=>x.email.toLowerCase()===email.toLowerCase());
const click=async(p,l)=>Promise.all([p.waitForNavigation({waitUntil:'domcontentloaded'}),l.click()]);
async function save(p,id){await p.screenshot({path:path.join(out,id+'.png'),fullPage:true,mask:[p.locator('input[type=password]')]});fs.writeFileSync(path.join(out,id+'.txt'),await p.locator('body').innerText());return id+'.png';}
async function login(p,alias,pass){await p.goto(base+'/');await p.locator('[name=email]').fill(creds[alias]?.email||alias);await p.locator('[name=password]').fill(creds[alias]?.password||pass);await click(p,p.locator('button[type=submit]'));}
async function search(p,value){await p.goto(base+'/empleados/');await p.locator('[name=q]').fill(value);await click(p,p.locator('form[role=search] button'));}
async function row(p,text){return p.locator('tbody tr').filter({hasText:text});}
async function edit(p,email){await search(p,email);await click(p,(await row(p,email)).getByRole('link',{name:'Editar'}));}
async function csrf(p){await p.goto(base+'/salir/');return p.locator('[name=csrfmiddlewaretoken]').inputValue();}
async function ariaFields(p){return p.locator('main form').evaluate(form=>Array.from(form.querySelectorAll('input:not([type=hidden]),select')).map(el=>({field:el.name,errorText:el.parentElement.querySelector('.text-danger')?.innerText||'',ariaInvalid:el.getAttribute('aria-invalid'),ariaDescribedby:el.getAttribute('aria-describedby'),describedbyTargets:(el.getAttribute('aria-describedby')||'').split(/\s+/).filter(Boolean).map(id=>({id,exists:!!document.getElementById(id)})),errorRole:el.parentElement.querySelector('.text-danger')?.getAttribute('role')||null})));}
(async()=>{
 const browser=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true});report.browser=browser.version();
 const contexts=await Promise.all(Array.from({length:5},()=>browser.newContext({viewport:report.viewport})));
 const [ac,bc,sc,wc,tc]=contexts;const [a,b,s,w,t]=await Promise.all(contexts.map(c=>c.newPage()));
 for(const p of [a,b,s,w,t])p.setDefaultTimeout(12000);
 try {
  const nonce=crypto.randomBytes(32).toString('hex'),response=await ac.request.get(base+'/',{headers:{'X-Audit02a-Challenge':nonce}});
  const expected=crypto.createHmac('sha256',fs.readFileSync(path.join(run,'.django-key'),'utf8')).update(nonce).digest('hex');
  if(response.headers()['x-audit02a-proof']!==expected||response.headers()['x-audit02a-run']!==path.basename(run))throw Error('proof mismatch');
  rec('B00-instance',true,{status:response.status()});
  await login(a,'admin');await click(a,a.getByRole('link',{name:'Empleados',exact:true}));
  const initial=snap(),texts=await a.locator('tbody tr').allInnerTexts();
  let matching=0;for(const x of initial.accounts){if(texts.some(t=>t.includes(x.name)&&t.includes(x.email)&&t.includes(x.active?'Activo':'Inactivo')&&t.includes(x.role==='ADMIN'?'Administrador':x.role==='VENDEDOR'?'Vendedor':'Almacenero')))matching++;}
  rec('B01-USR01-tabla',matching===initial.accounts.length,{accounts:initial.accounts.length,matching,headers:await a.locator('thead th').allTextContents(),screenshot:await save(a,'B01-lista')});
  await search(a,'  VENDEDOR UNO  ');let r1=await a.locator('tbody tr').allInnerTexts();
  await search(a,' INACTIVE@AUDIT02A.INVALID ');let r2=await a.locator('tbody tr').allInnerTexts();
  await search(a,'ausente-02b');let empty=(await a.locator('main').innerText()).includes('No se encontraron empleados');
  await click(a,a.getByRole('link',{name:'Limpiar',exact:true}));let cleared=await a.locator('tbody tr').count();
  rec('B02-USR01-busquedas',r1.length===1&&r1[0].includes('Vendedor Uno')&&r2.length===1&&r2[0].includes('Inactivo')&&empty&&cleared===initial.accounts.length,{nameCount:r1.length,emailCount:r2.length,empty,cleared});
  const anon=await tc.request.get(base+'/empleados/',{maxRedirects:0});
  await login(s,'seller');await login(w,'warehouse');
  const id=initial.accounts.find(x=>x.role==='VENDEDOR').id;
  let statuses=[];const unchangedBefore=snap();
  for(const [name,c,p] of [['seller',sc,s],['warehouse',wc,w]]){
   const token=await csrf(p);
   for(const u of ['/empleados/','/empleados/nuevo/',`/empleados/${id}/editar/`,`/empleados/${id}/estado/`]){
    if(!u.endsWith('/estado/')){const r=await c.request.get(base+u,{maxRedirects:0});statuses.push({role:name,method:'GET',path:u,status:r.status()});}
    const r=await c.request.post(base+u,{maxRedirects:0,form:{csrfmiddlewaretoken:token}});statuses.push({role:name,method:'POST',path:u,status:r.status()});
   }
   await p.goto(base+'/empleados/');await save(p,'B03-403-'+name);
  }
  const unchangedAfter=snap();
  rec('B03-RN29-denegacion',anon.status()===302&&statuses.every(x=>x.status===403)&&eq(unchangedBefore.accounts,unchangedAfter.accounts),{anon:anon.status(),statuses,accountMutation:!eq(unchangedBefore.accounts,unchangedAfter.accounts)});
  await a.goto(base+'/empleados/nuevo/');
  const labels=await a.locator('main form label').allInnerTexts();
  const limits=await a.locator('main form input').evaluateAll(xs=>xs.map(x=>({name:x.name,type:x.type,maxlength:x.maxLength,minlength:x.minLength,required:x.required})).filter(x=>x.type!=='hidden'));
  const opts=await a.locator('select[name=role] option').allTextContents();
  const roleSeller=await a.locator('select[name=role] option').filter({hasText:'Vendedor'}).getAttribute('value');
  const roleWh=await a.locator('select[name=role] option').filter({hasText:'Almacenero'}).getAttribute('value');
  await click(a,a.locator('main button[type=submit]'));const emptyText=await a.locator('main').innerText();
  rec('B04-formulario-campos-vacios',emptyText.includes('Este campo es obligatorio')&&emptyText.includes('Ingrese una contraseña inicial')&&emptyText.includes('Seleccione un rol'),{labels,limits,roleOptions:opts,screenshot:await save(a,'B04-vacios')});
  const errorAccessibility=await ariaFields(a);
  await a.locator('[name=display_name]').focus();await a.keyboard.press('Tab');const nextFocused=await a.evaluate(()=>document.activeElement?.getAttribute('name'));
  rec('B04A-asociacion-accesibilidad-alta',errorAccessibility.length===4&&errorAccessibility.every(f=>f.errorText&&f.ariaInvalid==='true'&&f.describedbyTargets.length>0&&f.describedbyTargets.every(x=>x.exists)&&f.errorRole==='alert')&&nextFocused==='email',{fields:errorAccessibility,tabAfterName:nextFocused});
  const initCount=snap().accounts.length;
  await a.locator('[name=display_name]').fill('AUD02B Duplicado');await a.locator('[name=email]').fill(' SELLER@AUDIT02A.INVALID ');
  await a.locator('[name=password]').fill('Abcdef1');await a.locator('[name=role]').selectOption(roleSeller);
  await click(a,a.locator('main button[type=submit]'));const dup1=(await a.locator('main').innerText()).includes('El correo ya está registrado.');
  await a.locator('[name=email]').fill('INACTIVE@AUDIT02A.INVALID');await a.locator('[name=password]').fill('Abcdef1');
  await click(a,a.locator('main button[type=submit]'));const dup2=(await a.locator('main').innerText()).includes('El correo ya está registrado.');
  await a.locator('[name=email]').fill('new@audit02b.invalid');await a.locator('[name=password]').fill('abcdef1');
  await click(a,a.locator('main button[type=submit]'));const weak=(await a.locator('main').innerText()).includes('mayúscula, minúscula y número');
  rec('B05-USR02-duplicados-y-clave',dup1&&dup2&&weak&&snap().accounts.length===initCount,{activeDuplicate:dup1,inactiveDuplicate:dup2,weakRejected:weak,unchangedCount:snap().accounts.length===initCount,screenshot:await save(a,'B05-invalido')});
  const token=await a.locator('[name=csrfmiddlewaretoken]').inputValue();
  const cases=[
   {id:'name121',data:{display_name:'A'.repeat(121),email:'length@audit02b.invalid',password:'Abcdef1',role:roleSeller},expected:'120'},
   {id:'bademail',data:{display_name:'AUD02B',email:'invalido',password:'Abcdef1',role:roleSeller},expected:'correo electrónico válida'},
   {id:'roleforged',data:{display_name:'AUD02B',email:'forged@audit02b.invalid',password:'Abcdef1',role:'999999999'},expected:'rol válido'},
   {id:'shortpw',data:{display_name:'AUD02B',email:'short@audit02b.invalid',password:'Abc1aa',role:roleSeller},expected:'al menos 7 caracteres'},
  ];
  let fieldchecks=[];for(const x of cases){const r=await ac.request.post(base+'/empleados/nuevo/',{form:{csrfmiddlewaretoken:token,...x.data},maxRedirects:0});const text=await r.text();fieldchecks.push({id:x.id,status:r.status(),messageFound:text.includes(x.expected)});}
  rec('B06-fronteras-y-peticion-alterada',fieldchecks.every(x=>x.status===200&&x.messageFound)&&snap().accounts.length===initCount,{fieldchecks,accountCountUnchanged:snap().accounts.length===initCount});
  await a.goto(base+'/empleados/nuevo/');await a.locator('[name=display_name]').fill('AUD02B Nueva');await a.locator('[name=email]').fill('new@audit02b.invalid');
  await a.locator('[name=password]').fill('Abcdef1');await a.locator('[name=role]').selectOption(roleSeller);
  await click(a,a.locator('main button[type=submit]'));
  const createdText=await a.locator('body').innerText(),newRow=await (await row(a,'new@audit02b.invalid')).innerText(),newAccount=byemail(snap(),'new@audit02b.invalid');
  rec('B07-USR02-alta-confirmacion',createdText.includes('AUD02B Nueva')&&newRow.includes('new@audit02b.invalid')&&newRow.includes('Vendedor')&&newRow.includes('Activo')&&newAccount.active&&newAccount.role==='VENDEDOR',{screenshot:await save(a,'B07-alta'),account:newAccount});
  await login(b,'new@audit02b.invalid','Abcdef1');const salesBefore=await bc.request.get(base+'/ventas/',{maxRedirects:0});
  rec('B08-USR02-login-empleado',b.url().endsWith('/inicio/')&&salesBefore.status()===200,{salesStatus:salesBefore.status()});
  await edit(a,'new@audit02b.invalid');await a.locator('[name=display_name]').fill('AUD02B Cambiada');await a.locator('[name=email]').fill('new@audit02b.invalid');await a.locator('[name=role]').selectOption(roleWh);
  await click(a,a.locator('main button[type=submit]'));
  const afterEdit=byemail(snap(),'new@audit02b.invalid');const sOld=await bc.request.get(base+'/ventas/',{maxRedirects:0}),sNew=await bc.request.get(base+'/inventario/carga-inicial/',{maxRedirects:0});
  await b.goto(base+'/inicio/');const menu=await b.locator('nav').innerText();
  rec('B09-USR03-rol-sesion-abierta',afterEdit.name==='AUD02B Cambiada'&&afterEdit.role==='ALMACENERO'&&sOld.status()===403&&sNew.status()===200&&menu.includes('Existencias iniciales')&&!menu.includes('Preparar venta'),{account:afterEdit,oldRoleStatus:sOld.status(),newRoleStatus:sNew.status(),screenshot:await save(b,'B09-rol')});
  await edit(a,'new@audit02b.invalid');await a.locator('[name=email]').fill('seller@audit02a.invalid');await click(a,a.locator('main button[type=submit]'));
  const editDup=(await a.locator('main').innerText()).includes('El correo ya está registrado.');
  rec('B10-USR03-colision-edicion',editDup&&byemail(snap(),'new@audit02b.invalid').role==='ALMACENERO',{duplicateRejected:editDup,screenshot:await save(a,'B10-edicion-duplicada')});
  const editAccessibility=await ariaFields(a),emailError=editAccessibility.find(f=>f.field==='email');
  rec('B10A-asociacion-accesibilidad-edicion',emailError?.errorText&&emailError.ariaInvalid==='true'&&emailError.errorRole==='alert'&&emailError.describedbyTargets.some(x=>x.id==='id_email_error'&&x.exists)&&editAccessibility.every(f=>f.describedbyTargets.every(x=>x.exists)),{fields:editAccessibility});
  // Two independent administrator sessions preserve a stale form while one request changes the target.
  await login(t,'admin');await search(a,'seller2@audit02a.invalid');await search(t,'seller2@audit02a.invalid');
  const staleButton=(await row(t,'seller2@audit02a.invalid')).getByRole('button',{name:'Desactivar'});
  await click(a,(await row(a,'seller2@audit02a.invalid')).getByRole('button',{name:'Desactivar'}));
  const deactivated=byemail(snap(),'seller2@audit02a.invalid');await click(t,staleButton);const staleAfter=byemail(snap(),'seller2@audit02a.invalid');
  rec('B11-estado-formulario-obsoleto',!deactivated.active&&!staleAfter.active,{afterFirstActive:deactivated.active,afterStaleActive:staleAfter.active,screenshot:await save(t,'B11-obsoleto')});
  // Reactivate seller2 if this execution left it inactive; preserve normal flow semantics.
  if(!staleAfter.active){await search(a,'seller2@audit02a.invalid');await click(a,(await row(a,'seller2@audit02a.invalid')).getByRole('button',{name:'Reactivar'}));}
  const oldCookie=await bc.cookies();await search(a,'new@audit02b.invalid');await click(a,(await row(a,'new@audit02b.invalid')).getByRole('button',{name:'Desactivar'}));
  const deact=byemail(snap(),'new@audit02b.invalid'),revoked=await bc.request.get(base+'/inicio/',{maxRedirects:0});
  await b.goto(base+'/');await b.locator('[name=email]').fill('NEW@audit02b.invalid');await b.locator('[name=password]').fill('Abcdef1');await click(b,b.locator('button[type=submit]'));
  const inactiveMsg=(await b.locator('body').innerText()).includes('Correo o contraseña incorrectos');
  rec('B12-USR04-sesion-e-ingreso',!deact.active&&deact.sessions===0&&revoked.status()===302&&inactiveMsg,{account:deact,revokedStatus:revoked.status(),genericMessage:inactiveMsg,screenshot:await save(b,'B12-inactivo')});
  await search(a,'new@audit02b.invalid');const inactRow=await (await row(a,'new@audit02b.invalid')).innerText();await click(a,(await row(a,'new@audit02b.invalid')).getByRole('button',{name:'Reactivar'}));
  const react=byemail(snap(),'new@audit02b.invalid');const old=await browser.newContext();await old.addCookies(oldCookie);const oldResp=await old.request.get(base+'/inicio/',{maxRedirects:0});await old.close();
  await login(b,'new@audit02b.invalid','Abcdef1');const whOk=await bc.request.get(base+'/inventario/carga-inicial/',{maxRedirects:0}),sellNo=await bc.request.get(base+'/ventas/',{maxRedirects:0});
  rec('B13-USR05-reactivacion',inactRow.includes('Inactivo')&&react.active&&react.role==='ALMACENERO'&&oldResp.status()===302&&b.url().endsWith('/inicio/')&&whOk.status()===200&&sellNo.status()===403,{account:react,oldCookieStatus:oldResp.status(),warehouseStatus:whOk.status(),salesStatus:sellNo.status()});
  await edit(a,'new@audit02b.invalid');await a.locator('[name=new_password]').fill('Xyz1234');await click(a,a.locator('main button[type=submit]'));
  const passwordRevoked=await bc.request.get(base+'/inicio/',{maxRedirects:0});
  await login(b,'new@audit02b.invalid','Abcdef1');const oldPassRejected=!b.url().endsWith('/inicio/');
  await login(b,'new@audit02b.invalid','Xyz1234');const newPassWorks=b.url().endsWith('/inicio/');
  rec('B13A-clave-sesion-existente',passwordRevoked.status()===302&&oldPassRejected&&newPassWorks,{previousSessionStatus:passwordRevoked.status(),oldPassRejected,newPassWorks});
  await s.goto(base+'/caja/abrir/');await s.locator('[name=opening_amount]').fill('30.00');await click(s,s.getByRole('button',{name:'Abrir turno',exact:true}));
  const shiftBefore=snap();await search(a,'seller@audit02a.invalid');await click(a,(await row(a,'seller@audit02a.invalid')).getByRole('button',{name:'Desactivar'}));
  const blocked=(await a.locator('body').innerText()).includes('turno de caja abierto');
  await edit(a,'seller@audit02a.invalid');await a.locator('[name=role]').selectOption(roleWh);await click(a,a.locator('main button[type=submit]'));
  const roleBlocked=(await a.locator('main').innerText()).includes('turno de caja abierto');const shiftAfter=snap();
  rec('B14-turno-abierto-bloqueos',blocked&&roleBlocked&&eq(shiftBefore.shifts,shiftAfter.shifts)&&byemail(shiftAfter,'seller@audit02a.invalid').active&&byemail(shiftAfter,'seller@audit02a.invalid').role==='VENDEDOR',{deactivationBlocked:blocked,roleChangeBlocked:roleBlocked,shiftUnchanged:eq(shiftBefore.shifts,shiftAfter.shifts)});
  await s.goto(base+'/caja/cerrar/');await s.locator('[name=counted_amount]').fill('30.00');await click(s,s.getByRole('button',{name:'Cerrar turno',exact:true}));
  const beforeHistory=snap();await search(a,'seller@audit02a.invalid');await click(a,(await row(a,'seller@audit02a.invalid')).getByRole('button',{name:'Desactivar'}));const afterHistory=snap();
  rec('B15-USR04-historial-turno',!byemail(afterHistory,'seller@audit02a.invalid').active&&eq(beforeHistory.shifts,afterHistory.shifts)&&beforeHistory.closes===afterHistory.closes,{shifts:afterHistory.shifts.length,closes:afterHistory.closes});
  await edit(a,'admin@audit02a.invalid');await a.locator('[name=role]').selectOption(roleWh);await click(a,a.locator('main button[type=submit]'));const ownRole=(await a.locator('main').innerText()).includes('No puedes cambiar el rol de tu propia cuenta');
  const adminid=byemail(snap(),'admin@audit02a.invalid').id;const tokenAdmin=await a.locator('[name=csrfmiddlewaretoken]').inputValue();
  const selfPost=await ac.request.post(base+`/empleados/${adminid}/estado/`,{form:{csrfmiddlewaretoken:tokenAdmin,action:'desactivar'},maxRedirects:0});const adminState=byemail(snap(),'admin@audit02a.invalid');
  await a.goto(base+'/empleados/');const selfMessage=(await a.locator('body').innerText()).includes('No puedes desactivar tu propia cuenta');
  rec('B16-ultimo-admin-proteccion-propia',ownRole&&selfPost.status()===302&&selfMessage&&adminState.active&&adminState.role==='ADMIN',{ownRoleRejected:ownRole,selfStatus:selfPost.status(),selfMessage,admin:adminState});
 } catch(e){report.errors.push({id:report.cases.at(-1)?.id||'inicio',type:e.name});}
 finally {await browser.close();report.finished_utc=new Date().toISOString();report.pass=report.cases.filter(x=>x.ok).length;report.failed=report.cases.filter(x=>!x.ok).length;fs.writeFileSync(path.join(out,'browser.json'),JSON.stringify(report,null,2));}
 console.log(JSON.stringify({cases:report.cases.length,pass:report.pass,failed:report.failed,errors:report.errors}));if(report.errors.length||report.failed)process.exitCode=1;
})();
