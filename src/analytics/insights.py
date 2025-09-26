"""
Match insights generator combining statistics, weather, sentiment and lineup data
Provides comprehensive match analysis for enhanced user experience
"""
from __future__ import annotations
import logging
from typing import Dict, Any, List, Optional
import sys
import os

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from fetchers.api_football import get_team_league_stats, get_fixture_extras
from fetchers.weather import weather_for_city_at
from fetchers.reddit import get_match_sentiment
from fetchers.gdelt import get_match_sentiment as get_gdelt_sentiment
from utils.config import settings

logger = logging.getLogger(__name__)

class MatchInsightsGenerator:
    """
    Generates comprehensive match insights combining multiple data sources
    """
    
    def __init__(self):
        self.max_insight_length = 500  # Telegram message limits
    
    def build_match_insights(self, fixture: Dict[str, Any], enriched_stats: Dict[str, Any] = None, 
                           weather: Dict[str, Any] = None, sentiment: Dict[str, Any] = None) -> str:
        """
        Build comprehensive match insights text
        
        Args:
            fixture: Match fixture data from Football-Data API
            enriched_stats: Additional team statistics
            weather: Weather data for match location
            sentiment: Sentiment analysis data
            
        Returns:
            str: Formatted insights text with emojis
        """
        try:
            insights = []
            
            # Basic match info
            home_team = fixture.get("home_name", "Home")
            away_team = fixture.get("away_name", "Away")
            
            # Add goals average if available
            goals_insight = self._build_goals_insight(fixture, enriched_stats)
            if goals_insight:
                insights.append(goals_insight)
            
            # Add key players/scorers info
            scorers_insight = self._build_scorers_insight(fixture, enriched_stats)
            if scorers_insight:
                insights.append(scorers_insight)
            
            # Add disciplinary record (cards)
            cards_insight = self._build_cards_insight(enriched_stats)
            if cards_insight:
                insights.append(cards_insight)
            
            # Add lineup availability
            lineup_insight = self._build_lineup_insight(fixture, enriched_stats)
            if lineup_insight:
                insights.append(lineup_insight)
            
            # Add weather conditions
            weather_insight = self._build_weather_insight(fixture, weather)
            if weather_insight:
                insights.append(weather_insight)
            
            # Add sentiment analysis
            sentiment_insight = self._build_sentiment_insight(sentiment)
            if sentiment_insight:
                insights.append(sentiment_insight)
            
            # Combine insights with separators
            if insights:
                combined = " • ".join(insights)
                # Truncate if too long
                if len(combined) > self.max_insight_length:
                    combined = combined[:self.max_insight_length-3] + "..."
                return f"🧠 {combined}"
            else:
                return "🧠 Standard match analysis available"
                
        except Exception as e:
            logger.error(f"Error building match insights: {str(e)}")
            return "🧠 Match insights unavailable"
    
    def _build_goals_insight(self, fixture: Dict, enriched_stats: Dict = None) -> Optional[str]:
        """Build goals average insight"""
        try:
            if not enriched_stats:
                return None
            
            home_stats = enriched_stats.get("home", {})
            away_stats = enriched_stats.get("away", {})
            
            home_goals_avg = home_stats.get("goals_for_avg")
            away_goals_avg = away_stats.get("goals_for_avg")
            
            if home_goals_avg is not None and away_goals_avg is not None:
                total_avg = home_goals_avg + away_goals_avg
                if total_avg > 2.8:
                    return f"⚽ High-scoring teams ({total_avg:.1f} avg goals)"
                elif total_avg < 2.0:
                    return f"🔒 Low-scoring affair ({total_avg:.1f} avg goals)"
                else:
                    return f"⚽ Balanced attack ({total_avg:.1f} avg goals)"
            
            return None
            
        except Exception as e:
            logger.debug(f"Error building goals insight: {str(e)}")
            return None
    
    def _build_scorers_insight(self, fixture: Dict, enriched_stats: Dict = None) -> Optional[str]:
        """Build key scorers insight"""
        try:
            fixture_id = fixture.get("id")
            if not fixture_id:
                return None
            
            # Get fixture extras for key scorers
            extras = get_fixture_extras(fixture_id)
            key_scorers = extras.get("key_scorers", [])
            
            if key_scorers:
                if len(key_scorers) == 1:
                    return f"⭐ Key player: {key_scorers[0]}"
                else:
                    return f"⭐ Key players: {', '.join(key_scorers[:2])}"
            
            return None
            
        except Exception as e:
            logger.debug(f"Error building scorers insight: {str(e)}")
            return None
    
    def _build_cards_insight(self, enriched_stats: Dict = None) -> Optional[str]:
        """Build cards/discipline insight"""
        try:
            if not enriched_stats:
                return None
            
            home_stats = enriched_stats.get("home", {})
            away_stats = enriched_stats.get("away", {})
            
            home_cards = home_stats.get("cards_avg")
            away_cards = away_stats.get("cards_avg")
            
            if home_cards is not None and away_cards is not None:
                avg_cards = (home_cards + away_cards) / 2
                if avg_cards > 4.0:
                    return f"🟨 Physical match expected ({avg_cards:.1f} avg cards)"
                elif avg_cards < 2.0:
                    return f"🤝 Clean game likely ({avg_cards:.1f} avg cards)"
            
            return None
            
        except Exception as e:
            logger.debug(f"Error building cards insight: {str(e)}")
            return None
    
    def _build_lineup_insight(self, fixture: Dict, enriched_stats: Dict = None) -> Optional[str]:
        """Build lineup/injuries insight"""
        try:
            fixture_id = fixture.get("id")
            if not fixture_id:
                return None
            
            extras = get_fixture_extras(fixture_id)
            lineups_ready = extras.get("lineups_ready", False)
            injuries_note = extras.get("injuries_note")
            
            if lineups_ready:
                if injuries_note:
                    return f"👥 Lineups confirmed, {injuries_note.lower()}"
                else:
                    return "👥 Full squads available"
            elif injuries_note:
                return f"🏥 {injuries_note}"
            
            return None
            
        except Exception as e:
            logger.debug(f"Error building lineup insight: {str(e)}")
            return None
    
    def _build_weather_insight(self, fixture: Dict, weather: Dict = None) -> Optional[str]:
        """Build weather conditions insight"""
        try:
            if weather:
                temp = weather.get("temp_c")
                wind = weather.get("wind_mps")
                pop = weather.get("pop")
                desc = weather.get("desc", "").lower()
                
                weather_parts = []
                
                if temp is not None:
                    weather_parts.append(f"{temp}°C")
                
                if wind is not None and wind > 5:
                    weather_parts.append(f"{wind}m/s wind")
                
                if pop is not None and pop > 0.3:
                    weather_parts.append(f"{int(pop*100)}% rain chance")
                
                if "rain" in desc or "storm" in desc:
                    weather_emoji = "🌧️"
                elif "snow" in desc:
                    weather_emoji = "❄️"
                elif "cloud" in desc:
                    weather_emoji = "☁️"
                else:
                    weather_emoji = "🌤️"
                
                if weather_parts:
                    return f"{weather_emoji} {', '.join(weather_parts)}"
            
            # Fallback: try to get weather from fixture location
            venue_city = fixture.get("venue_city")
            venue_country = fixture.get("venue_country")
            commence_time = fixture.get("utcDate")
            
            if all([venue_city, venue_country, commence_time]) and settings.has_weather():
                weather_data = weather_for_city_at(venue_city, venue_country, commence_time)
                if weather_data.get("temp_c") is not None:
                    return self._build_weather_insight(fixture, weather_data)
            
            return None
            
        except Exception as e:
            logger.debug(f"Error building weather insight: {str(e)}")
            return None
    
    def _build_sentiment_insight(self, sentiment: Dict = None) -> Optional[str]:
        """Build sentiment analysis insight"""
        try:
            if not sentiment:
                return None
            
            label = sentiment.get("label", "neutral")
            confidence = sentiment.get("confidence", 0.0)
            sources = sentiment.get("sources", 0)
            
            if sources == 0:
                return None
            
            # Only show sentiment if confidence is reasonable
            if confidence < 0.3:
                return None
            
            if label == "positive":
                emoji = "🟢"
                text = "Positive buzz"
            elif label == "negative":
                emoji = "🔴"
                text = "Negative sentiment"
            else:
                emoji = "🔵"
                text = "Neutral sentiment"
            
            return f"{emoji} {text} ({sources} sources)"
            
        except Exception as e:
            logger.debug(f"Error building sentiment insight: {str(e)}")
            return None
    
    def get_enriched_match_data(self, fixture: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get all enriched data for a match from various sources
        
        Args:
            fixture: Match fixture data
            
        Returns:
            dict: Combined data from all sources
        """
        try:
            home_team = fixture.get("home_name", "")
            away_team = fixture.get("away_name", "")
            fixture_id = fixture.get("id")
            
            enriched_data = {
                "fixture": fixture,
                "stats": {},
                "weather": {},
                "sentiment": {},
                "extras": {}
            }
            
            # Get team statistics if available
            if settings.has_api_football() and fixture_id:
                try:
                    # This would need proper team ID mapping in a real implementation
                    # For now, we'll skip detailed stats
                    pass
                except Exception as e:
                    logger.debug(f"Could not get team stats: {str(e)}")
            
            # Get weather data if available
            if settings.has_weather():
                venue_city = fixture.get("venue_city", "London")  # Fallback
                venue_country = fixture.get("venue_country", "GB")
                commence_time = fixture.get("utcDate")
                
                if commence_time:
                    try:
                        weather_data = weather_for_city_at(venue_city, venue_country, commence_time)
                        enriched_data["weather"] = weather_data
                    except Exception as e:
                        logger.debug(f"Could not get weather: {str(e)}")
            
            # Get sentiment analysis if available
            if settings.has_reddit():
                try:
                    sentiment_data = get_match_sentiment(home_team, away_team)
                    enriched_data["sentiment"] = sentiment_data
                except Exception as e:
                    logger.debug(f"Could not get sentiment: {str(e)}")
            
            # Get fixture extras
            if fixture_id:
                try:
                    extras_data = get_fixture_extras(fixture_id)
                    enriched_data["extras"] = extras_data
                except Exception as e:
                    logger.debug(f"Could not get fixture extras: {str(e)}")
            
            return enriched_data
            
        except Exception as e:
            logger.error(f"Error getting enriched match data: {str(e)}")
            return {"fixture": fixture, "stats": {}, "weather": {}, "sentiment": {}, "extras": {}}


# Global instance
insights_generator = MatchInsightsGenerator()

# Convenience function for backward compatibility
def build_match_insights(fixture: Dict[str, Any], enriched_stats: Dict[str, Any] = None, 
                        weather: Dict[str, Any] = None, sentiment: Dict[str, Any] = None) -> str:
    """Build comprehensive match insights text"""
    return insights_generator.build_match_insights(fixture, enriched_stats, weather, sentiment)