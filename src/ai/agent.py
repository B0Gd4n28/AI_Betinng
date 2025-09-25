
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Tuple
import math, joblib, numpy as np

@dataclass
class AgentConfig:
    use_model: bool = True
    model_path: str = "model/model.joblib"
    blend_w_odds: float = 0.8

class ForecastAgent:
    def __init__(self, cfg: AgentConfig):
        self.cfg = cfg
        self.model = None
        if self.cfg.use_model:
            try:
                self.model = joblib.load(self.cfg.model_path)
            except Exception:
                self.model = None

    def predict_triplet(self, feats: np.ndarray, odds_triplet: Optional[Tuple[float,float,float]], form_triplet: Tuple[float,float,float]):
        """
        feats: feature vector for ML model (if available). For MVP, ignored unless model is present.
        odds_triplet: (pH,pD,pA) derived from odds (after margin removal)
        form_triplet: (pH,pD,pA) from team form
        """
        # model prediction if available
        pm = None
        if self.model is not None:
            try:
                pr = self.model.predict_proba(feats.reshape(1,-1))[0]
                pm = (float(pr[0]), float(pr[1]), float(pr[2]))
            except Exception:
                pm = None

        # choose source of truth
        if odds_triplet and form_triplet:
            # odds + form blend
            po = odds_triplet
            pf = form_triplet
            p = (self.cfg.blend_w_odds*po[0] + (1-self.cfg.blend_w_odds)*pf[0],
                 self.cfg.blend_w_odds*po[1] + (1-self.cfg.blend_w_odds)*pf[1],
                 self.cfg.blend_w_odds*po[2] + (1-self.cfg.blend_w_odds)*pf[2])
        elif odds_triplet:
            p = odds_triplet
        else:
            p = form_triplet

        # blend with model if exists (small weight initially)
        if pm:
            w = 0.2
            p = ( (1-w)*p[0] + w*pm[0], (1-w)*p[1] + w*pm[1], (1-w)*p[2] + w*pm[2] )

        # normalize small numeric drift
        s = sum(p)
        return (p[0]/s, p[1]/s, p[2]/s)
