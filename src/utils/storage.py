
import json, os, threading
from pathlib import Path

STORE = Path(__file__).resolve().parents[2] / "storage" / "users.json"
STORE.parent.mkdir(parents=True, exist_ok=True)
_lock = threading.Lock()

def get_lang(user_id:int) -> str:
    with _lock:
        if not STORE.exists():
            STORE.write_text(json.dumps({}, indent=2))
        data = json.loads(STORE.read_text())
        return data.get(str(user_id), "RO")

def set_lang(user_id:int, lang:str):
    with _lock:
        if not STORE.exists():
            STORE.write_text(json.dumps({}, indent=2))
        data = json.loads(STORE.read_text())
        data[str(user_id)] = lang
        STORE.write_text(json.dumps(data, indent=2))
