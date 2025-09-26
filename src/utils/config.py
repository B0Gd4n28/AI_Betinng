
import os
from typing import Dict, Tuple
from pydantic import BaseModel
from dotenv import load_dotenv

# load .env from project root if present
try:
    load_dotenv()
except Exception:
    pass

class Settings(BaseModel):
    # Core Bot
    telegram_token: str | None = os.getenv("TELEGRAM_BOT_TOKEN")
    
    # Football Data APIs
    football_data_token: str | None = os.getenv("FOOTBALL_DATA_TOKEN")
    odds_api_key: str | None = os.getenv("ODDS_API_KEY")
    api_football_key: str | None = os.getenv("API_FOOTBALL_KEY")
    apifootball_key: str | None = os.getenv("APIFOOTBALL_KEY")
    
    # External Data APIs
    openweather_key: str | None = os.getenv("OPENWEATHER_KEY")
    video_api_token: str | None = os.getenv("VIDEO_API_TOKEN")
    
    # Reddit API (optional)
    reddit_client_id: str | None = os.getenv("REDDIT_CLIENT_ID")
    reddit_client_secret: str | None = os.getenv("REDDIT_CLIENT_SECRET")
    reddit_user_agent: str | None = os.getenv("REDDIT_USER_AGENT")
    
    # Feature flags
    gdelt_enabled: bool = os.getenv("GDELT_ENABLED", "0") == "1"

    # defaults
    odds_regions: str = os.getenv("ODDS_REGIONS", "uk,eu")
    odds_markets: str = os.getenv("ODDS_MARKETS", "h2h,totals,both_teams_to_score")

    def get_health_status(self) -> Dict[str, str]:
        """
        Returns health status for each API key (OK/MISSING) without exposing values
        """
        status = {}
        
        # Core keys (required)
        core_keys = [
            ("TELEGRAM_BOT_TOKEN", self.telegram_token),
            ("FOOTBALL_DATA_TOKEN", self.football_data_token),
            ("ODDS_API_KEY", self.odds_api_key)
        ]
        
        # Optional keys (nice to have)
        optional_keys = [
            ("API_FOOTBALL_KEY", self.api_football_key),
            ("APIFOOTBALL_KEY", self.apifootball_key),
            ("OPENWEATHER_KEY", self.openweather_key),
            ("VIDEO_API_TOKEN", self.video_api_token),
            ("REDDIT_CLIENT_ID", self.reddit_client_id),
            ("REDDIT_CLIENT_SECRET", self.reddit_client_secret),
            ("REDDIT_USER_AGENT", self.reddit_user_agent)
        ]
        
        for key_name, key_value in core_keys + optional_keys:
            status[key_name] = "OK" if key_value else "MISSING"
            
        return status

    def has_api_football(self) -> bool:
        """Check if we have at least one football stats API"""
        return bool(self.api_football_key or self.apifootball_key)
    
    def has_weather(self) -> bool:
        """Check if weather API is available"""
        return bool(self.openweather_key)
    
    def has_reddit(self) -> bool:
        """Check if Reddit API is configured"""
        return bool(self.reddit_client_id and self.reddit_client_secret and self.reddit_user_agent)

settings = Settings()
