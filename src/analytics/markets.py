"""
Markets analytics module for Over/Under and Both Teams To Score predictions.
Provides utilities for market normalization, EV calculation, and top picks selection.
"""

from __future__ import annotations
from typing import List, Dict, Any, Optional
import random
from src.fetchers.odds_api import parse_totals_prob, parse_btts_prob
from src.utils.matching import teams_match


def pick_best_totals_line(events: List[dict], target_line: float = 2.5) -> List[Dict[str, Any]]:
    """
    Din lista de evenimente The Odds API, selectează cele mai bune linii Over/Under 
    aproape de target_line pentru fiecare meci.
    
    Args:
        events: Lista de evenimente din The Odds API
        target_line: Linia țintă (default 2.5)
        
    Returns:
        Lista de dicționare cu informații despre Over/Under pentru fiecare meci valid
    """
    results = []
    
    for event in events:
        totals_data = parse_totals_prob(event, target_line)
        if not totals_data:
            continue
            
        home_team = event.get("home_team", "")
        away_team = event.get("away_team", "")
        
        if not home_team or not away_team:
            continue
            
        match_name = f"{home_team} vs {away_team}"
        
        # Adaugă rezultate pentru Over și Under
        for selection in ["Over", "Under"]:
            results.append({
                "match": match_name,
                "home_team": home_team,
                "away_team": away_team,
                "market": f"O/U {totals_data['line']}",
                "selection": selection,
                "p_est": totals_data[selection],
                "odds": totals_data["odds"][selection],
                "ev": (totals_data[selection] * totals_data["odds"][selection]) - 1,
                "event": event  # Pentru matching ulterior
            })
    
    return results


def extract_btts_picks(events: List[dict]) -> List[Dict[str, Any]]:
    """
    Din lista de evenimente The Odds API, extrage predicții Both Teams To Score.
    
    Args:
        events: Lista de evenimente din The Odds API
        
    Returns:
        Lista de dicționare cu informații BTTS pentru fiecare meci valid
    """
    results = []
    
    for event in events:
        btts_data = parse_btts_prob(event)
        if not btts_data:
            continue
            
        home_team = event.get("home_team", "")
        away_team = event.get("away_team", "")
        
        if not home_team or not away_team:
            continue
            
        match_name = f"{home_team} vs {away_team}"
        
        # Adaugă rezultate pentru Yes și No
        for selection in ["Yes", "No"]:
            results.append({
                "match": match_name,
                "home_team": home_team,
                "away_team": away_team,
                "market": "BTTS",
                "selection": selection,
                "p_est": btts_data[selection],
                "odds": btts_data["odds"][selection],
                "ev": (btts_data[selection] * btts_data["odds"][selection]) - 1,
                "event": event  # Pentru matching ulterior
            })
    
    return results


def normalize_market_pick(match: str, market_name: str, selection: str, 
                         p_est: float, odds: float) -> Dict[str, Any]:
    """
    Normalizează un pick de market la schema comună.
    
    Args:
        match: Numele meciului (ex: "Arsenal vs Chelsea")
        market_name: Numele pieței (ex: "O/U 2.5", "BTTS")
        selection: Selecția (ex: "Over", "Under", "Yes", "No")
        p_est: Probabilitatea estimată
        odds: Cotele
        
    Returns:
        Dict cu schema normalizată pentru bot
    """
    return {
        "match": match,
        "market": market_name,
        "selection": selection,
        "p_est": round(float(p_est), 3),
        "odds": round(float(odds), 2),
        "ev": round((float(p_est) * float(odds)) - 1, 3)
    }


def top_market_picks_for_date(fixtures: List[dict], odds_events_by_comp: Dict[str, List[dict]], 
                             target_line: float = 2.5, top_n: int = 6) -> List[Dict[str, Any]]:
    """
    Creează lista cu top picks pentru piețele Over/Under și BTTS pentru o dată.
    
    Args:
        fixtures: Lista de meciuri din Football-Data API
        odds_events_by_comp: Dict cu evenimente odds per competiție
        target_line: Linia țintă pentru Over/Under (default 2.5)
        top_n: Câte picks să returneze (default 6)
        
    Returns:
        Lista cu top picks normalizate pentru markets UI
    """
    all_market_picks = []
    
    # Procesează fiecare competiție
    for comp_code, odds_events in odds_events_by_comp.items():
        if not odds_events:
            continue
            
        # Extrage picks Over/Under
        totals_picks = pick_best_totals_line(odds_events, target_line)
        
        # Extrage picks BTTS  
        btts_picks = extract_btts_picks(odds_events)
        
        # Combină toate picks-urile
        comp_picks = totals_picks + btts_picks
        
        # Match cu fixtures pentru a verifica validitatea
        valid_picks = []
        for pick in comp_picks:
            # Caută meciul corespunzător în fixtures
            for fixture in fixtures:
                if (fixture.get("competition") == comp_code and 
                    teams_match(fixture.get("home_name", ""), pick["home_team"]) and
                    teams_match(fixture.get("away_name", ""), pick["away_team"])):
                    
                    # Normalizează pick-ul
                    normalized = normalize_market_pick(
                        pick["match"], pick["market"], pick["selection"],
                        pick["p_est"], pick["odds"]
                    )
                    valid_picks.append(normalized)
                    break
        
        all_market_picks.extend(valid_picks)
    
    # Sortează după EV descendent, apoi după probabilitate
    sorted_picks = sorted(all_market_picks, 
                         key=lambda x: (x["ev"], x["p_est"]), 
                         reverse=True)
    
    return sorted_picks[:top_n]


def seeded_shuffle_picks(picks: List[Dict[str, Any]], user_id: int, date_str: str, 
                        take_n: int) -> List[Dict[str, Any]]:
    """
    Shuffle-uie deterministic picks-urile pe baza user_id și dată, 
    apoi ia primele take_n și le sortează din nou după p_est descendent.
    
    Args:
        picks: Lista de picks
        user_id: ID-ul utilizatorului  
        date_str: Data în format YYYY-MM-DD
        take_n: Câte picks să ia după shuffle
        
    Returns:
        Lista cu take_n picks selectate deterministic și sortate după p_est
    """
    if len(picks) <= take_n:
        return sorted(picks, key=lambda x: x["p_est"], reverse=True)
    
    # Creează RNG deterministic bazat pe user_id și dată
    rng = random.Random(f"{user_id}:{date_str}")
    
    # Copiază lista și o shuffle-uie deterministic
    shuffled = picks.copy()
    rng.shuffle(shuffled)
    
    # Ia primele take_n și le sortează din nou după p_est
    selected = shuffled[:take_n]
    return sorted(selected, key=lambda x: x["p_est"], reverse=True)


def compute_parlay_metrics(legs: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    Calculează metrici pentru un parlay: probabilitate combinată, cote combinate, EV.
    Presupune independența între selecții.
    
    Args:
        legs: Lista de legs ale parlay-ului, fiecare cu 'p_est' și 'odds'
        
    Returns:
        Dict cu 'combined_prob', 'combined_odds', 'ev'
    """
    if not legs:
        return {"combined_prob": 0.0, "combined_odds": 1.0, "ev": -1.0}
    
    # Probabilitatea combinată (produsul probabilităților individuale)
    combined_prob = 1.0
    for leg in legs:
        combined_prob *= leg.get("p_est", 0.0)
    
    # Cotele combinate (produsul cotelor individuale)
    combined_odds = 1.0
    for leg in legs:
        combined_odds *= leg.get("odds", 1.0)
    
    # EV = prob_combinată * cote_combinate - 1
    ev = (combined_prob * combined_odds) - 1.0
    
    return {
        "combined_prob": round(combined_prob, 4),
        "combined_odds": round(combined_odds, 2),
        "ev": round(ev, 4)
    }