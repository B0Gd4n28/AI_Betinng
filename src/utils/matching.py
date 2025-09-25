
import re
from rapidfuzz import fuzz

def norm(s:str)->str:
    s = s.lower()
    s = re.sub(r'fc|cf|sc|afc|calcio|club|deportivo|ud|cd|ac|sp|athletic|real|ss|sv|sparta|sporting','', s)
    s = re.sub(r'[^a-z0-9]+',' ', s).strip()
    return s

def teams_match(a:str,b:str)->bool:
    return fuzz.token_sort_ratio(norm(a), norm(b)) >= 85
