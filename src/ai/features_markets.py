"""
Features extraction for different betting markets.
Provides feature builders for machine learning models supporting H2H, Over/Under, and BTTS markets.
"""

from __future__ import annotations
from typing import Dict, List, Any, Tuple, Optional
import numpy as np
from src.fetchers.odds_api import implied_probs_from_bookmakers, parse_totals_prob, parse_btts_prob


def p_from_odds_h2h(event: dict) -> Optional[Tuple[float, float, float]]:
    """
    Extract Home/Draw/Away probabilities from H2H odds.
    
    Args:
        event: The Odds API event with bookmaker data
        
    Returns:
        Tuple of (p_home, p_draw, p_away) or None if no valid odds
    """
    probs = implied_probs_from_bookmakers(event)
    if not probs:
        return None
    
    home_team = event.get("home_team", "")
    away_team = event.get("away_team", "")
    
    # Extract probabilities with fallback to generic names
    p_home = probs.get(home_team, probs.get("Home", 0.33))
    p_draw = probs.get("Draw", probs.get("X", 0.33))
    p_away = probs.get(away_team, probs.get("Away", 0.33))
    
    return (float(p_home), float(p_draw), float(p_away))


def p_from_odds_totals(event: dict, target_line: float = 2.5) -> Optional[Tuple[float, float]]:
    """
    Extract Over/Under probabilities from totals odds.
    
    Args:
        event: The Odds API event with bookmaker data
        target_line: Target line for totals (default 2.5)
        
    Returns:
        Tuple of (p_over, p_under) or None if no valid odds
    """
    totals_data = parse_totals_prob(event, target_line)
    if not totals_data:
        return None
    
    return (float(totals_data["Over"]), float(totals_data["Under"]))


def p_from_odds_btts(event: dict) -> Optional[Tuple[float, float]]:
    """
    Extract BTTS Yes/No probabilities from both teams to score odds.
    
    Args:
        event: The Odds API event with bookmaker data
        
    Returns:
        Tuple of (p_yes, p_no) or None if no valid odds
    """
    btts_data = parse_btts_prob(event)
    if not btts_data:
        return None
    
    return (float(btts_data["Yes"]), float(btts_data["No"]))


def p_from_form(home_form_points: float, away_form_points: float) -> Tuple[float, float, float]:
    """
    Convert team form points to H2H probabilities using existing logic.
    
    Args:
        home_form_points: Home team recent form points (0-3 scale)
        away_form_points: Away team recent form points (0-3 scale)
        
    Returns:
        Tuple of (p_home, p_draw, p_away) normalized probabilities
    """
    from src.analytics.probability import probs_from_form
    
    form_diff = home_form_points - away_form_points
    return probs_from_form(form_diff)


def form_diff_feature(home_form_points: float, away_form_points: float) -> float:
    """
    Simple form difference feature for ML models.
    
    Args:
        home_form_points: Home team recent form points
        away_form_points: Away team recent form points
        
    Returns:
        Form difference (home - away), normalized to [-3, 3] range
    """
    return max(-3.0, min(3.0, home_form_points - away_form_points))


def extract_h2h_features(event: dict, home_form: float, away_form: float) -> Dict[str, float]:
    """
    Extract comprehensive features for H2H (1X2) market prediction.
    
    Args:
        event: The Odds API event (can be None if no odds available)
        home_form: Home team form points
        away_form: Away team form points
        
    Returns:
        Dictionary with feature names and values
    """
    features = {
        "form_diff": form_diff_feature(home_form, away_form),
        "home_form": max(0.0, min(3.0, home_form)),
        "away_form": max(0.0, min(3.0, away_form)),
    }
    
    if event:
        odds_probs = p_from_odds_h2h(event)
        if odds_probs:
            features["odds_p_home"] = odds_probs[0]
            features["odds_p_draw"] = odds_probs[1] 
            features["odds_p_away"] = odds_probs[2]
            features["odds_available"] = 1.0
        else:
            features["odds_p_home"] = 0.33
            features["odds_p_draw"] = 0.33
            features["odds_p_away"] = 0.33
            features["odds_available"] = 0.0
    else:
        features["odds_p_home"] = 0.33
        features["odds_p_draw"] = 0.33
        features["odds_p_away"] = 0.33
        features["odds_available"] = 0.0
        
    return features


def extract_totals_features(event: dict, home_form: float, away_form: float, 
                           target_line: float = 2.5) -> Dict[str, float]:
    """
    Extract features for Over/Under totals market prediction.
    
    Args:
        event: The Odds API event (can be None if no odds available)
        home_form: Home team form points
        away_form: Away team form points
        target_line: Target line for totals
        
    Returns:
        Dictionary with feature names and values
    """
    features = {
        "form_diff": form_diff_feature(home_form, away_form),
        "home_form": max(0.0, min(3.0, home_form)),
        "away_form": max(0.0, min(3.0, away_form)),
        "target_line": target_line,
        "combined_form": (home_form + away_form) / 2.0,  # Higher = more goals expected
    }
    
    if event:
        odds_probs = p_from_odds_totals(event, target_line)
        if odds_probs:
            features["odds_p_over"] = odds_probs[0]
            features["odds_p_under"] = odds_probs[1]
            features["odds_available"] = 1.0
        else:
            features["odds_p_over"] = 0.5
            features["odds_p_under"] = 0.5
            features["odds_available"] = 0.0
    else:
        features["odds_p_over"] = 0.5
        features["odds_p_under"] = 0.5
        features["odds_available"] = 0.0
        
    return features


def extract_btts_features(event: dict, home_form: float, away_form: float) -> Dict[str, float]:
    """
    Extract features for Both Teams To Score market prediction.
    
    Args:
        event: The Odds API event (can be None if no odds available)
        home_form: Home team form points  
        away_form: Away team form points
        
    Returns:
        Dictionary with feature names and values
    """
    features = {
        "form_diff": form_diff_feature(home_form, away_form),
        "home_form": max(0.0, min(3.0, home_form)),
        "away_form": max(0.0, min(3.0, away_form)),
        "min_form": min(home_form, away_form),  # Weakest team affects BTTS
        "balanced_teams": 1.0 - abs(home_form - away_form) / 3.0,  # Balanced teams more likely BTTS
    }
    
    if event:
        odds_probs = p_from_odds_btts(event)
        if odds_probs:
            features["odds_p_yes"] = odds_probs[0]
            features["odds_p_no"] = odds_probs[1]
            features["odds_available"] = 1.0
        else:
            features["odds_p_yes"] = 0.5
            features["odds_p_no"] = 0.5
            features["odds_available"] = 0.0
    else:
        features["odds_p_yes"] = 0.5
        features["odds_p_no"] = 0.5
        features["odds_available"] = 0.0
        
    return features


# Future placeholder for team discipline features (cards, bookings markets)
def extract_discipline_features(event: dict, home_team_id: str, away_team_id: str) -> Dict[str, float]:
    """
    Placeholder for future team discipline features (cards, fouls, bookings).
    Currently returns empty dict - to be implemented when cards market data is available.
    
    Args:
        event: The Odds API event  
        home_team_id: Home team identifier
        away_team_id: Away team identifier
        
    Returns:
        Dictionary with discipline-related features (empty for now)
    """
    # TODO: Implement when cards/bookings market data becomes available
    # Could include: avg_cards_per_game, historical_referee_card_rate, etc.
    return {}


def create_feature_vector(features: Dict[str, float]) -> List[float]:
    """
    Convert feature dictionary to ordered vector for ML models.
    
    Args:
        features: Dictionary of feature name -> value
        
    Returns:
        List of feature values in consistent order
    """
    # Define consistent feature order for ML models
    feature_order = [
        "form_diff", "home_form", "away_form", 
        "odds_available", "odds_p_home", "odds_p_draw", "odds_p_away",
        "odds_p_over", "odds_p_under", "odds_p_yes", "odds_p_no",
        "target_line", "combined_form", "min_form", "balanced_teams"
    ]
    
    return [features.get(name, 0.0) for name in feature_order]