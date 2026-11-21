// Physical EAN/UPC observation. No synthetic barcode input or automatic save.
const fs=require('fs'),path=require('path'),os=require('os'),crypto=require('crypto');
const {execFileSync}=require('child_process');
const {chromium}=require(path.join(os.homedir(),'.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright-core'));
const out=process.env.AUDIT03_OUT,run=process.env.AUDIT03_RUN_DIR,base='http://127.0.0.1:'+process.env.AUDIT03_PORT;
const E='0012345678905',U='012345678905',report={mode:'03-Y physical phone; confirm by operator',checks:[],status:'preparing',posts:[]};
const write=(name,data)=>fs.writeFileSync(path.join(out,name),JSON.stringify(data,null,2));
function snapshot(){return JSON.parse(execFileSync(process.env.AUDIT03_PYTHON,[path.join(__dirname,'audit03y_browser_run.py'),'snapshot'],{encoding:'utf8',env:{...process.env,PYTHONIOENCODING:'utf-8'}}));}
function check(id,ok){report.checks.push({id,ok:!!ok});if(!ok)throw Error(id);}
function symbol(){
 // This specimen starts with 0: six left odd-parity digits and six right digits.
 const left=['0001101','0011001','0010011','0111101','0100011','0110001','0101111','0111011','0110111','0001011'];
 const sum=[...E.slice(0,12)].reduce((a,c,i)=>a+Number(c)*(i%2?3:1),0);
 if((10-sum%10)%10!==Number(E[12]))throw Error('check-digit');
 const bits='101'+[...E.slice(1,7)].map(d=>left[Number(d)]).join('')+'01010'+[...E.slice(7)].map(d=>[...left[Number(d)]].map(v=>v==='0'?'1':'0').join('')).join('')+'101';
 if(bits.length!==95)throw Error('symbol-width');
 const svg='<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 119 44" width="476" height="176" shape-rendering="crispEdges"><rect width="119" height="44" fill="white"/>'+[...bits].map((v,i)=>v==='1'?'<rect x="'+(12+i)+'" y="2" width="1" height="38"/>':'').join('')+'</svg>';
 fs.writeFileSync(path.join(out,'specimen-ean13.svg'),svg);return 'data:image/svg+xml;base64,'+Buffer.from(svg).toString('base64');
}
(async()=>{let browser;try{
browser=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:false,args:['--start-maximized']});report.browser=browser.version();const p=await(await browser.newContext({locale:'es-PE',viewport:null})).newPage();
const nonce=crypto.randomBytes(32).toString('hex');const res=await p.request.get(base,{headers:{'X-Audit03-Challenge':nonce}});check('isolation',res.headers()['x-audit03-proof']===crypto.createHmac('sha256',fs.readFileSync(path.join(run,'.django-key'))).update(nonce).digest('hex'));
const creds=JSON.parse(fs.readFileSync(path.join(run,'.credentials.json'),'utf8'));await p.goto(base);await p.locator('[name=email]').fill(creds.admin.email);await p.locator('[name=password]').fill(creds.admin.password);await p.locator('button[type=submit]').click();await p.getByRole('link',{name:'Registrar producto',exact:true}).click();
p.on('request',r=>{if(r.method()==='POST')report.posts.push(new URL(r.url()).pathname);});const before=snapshot();check('only-EAN-exists',before['catalog.Product'].length===1&&before['catalog.Product'][0].barcode===E);
await p.locator('[name=barcode_type]').selectOption('GTIN');
await p.getByRole('button',{name:'Escanear código',exact:true}).click();
await p.evaluate(({svg,E,U})=>{
 const d=document.querySelector('#barcode-capture-dialog'),f=document.querySelector('#barcode-capture-input');
 const panel=document.createElement('section');panel.style.cssText='background:white;color:#111;text-align:center;padding:8px;border:2px solid teal;';
 const title=document.createElement('strong');title.textContent='AUDITORÍA 03-Y · Leer una vez con el teléfono';
 const img=document.createElement('img');img.src=svg;img.style.cssText='display:block;width:476px;max-width:100%;margin:auto';
 const label=document.createElement('p');label.textContent='Etiqueta EAN-13: '+E+' · Retira la cámara después de leer.';
 const b=document.createElement('button');b.type='button';b.textContent='He leído con el teléfono: registrar observación';b.disabled=true;
 panel.append(title,img,label,b);d.insertBefore(panel,f.closest('.field'));
 const s={inputs:0,trusted:0,values:[],enter:0,tab:0,controlA:0,otherInputs:0,confirmed:false};
 document.addEventListener('input',e=>{if(e.target!==f){s.otherInputs++;return;}s.inputs++;if(e.isTrusted)s.trusted++;s.values.push({value:f.value,trusted:e.isTrusted});b.disabled=!(e.isTrusted&&(f.value===E||f.value===U));},true);
 d.addEventListener('keydown',e=>{if(e.key==='Enter')s.enter++;if(e.key==='Tab')s.tab++;if(e.ctrlKey&&e.key.toLowerCase()==='a')s.controlA++;});
 b.addEventListener('click',e=>{if(e.isTrusted&&!b.disabled){s.confirmed=true;b.disabled=true;}});
 window.auditXStatus=()=>({...s,value:f.value,dialogOpen:d.open,focused:document.hasFocus(),temporaryFocused:document.activeElement===f});f.focus();
},{svg:symbol(),E,U});
await p.bringToFront();report.status='waiting';report.deadline=new Date(Date.now()+300000).toISOString();write('ready.json',{url:p.url(),deadline:report.deadline,code:E});await p.screenshot({path:path.join(out,'ready.png')});
let last='';for(;;){const s=await p.evaluate(()=>window.auditXStatus());report.observed=s;const next=JSON.stringify(s);if(last!==next){write('progress.json',report);last=next;}if(s.confirmed)break;if(!s.dialogOpen)throw Error('dialog-closed');if(Date.now()>Date.parse(report.deadline))throw Error('operator-timeout');await new Promise(r=>setTimeout(r,250));}
check('operator-confirmed-input',report.observed.trusted>0&&[E,U].includes(report.observed.value));
const received=report.observed.value;const expected='El código de barras ya está registrado';await p.locator('#barcode-capture-status').filter({hasText:expected}).waitFor();
report.message=await p.locator('#barcode-capture-status').innerText();report.copyDisabled=await p.locator('#barcode-capture-apply').isDisabled();
check('duplicate-gtin-blocked',report.copyDisabled);check('no-post',report.posts.length===0);check('no-enter-tab',report.observed.enter===0&&report.observed.tab===0);check('final-field-empty',await p.locator('[name=barcode]').inputValue()==='');check('no-other-inputs',report.observed.otherInputs===0);check('commercial-state-preserved',JSON.stringify(before)===JSON.stringify(snapshot()));
await p.screenshot({path:path.join(out,'observed.png')});report.status='completed';
}catch(e){report.status='partial';report.error=e.message;process.exitCode=1;}finally{report.finished_utc=new Date().toISOString();write('phone.json',report);if(browser)await browser.close();}})();
