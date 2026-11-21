const fs=require('node:fs'),path=require('node:path'),os=require('node:os'),crypto=require('node:crypto'),assert=require('node:assert/strict');
const {chromium}=require(path.join(os.homedir(),'.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright-core'));
const root=path.resolve(__dirname,'../../..'),out=path.join(root,'auditoria_por_etapas/resultados/evidencias/01-K-20261115'),data=path.join(root,'auditoria_por_etapas/resultados/datos/01-K-20261115');
const plan=fs.readFileSync(path.join(root,'08_Historias_de_Usuario.md'),'utf8');
const credentials=JSON.parse(fs.readFileSync(path.join(data,'.credentials.json'),'utf8'));
const base='http://127.0.0.1:8800';
const report={checks:[],plan_sha256:crypto.createHash('sha256').update(plan).digest('hex'),screenshots:[],scope:'Ingreso local, literales HU-AUTH01/02; sin semántica completa de módulos destino'};
function check(id,ok,detail={}){report.checks.push({id,ok,...detail});assert(ok,id);}
function specified(text){check('PLAN_'+report.checks.length,plan.includes(text),{literal:text});}
async function submit(page,email,password){await page.locator('[name=email]').fill(email);await page.locator('[name=password]').fill(password);const [res]=await Promise.all([page.waitForResponse(r=>r.request().method()==='POST'&&r.url().startsWith(base)),page.locator('button[type=submit]').click()]);await page.waitForLoadState('domcontentloaded');return res;}
(async()=>{
 const browser=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true});report.chrome=browser.version();
 try{
  const ctx=await browser.newContext({locale:'es-PE',viewport:{width:1366,height:768}}),page=await ctx.newPage();
  await page.goto(base);
  const pairs=[['title','Ingresar — Sistema de gestión'],['.login-story .eyebrow','Gestión de minimarket'],['h1','Bienvenido. Escribe tu correo y tu contraseña.'],['.login-story > p:not(.eyebrow)','Cada persona ve solo las operaciones de su puesto: administración, almacén y caja.'],['.login-card .eyebrow','Acceso seguro'],['h2','Iniciar sesión'],['.login-card > .muted','Usa tu cuenta de trabajo para continuar.'],['label[for=id_email]','Correo de trabajo'],['label[for=id_password]','Contraseña'],['button[type=submit]','Iniciar sesión'],['.skip-link','Saltar al contenido']];
  for(const [sel,text] of pairs){specified(text);check('UI_'+sel,(await page.locator(sel).textContent()).trim()===text,{literal:text});}
  for(const [i,text] of ['Administrador','Almacenero','Vendedor'].entries()){specified(text);check('ROLE_'+i,(await page.locator('.login-role-grid strong').nth(i).innerText())===text);}
  for(const [i,text] of ['Productos, empleados, proveedores y resumen diario de ventas.','Inventario, mermas y alertas de stock.','Turno de caja y ventas.'].entries()){specified(text);check('ROLE_HELP_'+i,(await page.locator('.login-role-grid small').nth(i).innerText())===text);}
  for(const [name,text] of [['email','nombre@empresa.com'],['password','Ingrese su contraseña']]){specified(text);check('PLACEHOLDER_'+name,await page.locator('[name='+name+']').getAttribute('placeholder')===text);}
  specified('Tus permisos y acciones dependen del rol asignado.');check('PERMISSION_NOTE',(await page.locator('.security-note').innerText()).replace('●','').trim()==='Tus permisos y acciones dependen del rol asignado.');
  await submit(page,'','');let errors=await page.locator('.error-list li').allTextContents();specified('Este campo es obligatorio.');check('EMPTY_ERRORS_EXACT',JSON.stringify(errors)===JSON.stringify(['Este campo es obligatorio.','Este campo es obligatorio.']));
  await submit(page,'sin-arroba','Ficticia1!');specified('Introduzca una dirección de correo electrónico válida.');check('FORMAT_EXACT',await page.locator('.error-list li').innerText()==='Introduzca una dirección de correo electrónico válida.');
  await page.locator('[name=email]').evaluate(el=>el.removeAttribute('maxlength'));
  const tooLong='a'.repeat(255-'@example.invalid'.length)+'@example.invalid';await submit(page,tooLong,'Ficticia1!');const lengthMsg='Asegúrese de que este valor tenga como máximo 254 caracteres (tiene 255).';specified(lengthMsg.replace('255','{N}'));check('LENGTH_EXACT',await page.locator('.error-list li').innerText()===lengthMsg);
  for(const [id,email,password] of [['wrong',credentials.seller.email,'ClaveErronea1!'],['unknown','nadie.literal01k@example.invalid','ClaveErronea1!'],['inactive',credentials.inactive.email,credentials.inactive.password]]){await page.goto(base);await submit(page,email,password);specified('Correo o contraseña incorrectos');check('REJECTION_'+id,await page.locator('[data-testid=login-error] li').innerText()==='Correo o contraseña incorrectos');check('PASSWORD_EMPTY_'+id,await page.locator('[name=password]').inputValue()==='');}
  await page.goto(base);await submit(page,credentials.admin.email,credentials.admin.password);const locked=await page.locator('[data-testid=login-error] li').innerText();const m=locked.match(/^Demasiados intentos fallidos consecutivos\. Inténtelo nuevamente en (\d+) minuto\(s\)\.$/);check('LOCK_LITERAL',!!m&&Number(m[1])>=1&&Number(m[1])<=15);specified('Demasiados intentos fallidos consecutivos. Inténtelo nuevamente en {minutos} minuto(s).');
  await page.screenshot({path:path.join(out,'navegador/01-K-bloqueo-literal.png'),fullPage:true});report.screenshots.push('navegador/01-K-bloqueo-literal.png');
  await page.goto(base);await submit(page,credentials.seller.email,credentials.seller.password);check('SUCCESS_LOCAL_DESTINATION',new URL(page.url()).pathname==='/inicio/');
  await page.goto(base+'/empleados/');for(const text of ['Acceso denegado','No tienes permiso para esta operación','Tu cuenta no tiene autorización para realizar esta operación.','Volver a mi inicio']){specified(text);check('DENIED_'+text,(await page.locator('[data-testid=permission-denied]').innerText()).includes(text));}
  const anon=await browser.newContext(),q=await anon.newPage();await q.goto(base+'/admin/');for(const text of ['Error 404','Página no encontrada','La dirección solicitada no existe o el registro ya no está disponible.','Volver al inicio']){specified(text);check('NOT_FOUND_'+text,(await q.locator('[data-testid=not-found]').innerText()).includes(text));}
  const res=await q.request.post(base+'/',{form:{email:'a@example.invalid',password:'Ficticia1!'}});check('CSRF_STATUS',res.status()===403);const html=await res.text();for(const text of ['La verificación CSRF ha fallado. Solicitud abortada.','Más información disponible si se establece DEBUG=True.']){specified(text);check('CSRF_LITERAL_'+text,html.includes(text));}
  await ctx.close();await anon.close();
 } finally {fs.writeFileSync(path.join(out,'literales-browser.json'),JSON.stringify(report,null,2));await browser.close();}
 console.log(JSON.stringify({checks:report.checks.length,failures:report.checks.filter(x=>!x.ok).length}));
})().catch(e=>{console.error(e.message);process.exitCode=1;});
