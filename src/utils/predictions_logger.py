"""
Predictions logging system for local learning
Logs all predictions made by the bot for later evaluation and model training
"""
import csv
import os
import logging
from datetime import datetime
from typing import Dict, Any, List
from pathlib import Path

logger = logging.getLogger(__name__)

class PredictionsLogger:
    """
    Logs predictions to CSV for later analysis and model training
    """
    
    def __init__(self, log_path: str = "data/predictions.csv"):
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_csv_headers()
    
    def _ensure_csv_headers(self):
        """Ensure CSV file has proper headers"""
        if not self.log_path.exists():
            with open(self.log_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'timestamp',
                    'date', 
                    'match_id',
                    'competition',
                    'home_team',
                    'away_team',
                    'market',
                    'selection',
                    'p_est',
                    'odds',
                    'ev',
                    'source',
                    'user_id',
                    'extras'
                ])
    
    def log_prediction(self, prediction: Dict[str, Any], user_id: int = None, source: str = "bot") -> None:
        """
        Log a single prediction to CSV
        
        Args:
            prediction: Prediction dict with match, market, selection, p_est, odds, ev
            user_id: User ID who received this prediction (optional)
            source: Source of prediction (bot, express, markets, etc.)
        """
        try:
            with open(self.log_path, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # Extract data from prediction
                match_info = prediction.get('match', '').split(' vs ')
                home_team = match_info[0] if len(match_info) == 2 else prediction.get('home_team', 'Unknown')
                away_team = match_info[1] if len(match_info) == 2 else prediction.get('away_team', 'Unknown')
                
                extras = prediction.get('extras', {})
                if isinstance(extras, dict):
                    extras_str = ';'.join([f"{k}:{v}" for k, v in extras.items()])
                else:
                    extras_str = str(extras)
                
                row = [
                    datetime.now().isoformat(),  # timestamp
                    prediction.get('date', datetime.now().date().isoformat()),  # match date
                    prediction.get('match_id', ''),  # Football-Data match ID
                    prediction.get('competition', ''),  # Competition code
                    home_team,
                    away_team,
                    prediction.get('market', ''),
                    prediction.get('selection', ''),
                    prediction.get('p_est', 0.0),
                    prediction.get('odds', 1.0),
                    prediction.get('ev', 0.0),
                    source,
                    user_id or '',
                    extras_str
                ]
                
                writer.writerow(row)
                
        except Exception as e:
            logger.error(f"Failed to log prediction: {str(e)}")
    
    def log_batch_predictions(self, predictions: List[Dict[str, Any]], user_id: int = None, source: str = "bot") -> None:
        """Log multiple predictions at once"""
        for prediction in predictions:
            self.log_prediction(prediction, user_id, source)
    
    def get_recent_predictions(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get predictions from the last N days"""
        if not self.log_path.exists():
            return []
        
        predictions = []
        cutoff_date = datetime.now().date()
        
        try:
            with open(self.log_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    try:
                        pred_date = datetime.fromisoformat(row['date']).date()
                        if (cutoff_date - pred_date).days <= days:
                            predictions.append(row)
                    except ValueError:
                        continue  # Skip invalid date rows
                        
        except Exception as e:
            logger.error(f"Failed to read predictions: {str(e)}")
            
        return predictions
    
    def get_predictions_for_match(self, home_team: str, away_team: str, match_date: str) -> List[Dict[str, Any]]:
        """Get all logged predictions for a specific match"""
        if not self.log_path.exists():
            return []
        
        predictions = []
        
        try:
            with open(self.log_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if (row['home_team'].lower() == home_team.lower() and 
                        row['away_team'].lower() == away_team.lower() and
                        row['date'] == match_date):
                        predictions.append(row)
                        
        except Exception as e:
            logger.error(f"Failed to read match predictions: {str(e)}")
            
        return predictions


# Global logger instance
predictions_logger = PredictionsLogger()

# Convenience functions
def log_prediction(prediction: Dict[str, Any], user_id: int = None, source: str = "bot") -> None:
    """Log a single prediction"""
    predictions_logger.log_prediction(prediction, user_id, source)

def log_batch_predictions(predictions: List[Dict[str, Any]], user_id: int = None, source: str = "bot") -> None:
    """Log multiple predictions"""
    predictions_logger.log_batch_predictions(predictions, user_id, source)