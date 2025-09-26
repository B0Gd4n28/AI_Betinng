"""
Football rich stats fetcher with API-Sports.io primary and ApiFutball.com fallback
Provides team stats, fixtures details, lineups and injuries information
"""
from __future__ import annotations
import requests
import logging
from typing import Dict, Any, List, Optional
import sys
import os

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from utils.cache import cache
from utils.config import settings

logger = logging.getLogger(__name__)

class FootballStatsAPI:
    """
    Unified interface for football statistics with multiple provider support
    """
    
    def __init__(self):
        self.api_sports_base = "https://v3.football.api-sports.io"
        self.apifootball_base = "https://apiv3.apifootball.com"
        
    def _get_headers_api_sports(self) -> Dict[str, str]:
        """Headers for API-Sports.io"""
        if not settings.api_football_key:
            return {}
        return {
            "X-RapidAPI-Key": settings.api_football_key,
            "X-RapidAPI-Host": "v3.football.api-sports.io"
        }
    
    def _make_api_sports_request(self, endpoint: str, params: Dict[str, Any]) -> Optional[Dict]:
        """Make request to API-Sports.io with caching and error handling"""
        if not settings.api_football_key:
            return None
            
        cache_key = f"api_sports_{endpoint}_{str(sorted(params.items()))}"
        cached_result = cache.get(cache_key)
        if cached_result is not None:
            logger.debug(f"Using cached API-Sports data for {endpoint}")
            return cached_result
        
        try:
            headers = self._get_headers_api_sports()
            if not headers:
                return None
                
            url = f"{self.api_sports_base}/{endpoint}"
            response = requests.get(url, headers=headers, params=params, timeout=30)
            
            if response.status_code != 200:
                logger.error(f"API-Sports error {response.status_code}: {response.text[:200]}")
                return None
                
            data = response.json()
            
            # Cache for 10 minutes (stats don't change very frequently)
            cache.set(cache_key, data, ttl=600)
            
            return data
            
        except requests.RequestException as e:
            logger.error(f"API-Sports request failed for {endpoint}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected API-Sports error for {endpoint}: {str(e)}")
            return None
    
    def _make_apifootball_request(self, endpoint: str, params: Dict[str, Any]) -> Optional[Dict]:
        """Make request to ApiFutball.com with caching and error handling"""
        if not settings.apifootball_key:
            return None
            
        cache_key = f"apifootball_{endpoint}_{str(sorted(params.items()))}"
        cached_result = cache.get(cache_key)
        if cached_result is not None:
            logger.debug(f"Using cached ApiFutball data for {endpoint}")
            return cached_result
        
        try:
            params["APIkey"] = settings.apifootball_key
            url = f"{self.apifootball_base}/?action={endpoint}"
            
            response = requests.get(url, params=params, timeout=30)
            
            if response.status_code != 200:
                logger.error(f"ApiFutball error {response.status_code}: {response.text[:200]}")
                return None
                
            data = response.json()
            
            # Cache for 10 minutes
            cache.set(cache_key, data, ttl=600)
            
            return data
            
        except requests.RequestException as e:
            logger.error(f"ApiFutball request failed for {endpoint}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected ApiFutball error for {endpoint}: {str(e)}")
            return None

    def get_team_league_stats(self, team_id: int, league_id: int, season: int = 2024) -> Dict[str, Any]:
        """
        Get comprehensive team statistics for a league/season
        
        Returns:
            dict: {
                goals_for_avg: float,
                goals_against_avg: float, 
                btts_pct: float,
                clean_sheets_pct: float,
                cards_avg: float,
                venue_city: str,
                venue_country: str
            }
        """
        # Try API-Sports first
        if settings.api_football_key:
            data = self._make_api_sports_request("teams/statistics", {
                "team": team_id,
                "league": league_id,
                "season": season
            })
            
            if data and data.get("response"):
                stats = data["response"]
                fixtures = stats.get("fixtures", {})
                goals = stats.get("goals", {})
                cards = stats.get("cards", {})
                venue = stats.get("venue", {})
                
                played = fixtures.get("played", {}).get("total", 0)
                
                if played > 0:
                    goals_for = goals.get("for", {}).get("total", {}).get("total", 0)
                    goals_against = goals.get("against", {}).get("total", {}).get("total", 0)
                    clean_sheets = stats.get("clean_sheet", {}).get("total", 0)
                    
                    # Calculate BTTS percentage from goals data
                    home_goals_for = goals.get("for", {}).get("total", {}).get("home", 0) or 0
                    away_goals_for = goals.get("for", {}).get("total", {}).get("away", 0) or 0
                    home_goals_against = goals.get("against", {}).get("total", {}).get("home", 0) or 0
                    away_goals_against = goals.get("against", {}).get("total", {}).get("away", 0) or 0
                    
                    # Estimate BTTS from average goals (rough approximation)
                    avg_goals_for = goals_for / played
                    avg_goals_against = goals_against / played
                    btts_estimate = min(0.9, (avg_goals_for * avg_goals_against) / 2.0)
                    
                    yellow_cards = cards.get("yellow", {}).get("total", 0) or 0
                    red_cards = cards.get("red", {}).get("total", 0) or 0
                    
                    return {
                        "goals_for_avg": round(goals_for / played, 2),
                        "goals_against_avg": round(goals_against / played, 2),
                        "btts_pct": round(btts_estimate * 100, 1),
                        "clean_sheets_pct": round((clean_sheets / played) * 100, 1),
                        "cards_avg": round((yellow_cards + red_cards) / played, 2),
                        "venue_city": venue.get("city", "n/a"),
                        "venue_country": venue.get("country", "n/a")
                    }
        
        # Fallback to ApiFutball (limited data)
        if settings.apifootball_key:
            data = self._make_apifootball_request("get_teams", {"team_id": team_id})
            if data and isinstance(data, list) and len(data) > 0:
                team = data[0]
                return {
                    "goals_for_avg": None,
                    "goals_against_avg": None,
                    "btts_pct": None,
                    "clean_sheets_pct": None,
                    "cards_avg": None,
                    "venue_city": team.get("venue_city", "n/a"),
                    "venue_country": team.get("venue_country", "n/a")
                }
        
        # No data available
        return {
            "goals_for_avg": None,
            "goals_against_avg": None,
            "btts_pct": None,
            "clean_sheets_pct": None,
            "cards_avg": None,
            "venue_city": "n/a",
            "venue_country": "n/a"
        }
    
    def get_fixture_extras(self, fixture_id: int) -> Dict[str, Any]:
        """
        Get fixture details: lineups, injuries, key players
        
        Returns:
            dict: {
                lineups_ready: bool,
                injuries_note: str|None,
                key_scorers: list[str]
            }
        """
        # Try API-Sports first
        if settings.api_football_key:
            # Get lineups
            lineups_data = self._make_api_sports_request("fixtures/lineups", {"fixture": fixture_id})
            lineups_ready = False
            if lineups_data and lineups_data.get("response"):
                lineups_ready = len(lineups_data["response"]) >= 2  # Both teams have lineups
            
            # Get injuries
            injuries_data = self._make_api_sports_request("injuries", {"fixture": fixture_id})
            injuries_note = None
            if injuries_data and injuries_data.get("response"):
                injury_count = len(injuries_data["response"])
                if injury_count > 0:
                    injuries_note = f"{injury_count} injury concerns reported"
            
            # Get players stats for key scorers (simplified)
            key_scorers = []
            players_data = self._make_api_sports_request("fixtures/players", {"fixture": fixture_id})
            if players_data and players_data.get("response"):
                for team_data in players_data["response"]:
                    for player in team_data.get("players", []):
                        stats = player.get("statistics", [])
                        if stats and any(stat.get("goals", {}).get("total", 0) > 0 for stat in stats):
                            key_scorers.append(player.get("player", {}).get("name", "Unknown"))
            
            return {
                "lineups_ready": lineups_ready,
                "injuries_note": injuries_note,
                "key_scorers": key_scorers[:3]  # Top 3 scorers max
            }
        
        # Fallback to ApiFutball (very limited fixture details)
        if settings.apifootball_key:
            data = self._make_apifootball_request("get_events", {"match_id": fixture_id})
            return {
                "lineups_ready": False,  # Not available in free tier
                "injuries_note": None,   # Not available in free tier
                "key_scorers": []        # Not available in free tier
            }
        
        # No data available
        return {
            "lineups_ready": False,
            "injuries_note": None,
            "key_scorers": []
        }


# Global instance
football_api = FootballStatsAPI()

# Convenience functions for backward compatibility
def get_team_league_stats(team_id: int, league_id: int, season: int = 2024) -> Dict[str, Any]:
    """Get team statistics for league/season"""
    return football_api.get_team_league_stats(team_id, league_id, season)

def get_fixture_extras(fixture_id: int) -> Dict[str, Any]:
    """Get fixture details: lineups, injuries, key players"""
    return football_api.get_fixture_extras(fixture_id)