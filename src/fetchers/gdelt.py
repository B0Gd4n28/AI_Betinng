"""
GDELT sentiment analysis for football teams and matches
Analyzes global news sentiment about teams using GDELT Project data
"""
from __future__ import annotations
import requests
import logging
from typing import Dict, Any, List, Optional
import sys
import os
from datetime import datetime, timedelta
import json

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from utils.cache import cache
from utils.config import settings

logger = logging.getLogger(__name__)

class GDELTSentimentAPI:
    """
    GDELT (Global Database of Events, Language, and Tone) sentiment analysis
    Uses GDELT DOC 2.0 API to analyze news sentiment about football teams
    """
    
    def __init__(self):
        self.gdelt_base = "https://api.gdeltproject.org/api/v2/doc/doc"
    
    def _make_gdelt_request(self, params: Dict[str, Any]) -> Optional[Dict]:
        """Make GDELT API request with error handling"""
        try:
            response = requests.get(self.gdelt_base, params=params, timeout=30)
            
            if response.status_code != 200:
                logger.error(f"GDELT error {response.status_code}: {response.text[:200]}")
                return None
            
            # GDELT returns JSON
            return response.json()
            
        except requests.RequestException as e:
            logger.error(f"GDELT request failed: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected GDELT error: {str(e)}")
            return None
    
    def get_team_sentiment(self, team_name: str, days_back: int = 3) -> Dict[str, Any]:
        """
        Get news sentiment for a football team from GDELT
        
        Args:
            team_name: Team name to search for
            days_back: Number of days to look back for articles
            
        Returns:
            dict: {
                "label": "positive|neutral|negative",
                "score": float,  # Average tone score
                "confidence": float,  # Based on article count and consistency
                "articles_count": int,
                "sources": list[str]  # Sample news sources
            }
        """
        if not settings.gdelt_enabled:
            logger.debug("GDELT analysis disabled")
            return self._neutral_sentiment()
        
        cache_key = f"gdelt_team_{team_name}_{days_back}"
        cached_result = cache.get(cache_key)
        if cached_result is not None:
            logger.debug(f"Using cached GDELT sentiment for {team_name}")
            return cached_result
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        params = {
            "query": f'"{team_name}" football OR soccer',
            "mode": "artlist",
            "format": "json",
            "maxrecords": "50",
            "startdatetime": start_date.strftime("%Y%m%d%H%M%S"),
            "enddatetime": end_date.strftime("%Y%m%d%H%M%S"),
            "sort": "hybridrel"
        }
        
        data = self._make_gdelt_request(params)
        
        if not data or "articles" not in data:
            result = self._neutral_sentiment()
            cache.set(cache_key, result, ttl=3600)  # Cache for 1 hour
            return result
        
        articles = data["articles"]
        
        if not articles:
            result = self._neutral_sentiment()
            cache.set(cache_key, result, ttl=3600)
            return result
        
        # Analyze sentiment from article tone scores
        tone_scores = []
        sources = set()
        
        for article in articles:
            # GDELT tone is between -100 (very negative) and +100 (very positive)
            tone = article.get("tone")
            if tone is not None:
                try:
                    tone_value = float(tone)
                    tone_scores.append(tone_value)
                except (ValueError, TypeError):
                    continue
            
            # Collect unique sources
            source = article.get("domain", "")
            if source:
                sources.add(source)
        
        if not tone_scores:
            result = self._neutral_sentiment()
            cache.set(cache_key, result, ttl=3600)
            return result
        
        # Calculate average tone
        avg_tone = sum(tone_scores) / len(tone_scores)
        
        # Convert GDELT tone (-100 to +100) to our scale (-1.0 to +1.0)
        normalized_score = max(-1.0, min(1.0, avg_tone / 100.0))
        
        # Calculate confidence based on article count and tone consistency
        article_confidence = min(1.0, len(articles) / 20)  # More articles = higher confidence
        tone_std = (sum((t - avg_tone) ** 2 for t in tone_scores) / len(tone_scores)) ** 0.5
        consistency_confidence = max(0.1, 1.0 - (tone_std / 50))  # Lower std = higher confidence
        
        confidence = (article_confidence + consistency_confidence) / 2
        
        # Determine label based on normalized score
        if normalized_score > 0.1:
            label = "positive"
        elif normalized_score < -0.1:
            label = "negative"
        else:
            label = "neutral"
        
        result = {
            "label": label,
            "score": round(normalized_score, 3),
            "confidence": round(confidence, 3),
            "articles_count": len(articles),
            "sources": list(sources)[:5]  # Top 5 sources
        }
        
        # Cache for 1 hour
        cache.set(cache_key, result, ttl=3600)
        
        return result
    
    def get_match_sentiment(self, home_team: str, away_team: str) -> Dict[str, Any]:
        """
        Get combined sentiment for both teams in a match
        
        Args:
            home_team: Home team name
            away_team: Away team name
            
        Returns:
            dict: Combined sentiment analysis
        """
        cache_key = f"gdelt_match_{home_team}_{away_team}"
        cached_result = cache.get(cache_key)
        if cached_result is not None:
            return cached_result
        
        # Get sentiment for both teams
        home_sentiment = self.get_team_sentiment(home_team)
        away_sentiment = self.get_team_sentiment(away_team)
        
        # Combine sentiments (simple average)
        combined_score = (home_sentiment["score"] + away_sentiment["score"]) / 2
        combined_confidence = (home_sentiment["confidence"] + away_sentiment["confidence"]) / 2
        
        # Determine combined label
        if combined_score > 0.1:
            label = "positive"
        elif combined_score < -0.1:
            label = "negative"
        else:
            label = "neutral"
        
        result = {
            "label": label,
            "score": round(combined_score, 3),
            "confidence": round(combined_confidence, 3),
            "articles_count": home_sentiment["articles_count"] + away_sentiment["articles_count"],
            "sources": list(set(home_sentiment["sources"] + away_sentiment["sources"]))[:5]
        }
        
        # Cache for 1 hour
        cache.set(cache_key, result, ttl=3600)
        
        return result
    
    def _neutral_sentiment(self) -> Dict[str, Any]:
        """Return neutral sentiment when no data available"""
        return {
            "label": "neutral",
            "score": 0.0,
            "confidence": 0.0,
            "articles_count": 0,
            "sources": []
        }


# Global instance
gdelt_api = GDELTSentimentAPI()

# Convenience functions for backward compatibility
def get_team_sentiment(team_name: str, days_back: int = 3) -> Dict[str, Any]:
    """Get news sentiment for a football team from GDELT"""
    return gdelt_api.get_team_sentiment(team_name, days_back)

def get_match_sentiment(home_team: str, away_team: str) -> Dict[str, Any]:
    """Get combined sentiment for both teams in a match"""
    return gdelt_api.get_match_sentiment(home_team, away_team)