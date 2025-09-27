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
    # Main admin ID - Bogdan
    if uid == 1622719347:
        return True
    
    data = _load()
    return str(uid) in [str(a) for a in data.get('admins', [])]

def get_plan(uid: int) -> tuple[str, str|None]:
    data = _load()
    user = data['users'].get(str(uid))
    if not user:
        return 'free', None
    return user.get('plan', 'free'), user.get('expires')

def get_plan_limits(plan: str) -> dict:
    """Get generation limits and features for each plan"""
    limits = {
        'free': {
            'daily_predictions': 2,
            'express_selections': 0,
            'features': ['basic_predictions']
        },
        'basic': {
            'daily_predictions': 50,
            'express_selections': 3,
            'features': ['basic_predictions', 'stats', 'live_analysis']
        },
        'starter': {
            'daily_predictions': 50,
            'express_selections': 3,
            'features': ['basic_predictions', 'stats', 'live_analysis', 'bankroll']
        },
        'pro': {
            'daily_predictions': -1,  # unlimited
            'express_selections': 4,
            'features': ['all']
        },
        'premium': {
            'daily_predictions': -1,  # unlimited  
            'express_selections': 5,
            'features': ['all', 'premium']
        }
    }
    return limits.get(plan, limits['free'])

def grant_days(uid: int, plan: str, days: int) -> str:
    data = _load()
    uid = str(uid)
    expires = None
    
    # Calculate expiration date
    if uid in data['users'] and data['users'][uid].get('expires'):
        old_exp = datetime.strptime(data['users'][uid]['expires'], '%Y-%m-%d')
        new_exp = max(datetime.now(), old_exp) + timedelta(days=days)
    else:
        new_exp = datetime.now() + timedelta(days=days)
    expires = new_exp.strftime('%Y-%m-%d')
    
    # Preserve existing user data or create new
    if uid not in data['users']:
        data['users'][uid] = {
            'plan': plan,
            'expires': expires,
            'trial_used': 0,
            'daily_usage': {},
            'joined': datetime.now().isoformat()
        }
    else:
        # Update plan but preserve usage counters
        data['users'][uid]['plan'] = plan
        data['users'][uid]['expires'] = expires
        # Reset daily usage when upgrading
        data['users'][uid]['daily_usage'] = {}
    
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
    plan = user.get('plan', 'free')
    
    # Get plan limits
    limits = get_plan_limits(plan)
    max_daily = limits['daily_predictions']
    
    # For free users, use trial_used counter
    if plan == 'free':
        trial_used = user.get('trial_used', 0)
        trial_remaining = max(0, max_daily - trial_used)
        return trial_used, trial_remaining
    
    # For paid users with unlimited (-1)
    if max_daily == -1:
        return 0, float('inf')
    
    # For paid users with daily limits
    today = datetime.now().strftime('%Y-%m-%d')
    daily_usage = user.get('daily_usage', {})
    used_today = daily_usage.get(today, 0)
    remaining_today = max(0, max_daily - used_today)
    
    return used_today, remaining_today

def use_trial(uid: int) -> bool:
    """Use one generation based on user plan. Returns True if successful, False if no generations left"""
    data = _load()
    uid_str = str(uid)
    
    if uid_str not in data['users']:
        data['users'][uid_str] = {
            'plan': 'free', 
            'trial_used': 0,
            'daily_usage': {},
            'joined': datetime.now().isoformat()
        }
    
    user = data['users'][uid_str]
    plan = user.get('plan', 'free')
    limits = get_plan_limits(plan)
    max_daily = limits['daily_predictions']
    
    # For free users - use trial_used counter
    if plan == 'free':
        trial_used = user.get('trial_used', 0)
        if trial_used >= max_daily:
            return False  # No trials left
        user['trial_used'] = trial_used + 1
        _save(data)
        return True
    
    # For unlimited plans
    if max_daily == -1:
        return True
    
    # For paid users with daily limits
    today = datetime.now().strftime('%Y-%m-%d')
    if 'daily_usage' not in user:
        user['daily_usage'] = {}
    
    used_today = user['daily_usage'].get(today, 0)
    if used_today >= max_daily:
        return False  # Daily limit reached
    
    user['daily_usage'][today] = used_today + 1
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

def get_user_account_info(uid: int) -> dict:
    """Get user account information for account menu"""
    data = _load()
    uid_str = str(uid)
    
    if uid_str not in data['users']:
        # Create new user with trial
        data['users'][uid_str] = {
            'plan': 'free',
            'expires': None,
            'trial_used': 0,
            'joined': datetime.now().isoformat()
        }
        _save(data)
    
    user = data['users'][uid_str]
    plan = user.get('plan', 'free')
    expires = user.get('expires')
    trial_used = user.get('trial_used', 0)
    joined = user.get('joined', 'Unknown')
    
    # Calculate remaining trials
    remaining_trials = max(0, 2 - trial_used) if plan == 'free' else float('inf')
    
    # Check if subscription is active
    subscription_active = False
    if plan != 'free' and expires:
        exp_date = datetime.strptime(expires, '%Y-%m-%d')
        subscription_active = datetime.now().date() <= exp_date.date()
    
    return {
        'user_id': uid,
        'plan': plan,
        'expires': expires,
        'trial_used': trial_used,
        'remaining_trials': remaining_trials,
        'joined': joined,
        'subscription_active': subscription_active
    }

def get_pricing_catalog() -> dict:
    """Get pricing catalog for subscription plans with attractive USD pricing"""
    return {
        'BASIC': {
            'plan_key': 'basic',
            'price_monthly': '$7.99/month',
            'price_yearly': '$79.99/year (SAVE 17%)',
            'price_original': '$95.88',
            'features': [
                '✅ 50 AI predictions daily',
                '✅ Express builder (3 selections)',
                '✅ LIVE match analysis',
                '✅ Detailed statistics & insights',
                '✅ 24/7 premium support',
                '✅ Win rate tracking'
            ],
            'savings': 'SAVE $15.89/year',
            'discount': '17% OFF'
        },
        'PRO': {
            'plan_key': 'pro',
            'price_monthly': '$12.99/month', 
            'price_yearly': '$119.99/year (SAVE 23%)',
            'price_original': '$155.88',
            'features': [
                '🔥 UNLIMITED AI PREDICTIONS',
                '🔥 Express builder (4 selections)',
                '🔥 Advanced ML algorithms',
                '🔥 Personal betting strategies',
                '🔥 Bankroll management',
                '🔥 VIP priority support',
                '🔥 Exclusive features',
                '🔥 Weekly expert insights'
            ],
            'savings': 'SAVE $35.89/year',
            'popular': True,
            'discount': '23% OFF'
        },
        'PREMIUM': {
            'plan_key': 'premium',
            'price_monthly': '$19.99/month',
            'price_yearly': '$179.99/year (SAVE 25%)', 
            'price_original': '$239.88',
            'features': [
                '💎 ALL PRO features included',
                '💎 Express builder (5 selections)',
                '💎 Psychology-based analysis',
                '💎 Weather impact predictions',
                '💎 Advanced portfolio tracking',
                '💎 1-on-1 expert consultations',
                '💎 Developer API access',
                '💎 Custom tools & insights'
            ],
            'savings': 'SAVE $59.89/year',
            'exclusive': True,
            'discount': '25% OFF'
        }
    }

def get_remaining_generations(uid: int) -> int:
    """Get remaining generations for user based on their plan"""
    data = _load()
    uid_str = str(uid)
    
    if uid_str not in data['users']:
        # New user gets 2 free generations
        return 2
    
    user = data['users'][uid_str]
    plan = user.get('plan', 'free')
    limits = get_plan_limits(plan)
    max_daily = limits['daily_predictions']
    
    # Check if subscription is active for paid users
    if plan != 'free':
        expires = user.get('expires')
        if expires:
            try:
                exp_date = datetime.strptime(expires, '%Y-%m-%d')
                if datetime.now().date() > exp_date.date():
                    # Subscription expired - downgrade to free
                    plan = 'free'
                    max_daily = 2
                elif max_daily == -1:
                    return float('inf')  # Unlimited for active subscribers
            except:
                plan = 'free'
                max_daily = 2
    
    # For free users: max_daily - trial_used
    if plan == 'free':
        trial_used = user.get('trial_used', 0)
        remaining = max(0, max_daily - trial_used)
        return remaining
    
    # For paid users with daily limits
    today = datetime.now().strftime('%Y-%m-%d')
    daily_usage = user.get('daily_usage', {})
    used_today = daily_usage.get(today, 0)
    remaining_today = max(0, max_daily - used_today)
    
    return remaining_today

def format_remaining_generations(uid: int) -> str:
    """Format remaining generations for display"""
    data = _load()
    uid_str = str(uid)
    user = data['users'].get(uid_str, {})
    plan = user.get('plan', 'free')
    limits = get_plan_limits(plan)
    max_daily = limits['daily_predictions']
    
    remaining = get_remaining_generations(uid)
    
    if remaining == float('inf'):
        return "♾️ **NELIMITAT** (Plan Premium)"
    elif plan == 'free':
        return f"� **{remaining}/{max_daily}** generări gratuite"
    elif max_daily > 0:
        return f"💎 **{remaining}/{max_daily}** generări astăzi (Plan {plan.title()})"
    else:
        return "❌ **Limita zilnică atinsă** - Încearcă mâine!"
