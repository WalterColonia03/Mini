"""Expire only fictional warehouse sessions in AJ's marked database."""
import json
import os
from pathlib import Path
from datetime import timedelta


def inspect_or_expire(expire=False):
    from django.conf import settings
    from django.contrib.sessions.models import Session
    from django.utils import timezone
    from identity.models import Account
    run = Path(os.environ['AUDIT03_RUN_DIR']).resolve()
    assert '-AJ-' in run.name and json.loads((run/'marker.json').read_text())['run'] == run.name
    assert Path(settings.DATABASES['default']['NAME']).resolve() == run/'audit.sqlite3'
    actor = Account.objects.select_related('role').get(email='warehouse@audit03.invalid')
    sessions = [s for s in Session.objects.all() if s.get_decoded().get('_auth_user_id') == str(actor.pk)]
    changed = 0
    if expire:
        for session in sessions:
            session.expire_date = timezone.now()-timedelta(seconds=1)
            session.save(update_fields=['expire_date'])
            changed += 1
    return {'role':actor.role.code,'active':actor.is_active,'sessions_expired':changed}
