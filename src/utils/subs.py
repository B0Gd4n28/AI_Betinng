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
    plan, expires = get_plan(uid)
    
    # Check if subscription expired
    if expires:
        exp_date = datetime.strptime(expires, '%Y-%m-%d')
        if datetime.now().date() > exp_date.date():
            # Downgrade to free if expired
            data = _load()
            if str(uid) in data['users']:
                del data['users'][str(uid)]
                _save(data)
            plan = 'free'
    
    if plan == 'free':
        if feature in ['today', 'help', 'start', 'lang']:
            return True, ''
        return False, '⛔ Upgrade la Starter/Pro pentru acces complet!'
    
    if plan == 'starter':
        if feature in ['today', 'markets', 'stats', 'bankroll']:
            return True, ''
        if feature == 'express':
            return True, 'max 3 selecții'
        return False, '⛔ Upgrade la Pro pentru funcții avansate!'
    
    if plan == 'pro':
        if feature == 'express':
            return True, 'max 4 selecții'
        return True, ''  # Pro has access to everything
    
    return False, '⛔ Funcție indisponibilă.'

def get_user_stats(uid: int) -> dict:
    """Get user subscription stats"""
    plan, expires = get_plan(uid)
    days_left = 0
    if expires:
        exp_date = datetime.strptime(expires, '%Y-%m-%d')
        days_left = max(0, (exp_date.date() - datetime.now().date()).days)
    
    return {
        'plan': plan,
        'expires': expires,
        'days_left': days_left,
        'is_active': plan != 'free' and days_left > 0
    }

def list_active_codes() -> list:
    """List all available promo codes (admin only)"""
    data = _load()
    return list(data.get('codes', {}).keys())

def add_promo_code(code: str, plan: str, days: int) -> bool:
    """Add new promo code (admin only)"""
    data = _load()
    if code in data['codes']:
        return False  # Code already exists
    data['codes'][code] = {'plan': plan, 'days': days}
    _save(data)
    return True
