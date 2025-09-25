
from __future__ import annotations
import requests, time
from typing import Dict, Any, List

BASE = "https://api.the-odds-api.com/v4"

def get_odds_for_sport(api_key:str, sport_key:str, regions:str="uk,eu", markets:str="h2h")->list[dict]:
    """
    Returnează lista de evenimente cu cote pentru un sport key (ex: soccer_epl).
    markets poate fi "h2h", "totals", "both_teams_to_score" sau combinații separate prin virgulă.
    """
    url = f"{BASE}/sports/{sport_key}/odds"
    params = {"apiKey": api_key, "regions": regions, "markets": markets, "oddsFormat":"decimal", "dateFormat":"iso"}
    r = requests.get(url, params=params, timeout=30)
    if r.status_code!=200:
        return []
    # headers include remaining-requests, used-requests this month
    return r.json(), r.headers

def implied_probs_from_bookmakers(event:dict) -> dict|None:
    """
    Din structura The Odds API (markets h2h), întoarce dict {home, draw, away} probabilități implicite consens (media).
    """
    mkts = [m for m in event.get("bookmakers",[]) for mkt in m.get("markets",[]) if mkt.get("key")=="h2h" for m in [mkt]]
    if not mkts:
        return None
    # fiecare market are outcomes list [{name:'Team A'|'Draw', price:1.85}]
    probs = []
    for m in mkts:
        prices = {o["name"]: float(o["price"]) for o in m.get("outcomes",[]) if "price" in o and "name" in o}
        names = list(prices.keys())
        # trebuie să avem 2-3 outcome-uri
        if not prices: 
            continue
        inv = {k: 1.0/v for k,v in prices.items()}
        s = sum(inv.values())
        # normalizează pentru a scoate marja
        p = {k: inv[k]/s for k in inv}
        probs.append(p)
    if not probs:
        return None
    # agregare simplă
    agg = {}
    for p in probs:
        for k,v in p.items():
            agg.setdefault(k, []).append(v)
    return {k: sum(vs)/len(vs) for k,vs in agg.items()}


def parse_totals_prob(event: dict, target_line: float = 2.5) -> dict | None:
    """
    Extrage probabilități Over/Under din structura The Odds API pentru piața 'totals'.
    Caută linia cea mai apropiată de target_line (default 2.5).
    
    Returns:
        dict: {"Over": p_over, "Under": p_under, "line": line, "odds": {"Over": odds_over, "Under": odds_under}}
        None: dacă nu găsește piața totals sau date valide
    """
    best_market = None
    best_diff = float('inf')
    
    for bookmaker in event.get("bookmakers", []):
        for market in bookmaker.get("markets", []):
            if market.get("key") != "totals":
                continue
                
            # Căutam linia target - poate fi în market-level "point" sau în outcome-level "point"
            market_point = market.get("point")
            
            for outcome in market.get("outcomes", []):
                outcome_point = outcome.get("point", market_point)
                if outcome_point is None:
                    continue
                    
                line_diff = abs(float(outcome_point) - target_line)
                if line_diff < best_diff:
                    best_diff = line_diff
                    best_market = (market, float(outcome_point))
                    break  # Prima linie găsită pentru acest market
    
    if not best_market or best_diff > 0.25:  # Acceptăm diferențe până la 0.25
        return None
        
    market, line = best_market
    
    # Extrageți cotele pentru Over și Under
    odds_data = {}
    for outcome in market.get("outcomes", []):
        name = outcome.get("name", "")
        price = outcome.get("price")
        if name in ["Over", "Under"] and price:
            odds_data[name] = float(price)
    
    if len(odds_data) < 2:
        return None
    
    # Calculează probabilitățile implicite și normalizează (elimină marja)
    implied = {k: 1.0/v for k, v in odds_data.items()}
    total_implied = sum(implied.values())
    probs = {k: implied[k]/total_implied for k in implied}
    
    return {
        "Over": probs.get("Over", 0.0),
        "Under": probs.get("Under", 0.0), 
        "line": line,
        "odds": odds_data
    }


def parse_btts_prob(event: dict) -> dict | None:
    """
    Extrage probabilități Both Teams To Score din structura The Odds API pentru piața 'both_teams_to_score'.
    
    Returns:
        dict: {"Yes": p_yes, "No": p_no, "odds": {"Yes": odds_yes, "No": odds_no}}
        None: dacă nu găsește piața BTTS sau date valide
    """
    for bookmaker in event.get("bookmakers", []):
        for market in bookmaker.get("markets", []):
            if market.get("key") != "both_teams_to_score":
                continue
                
            # Extrageți cotele pentru Yes și No
            odds_data = {}
            for outcome in market.get("outcomes", []):
                name = outcome.get("name", "")
                price = outcome.get("price")
                if name in ["Yes", "No"] and price:
                    odds_data[name] = float(price)
            
            if len(odds_data) < 2:
                continue
            
            # Calculează probabilitățile implicite și normalizează (elimină marja)
            implied = {k: 1.0/v for k, v in odds_data.items()}
            total_implied = sum(implied.values())
            probs = {k: implied[k]/total_implied for k in implied}
            
            return {
                "Yes": probs.get("Yes", 0.0),
                "No": probs.get("No", 0.0),
                "odds": odds_data
            }
    
    return None
