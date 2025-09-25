
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Tuple, Dict, Any
import math, joblib, numpy as np


@dataclass
class AgentConfig:
    use_model: bool = True
    model_path: str = "model/model.joblib"
    blend_w_odds: float = 0.8
    blend_w_model: float = 0.2  # Weight for model predictions when available


class ForecastAgent:
    """
    Enhanced forecast agent supporting multiple betting markets.
    Supports H2H (1X2), Over/Under totals, and Both Teams To Score predictions.
    """
    
    def __init__(self, cfg: AgentConfig):
        self.cfg = cfg
        self.model = None
        if self.cfg.use_model:
            try:
                self.model = joblib.load(self.cfg.model_path)
            except Exception:
                self.model = None

    def predict_h2h(self, features: Dict[str, Any], odds_triplet: Optional[Tuple[float,float,float]], 
                    form_triplet: Tuple[float,float,float]) -> Tuple[float, float, float]:
        """
        Predict Home/Draw/Away probabilities for H2H (1X2) market.
        
        Args:
            features: Feature dictionary from extract_h2h_features()
            odds_triplet: (p_home, p_draw, p_away) from odds (after margin removal)
            form_triplet: (p_home, p_draw, p_away) from team form
            
        Returns:
            Normalized (p_home, p_draw, p_away) probabilities
        """
        # Convert features to vector if model exists
        feats = None
        if self.model is not None:
            from src.ai.features_markets import create_feature_vector
            feats = np.array(create_feature_vector(features))
        
        return self._predict_triplet(feats, odds_triplet, form_triplet)
    
    def predict_totals(self, features: Dict[str, Any], odds_pair: Optional[Tuple[float,float]], 
                      form_based_over_prob: float = 0.5) -> Tuple[float, float]:
        """
        Predict Over/Under probabilities for totals market.
        
        Args:
            features: Feature dictionary from extract_totals_features()
            odds_pair: (p_over, p_under) from odds (after margin removal)
            form_based_over_prob: Estimated Over probability from team form
            
        Returns:
            Normalized (p_over, p_under) probabilities
        """
        form_pair = (form_based_over_prob, 1.0 - form_based_over_prob)
        
        # Model prediction if available
        model_pair = None
        if self.model is not None:
            try:
                from src.ai.features_markets import create_feature_vector
                feats = np.array(create_feature_vector(features)).reshape(1, -1)
                # Assuming model can predict binary outcomes for totals
                pr = self.model.predict_proba(feats)[0]
                if len(pr) >= 2:
                    model_pair = (float(pr[0]), float(pr[1]))
            except Exception:
                model_pair = None

        # Blend predictions
        if odds_pair and form_pair:
            # Odds + form blend
            p = (self.cfg.blend_w_odds * odds_pair[0] + (1 - self.cfg.blend_w_odds) * form_pair[0],
                 self.cfg.blend_w_odds * odds_pair[1] + (1 - self.cfg.blend_w_odds) * form_pair[1])
        elif odds_pair:
            p = odds_pair
        else:
            p = form_pair

        # Blend with model if exists
        if model_pair:
            w = self.cfg.blend_w_model
            p = ((1 - w) * p[0] + w * model_pair[0], (1 - w) * p[1] + w * model_pair[1])

        # Normalize
        s = sum(p)
        return (p[0] / s, p[1] / s)
    
    def predict_btts(self, features: Dict[str, Any], odds_pair: Optional[Tuple[float,float]], 
                     form_based_yes_prob: float = 0.5) -> Tuple[float, float]:
        """
        Predict Yes/No probabilities for Both Teams To Score market.
        
        Args:
            features: Feature dictionary from extract_btts_features()
            odds_pair: (p_yes, p_no) from odds (after margin removal)
            form_based_yes_prob: Estimated Yes probability from team form
            
        Returns:
            Normalized (p_yes, p_no) probabilities
        """
        form_pair = (form_based_yes_prob, 1.0 - form_based_yes_prob)
        
        # Model prediction if available (similar to totals)
        model_pair = None
        if self.model is not None:
            try:
                from src.ai.features_markets import create_feature_vector
                feats = np.array(create_feature_vector(features)).reshape(1, -1)
                pr = self.model.predict_proba(feats)[0]
                if len(pr) >= 2:
                    model_pair = (float(pr[0]), float(pr[1]))
            except Exception:
                model_pair = None

        # Blend predictions
        if odds_pair and form_pair:
            p = (self.cfg.blend_w_odds * odds_pair[0] + (1 - self.cfg.blend_w_odds) * form_pair[0],
                 self.cfg.blend_w_odds * odds_pair[1] + (1 - self.cfg.blend_w_odds) * form_pair[1])
        elif odds_pair:
            p = odds_pair
        else:
            p = form_pair

        # Blend with model if exists
        if model_pair:
            w = self.cfg.blend_w_model
            p = ((1 - w) * p[0] + w * model_pair[0], (1 - w) * p[1] + w * model_pair[1])

        # Normalize
        s = sum(p)
        return (p[0] / s, p[1] / s)

    def predict_triplet(self, feats: np.ndarray, odds_triplet: Optional[Tuple[float,float,float]], 
                       form_triplet: Tuple[float,float,float]) -> Tuple[float, float, float]:
        """Legacy method for backward compatibility"""
        return self._predict_triplet(feats, odds_triplet, form_triplet)
    
    def _predict_triplet(self, feats: Optional[np.ndarray], odds_triplet: Optional[Tuple[float,float,float]], 
                        form_triplet: Tuple[float,float,float]) -> Tuple[float, float, float]:
        """
        Internal method for H2H triplet prediction.
        
        Args:
            feats: feature vector for ML model (if available)
            odds_triplet: (pH,pD,pA) derived from odds (after margin removal)  
            form_triplet: (pH,pD,pA) from team form
            
        Returns:
            Normalized (p_home, p_draw, p_away) probabilities
        """
        # Model prediction if available
        pm = None
        if self.model is not None and feats is not None:
            try:
                pr = self.model.predict_proba(feats.reshape(1, -1))[0]
                if len(pr) >= 3:
                    pm = (float(pr[0]), float(pr[1]), float(pr[2]))
            except Exception:
                pm = None

        # Choose source of truth for base prediction
        if odds_triplet and form_triplet:
            # Odds + form blend
            po = odds_triplet
            pf = form_triplet
            p = (self.cfg.blend_w_odds * po[0] + (1 - self.cfg.blend_w_odds) * pf[0],
                 self.cfg.blend_w_odds * po[1] + (1 - self.cfg.blend_w_odds) * pf[1],
                 self.cfg.blend_w_odds * po[2] + (1 - self.cfg.blend_w_odds) * pf[2])
        elif odds_triplet:
            p = odds_triplet
        else:
            p = form_triplet

        # Blend with model if exists
        if pm:
            w = self.cfg.blend_w_model
            p = ((1 - w) * p[0] + w * pm[0], (1 - w) * p[1] + w * pm[1], (1 - w) * p[2] + w * pm[2])

        # Normalize to handle small numeric drift
        s = sum(p)
        return (p[0] / s, p[1] / s, p[2] / s)
