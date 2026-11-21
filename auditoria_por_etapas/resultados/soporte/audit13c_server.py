"""Start fixture server with test-only fault middleware; ignores operator .env."""
import os, sys
from pathlib import Path
from audit13_run import APP, SUPPORT
sys.path[:0] = [str(APP), str(SUPPORT)]
os.environ['DJANGO_SETTINGS_MODULE'] = 'audit13c_settings'
import django
django.setup()
from django.core.management import call_command
call_command('runserver','127.0.0.1:'+sys.argv[1],use_reloader=False,insecure=True)
