"""
🤖 AI Learning & Personalization
Personal model training, betting pattern analysis, adaptive strategies
"""

import json
import numpy as np
from typing import Dict, List, Tuple, Optional
from collections import defaultdict, Counter
from datetime import datetime, timedelta
from pathlib import Path

# Storage paths
AI_DIR = Path(__file__).resolve().parents[2] / "storage" / "ai_models"
PATTERNS_FILE = AI_DIR / "user_patterns.json"
RECOMMENDATIONS_FILE = AI_DIR / "recommendations.json"

def ensure_ai_files():
    """Ensure AI storage directory and files exist"""
    AI_DIR.mkdir(parents=True, exist_ok=True)
    if not PATTERNS_FILE.exists():
        PATTERNS_FILE.write_text(json.dumps({}))
    if not RECOMMENDATIONS_FILE.exists():
        RECOMMENDATIONS_FILE.write_text(json.dumps({}))

def analyze_betting_patterns(user_id: str, bet_history: List[Dict]) -> Dict:
    """Analyze user's betting patterns and preferences"""
    if not bet_history:
        return {'error': 'No betting history available'}
    
    patterns = {
        'favorite_markets': Counter(),
        'favorite_odds_range': {'low': 0, 'medium': 0, 'high': 0},
        'stake_patterns': {'conservative': 0, 'moderate': 0, 'aggressive': 0},
        'time_preferences': Counter(),
        'league_preferences': Counter(),
        'win_rate_by_market': defaultdict(list),
        'win_rate_by_odds_range': defaultdict(list),
        'streak_behavior': {'after_wins': [], 'after_losses': []},
        'risk_profile': 'unknown'
    }
    
    for i, bet in enumerate(bet_history):
        market = bet.get('market', 'unknown')
        odds = bet.get('odds', 1.0)
        stake = bet.get('stake', 0)
        result = bet.get('result', 'pending')
        date = bet.get('date', '')
        
        # Market preferences
        patterns['favorite_markets'][market] += 1
        
        # Odds range analysis
        if odds < 1.8:
            patterns['favorite_odds_range']['low'] += 1
            patterns['win_rate_by_odds_range']['low'].append(1 if result == 'won' else 0)
        elif odds < 2.5:
            patterns['favorite_odds_range']['medium'] += 1
            patterns['win_rate_by_odds_range']['medium'].append(1 if result == 'won' else 0)
        else:
            patterns['favorite_odds_range']['high'] += 1
            patterns['win_rate_by_odds_range']['high'].append(1 if result == 'won' else 0)
        
        # Stake patterns (assuming bankroll context)
        if stake < 50:
            patterns['stake_patterns']['conservative'] += 1
        elif stake < 100:
            patterns['stake_patterns']['moderate'] += 1
        else:
            patterns['stake_patterns']['aggressive'] += 1
        
        # Time analysis
        if date:
            try:
                dt = datetime.fromisoformat(date.replace('Z', '+00:00'))
                hour = dt.hour
                if 9 <= hour < 12:
                    patterns['time_preferences']['morning'] += 1
                elif 12 <= hour < 18:
                    patterns['time_preferences']['afternoon'] += 1
                elif 18 <= hour < 22:
                    patterns['time_preferences']['evening'] += 1
                else:
                    patterns['time_preferences']['night'] += 1
            except:
                pass
        
        # Win rate by market
        if result in ['won', 'lost']:
            patterns['win_rate_by_market'][market].append(1 if result == 'won' else 0)
        
        # Streak behavior analysis
        if i > 0:
            prev_result = bet_history[i-1].get('result')
            if prev_result == 'won':
                patterns['streak_behavior']['after_wins'].append({
                    'odds': odds,
                    'stake': stake,
                    'market': market,
                    'result': result
                })
            elif prev_result == 'lost':
                patterns['streak_behavior']['after_losses'].append({
                    'odds': odds,
                    'stake': stake,
                    'market': market,
                    'result': result
                })
    
    # Calculate win rates
    for market, results in patterns['win_rate_by_market'].items():
        if results:
            patterns['win_rate_by_market'][market] = sum(results) / len(results) * 100
    
    for odds_range, results in patterns['win_rate_by_odds_range'].items():
        if results:
            patterns['win_rate_by_odds_range'][odds_range] = sum(results) / len(results) * 100
    
    # Determine risk profile
    aggressive_bets = patterns['stake_patterns']['aggressive']
    total_bets = len(bet_history)
    high_odds_bets = patterns['favorite_odds_range']['high']
    
    if aggressive_bets / total_bets > 0.4 or high_odds_bets / total_bets > 0.5:
        patterns['risk_profile'] = 'aggressive'
    elif aggressive_bets / total_bets < 0.1 and high_odds_bets / total_bets < 0.2:
        patterns['risk_profile'] = 'conservative'
    else:
        patterns['risk_profile'] = 'moderate'
    
    return patterns

def generate_personal_recommendations(user_id: str, patterns: Dict, current_predictions: List[Dict]) -> Dict:
    """Generate personalized recommendations based on user patterns"""
    if not patterns or 'error' in patterns:
        return {
            'recommendations': [],
            'message': 'Insufficient data for personalization. Place more bets to unlock AI recommendations!'
        }
    
    recommendations = []
    
    # Favorite market recommendations
    favorite_markets = patterns.get('favorite_markets', {})
    if favorite_markets:
        top_market = max(favorite_markets.items(), key=lambda x: x[1])[0]
        
        for pred in current_predictions:
            if pred.get('market') == top_market:
                recommendations.append({
                    'type': 'market_preference',
                    'match': pred.get('match'),
                    'market': pred.get('market'),
                    'selection': pred.get('selection'),
                    'odds': pred.get('odds'),
                    'reason': f'Matches your favorite market: {top_market}',
                    'confidence': 'high',
                    'priority': 1
                })
    
    # Odds range preferences
    win_rates_by_odds = patterns.get('win_rate_by_odds_range', {})
    best_odds_range = None
    best_win_rate = 0
    
    for odds_range, win_rate in win_rates_by_odds.items():
        if win_rate > best_win_rate and win_rate > 55:  # Only if above 55%
            best_win_rate = win_rate
            best_odds_range = odds_range
    
    if best_odds_range:
        odds_ranges = {
            'low': (1.0, 1.8),
            'medium': (1.8, 2.5),
            'high': (2.5, 10.0)
        }
        
        min_odds, max_odds = odds_ranges.get(best_odds_range, (1.0, 10.0))
        
        for pred in current_predictions:
            odds = pred.get('odds', 0)
            if min_odds <= odds < max_odds:
                recommendations.append({
                    'type': 'odds_preference',
                    'match': pred.get('match'),
                    'market': pred.get('market'),
                    'selection': pred.get('selection'),
                    'odds': odds,
                    'reason': f'Odds range where you win {best_win_rate:.1f}% of the time',
                    'confidence': 'high',
                    'priority': 2
                })
    
    # Risk profile based recommendations
    risk_profile = patterns.get('risk_profile', 'moderate')
    
    for pred in current_predictions:
        ev = pred.get('expected_value', 0)
        prob = pred.get('probability', 0)
        
        if risk_profile == 'conservative' and prob > 0.6 and ev > 3:
            recommendations.append({
                'type': 'risk_match',
                'match': pred.get('match'),
                'market': pred.get('market'),
                'selection': pred.get('selection'),
                'odds': pred.get('odds'),
                'reason': 'High-probability pick matching your conservative style',
                'confidence': 'high',
                'priority': 1
            })
        elif risk_profile == 'aggressive' and ev > 8:
            recommendations.append({
                'type': 'risk_match',
                'match': pred.get('match'),
                'market': pred.get('market'),
                'selection': pred.get('selection'),
                'odds': pred.get('odds'),
                'reason': 'High-value pick matching your aggressive style',
                'confidence': 'medium',
                'priority': 2
            })
    
    # Sort by priority and confidence
    recommendations.sort(key=lambda x: (x['priority'], {'high': 3, 'medium': 2, 'low': 1}[x['confidence']]))
    
    return {
        'recommendations': recommendations[:5],  # Top 5 recommendations
        'risk_profile': risk_profile,
        'insights': generate_insights(patterns),
        'total_found': len(recommendations)
    }

def generate_insights(patterns: Dict) -> List[str]:
    """Generate insights about user's betting behavior"""
    insights = []
    
    # Market insights
    favorite_markets = patterns.get('favorite_markets', {})
    if favorite_markets:
        top_market = max(favorite_markets.items(), key=lambda x: x[1])[0]
        market_count = favorite_markets[top_market]
        total_bets = sum(favorite_markets.values())
        percentage = (market_count / total_bets) * 100
        
        insights.append(f"📊 Preferi piața {top_market} ({percentage:.1f}% din pariuri)")
    
    # Win rate insights
    win_rates = patterns.get('win_rate_by_market', {})
    if win_rates:
        best_market = max(win_rates.items(), key=lambda x: x[1])
        worst_market = min(win_rates.items(), key=lambda x: x[1])
        
        insights.append(f"🏆 Cea mai bună piață: {best_market[0]} ({best_market[1]:.1f}% win rate)")
        if worst_market[1] < 40:
            insights.append(f"⚠️ Evită piața {worst_market[0]} (doar {worst_market[1]:.1f}% win rate)")
    
    # Odds insights
    odds_win_rates = patterns.get('win_rate_by_odds_range', {})
    if odds_win_rates:
        best_odds_range = max(odds_win_rates.items(), key=lambda x: x[1])
        range_names = {'low': 'cote mici (1.0-1.8)', 'medium': 'cote medii (1.8-2.5)', 'high': 'cote mari (2.5+)'}
        
        insights.append(f"💰 Performezi cel mai bine la {range_names.get(best_odds_range[0])} - {best_odds_range[1]:.1f}% win rate")
    
    # Risk profile insights
    risk_profile = patterns.get('risk_profile', 'moderate')
    risk_messages = {
        'conservative': '🛡️ Profil conservator - preferi siguranța la profit',
        'moderate': '⚖️ Profil moderat - balans bun între risc și recompensă',
        'aggressive': '🚀 Profil agresiv - cauți value bets cu risc mare'
    }
    insights.append(risk_messages.get(risk_profile))
    
    # Time insights
    time_prefs = patterns.get('time_preferences', {})
    if time_prefs:
        best_time = max(time_prefs.items(), key=lambda x: x[1])[0]
        time_names = {'morning': 'dimineața', 'afternoon': 'după-amiaza', 'evening': 'seara', 'night': 'noaptea'}
        insights.append(f"🕐 Pariezi cel mai des {time_names.get(best_time)}")
    
    return insights

def adaptive_odds_evaluation(user_id: str, prediction: Dict, user_patterns: Dict) -> Dict:
    """Adapt prediction evaluation based on user's historical performance"""
    if not user_patterns or 'error' in user_patterns:
        return prediction
    
    market = prediction.get('market')
    odds = prediction.get('odds', 1.0)
    base_probability = prediction.get('probability', 0.5)
    
    # Adjust based on user's performance in this market
    win_rates_by_market = user_patterns.get('win_rate_by_market', {})
    user_market_wr = win_rates_by_market.get(market, 50) / 100  # Default 50%
    
    # Adjust based on odds range performance
    odds_ranges = {
        'low': (1.0, 1.8),
        'medium': (1.8, 2.5), 
        'high': (2.5, 10.0)
    }
    
    odds_range = None
    for range_name, (min_odds, max_odds) in odds_ranges.items():
        if min_odds <= odds < max_odds:
            odds_range = range_name
            break
    
    win_rates_by_odds = user_patterns.get('win_rate_by_odds_range', {})
    user_odds_wr = win_rates_by_odds.get(odds_range, 50) / 100 if odds_range else 0.5
    
    # Weighted adjustment (70% base prediction, 20% market performance, 10% odds performance)
    adjusted_probability = (0.7 * base_probability + 0.2 * user_market_wr + 0.1 * user_odds_wr)
    
    # Ensure probability stays within reasonable bounds
    adjusted_probability = max(0.1, min(0.9, adjusted_probability))
    
    # Recalculate expected value
    implied_prob = 1 / odds
    adjusted_ev = (adjusted_probability * odds - 1) * 100
    
    adapted_prediction = prediction.copy()
    adapted_prediction.update({
        'original_probability': base_probability,
        'adjusted_probability': adjusted_probability,
        'probability': adjusted_probability,  # Update main probability
        'original_ev': prediction.get('expected_value', 0),
        'adjusted_ev': adjusted_ev,
        'expected_value': adjusted_ev,  # Update main EV
        'personalization_factor': {
            'market_performance': user_market_wr,
            'odds_performance': user_odds_wr,
            'adjustment_made': abs(adjusted_probability - base_probability) > 0.05
        }
    })
    
    return adapted_prediction

def get_strategy_recommendation(user_patterns: Dict, bankroll: float = 1000) -> Dict:
    """Get personalized strategy recommendation"""
    if not user_patterns or 'error' in user_patterns:
        return {
            'strategy': 'basic',
            'description': 'Start with basic betting until we learn your patterns!'
        }
    
    risk_profile = user_patterns.get('risk_profile', 'moderate')
    win_rates = user_patterns.get('win_rate_by_market', {})
    favorite_markets = user_patterns.get('favorite_markets', {})
    
    # Calculate overall win rate
    all_results = []
    for market_results in win_rates.values():
        if isinstance(market_results, list):
            all_results.extend(market_results)
    
    overall_wr = sum(all_results) / len(all_results) * 100 if all_results else 50
    
    strategies = {
        'conservative_value': {
            'name': 'Conservative Value Betting',
            'description': 'Focus on high-probability bets with positive EV',
            'criteria': 'Conservative profile + good win rate',
            'stake_percentage': 2,
            'min_probability': 60,
            'min_ev': 3
        },
        'moderate_mixed': {
            'name': 'Moderate Mixed Strategy',
            'description': 'Balanced approach across different markets',
            'criteria': 'Moderate profile',
            'stake_percentage': 3,
            'min_probability': 50,
            'min_ev': 2
        },
        'aggressive_value': {
            'name': 'Aggressive Value Hunting', 
            'description': 'Target high-EV bets with calculated risks',
            'criteria': 'Aggressive profile',
            'stake_percentage': 5,
            'min_probability': 40,
            'min_ev': 8
        }
    }
    
    # Select strategy based on profile and performance
    if risk_profile == 'conservative' and overall_wr >= 55:
        recommended_strategy = strategies['conservative_value']
    elif risk_profile == 'aggressive' and len(favorite_markets) >= 3:
        recommended_strategy = strategies['aggressive_value']
    else:
        recommended_strategy = strategies['moderate_mixed']
    
    # Calculate recommended stakes
    recommended_strategy['stake_amount'] = bankroll * (recommended_strategy['stake_percentage'] / 100)
    recommended_strategy['daily_budget'] = recommended_strategy['stake_amount'] * 3  # Max 3 bets per day
    
    return {
        'recommended_strategy': recommended_strategy,
        'rationale': f"Based on your {risk_profile} profile and {overall_wr:.1f}% win rate",
        'customizations': generate_strategy_customizations(user_patterns)
    }

def generate_strategy_customizations(patterns: Dict) -> List[str]:
    """Generate specific strategy customizations"""
    customizations = []
    
    # Market focus
    favorite_markets = patterns.get('favorite_markets', {})
    if favorite_markets:
        top_market = max(favorite_markets.items(), key=lambda x: x[1])[0]
        customizations.append(f"Focus 60% of bets on {top_market} market")
    
    # Time optimization
    time_prefs = patterns.get('time_preferences', {})
    if time_prefs:
        best_time = max(time_prefs.items(), key=lambda x: x[1])[0]
        customizations.append(f"Place bets primarily in the {best_time}")
    
    # Odds range optimization
    win_rates_by_odds = patterns.get('win_rate_by_odds_range', {})
    best_range = max(win_rates_by_odds.items(), key=lambda x: x[1])[0] if win_rates_by_odds else None
    
    if best_range:
        range_descriptions = {
            'low': 'lower odds (1.0-1.8)',
            'medium': 'medium odds (1.8-2.5)', 
            'high': 'higher odds (2.5+)'
        }
        customizations.append(f"Prioritize {range_descriptions[best_range]} where you excel")
    
    return customizations