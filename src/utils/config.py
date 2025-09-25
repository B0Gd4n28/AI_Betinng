
import os
from pydantic import BaseModel
from dotenv import load_dotenv

# load .env from project root if present
try:
    load_dotenv()
except Exception:
    pass

class Settings(BaseModel):
    football_data_token: str | None = os.getenv("FOOTBALL_DATA_TOKEN")
    odds_api_key: str | None = os.getenv("ODDS_API_KEY")
    telegram_token: str | None = os.getenv("TELEGRAM_BOT_TOKEN")
    gdelt_enabled: bool = os.getenv("GDELT_ENABLED","0") == "1"

    # defaults
    odds_regions: str = os.getenv("ODDS_REGIONS", "uk,eu")
    odds_markets: str = os.getenv("ODDS_MARKETS", "h2h")

settings = Settings()
