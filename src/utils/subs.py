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
                data['users'][str(uid)]['plan'] = 'free'
                data['users'][str(uid)]['expires'] = None
                _save(data)
            plan = 'free'
    
    # Special handling for prediction features (use trial system)
    if feature in ['today', 'markets', 'express']:
        if plan != 'free':
            # Paid users have unlimited access
            if plan == 'starter':
                return True, 'max 3 selecții' if feature == 'express' else ''
            elif plan == 'pro':
                return True, 'max 4 selecții' if feature == 'express' else ''
        else:
            # Free users use trial system
            trial_used, trial_remaining = get_trial_usage(uid)
            if trial_remaining > 0:
                return True, f'trial: {trial_remaining} generări rămase'
            else:
                return False, '⛔ Trial expirat! Alege un abonament pentru acces nelimitat.'
    
    # Non-prediction features
    if feature in ['help', 'start', 'lang', 'status', 'subscribe', 'redeem']:
        return True, ''
    
    if plan == 'free':
        return False, '⛔ Funcție disponibilă doar pentru abonați!'
    
    if plan == 'starter':
        if feature in ['stats', 'bankroll']:
            return True, ''
        return False, '⛔ Upgrade la Pro pentru funcții avansate!'
    
    if plan == 'pro':
        return True, ''  # Pro has access to everything
    
    return False, '⛔ Funcție indisponibilă.'

def get_user_stats(uid: int) -> dict:
    """Get user subscription stats including trial usage"""
    plan, expires = get_plan(uid)
    days_left = 0
    if expires:
        exp_date = datetime.strptime(expires, '%Y-%m-%d')
        days_left = max(0, (exp_date.date() - datetime.now().date()).days)
    
    # Get trial usage
    trial_used, trial_remaining = get_trial_usage(uid)
    
    return {
        'plan': plan,
        'expires': expires,
        'days_left': days_left,
        'is_active': plan != 'free' and days_left > 0,
        'trial_used': trial_used,
        'trial_remaining': trial_remaining,
        'is_new_user': trial_used == 0
    }

def get_trial_usage(uid: int) -> tuple[int, int]:
    """Get trial usage for user (used, remaining)"""
    data = _load()
    user = data['users'].get(str(uid), {})
    trial_used = user.get('trial_used', 0)
    trial_remaining = max(0, 2 - trial_used)  # 2 generări gratuite
    return trial_used, trial_remaining

def use_trial(uid: int) -> bool:
    """Use one trial generation. Returns True if successful, False if no trials left"""
    data = _load()
    uid_str = str(uid)
    
    if uid_str not in data['users']:
        data['users'][uid_str] = {'plan': 'free', 'trial_used': 0}
    
    user = data['users'][uid_str]
    trial_used = user.get('trial_used', 0)
    
    if trial_used >= 2:
        return False  # No trials left
    
    user['trial_used'] = trial_used + 1
    _save(data)
    return True

def reset_trial(uid: int) -> bool:
    """Reset trial for user (admin only)"""
    data = _load()
    uid_str = str(uid)
    
    if uid_str in data['users']:
        data['users'][uid_str]['trial_used'] = 0
        _save(data)
        return True
    return False

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

def log_user_activity(uid: int, action: str, ip: str = None):
    """Log user activity for admin tracking"""
    data = _load()
    
    if 'activity_log' not in data:
        data['activity_log'] = []
    
    log_entry = {
        'uid': uid,
        'action': action,
        'timestamp': datetime.now().isoformat(),
        'ip': ip
    }
    
    data['activity_log'].append(log_entry)
    
    # Keep only last 1000 entries
    if len(data['activity_log']) > 1000:
        data['activity_log'] = data['activity_log'][-1000:]
    
    _save(data)

def get_user_activity(uid: int = None, limit: int = 50) -> list:
    """Get user activity log for admin"""
    data = _load()
    logs = data.get('activity_log', [])
    
    if uid:
        logs = [log for log in logs if log['uid'] == uid]
    
    return logs[-limit:]

def get_user_statistics() -> dict:
    """Get comprehensive user statistics for admin"""
    data = _load()
    
    total_users = len(data.get('users', {}))
    active_subscribers = 0
    trial_users = 0
    expired_users = 0
    
    for uid, user_data in data.get('users', {}).items():
        plan = user_data.get('plan', 'free')
        expires = user_data.get('expires')
        trial_used = user_data.get('trial_used', 0)
        
        if plan != 'free' and expires:
            exp_date = datetime.strptime(expires, '%Y-%m-%d')
            if datetime.now().date() <= exp_date.date():
                active_subscribers += 1
            else:
                expired_users += 1
        elif trial_used > 0:
            trial_users += 1
    
    return {
        'total_users': total_users,
        'active_subscribers': active_subscribers,
        'trial_users': trial_users,
        'expired_users': expired_users,
        'total_codes': len(data.get('codes', {})),
        'total_admins': len(data.get('admins', []))
    }
