"""Browser fault injection only on the marked isolated audit13 database."""
from audit13_settings import *
MIDDLEWARE = ['audit13c_faults.QueryFailureMiddleware', *MIDDLEWARE]
slot = os.environ.get('AUDIT13_SESSION_SLOT', 'admin')
if slot not in {'admin','warehouse','seller','empty'}:
    raise RuntimeError('Unknown isolated browser slot')
SESSION_COOKIE_NAME = 'audit13c_' + slot + '_session'
CSRF_COOKIE_NAME = 'audit13c_' + slot + '_csrf'
