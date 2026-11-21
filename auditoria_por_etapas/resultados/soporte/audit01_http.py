"""Real HTTP + ORM stage-01 checks, new fictional fixtures per execution."""
from __future__ import annotations
import hashlib
import hmac
import http.cookiejar
import json
import os
from pathlib import Path
import secrets
import sys
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import urllib.error
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'r1-pmv'))
os.environ['DJANGO_SETTINGS_MODULE'] = 'audit01_settings'
import django
django.setup()
from django.conf import settings
from django.apps import apps
from django.contrib.sessions.models import Session
from django.db import connection
from django.utils import timezone
from django.utils.crypto import salted_hmac
from identity.models import Account, LoginAttempt, Role

DATA = ROOT / 'auditoria_por_etapas/resultados/datos/etapa01-20261109'
assert Path(connection.settings_dict['NAME']).resolve() == (DATA / 'audit.sqlite3').resolve()
assert (DATA / 'prepared.json').exists()
BASE = 'http://127.0.0.1:8766'
started = datetime.now(ZoneInfo('America/Lima'))
runid = started.strftime('%Y%m%d%H%M%S') + secrets.token_hex(3)

def protected_hashes():
    return {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in [
        ROOT / 'r1-pmv/r1_pmv.sqlite3', DATA.parent / 'etapa00-20261105/audit.sqlite3']}

def business():
    # Compare all commercial rows, not just counts; no data is printed.
    result = {}
    for label in ('catalog','inventory','cash','sales'):
        for model in apps.get_app_config(label).get_models():
            records = list(model.objects.order_by('pk').values())
            result[model._meta.label] = {'count': len(records), 'sha256': hashlib.sha256(
                json.dumps(records, sort_keys=True, default=str).encode()).hexdigest()}
    return result

def identity(email):
    return salted_hmac('identity.login.throttle', Account.normalize_email(email), algorithm='sha256').hexdigest()

def state(email):
    return LoginAttempt.objects.filter(pk=identity(email)).values('failures','locked_until').first()

def check(case, expected, observed, classification='CUMPLE caso acotado'):
    results.append({'case':case,'expected':expected,'observed':observed,'passed':expected==observed,
                    'classification':classification})

def message(body):
    import re
    if 'Correo o contraseña incorrectos' in body:
        return 'Correo o contraseña incorrectos'
    match = re.search(r'Demasiados intentos fallidos consecutivos\. Inténtelo nuevamente en \d+ minuto\(s\)\.',body)
    return match.group(0) if match else None

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

class BrowserSession:
    def __init__(self):
        self.jar=http.cookiejar.CookieJar()
        self.opener=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.jar),NoRedirect())
    def cookie(self,name):
        return next((c.value for c in self.jar if c.name==name),None)
    def request(self,path='/',data=None,headers=None,method=None):
        payload=urllib.parse.urlencode(data).encode() if data is not None else None
        req=urllib.request.Request(BASE+path,data=payload,headers={'Referer':BASE+'/',**(headers or {})},method=method)
        try:
            response=self.opener.open(req,timeout=15)
        except urllib.error.HTTPError as exc:
            response=exc
        with response:
            return response.code,response.headers,response.read().decode('utf-8')
    def post(self,path='/',data=None,headers=None):
        token=self.cookie(settings.CSRF_COOKIE_NAME)
        return self.request(path,data=data or {},headers={'X-CSRFToken':token or '',**(headers or {})})
    def login(self,fixture,password=None,next_url=None):
        self.request('/')
        data={'email':fixture['email'],'password':fixture['password'] if password is None else password}
        if next_url is not None:
            data['next']=next_url
        return self.post('/',data)

# Prove this listening port belongs to isolated stage01 before fixtures or POST.
challenge=secrets.token_hex(32)
expected=hmac.new(settings.SECRET_KEY.encode(),challenge.encode(),hashlib.sha256).hexdigest()
with urllib.request.urlopen(urllib.request.Request(BASE+'/',headers={'X-Audit01-Challenge':challenge}),timeout=10) as response:
    assert hmac.compare_digest(expected,response.headers.get('X-Audit01-Proof','')), 'Wrong instance; no POST sent'
before_hashes=protected_hashes()
before_business=business()
results=[]
fixtures={}
for key,code,active,staff in [('admin',Role.Code.ADMIN,True,False),('almacen',Role.Code.WAREHOUSE,True,False),
                             ('vendedor',Role.Code.SELLER,True,False),('inactive',Role.Code.SELLER,False,False),
                             ('staff',Role.Code.ADMIN,True,True)]:
    email=f'{key}.{runid}@example.invalid'
    password=secrets.token_urlsafe(24)
    account=Account.objects.create_user(email,password,display_name=f'AUD01HTTP {key} {runid}',
        role=Role.objects.get(code=code),is_active=active,is_staff=staff)
    fixtures[key]={'email':email,'password':password,'pk':str(account.pk)}

s=BrowserSession()
status,headers,body=s.request('/')
check('HTTP-01 GET login/cache', [200,True], [status,'no-store' in headers.get('Cache-Control','')])
before_count=LoginAttempt.objects.count()
for name,headers,data in [
    ('missing',{}, {'email':fixtures['admin']['email'],'password':fixtures['admin']['password']}),
    ('altered',{'X-CSRFToken':'invalid'}, {'email':fixtures['admin']['email'],'password':fixtures['admin']['password']}),
    ('cross-origin',{'X-CSRFToken':s.cookie(settings.CSRF_COOKIE_NAME),'Origin':'https://example.invalid'},
      {'email':fixtures['admin']['email'],'password':fixtures['admin']['password']})]:
    status,_,body=s.request('/',data,headers)
    check('HTTP-CSRF-'+name,[403,before_count,False],[status,LoginAttempt.objects.count(),fixtures['admin']['password'] in body])
status,_,body=s.post('/',{})
check('HTTP-EMPTY POST vacio con CSRF header',[200,2,before_count],[status,body.count('Este campo es obligatorio.'),LoginAttempt.objects.count()])

sessions={}
for key in ('admin','almacen','vendedor'):
    session=BrowserSession(); sessions[key]=session
    fixture=fixtures[key]
    normalized={**fixture,'email':'  '+fixture['email'].upper()+'  '}
    status,headers,body=session.login(normalized)
    session_key=session.cookie(settings.SESSION_COOKIE_NAME)
    stored=Session.objects.get(session_key=session_key).get_decoded()
    check('HTTP-ROLE-'+key,[302,'/inicio/',fixture['pk'],True,False],
        [status,headers.get('Location'),stored.get('_auth_user_id'),Account.objects.get(pk=fixture['pk']).last_login is not None,
         fixture['password'] in json.dumps(stored)])
    status,_,body=session.request('/inicio/')
    check('HTTP-SESSION-'+key,[200,True],[status,'AUD01HTTP '+key in body])
    cookies=[c for c in session.jar if c.name==settings.SESSION_COOKIE_NAME]
    check('HTTP-COOKIE-'+key,[True,True,False],[cookies[0].has_nonstandard_attr('HttpOnly'),cookies[0].get_nonstandard_attr('SameSite')=='Lax',fixture['password'] in cookies[0].value])
    status,_,_=session.request('/admin/')
    check('HTTP-NONSTAFF-'+key,302,status)

for key,route in [('admin','/caja/abrir/'),('almacen','/empleados/nuevo/'),('vendedor','/empleados/nuevo/')]:
    for method in ('GET','POST'):
        s=sessions[key]
        status,_,body=s.request(route) if method=='GET' else s.post(route,{'display_name':'SHOULD NOT EXIST','email':'denied@example.invalid'})
        check('HTTP-DENIED-'+key+'-'+method,[403,False],[status,fixtures['inactive']['email'] in body])
target_pk=fixtures['vendedor']['pk']
for key in ('almacen','vendedor'):
    s=sessions[key]
    status,_,body=s.request('/empleados/')
    check('HTTP-DENIED-'+key+'-LIST',[403,False],[status,fixtures['inactive']['email'] in body])
    status,_,body=s.post(f'/empleados/{target_pk}/editar/',{'display_name':'MUTATED','email':fixtures['vendedor']['email'],'role':'1'})
    check('HTTP-DENIED-'+key+'-EDIT-POST',[403,False],[status,fixtures['inactive']['email'] in body])
    status,_,body=s.post(f'/empleados/{target_pk}/estado/',{})
    check('HTTP-DENIED-'+key+'-DEACT-POST',[403,True],[status,Account.objects.get(pk=target_pk).is_active])
s=BrowserSession()
for method in ('GET','POST'):
    s.request('/')
    status,headers,body=s.request('/empleados/nuevo/') if method=='GET' else s.post('/empleados/nuevo/',{'display_name':'DENIED'})
    check('HTTP-VISITOR-'+method,[302,'/?next=/empleados/nuevo/',False],[status,headers.get('Location'),fixtures['inactive']['email'] in body])
for vpath,vmeth in [('/inicio/','GET'),('/empleados/','GET'),(f'/empleados/{target_pk}/estado/','POST')]:
    s=BrowserSession(); s.request('/')
    status,headers,_=s.request(vpath) if vmeth=='GET' else s.post(vpath,{})
    check('HTTP-VISITOR-'+vmeth+'-'+vpath,[302,f'/?next={vpath}',True],[status,headers.get('Location'),Account.objects.get(pk=target_pk).is_active])

for key,pwd in [('admin','wrong'),('inactive',fixtures['inactive']['password']),('unknown','wrong')]:
    fixture=fixtures.get(key,{'email':f'unknown.{runid}@example.invalid','password':'unused'})
    s=BrowserSession(); status,_,body=s.login(fixture,password=pwd)
    check('HTTP-UNIFORM-'+key,[200,'Correo o contraseña incorrectos',None,False],
        [status,message(body),s.cookie(settings.SESSION_COOKIE_NAME),pwd in body])

for next_url,expected in [('/empleados/','/empleados/'),('https://example.invalid/','/inicio/'),('//example.invalid/','/inicio/'),('javascript:alert(1)','/inicio/')]:
    s=BrowserSession(); status,headers,_=s.login(fixtures['admin'],next_url=next_url)
    check('HTTP-NEXT-'+next_url,[302,expected],[status,headers.get('Location')])
s=BrowserSession(); s.request('/?next=/caja/abrir/')
status,headers,_=s.post('/?next=/caja/abrir/',{'email':fixtures['admin']['email'],'password':fixtures['admin']['password'],'next':'/empleados/'})
check('HTTP-NEXT-POST-PRIORITY',[302,'/empleados/'],[status,headers.get('Location')])
s=BrowserSession(); s.request('/?next=/empleados/')
status,headers,_=s.post('/?next=/empleados/',{'email':fixtures['admin']['email'],'password':fixtures['admin']['password'],'next':'https://example.invalid/'})
check('HTTP-NEXT-POST-EXTERNAL-OVERRIDES-GET',[302,'/inicio/'],[status,headers.get('Location')])
s=BrowserSession(); status,headers,_=s.login(fixtures['admin'],next_url='/ruta-inexistente-aud01/')
status404,_,body404=s.request('/ruta-inexistente-aud01/')
status_dash,_,_=s.request('/inicio/')
check('HTTP-NEXT-NONEXISTENT',[302,'/ruta-inexistente-aud01/',404,False,200],
    [status,headers.get('Location'),status404,fixtures['admin']['password'] in body404,status_dash])
status_g,headers_g,_=s.request('/?next=/empleados/')
status_p,headers_p,_=s.post('/?next=/empleados/',{'email':fixtures['admin']['email'],'password':'wrong','next':'/empleados/'})
check('HTTP-AUTH-LOGIN-IGNORES-NEXT',[302,'/inicio/',302,'/inicio/'],
    [status_g,headers_g.get('Location'),status_p,headers_p.get('Location')])
s=BrowserSession(); status,headers,_=s.login(fixtures['vendedor'],next_url='/empleados/')
status,_,body=s.request(headers['Location'])
check('HTTP-NEXT-ROLE',[403,False],[status,fixtures['inactive']['email'] in body])

# Reset via a valid login before starting the consecutive sequence, not via DB deletion.
s=BrowserSession(); s.login(fixtures['almacen'])
s=BrowserSession()
for n in range(1,6):
    status,_,body=s.login(fixtures['almacen'],password='wrong')
    row=state(fixtures['almacen']['email'])
    check(f'HTTP-LOCK-{n}',[200,n,n==5],[status,row['failures'],bool(row['locked_until'])])
locked=state(fixtures['almacen']['email'])
check('HTTP-LOCK-DURATION',True,890 <= (locked['locked_until']-timezone.now()).total_seconds() <= 900)
other=BrowserSession(); status,_,body=other.login(fixtures['almacen'])
check('HTTP-LOCK-OTHER-SESSION',[200,True,locked],[status,'15 minuto(s)' in body,state(fixtures['almacen']['email'])])
for seconds,expected_minutes in [(115,2),(45,1)]:
    LoginAttempt.objects.filter(pk=identity(fixtures['almacen']['email'])).update(locked_until=timezone.now()+timedelta(seconds=seconds))
    status,_,body=other.login(fixtures['almacen'])
    check('HTTP-REMAINING-'+str(expected_minutes),[200,True],[status,f'en {expected_minutes} minuto(s)' in body])
LoginAttempt.objects.filter(pk=identity(fixtures['almacen']['email'])).update(locked_until=timezone.now()-timedelta(seconds=1))
status,headers,_=other.login(fixtures['almacen'])
check('HTTP-EXPIRY',[302,'/inicio/',{'failures':0,'locked_until':None}],
    [status,headers.get('Location'),state(fixtures['almacen']['email'])])

# Small bounded sample establishes aggregate-row growth, not resistance to load.
before=LoginAttempt.objects.count()
for n in range(3):
    unknown={'email':f'growth{n}.{runid}@example.invalid','password':'unused'}
    BrowserSession().login(unknown,password='wrong')
after=LoginAttempt.objects.count()
check('HTTP-GROWTH-THREE-NEW',3,after-before,'CONFIRMA hallazgo de acumulacion; no prueba carga')
BrowserSession().login(unknown,password='wrong')
check('HTTP-GROWTH-REPEATED',[after,2],[LoginAttempt.objects.count(),state(unknown['email'])['failures']],
      'CONFIRMA una fila agregada por identificador')

# Admin is a distinct authentication surface. No superuser or model grants.
for k in ('admin','almacen','vendedor','inactive'):
    na=BrowserSession(); na.request('/admin/login/?next=/admin/')
    st,_,_=na.post('/admin/login/?next=/admin/',{'username':fixtures[k]['email'],'password':fixtures[k]['password'],'next':'/admin/'})
    check('HTTP-ADMIN-POST-NONSTAFF-'+k,[200,None],[st,na.cookie(settings.SESSION_COOKIE_NAME)],
          'CUMPLE rechazo POST directo de cuenta no-staff/inactiva en admin')
staff=fixtures['staff']; a=BrowserSession(); a.request('/admin/login/?next=/admin/')
st_up,_,_=a.post('/admin/login/?next=/admin/',{'username':'  '+staff['email'].upper()+'  ','password':staff['password'],'next':'/admin/'})
check('HTTP-ADMIN-STAFF-UPPERCASE-REJECTED',[200,None],[st_up,a.cookie(settings.SESSION_COOKIE_NAME)],
      'CONFIRMA ModelBackend de admin no normaliza mayusculas/espacios como login publico')
before=LoginAttempt.objects.count()
for _ in range(5):
    status,_,body=a.post('/admin/login/?next=/admin/',{'username':staff['email'],'password':'wrong','next':'/admin/'})
check('HTTP-ADMIN-FIVE-FAILS',[200,before,None],[status,LoginAttempt.objects.count(),state(staff['email'])],
      'CONFIRMA admin no usa bloqueo funcional')
b=BrowserSession()
for _ in range(5):
    b.login(staff,password='wrong')
before_admin=state(staff['email'])
check('HTTP-ADMIN-APP-LOCK-SET',5,before_admin['failures'])
status,headers,_=a.post('/admin/login/?next=/admin/',{'username':staff['email'],'password':staff['password'],'next':'/admin/'})
check('HTTP-ADMIN-BYPASSES-APP-LOCK',[302,'/admin/',before_admin],[status,headers.get('Location'),state(staff['email'])],
      'CONFIRMA superficie separada; politica pendiente P1')
status,_,body=a.request('/admin/')
check('HTTP-ADMIN-STAFF-NO-GRANTS',[200,False],[status,'/admin/identity/account/' in body],
      'CUMPLE entrada staff sin permisos de modelo; CRUD no examinado')
st_root,hd_root,_=a.request('/')
st_dash,_,_=a.request('/inicio/')
check('HTTP-ADMIN-SESSION-BYPASSES-PUBLIC-LOCK-TO-DASHBOARD',[302,'/inicio/',200],
      [st_root,hd_root.get('Location'),st_dash],
      'CONFIRMA sesion creada en /admin/login/ elude bloqueo de / tambien hacia /inicio/')
check('HTTP-BUSINESS-UNCHANGED',before_business,business())
check('HTTP-PROTECTED-DATABASES',before_hashes,protected_hashes())

evidence=ROOT/'auditoria_por_etapas/resultados/evidencias'/f'01-http-{runid}.json'
manifest={'started_lima':started.isoformat(),'finished_lima':datetime.now(ZoneInfo('America/Lima')).isoformat(),
    'tool':'urllib real HTTP + cookies/CSRF + Django ORM; no browser', 'database':str(DATA/'audit.sqlite3'),
    'server_identity_verified':True,'fixture_prefix':'AUD01HTTP','fixture_run':runid,'accounts_created':5,
    'clock':'remaining/expiry via locked_until fixture adjustment; exact T+900 covered in unit tests',
    'results':results,'passed':sum(r['passed'] for r in results),'total':len(results),
    'limitations':['No PostgreSQL concurrency','No production infrastructure or load test','No complete admin CRUD','No full RBAC matrix'],
    'source_hashes':{name:hashlib.sha256((ROOT/'r1-pmv'/name).read_bytes()).hexdigest() for name in ['identity/views.py','identity/services.py','identity/forms.py','identity/models.py']}}
with evidence.open('x',encoding='utf-8') as handle:
    json.dump(manifest,handle,ensure_ascii=False,indent=2,default=str)
print(json.dumps({'evidence':str(evidence.relative_to(ROOT)),'passed':manifest['passed'],'total':manifest['total'],
    'failed_cases':[r['case'] for r in results if not r['passed']]},ensure_ascii=False))
raise SystemExit(0 if manifest['passed']==manifest['total'] else 1)
