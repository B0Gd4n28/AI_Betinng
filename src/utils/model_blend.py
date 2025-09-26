"""
Model blending system for enhanced predictions
Integrates local ML models with existing form and odds-based predictions
"""
import os
import joblib
import logging
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import sys

# Add project root to path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

logger = logging.getLogger(__name__)

class ModelBlender:
    """
    Blends predictions from multiple sources including trained ML models
    """
    
    def __init__(self, model_path: str = "model/model.joblib"):
        self.model_path = Path(model_path)
        self.model = None
        self.model_available = False
        self._load_model()
    
    def _load_model(self) -> None:
        """Load trained model if available"""
        try:
            if self.model_path.exists():
                self.model = joblib.load(self.model_path)
                self.model_available = True
                logger.info(f"Loaded ML model from {self.model_path}")
            else:
                logger.info("No trained model found - using form and odds only")
                
        except Exception as e:
            logger.error(f"Failed to load model: {str(e)}")
            self.model_available = False
    
    def blend_prediction(self, base_prediction: Dict[str, Any], 
                        match_features: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Blend base prediction with ML model prediction if available
        
        Args:
            base_prediction: Original prediction with p_est, odds, etc.
            match_features: Match features for ML model (optional)
            
        Returns:
            dict: Enhanced prediction with blended probability
        """
        if not self.model_available or not match_features:
            # Return original prediction if no model or features
            return base_prediction
        
        try:
            # Get ML model prediction
            ml_prob = self._predict_with_model(match_features, base_prediction.get('market', '1X2'))
            
            if ml_prob is not None:
                # Blend predictions: 80% original, 20% ML model
                original_prob = base_prediction.get('p_est', 0.5)
                blended_prob = 0.8 * original_prob + 0.2 * ml_prob
                
                # Update prediction with blended probability
                enhanced_prediction = base_prediction.copy()
                enhanced_prediction['p_est'] = blended_prob
                
                # Recalculate EV with new probability
                odds = base_prediction.get('odds', 1.0)
                enhanced_prediction['ev'] = (blended_prob * odds) - 1.0
                
                # Add metadata about blending
                extras = enhanced_prediction.get('extras', {})
                if isinstance(extras, dict):
                    extras['ml_enhanced'] = True
                    extras['original_p'] = original_prob
                    extras['ml_p'] = ml_prob
                    enhanced_prediction['extras'] = extras
                
                return enhanced_prediction
            
        except Exception as e:
            logger.error(f"Error in model blending: {str(e)}")
        
        # Fallback to original prediction
        return base_prediction
    
    def _predict_with_model(self, features: Dict[str, Any], market: str) -> Optional[float]:
        """
        Make prediction using trained ML model
        
        Args:
            features: Match features dictionary
            market: Market type (1X2, O/U 2.5, BTTS)
            
        Returns:
            float: Model probability prediction or None if failed
        """
        try:
            if not self.model:
                return None
            
            # Convert features to model input format
            feature_vector = self._extract_feature_vector(features, market)
            
            if feature_vector is None:
                return None
            
            # Make prediction
            if hasattr(self.model, 'predict_proba'):
                # Classification model - get probability for positive class
                probabilities = self.model.predict_proba([feature_vector])
                return float(probabilities[0][1])  # Assuming binary classification
            elif hasattr(self.model, 'predict'):
                # Regression model - direct probability prediction
                prediction = self.model.predict([feature_vector])
                return float(np.clip(prediction[0], 0.0, 1.0))
            else:
                logger.warning("Model has no predict or predict_proba method")
                return None
                
        except Exception as e:
            logger.error(f"Model prediction failed: {str(e)}")
            return None
    
    def _extract_feature_vector(self, features: Dict[str, Any], market: str) -> Optional[List[float]]:
        """
        Extract numerical feature vector from match features dictionary
        
        This is a simplified feature extraction - in practice you'd want more sophisticated
        feature engineering based on your specific model training pipeline.
        """
        try:
            vector = []
            
            # Team form features (basic example)
            home_form = features.get('home_form_points', 1.5)
            away_form = features.get('away_form_points', 1.5)
            vector.extend([home_form, away_form])
            
            # Goals averages if available
            home_goals_avg = features.get('home_goals_avg', 1.5)
            away_goals_avg = features.get('away_goals_avg', 1.3)
            home_concede_avg = features.get('home_concede_avg', 1.2)
            away_concede_avg = features.get('away_concede_avg', 1.2)
            vector.extend([home_goals_avg, away_goals_avg, home_concede_avg, away_concede_avg])
            
            # Weather features (if available)
            temperature = features.get('temperature', 15.0)  # Default 15°C
            wind_speed = features.get('wind_speed', 0.0)
            precipitation = features.get('precipitation_prob', 0.0)
            vector.extend([temperature, wind_speed, precipitation])
            
            # Sentiment features (if available) 
            sentiment_score = features.get('sentiment_score', 0.0)  # -1 to 1
            vector.append(sentiment_score)
            
            # Market-specific features
            if market == 'O/U 2.5':
                estimated_goals = (home_goals_avg + away_goals_avg + home_concede_avg + away_concede_avg) / 2
                vector.append(estimated_goals)
            elif market == 'BTTS':
                btts_prob_est = min(0.8, max(0.2, (home_goals_avg * away_concede_avg + away_goals_avg * home_concede_avg) / 4))
                vector.append(btts_prob_est)
            else:  # 1X2
                form_diff = home_form - away_form
                vector.append(form_diff)
            
            return vector
            
        except Exception as e:
            logger.error(f"Feature extraction failed: {str(e)}")
            return None
    
    def batch_blend_predictions(self, predictions: List[Dict[str, Any]], 
                              match_features_list: List[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Blend multiple predictions at once"""
        if not match_features_list:
            match_features_list = [None] * len(predictions)
        
        enhanced_predictions = []
        
        for prediction, features in zip(predictions, match_features_list):
            enhanced = self.blend_prediction(prediction, features)
            enhanced_predictions.append(enhanced)
        
        return enhanced_predictions
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about loaded model"""
        if not self.model_available:
            return {"available": False, "path": str(self.model_path)}
        
        info = {
            "available": True,
            "path": str(self.model_path),
            "type": type(self.model).__name__
        }
        
        # Add model-specific info if available
        if hasattr(self.model, 'n_features_in_'):
            info["features_count"] = self.model.n_features_in_
        
        if hasattr(self.model, 'classes_'):
            info["classes"] = list(self.model.classes_)
        
        return info


# Global model blender instance
model_blender = ModelBlender()

# Convenience functions
def blend_prediction(prediction: Dict[str, Any], match_features: Dict[str, Any] = None) -> Dict[str, Any]:
    """Blend a single prediction with ML model if available"""
    return model_blender.blend_prediction(prediction, match_features)

def batch_blend_predictions(predictions: List[Dict[str, Any]], 
                          match_features_list: List[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """Blend multiple predictions with ML models if available"""
    return model_blender.batch_blend_predictions(predictions, match_features_list)