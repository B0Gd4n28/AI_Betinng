"""
🎯 Advanced Betting Strategies
Arbitrage, Value Betting, Hedging, Risk Management
"""

from typing import Dict, List, Tuple, Optional
import math
from collections import defaultdict

def detect_arbitrage_opportunities(matches_odds: List[Dict]) -> List[Dict]:
    """Detect arbitrage opportunities across bookmakers"""
    arb_opportunities = []
    
    for match in matches_odds:
        home_odds = []
        draw_odds = []
        away_odds = []
        
        # Collect odds from different bookmakers
        for bookmaker in match.get('bookmakers', []):
            for market in bookmaker.get('markets', []):
                if market.get('key') == 'h2h':
                    outcomes = market.get('outcomes', [])
                    for outcome in outcomes:
                        if outcome.get('name') == match.get('home_team'):
                            home_odds.append(outcome.get('price', 1.0))
                        elif outcome.get('name') == match.get('away_team'):
                            away_odds.append(outcome.get('price', 1.0))
                        elif outcome.get('name') == 'Draw':
                            draw_odds.append(outcome.get('price', 1.0))
        
        if home_odds and draw_odds and away_odds:
            # Find best odds for each outcome
            best_home = max(home_odds)
            best_draw = max(draw_odds)
            best_away = max(away_odds)
            
            # Calculate arbitrage
            arb_percentage = (1/best_home + 1/best_draw + 1/best_away) * 100
            
            if arb_percentage < 100:
                profit_margin = 100 - arb_percentage
                
                # Calculate optimal stakes for 1000 RON
                total_stake = 1000
                stake_home = (total_stake / best_home) / (1/best_home + 1/best_draw + 1/best_away)
                stake_draw = (total_stake / best_draw) / (1/best_home + 1/best_draw + 1/best_away)
                stake_away = (total_stake / best_away) / (1/best_home + 1/best_draw + 1/best_away)
                
                guaranteed_profit = total_stake * (profit_margin / 100)
                
                arb_opportunities.append({
                    'match': f"{match.get('home_team')} vs {match.get('away_team')}",
                    'profit_margin': profit_margin,
                    'guaranteed_profit': guaranteed_profit,
                    'total_stake': total_stake,
                    'stakes': {
                        'home': {'odds': best_home, 'stake': stake_home},
                        'draw': {'odds': best_draw, 'stake': stake_draw},
                        'away': {'odds': best_away, 'stake': stake_away}
                    }
                })
    
    # Sort by profit margin (highest first)
    return sorted(arb_opportunities, key=lambda x: x['profit_margin'], reverse=True)

def find_value_bets(matches_predictions: List[Dict], min_ev: float = 5.0) -> List[Dict]:
    """Find value bets with positive expected value"""
    value_bets = []
    
    for match in matches_predictions:
        predictions = match.get('predictions', {})
        odds = match.get('odds', {})
        
        for market, pred_data in predictions.items():
            if market in odds:
                market_odds = odds[market]
                market_probs = pred_data.get('probabilities', {})
                
                for outcome, prob in market_probs.items():
                    if outcome in market_odds:
                        odd = market_odds[outcome]
                        implied_prob = (1 / odd) * 100
                        our_prob = prob * 100
                        
                        if our_prob > implied_prob:
                            ev = ((our_prob / 100 * odd) - 1) * 100
                            
                            if ev >= min_ev:
                                value_bets.append({
                                    'match': match.get('match_name'),
                                    'market': market,
                                    'outcome': outcome,
                                    'odds': odd,
                                    'our_probability': our_prob,
                                    'implied_probability': implied_prob,
                                    'expected_value': ev,
                                    'confidence': pred_data.get('confidence', 'medium'),
                                    'suggested_stake_pct': min(5.0, ev / 2)  # Conservative Kelly
                                })
    
    return sorted(value_bets, key=lambda x: x['expected_value'], reverse=True)

def build_accumulator(picks: List[Dict], max_legs: int = 5, min_total_odds: float = 3.0) -> Dict:
    """Build optimized accumulator with risk analysis"""
    if not picks or len(picks) < 2:
        return {'error': 'Need at least 2 picks for accumulator'}
    
    # Sort picks by probability (highest first) for better success chance
    sorted_picks = sorted(picks, key=lambda x: x.get('probability', 0), reverse=True)
    
    best_combinations = []
    
    # Try different combinations
    for num_legs in range(2, min(max_legs + 1, len(sorted_picks) + 1)):
        for i in range(len(sorted_picks) - num_legs + 1):
            combination_picks = sorted_picks[i:i + num_legs]
            
            # Calculate combined probability and odds
            combined_prob = 1.0
            combined_odds = 1.0
            
            for pick in combination_picks:
                combined_prob *= pick.get('probability', 0.5)
                combined_odds *= pick.get('odds', 1.0)
            
            if combined_odds >= min_total_odds:
                # Risk analysis
                individual_probs = [p.get('probability', 0.5) for p in combination_picks]
                variance = sum([(p - combined_prob)**2 for p in individual_probs]) / len(individual_probs)
                
                best_combinations.append({
                    'legs': num_legs,
                    'picks': combination_picks,
                    'combined_probability': combined_prob,
                    'combined_odds': combined_odds,
                    'expected_value': (combined_prob * combined_odds - 1) * 100,
                    'variance': variance,
                    'risk_level': 'low' if variance < 0.1 else 'medium' if variance < 0.2 else 'high'
                })
    
    if not best_combinations:
        return {'error': 'No suitable combinations found'}
    
    # Return best combination by EV
    best = max(best_combinations, key=lambda x: x['expected_value'])
    
    return {
        'recommended_combination': best,
        'all_combinations': sorted(best_combinations, key=lambda x: x['expected_value'], reverse=True)[:3],
        'risk_analysis': {
            'success_probability': best['combined_probability'] * 100,
            'failure_probability': (1 - best['combined_probability']) * 100,
            'breakeven_probability': (1 / best['combined_odds']) * 100,
            'edge': (best['combined_probability'] - 1/best['combined_odds']) * 100
        }
    }

def calculate_hedge_bet(original_bet: Dict, current_odds: Dict) -> Dict:
    """Calculate optimal hedge bet to guarantee profit"""
    original_stake = original_bet.get('stake', 0)
    original_odds = original_bet.get('odds', 1.0)
    original_outcome = original_bet.get('outcome')
    
    potential_win = original_stake * original_odds
    
    # Find best opposing odds
    opposing_outcomes = [k for k in current_odds.keys() if k != original_outcome]
    
    if not opposing_outcomes:
        return {'error': 'No opposing outcomes available'}
    
    best_opposing_outcome = max(opposing_outcomes, key=lambda x: current_odds.get(x, 1.0))
    best_opposing_odds = current_odds[best_opposing_outcome]
    
    # Calculate hedge stake for guaranteed profit
    # We want: original_win - hedge_stake = hedge_stake * hedge_odds - original_stake
    # Solving: hedge_stake = (potential_win - original_stake) / (hedge_odds + 1)
    
    hedge_stake = (potential_win - original_stake) / (best_opposing_odds + 1)
    
    if hedge_stake <= 0:
        return {'error': 'No profitable hedge available'}
    
    # Calculate guaranteed profit
    scenario1_profit = potential_win - original_stake - hedge_stake  # Original bet wins
    scenario2_profit = (hedge_stake * best_opposing_odds) - original_stake - hedge_stake  # Hedge wins
    
    guaranteed_profit = min(scenario1_profit, scenario2_profit)
    
    return {
        'hedge_outcome': best_opposing_outcome,
        'hedge_odds': best_opposing_odds,
        'hedge_stake': hedge_stake,
        'guaranteed_profit': guaranteed_profit,
        'profit_margin': (guaranteed_profit / (original_stake + hedge_stake)) * 100,
        'total_risk': original_stake + hedge_stake,
        'scenarios': {
            'original_wins': scenario1_profit,
            'hedge_wins': scenario2_profit
        }
    }

def kelly_criterion_stake(probability: float, odds: float, bankroll: float, 
                         conservative: bool = True) -> Dict:
    """Calculate optimal stake using Kelly Criterion"""
    if probability <= 0 or probability >= 1:
        return {'error': 'Probability must be between 0 and 1'}
    
    if odds <= 1:
        return {'error': 'Odds must be greater than 1'}
    
    # Kelly fraction: f = (bp - q) / b
    # where b = odds - 1, p = probability, q = 1 - p
    b = odds - 1
    p = probability
    q = 1 - p
    
    kelly_fraction = (b * p - q) / b
    
    if kelly_fraction <= 0:
        return {
            'recommendation': 'No bet',
            'reason': 'Negative expected value',
            'kelly_fraction': kelly_fraction
        }
    
    # Conservative Kelly (typically 25-50% of full Kelly)
    if conservative:
        kelly_fraction *= 0.25
    
    # Cap at 5% of bankroll for safety
    kelly_fraction = min(kelly_fraction, 0.05)
    
    optimal_stake = bankroll * kelly_fraction
    
    return {
        'optimal_stake': optimal_stake,
        'kelly_fraction': kelly_fraction,
        'percentage_of_bankroll': kelly_fraction * 100,
        'expected_growth': kelly_fraction * (probability * odds - 1),
        'risk_of_ruin': calculate_risk_of_ruin(kelly_fraction, probability, odds),
        'conservative_mode': conservative
    }

def calculate_risk_of_ruin(kelly_fraction: float, win_prob: float, odds: float) -> float:
    """Calculate approximate risk of ruin"""
    if kelly_fraction <= 0:
        return 0.0
    
    # Simplified risk of ruin calculation
    # This is an approximation for practical use
    edge = win_prob * odds - 1
    if edge <= 0:
        return 100.0
    
    # For Kelly betting with edge, risk of ruin is very low if fraction < full Kelly
    variance = win_prob * (odds - 1)**2 + (1 - win_prob) * (-1)**2
    
    # Approximate using exponential decay based on edge and variance
    risk_factor = (kelly_fraction / edge) * math.sqrt(variance)
    risk_of_ruin = max(0, min(100, 10 * math.exp(-5 / risk_factor)))
    
    return risk_of_ruin

def martingale_protection_check(user_history: List[Dict]) -> Dict:
    """Check for dangerous martingale patterns and warn user"""
    if len(user_history) < 3:
        return {'status': 'safe', 'message': 'Insufficient history for pattern detection'}
    
    recent_bets = user_history[-10:]  # Last 10 bets
    
    # Check for doubling pattern after losses
    doubling_pattern = 0
    consecutive_losses = 0
    
    for i in range(1, len(recent_bets)):
        current_bet = recent_bets[i]
        previous_bet = recent_bets[i-1]
        
        if previous_bet.get('result') == 'lost':
            consecutive_losses += 1
            
            # Check if stake doubled
            current_stake = current_bet.get('stake', 0)
            previous_stake = previous_bet.get('stake', 0)
            
            if previous_stake > 0 and 1.8 <= current_stake / previous_stake <= 2.2:
                doubling_pattern += 1
        else:
            consecutive_losses = 0
    
    # Warning levels
    if doubling_pattern >= 3:
        return {
            'status': 'danger',
            'risk_level': 'high',
            'message': 'ATENȚIE: Pattern martingale detectat! Această strategie poate cauza pierderi masive.',
            'recommendation': 'Folosește Kelly Criterion sau fixed staking în loc de martingale.',
            'consecutive_losses': consecutive_losses,
            'doubling_instances': doubling_pattern
        }
    elif doubling_pattern >= 2:
        return {
            'status': 'warning',
            'risk_level': 'medium', 
            'message': 'Posibil pattern martingale detectat. Fii atent la sizing-ul stakilor.',
            'recommendation': 'Evită dublarea stakilor după pierderi.',
            'consecutive_losses': consecutive_losses,
            'doubling_instances': doubling_pattern
        }
    else:
        return {
            'status': 'safe',
            'risk_level': 'low',
            'message': 'Nu s-au detectat pattern-uri periculoase în betting.',
            'consecutive_losses': consecutive_losses
        }