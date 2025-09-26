#!/usr/bin/env python3
"""
Results labeler script - labels prediction outcomes based on actual match results
Run this daily to update predictions with actual results for model training
"""
import sys
import os
from pathlib import Path

# Add project root to path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import csv
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from src.fetchers.football_data import get_matches_for_date, get_match_by_id
from src.utils.config import settings
from src.utils.matching import teams_match

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class ResultsLabeler:
    """
    Labels predictions with actual match results for model training
    """
    
    def __init__(self, predictions_file: str = "data/predictions.csv", 
                 labeled_file: str = "data/labeled_predictions.csv"):
        self.predictions_file = Path(predictions_file)
        self.labeled_file = Path(labeled_file)
        self.labeled_file.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_labeled_headers()
    
    def _ensure_labeled_headers(self):
        """Ensure labeled CSV has proper headers"""
        if not self.labeled_file.exists():
            with open(self.labeled_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'timestamp', 'date', 'match_id', 'competition', 'home_team', 'away_team',
                    'market', 'selection', 'p_est', 'odds', 'ev', 'source', 'user_id', 'extras',
                    'home_score', 'away_score', 'result', 'label', 'labeled_at'
                ])
    
    def label_predictions_for_date(self, date_str: str) -> int:
        """
        Label all predictions for a specific date with actual results
        
        Args:
            date_str: Date in YYYY-MM-DD format
            
        Returns:
            int: Number of predictions labeled
        """
        if not self.predictions_file.exists():
            logger.warning(f"Predictions file {self.predictions_file} not found")
            return 0
        
        # Get match results for the date
        logger.info(f"Fetching match results for {date_str}")
        matches = get_matches_for_date(settings.football_data_token, None, date_str)
        
        if not matches:
            logger.info(f"No matches found for {date_str}")
            return 0
        
        # Only process finished matches
        finished_matches = [m for m in matches if m.get('status') in ('FINISHED', 'AWARDED')]
        logger.info(f"Found {len(finished_matches)} finished matches")
        
        # Read existing labeled predictions to avoid duplicates
        existing_labeled = set()
        if self.labeled_file.exists():
            with open(self.labeled_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    key = f"{row['timestamp']}_{row['home_team']}_{row['away_team']}_{row['market']}_{row['selection']}"
                    existing_labeled.add(key)
        
        # Read predictions and label them
        labeled_count = 0
        
        with open(self.predictions_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for prediction in reader:
                if prediction['date'] != date_str:
                    continue
                
                # Check if already labeled
                key = f"{prediction['timestamp']}_{prediction['home_team']}_{prediction['away_team']}_{prediction['market']}_{prediction['selection']}"
                if key in existing_labeled:
                    continue
                
                # Find matching match
                match_result = self._find_matching_match(prediction, finished_matches)
                if not match_result:
                    logger.debug(f"No match found for prediction: {prediction['home_team']} vs {prediction['away_team']}")
                    continue
                
                # Label the prediction
                label = self._calculate_label(prediction, match_result)
                if label is not None:
                    self._write_labeled_prediction(prediction, match_result, label)
                    labeled_count += 1
        
        logger.info(f"Labeled {labeled_count} predictions for {date_str}")
        return labeled_count
    
    def _find_matching_match(self, prediction: Dict[str, Any], matches: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Find the match that corresponds to this prediction"""
        pred_home = prediction['home_team']
        pred_away = prediction['away_team']
        
        for match in matches:
            match_home = match.get('home_name', '') or match.get('homeTeam', {}).get('name', '')
            match_away = match.get('away_name', '') or match.get('awayTeam', {}).get('name', '')
            
            if teams_match(pred_home, match_home) and teams_match(pred_away, match_away):
                return match
                
        return None
    
    def _calculate_label(self, prediction: Dict[str, Any], match: Dict[str, Any]) -> Optional[int]:
        """
        Calculate label (1=correct, 0=incorrect) for a prediction based on actual result
        
        Args:
            prediction: Prediction row from CSV
            match: Match result from Football-Data
            
        Returns:
            int: 1 if prediction was correct, 0 if incorrect, None if cannot determine
        """
        try:
            # Get match score
            score = match.get('score', {}) or {}
            full_time = score.get('fullTime', {}) or {}
            home_score = full_time.get('home') or full_time.get('homeTeam') or 0
            away_score = full_time.get('away') or full_time.get('awayTeam') or 0
            
            market = prediction['market']
            selection = prediction['selection']
            
            # Handle different markets
            if market == '1X2':
                if selection == 'Home' and home_score > away_score:
                    return 1
                elif selection == 'Draw' and home_score == away_score:
                    return 1
                elif selection == 'Away' and away_score > home_score:
                    return 1
                else:
                    return 0
            
            elif market.startswith('O/U'):
                # Extract line from market (e.g., "O/U 2.5" -> 2.5)
                try:
                    line = float(market.split(' ')[1])
                    total_goals = home_score + away_score
                    
                    if selection.startswith('Over') and total_goals > line:
                        return 1
                    elif selection.startswith('Under') and total_goals < line:
                        return 1
                    else:
                        return 0
                except (IndexError, ValueError):
                    return None
            
            elif market == 'BTTS':
                both_scored = home_score > 0 and away_score > 0
                
                if selection == 'Yes' and both_scored:
                    return 1
                elif selection == 'No' and not both_scored:
                    return 1
                else:
                    return 0
            
            # Unknown market
            return None
            
        except Exception as e:
            logger.error(f"Error calculating label: {str(e)}")
            return None
    
    def _write_labeled_prediction(self, prediction: Dict[str, Any], match: Dict[str, Any], label: int):
        """Write labeled prediction to output file"""
        try:
            # Get match score
            score = match.get('score', {}) or {}
            full_time = score.get('fullTime', {}) or {}
            home_score = full_time.get('home') or full_time.get('homeTeam') or 0
            away_score = full_time.get('away') or full_time.get('awayTeam') or 0
            
            # Determine match result
            if home_score > away_score:
                result = 'H'
            elif away_score > home_score:
                result = 'A'
            else:
                result = 'D'
            
            with open(self.labeled_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                row = list(prediction.values()) + [
                    home_score,
                    away_score,
                    result,
                    label,
                    datetime.now().isoformat()
                ]
                
                writer.writerow(row)
                
        except Exception as e:
            logger.error(f"Error writing labeled prediction: {str(e)}")
    
    def label_recent_predictions(self, days: int = 7) -> int:
        """Label predictions from the last N days"""
        total_labeled = 0
        
        for i in range(days):
            date = datetime.now().date() - timedelta(days=i+1)  # Start from yesterday
            date_str = date.isoformat()
            labeled = self.label_predictions_for_date(date_str)
            total_labeled += labeled
        
        return total_labeled


def main():
    """Main script entry point"""
    labeler = ResultsLabeler()
    
    if len(sys.argv) > 1:
        # Label specific date
        date_str = sys.argv[1]
        try:
            datetime.fromisoformat(date_str)
            labeled = labeler.label_predictions_for_date(date_str)
            print(f"Labeled {labeled} predictions for {date_str}")
        except ValueError:
            print(f"Invalid date format: {date_str}. Use YYYY-MM-DD")
            sys.exit(1)
    else:
        # Label recent predictions (last 7 days)
        print("Labeling predictions from the last 7 days...")
        total = labeler.label_recent_predictions(7)
        print(f"Total labeled predictions: {total}")


if __name__ == "__main__":
    main()