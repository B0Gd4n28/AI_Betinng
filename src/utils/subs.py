import os
import json
from datetime import datetime, timedelta

SUBS_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'subscriptions.json')

# Internal helpers

def _load():
    if not os.path.exists(SUBS_PATH):
        with open(SUBS_PATH, 'w', encoding='utf-8') as f:
            json.dump({"admins": [], "users": {}, "codes": {}}, f)
    with open(SUBS_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def _save(data):
    with open(SUBS_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# API

def is_admin(uid: int) -> bool:
    data = _load()
    return str(uid) in [str(a) for a in data.get('admins', [])]

def get_plan(uid: int) -> tuple[str, str|None]:
    data = _load()
    user = data['users'].get(str(uid))
    if not user:
        return 'free', None
    return user.get('plan', 'free'), user.get('expires')

def grant_days(uid: int, plan: str, days: int) -> str:
    data = _load()
    uid = str(uid)
    expires = None
    if uid in data['users'] and data['users'][uid].get('expires'):
        old_exp = datetime.strptime(data['users'][uid]['expires'], '%Y-%m-%d')
        new_exp = max(datetime.now(), old_exp) + timedelta(days=days)
    else:
        new_exp = datetime.now() + timedelta(days=days)
    expires = new_exp.strftime('%Y-%m-%d')
    data['users'][uid] = {'plan': plan, 'expires': expires}
    _save(data)
    return expires

def redeem(code: str, uid: int) -> tuple[bool, str]:
    data = _load()
    code = code.strip()
    if code not in data['codes']:
        return False, 'Cod invalid sau folosit.'
    info = data['codes'][code]
    plan = info.get('plan', 'starter')
    days = info.get('days', 30)
    expires = grant_days(uid, plan, days)
    del data['codes'][code]
    _save(data)
    return True, expires

def plan_gate(uid: int, feature: str) -> tuple[bool, str]:
    plan, _ = get_plan(uid)
    if plan == 'free':
        if feature == 'today':
            return True, ''
        return False, '⛔ Doar pentru abonați.'
    if plan == 'starter':
        if feature == 'markets':
            return True, 'max 3 legs'
    if plan == 'pro':
        if feature == 'markets':
            return True, 'max 4 legs'
    return False, '⛔ Funcție indisponibilă.'
