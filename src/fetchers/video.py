"""
Video highlights fetcher for football matches
Provides match highlights and video content when available
"""
from __future__ import annotations
import requests
import logging
from typing import List, Dict, Any
import sys
import os
from datetime import datetime

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from utils.cache import cache
from utils.config import settings

logger = logging.getLogger(__name__)

class VideoHighlightsAPI:
    """
    Video highlights fetcher with fallback to placeholder content
    """
    
    def __init__(self):
        self.api_base = "https://www.scorebat.com/video-api/v3"
        # Note: ScoreBat is free but we'll use VIDEO_API_TOKEN as a placeholder
        # for future paid video API integration
    
    def highlights_for_match(self, home_team: str, away_team: str, match_date: str) -> List[Dict[str, Any]]:
        """
        Get video highlights for a specific match
        
        Args:
            home_team: Home team name
            away_team: Away team name  
            match_date: Match date in YYYY-MM-DD format
            
        Returns:
            list[dict]: [{"title": str, "url": str}, ...]
        """
        cache_key = f"highlights_{home_team}_{away_team}_{match_date}"
        cached_result = cache.get(cache_key)
        if cached_result is not None:
            logger.debug(f"Using cached highlights for {home_team} vs {away_team}")
            return cached_result
        
        # If we have a configured video API token, try to use it
        if settings.video_api_token:
            highlights = self._fetch_from_configured_api(home_team, away_team, match_date)
        else:
            # Fallback to free ScoreBat API
            highlights = self._fetch_from_scorebat(home_team, away_team, match_date)
        
        # Cache results for 6 hours
        cache.set(cache_key, highlights, ttl=21600)
        
        return highlights
    
    def _fetch_from_configured_api(self, home_team: str, away_team: str, match_date: str) -> List[Dict[str, Any]]:
        """
        Fetch highlights from configured video API
        This is a placeholder for future integration with paid video services
        """
        logger.debug(f"VIDEO_API_TOKEN configured but no specific provider implemented")
        
        # Placeholder implementation - return empty list for now
        # In the future, this could integrate with services like:
        # - Football Highlights API
        # - YouTube Data API v3 (for public highlights)
        # - Sportmonks Video API
        # etc.
        
        return []
    
    def _fetch_from_scorebat(self, home_team: str, away_team: str, match_date: str) -> List[Dict[str, Any]]:
        """
        Fetch highlights from free ScoreBat API
        """
        try:
            # ScoreBat provides free highlights but without search by team names
            # We'll fetch recent highlights and try to match
            response = requests.get(self.api_base, timeout=30)
            
            if response.status_code != 200:
                logger.error(f"ScoreBat API error {response.status_code}")
                return []
            
            data = response.json()
            highlights = []
            
            # Try to find matches containing our team names
            for video in data.get("response", []):
                title = video.get("title", "").lower()
                home_lower = home_team.lower()
                away_lower = away_team.lower()
                
                # Simple matching - look for team names in title
                if (home_lower in title or away_lower in title) and len(highlights) < 3:
                    highlights.append({
                        "title": video.get("title", "Match Highlights"),
                        "url": video.get("embed", "")
                    })
            
            return highlights
            
        except requests.RequestException as e:
            logger.error(f"ScoreBat request failed: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error fetching ScoreBat highlights: {str(e)}")
            return []


# Global instance
video_api = VideoHighlightsAPI()

# Convenience function for backward compatibility
def highlights_for_match(home_team: str, away_team: str, match_date: str) -> List[Dict[str, Any]]:
    """Get video highlights for a specific match"""
    return video_api.highlights_for_match(home_team, away_team, match_date)