
from __future__ import annotations
import os, requests, datetime as dt, logging, sys
from typing import List, Dict, Any

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from utils.cache import cache, get_cache

logger = logging.getLogger(__name__)
BASE = "https://api.football-data.org/v4"

def _headers(token:str|None):
    return {"X-Auth-Token": token} if token else {}

def get_matches_for_date(token: str | None, comp_codes: List[str], date_iso: str) -> list[dict]:
    """
    Returnează toate meciurile din lista de competiții pentru data dată (yyyy-mm-dd).
    """
    cache_key = f"football_data_matches_{','.join(comp_codes)}_{date_iso}"
    
    # Check cache first
    cached_result = get_cache(cache_key)
    if cached_result is not None:
        logger.debug(f"Using cached Football-Data matches for {date_iso}")
        return cached_result
    
    # Endpoint doc: /v4/competitions/{id}/matches?dateFrom&dateTo
    res = []
    
    try:
        for code in comp_codes:
            url = f"{BASE}/competitions/{code}/matches"
            params = {
                "dateFrom": date_iso, 
                "dateTo": date_iso, 
                "status": "SCHEDULED,IN_PLAY,PAUSED,FINISHED"
            }
            
            response = requests.get(url, headers=_headers(token), params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                for m in data.get("matches", []):
                    res.append({
                        "competition": code,
                        "match_id": m.get("id"),
                        "utcDate": m.get("utcDate"),
                        "status": m.get("status"),
                        "home_id": m.get("homeTeam", {}).get("id"),
                        "home_name": m.get("homeTeam", {}).get("name"),
                        "away_id": m.get("awayTeam", {}).get("id"),
                        "away_name": m.get("awayTeam", {}).get("name"),
                        "score": m.get("score"),
                        "venue": m.get("venue", {}).get("name", "Unknown")
                    })
            else:
                logger.error(f"Football-Data error {response.status_code} for {code}: {response.text[:200]}")
                
    except requests.RequestException as e:
        logger.error(f"Football-Data request failed: {str(e)}")
        return []
    except Exception as e:
        logger.error(f"Unexpected Football-Data error: {str(e)}")
        return []
    
    # Cache for 5 minutes (football data changes frequently during match days)
    cache(cache_key, res, 300)
    
    return res

def get_team_recent_results(token:str|None, team_id:int, end_date:str, days:int=120) -> list[dict]:
    """
    IA ultimele meciuri ale echipei până la end_date (fără a include ziua curentă).
    """
    date_to = dt.datetime.fromisoformat(end_date).date()
    date_from = date_to - dt.timedelta(days=days)
    url = f"{BASE}/teams/{team_id}/matches"
    r = requests.get(url, headers=_headers(token), params={"dateFrom": str(date_from), "dateTo": str(date_to)})
    if r.status_code!=200:
        return []
    data = r.json()
    return data.get("matches", [])
