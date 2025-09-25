
from __future__ import annotations
import requests, time
from typing import Dict, Any, List

BASE = "https://api.the-odds-api.com/v4"

def get_odds_for_sport(api_key:str, sport_key:str, regions:str="uk,eu", markets:str="h2h")->list[dict]:
    """
    Returnează lista de evenimente cu cote H2H pentru un sport key (ex: soccer_epl).
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
