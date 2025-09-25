
from __future__ import annotations
import numpy as np
from typing import List, Dict

def greedy_highprob(picks: List[Dict], min_odds: float=2.0, max_odds: float=4.0, max_legs:int=3):
    """
    picks: [{match, selection, p_est, odds}]
    return: dict cu legs_detail, prob, odds, ev
    """
    picks = sorted(picks, key=lambda x: (x["p_est"], x.get("ev",0)), reverse=True)
    best=None
    combo=[]
    prod_odds=1.0
    for r in picks:
        if len(combo)>=max_legs: break
        # dacă odds lipsesc, approximăm 1/p
        o = float(r.get("odds", max(1.01, 1.0/max(r["p_est"],1e-6))))
        new = prod_odds*o
        if new <= max_odds or prod_odds < min_odds:
            combo.append(r)
            prod_odds = new
        if prod_odds >= min_odds and len(combo)>=2:
            prob = float(np.prod([x["p_est"] for x in combo]))
            ev = prob*prod_odds - 1.0
            cand = {"legs_detail": combo[:], "prob": prob, "odds": prod_odds, "ev": ev, "legs": len(combo)}
            if best is None or cand["prob"]>best["prob"]:
                best = cand
    if best is None and len(picks)>=2:
        sub = picks[:min(max_legs,2)]
        prod = float(np.prod([x.get("odds", max(1.01,1.0/max(x["p_est"],1e-6))) for x in sub]))
        prob = float(np.prod([x["p_est"] for x in sub]))
        best = {"legs_detail": sub, "prob": prob, "odds": prod, "ev": prob*prod-1.0, "legs": len(sub)}
    return best
