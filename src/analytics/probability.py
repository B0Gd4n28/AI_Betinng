
from __future__ import annotations
import math, numpy as np

def logistic(x): 
    return 1.0/(1.0+math.exp(-x))

def probs_from_form(form_diff: float) -> tuple[float,float,float]:
    """
    Heuristic: forma home - forma away (0..3 puncte pe meci). 
    Mapăm la p_home prin logistic, p_draw mic constant, p_away restul.
    """
    # p_draw ancoră ~0.25 în medie, ușor dependent de echilibru
    p_draw = 0.24 - 0.04*math.tanh(abs(form_diff)/3.0)
    p_home = 0.50 + 0.18*math.tanh(form_diff/2.0)  # 0.32..0.68 approx
    # renormalize
    rest = max(1e-6, 1.0 - p_draw)
    p_home = min(max(1e-6, p_home*(rest)), rest-1e-6)
    p_away = rest - p_home
    return p_home, p_draw, p_away

def blend_probs(odds_p: dict|None, form_p: tuple[float,float,float]|None, home_name:str, away_name:str, w_odds:float=0.8)->tuple[float,float,float]:
    """
    Combina probabilitățile din cote (odds_p) cu cele din formă (form_p).
    """
    # mapare nume la 'home','away','draw'
    def _from_odds(odds_p):
        if odds_p is None: return None
        # Outcomes pot fi 'Draw', 'Team Name' etc.
        keys = list(odds_p.keys())
        pH = odds_p.get(home_name) or odds_p.get("Home") or odds_p.get("1") or 0.0
        pD = odds_p.get("Draw") or odds_p.get("X") or 0.0
        pA = odds_p.get(away_name) or odds_p.get("Away") or odds_p.get("2") or 0.0
        # dacă lipsește unul, încearcă să normalizezi din rest
        s = pH+pD+pA
        if s>0:
            return (pH/s, pD/s, pA/s)
        return None

    po = _from_odds(odds_p)
    pf = form_p
    if po and pf:
        return (w_odds*po[0]+(1-w_odds)*pf[0],
                w_odds*po[1]+(1-w_odds)*pf[1],
                w_odds*po[2]+(1-w_odds)*pf[2])
    if po: return po
    if pf: return pf
    # fallback neutru
    return (0.38, 0.24, 0.38)

def ev_from_probs_odds(p:tuple[float,float,float], odds:tuple[float,float,float])->tuple[float,float,float]:
    return (p[0]*odds[0]-1.0, p[1]*odds[1]-1.0, p[2]*odds[2]-1.0)
