
from __future__ import annotations
import os, requests, datetime as dt
from typing import List, Dict, Any

BASE = "https://api.football-data.org/v4"

def _headers(token:str|None):
    return {"X-Auth-Token": token} if token else {}

def get_matches_for_date(token:str|None, comp_codes:List[str], date_iso:str) -> list[dict]:
    """
    Returnează toate meciurile din lista de competiții pentru data dată (yyyy-mm-dd).
    """
    # Endpoint doc: /v4/competitions/{id}/matches?dateFrom&dateTo
    res=[]
    for code in comp_codes:
        url = f"{BASE}/competitions/{code}/matches"
        r = requests.get(url, headers=_headers(token), params={"dateFrom":date_iso, "dateTo":date_iso, "status":"SCHEDULED,IN_PLAY,PAUSED,FINISHED"})
        if r.status_code==200:
            data = r.json()
            for m in data.get("matches", []):
                res.append({
                    "competition": code,
                    "match_id": m.get("id"),
                    "utcDate": m.get("utcDate"),
                    "status": m.get("status"),
                    "home_id": m.get("homeTeam",{}).get("id"),
                    "home_name": m.get("homeTeam",{}).get("name"),
                    "away_id": m.get("awayTeam",{}).get("id"),
                    "away_name": m.get("awayTeam",{}).get("name"),
                })
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
