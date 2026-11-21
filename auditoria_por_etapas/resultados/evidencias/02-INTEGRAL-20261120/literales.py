"""Measure specified text in rendered Django responses using only isolated test fixtures."""
from pathlib import Path
from html.parser import HTMLParser
import os, re, sys, json
from unittest.mock import patch
d=Path(__file__).resolve().parent
root=next(p for p in d.parents if (p/"r1-pmv/manage.py").is_file())
os.chdir(root/"r1-pmv"); sys.path.insert(0,os.getcwd())
os.environ.update(APP_ENV="test", DJANGO_SETTINGS_MODULE="config.settings")
import django
django.setup()
from django.core.management import call_command
from django.test import Client
from django.utils import translation
from django.template.loader import render_to_string
from django.test.utils import override_settings
from identity.forms import EmployeeEditForm, EmployeeCreationForm
catalog=(d.parents[1]/"soporte/02-catalogo-entrega.md").read_text(encoding="utf-8")
sections=re.split(r"\n## ", catalog)[1:]
cases={}
for section in sections:
    key=section.split(" · ")[0]
    for block in re.findall(r"```text\n(.*?)\n```",section,re.S):
        for line in block.splitlines():
            pat=re.escape(line)
            for tag in ("nombre","correo","rol","estado","hasta"):
                pat=pat.replace(re.escape("{"+tag+"}"),r"[^<>]{1,120}?")
            cases[(key,line)]=re.compile(pat)
matched=set()
class Text(HTMLParser):
    def __init__(self):
        super().__init__();self.parts=[];self.placeholders=[]
    def handle_data(self,text):self.parts.append(text)
    def handle_starttag(self,tag,attrs):
        ph=dict(attrs).get("placeholder")
        if ph:self.placeholders.append(ph)
def observe(path,response):
    if not (path in ("/","/salir/") or path.startswith("/empleados/")):return
    p=Text();p.feed(response.content.decode("utf-8",errors="replace"))
    content=" ".join((" ".join(p.parts+p.placeholders)).split())
    for k,pat in cases.items():
        if k not in matched and pat.search(content):matched.add(k)
request=Client.request
def audited(c,**args):
    response=request(c,**args)
    observe(args.get("PATH_INFO",""),response)
    return response
try:
    with patch.object(Client,"request",audited):
        call_command("test","identity",verbosity=0,interactive=False)
finally:
    rows=[dict(group=k[0],literal=k[1],observed=k in matched) for k in cases]
    (d/"literales.json").write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding="utf-8")
    print("Coincidencias en respuestas:",len(matched),"/",len(cases))
