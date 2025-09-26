"""
📊 Interactive Statistics & Analytics
Personal betting performance tracking with visual charts
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from collections import defaultdict
import os

# Storage paths
STATS_DIR = Path(__file__).resolve().parents[2] / "storage"
STATS_FILE = STATS_DIR / "user_stats.json"
BETS_FILE = STATS_DIR / "user_bets.json"

def ensure_stats_files():
    """Ensure storage directory and files exist"""
    STATS_DIR.mkdir(exist_ok=True)
    if not STATS_FILE.exists():
        STATS_FILE.write_text(json.dumps({}))
    if not BETS_FILE.exists():
        BETS_FILE.write_text(json.dumps({}))

def load_user_stats(user_id: str) -> Dict:
    """Load user statistics"""
    ensure_stats_files()
    try:
        with open(STATS_FILE, 'r', encoding='utf-8') as f:
            all_stats = json.load(f)
        return all_stats.get(str(user_id), {
            'total_bets': 0,
            'won_bets': 0,
            'lost_bets': 0,
            'pending_bets': 0,
            'total_staked': 0.0,
            'total_returns': 0.0,
            'best_odds': 0.0,
            'longest_win_streak': 0,
            'current_streak': 0,
            'streak_type': 'none',  # 'win', 'loss', 'none'
            'favorite_market': 'unknown',
            'join_date': datetime.now().isoformat(),
            'last_bet': None,
            'roi_percentage': 0.0,
            'profit_loss': 0.0,
            'average_odds': 0.0,
            'win_rate': 0.0,
            'monthly_stats': {},
            'market_performance': {
                '1X2': {'bets': 0, 'wins': 0, 'profit': 0.0},
                'OU25': {'bets': 0, 'wins': 0, 'profit': 0.0},
                'BTTS': {'bets': 0, 'wins': 0, 'profit': 0.0}
            }
        })
    except Exception:
        return {}

def save_user_stats(user_id: str, stats: Dict):
    """Save user statistics"""
    ensure_stats_files()
    try:
        with open(STATS_FILE, 'r', encoding='utf-8') as f:
            all_stats = json.load(f)
    except Exception:
        all_stats = {}
    
    all_stats[str(user_id)] = stats
    
    with open(STATS_FILE, 'w', encoding='utf-8') as f:
        json.dump(all_stats, f, indent=2, ensure_ascii=False)

def add_bet_record(user_id: str, bet_data: Dict):
    """Add a new bet record"""
    ensure_stats_files()
    try:
        with open(BETS_FILE, 'r', encoding='utf-8') as f:
            all_bets = json.load(f)
    except Exception:
        all_bets = {}
    
    if str(user_id) not in all_bets:
        all_bets[str(user_id)] = []
    
    bet_record = {
        'id': len(all_bets[str(user_id)]) + 1,
        'date': datetime.now().isoformat(),
        'match': bet_data.get('match', 'Unknown'),
        'market': bet_data.get('market', 'Unknown'),
        'selection': bet_data.get('selection', 'Unknown'),
        'odds': bet_data.get('odds', 1.0),
        'stake': bet_data.get('stake', 0.0),
        'status': 'pending',  # 'won', 'lost', 'pending'
        'potential_return': bet_data.get('stake', 0.0) * bet_data.get('odds', 1.0),
        'ev': bet_data.get('ev', 0.0),
        'probability': bet_data.get('probability', 0.0)
    }
    
    all_bets[str(user_id)].append(bet_record)
    
    with open(BETS_FILE, 'w', encoding='utf-8') as f:
        json.dump(all_bets, f, indent=2, ensure_ascii=False)

def create_ascii_chart(values: List[float], labels: List[str], width: int = 20) -> str:
    """Create ASCII bar chart"""
    if not values:
        return "📊 No data available"
    
    max_val = max(values) if values else 1
    if max_val == 0:
        max_val = 1
    
    chart = "📊 **Performance Chart**\n```\n"
    for i, (val, label) in enumerate(zip(values, labels)):
        bar_length = int((val / max_val) * width)
        bar = "█" * bar_length + "░" * (width - bar_length)
        chart += f"{label:<8} {bar} {val:.1f}%\n"
    chart += "```"
    return chart

def get_stats_summary(user_id: str) -> str:
    """Get comprehensive stats summary with visual elements"""
    stats = load_user_stats(user_id)
    
    if stats.get('total_bets', 0) == 0:
        return (
            "📊 **Statistici Personale**\n\n"
            "🎯 Nu ai încă pariuri înregistrate!\n"
            "💡 Folosește /track pentru a înregistra pariurile tale\n\n"
            "🚀 Odată ce începi să trackuiești, vei vedea:\n"
            "• 📈 Rate de câștig per piață\n"
            "• 💰 Profit/Loss în timp real\n"
            "• 🔥 Streak-uri și achievement-uri\n"
            "• 🎯 ROI și metrici avansate"
        )
    
    total_bets = stats.get('total_bets', 0)
    won_bets = stats.get('won_bets', 0)
    win_rate = (won_bets / total_bets * 100) if total_bets > 0 else 0
    profit_loss = stats.get('profit_loss', 0.0)
    roi = stats.get('roi_percentage', 0.0)
    current_streak = stats.get('current_streak', 0)
    streak_type = stats.get('streak_type', 'none')
    
    # Streak emoji
    if streak_type == 'win':
        streak_emoji = "🔥" if current_streak >= 5 else "✅"
    elif streak_type == 'loss':
        streak_emoji = "❄️" if current_streak >= 3 else "❌"
    else:
        streak_emoji = "⚪"
    
    # Performance emoji
    if roi >= 10:
        perf_emoji = "🚀"
    elif roi >= 5:
        perf_emoji = "📈"
    elif roi >= 0:
        perf_emoji = "💫"
    else:
        perf_emoji = "📉"
    
    # Market performance
    markets = stats.get('market_performance', {})
    market_text = ""
    for market, data in markets.items():
        if data.get('bets', 0) > 0:
            m_win_rate = (data.get('wins', 0) / data.get('bets', 1)) * 100
            m_emoji = "🏆" if m_win_rate >= 60 else "⭐" if m_win_rate >= 50 else "🎯"
            market_text += f"• {m_emoji} {market}: {m_win_rate:.1f}% ({data.get('wins', 0)}/{data.get('bets', 0)})\n"
    
    summary = f"""📊 **Statistici Personale** {perf_emoji}

🎯 **Performanță Generală:**
• Total Pariuri: {total_bets}
• Rate Câștig: {win_rate:.1f}% ({won_bets}/{total_bets})
• ROI: {roi:+.1f}%
• Profit/Loss: {profit_loss:+.2f} RON

{streak_emoji} **Streak Actual:**
• {streak_type.title() if streak_type != 'none' else 'Neutru'}: {current_streak} pariuri

📈 **Per Piață:**
{market_text if market_text else '• Nu există date suficiente'}

💡 **Insight:** {"Excelent! Continua strategia!" if roi >= 5 else "Fokusează pe value bets cu EV pozitiv!" if roi >= 0 else "Revizuiește strategia - folosește /tips pentru sfaturi"}
"""
    
    return summary

def get_monthly_chart(user_id: str) -> str:
    """Get monthly performance chart"""
    stats = load_user_stats(user_id)
    monthly = stats.get('monthly_stats', {})
    
    if not monthly:
        return "📊 Nu există date lunare suficiente"
    
    # Get last 6 months
    current = datetime.now()
    months = []
    values = []
    
    for i in range(5, -1, -1):
        month = (current - timedelta(days=30*i)).strftime('%Y-%m')
        months.append(month.split('-')[1])
        roi = monthly.get(month, {}).get('roi', 0.0)
        values.append(max(0, roi))  # Only positive for visual
    
    return create_ascii_chart(values, months, 15)

def update_bet_result(user_id: str, bet_id: int, result: str, actual_return: float = 0.0):
    """Update bet result (won/lost)"""
    ensure_stats_files()
    
    # Update bet record
    try:
        with open(BETS_FILE, 'r', encoding='utf-8') as f:
            all_bets = json.load(f)
        
        user_bets = all_bets.get(str(user_id), [])
        for bet in user_bets:
            if bet.get('id') == bet_id:
                bet['status'] = result
                if result == 'won':
                    bet['actual_return'] = actual_return
                break
        
        all_bets[str(user_id)] = user_bets
        
        with open(BETS_FILE, 'w', encoding='utf-8') as f:
            json.dump(all_bets, f, indent=2, ensure_ascii=False)
    except Exception:
        pass
    
    # Update user stats
    stats = load_user_stats(user_id)
    
    if result == 'won':
        stats['won_bets'] = stats.get('won_bets', 0) + 1
        stats['total_returns'] = stats.get('total_returns', 0.0) + actual_return
        # Update streak
        if stats.get('streak_type') == 'win':
            stats['current_streak'] = stats.get('current_streak', 0) + 1
        else:
            stats['current_streak'] = 1
            stats['streak_type'] = 'win'
        
        stats['longest_win_streak'] = max(
            stats.get('longest_win_streak', 0),
            stats.get('current_streak', 0)
        )
    
    elif result == 'lost':
        stats['lost_bets'] = stats.get('lost_bets', 0) + 1
        # Update streak
        if stats.get('streak_type') == 'loss':
            stats['current_streak'] = stats.get('current_streak', 0) + 1
        else:
            stats['current_streak'] = 1
            stats['streak_type'] = 'loss'
    
    # Recalculate derived stats
    total_bets = stats.get('total_bets', 0)
    won_bets = stats.get('won_bets', 0)
    total_staked = stats.get('total_staked', 0.0)
    total_returns = stats.get('total_returns', 0.0)
    
    stats['win_rate'] = (won_bets / total_bets * 100) if total_bets > 0 else 0.0
    stats['profit_loss'] = total_returns - total_staked
    stats['roi_percentage'] = (stats['profit_loss'] / total_staked * 100) if total_staked > 0 else 0.0
    
    save_user_stats(user_id, stats)

def get_leaderboard() -> str:
    """Get top performers leaderboard"""
    ensure_stats_files()
    try:
        with open(STATS_FILE, 'r', encoding='utf-8') as f:
            all_stats = json.load(f)
    except Exception:
        return "🏆 Leaderboard nu este disponibil"
    
    # Filter users with at least 5 bets
    qualified_users = []
    for user_id, stats in all_stats.items():
        if stats.get('total_bets', 0) >= 5:
            qualified_users.append({
                'user_id': user_id,
                'roi': stats.get('roi_percentage', 0.0),
                'win_rate': stats.get('win_rate', 0.0),
                'profit': stats.get('profit_loss', 0.0),
                'bets': stats.get('total_bets', 0)
            })
    
    if not qualified_users:
        return "🏆 **Leaderboard**\n\nNu există utilizatori cu minim 5 pariuri încă!"
    
    # Sort by ROI
    qualified_users.sort(key=lambda x: x['roi'], reverse=True)
    
    leaderboard = "🏆 **TOP Performeri** (min. 5 pariuri)\n\n"
    
    for i, user in enumerate(qualified_users[:10], 1):
        emoji = ["🥇", "🥈", "🥉"][i-1] if i <= 3 else f"{i}."
        roi = user['roi']
        win_rate = user['win_rate']
        
        leaderboard += f"{emoji} ROI: {roi:+.1f}% | WR: {win_rate:.1f}% | {user['bets']} pariuri\n"
    
    return leaderboard