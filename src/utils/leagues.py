
# How many candidates we build before per-user selection for diversification
TOP_N_FOR_UI = 6

# Football-Data.org competition codes (see docs: CL=Champions Lg, EL=Europa Lg, UCL=UEFA Conference Lg)
# Coverage/codes: https://docs.football-data.org/general/v4/lookup_tables.html
TOP_COMP_CODES = [
    "PL","PD","SA","BL1","FL1","DED","PPL",
    "CL","EL","UCL"
]

# Number of top candidates to build before per-user selection for UI diversification
TOP_N_FOR_UI = 6

# The Odds API sport keys mapping (adjust if needed; use /v4/sports to verify exact keys)
# Docs: https://the-odds-api.com/liveapi/guides/v4/
ODDS_SPORT_KEYS = {
    "PL":  "soccer_epl",
    "PD":  "soccer_spain_la_liga",
    "SA":  "soccer_italy_serie_a",
    "BL1": "soccer_germany_bundesliga",
    "FL1": "soccer_france_ligue_one",
    "DED": "soccer_netherlands_eredivisie",
    "PPL": "soccer_portugal_primeira_liga",
    "CL":  "soccer_uefa_champions_league",
    "EL":  "soccer_uefa_europa_league",
    "UCL": "soccer_uefa_europa_conference_league",
}
