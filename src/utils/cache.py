"""Simple in-memory cache for API requests"""
import time
from typing import Any, Optional

# Simple in-memory cache
_cache = {}

def cache(key: str, data: Any, ttl_seconds: int = 300) -> None:
    """Store data in cache with TTL"""
    _cache[key] = {
        'data': data,
        'expires': time.time() + ttl_seconds
    }

def get_cache(key: str) -> Optional[Any]:
    """Get data from cache if not expired"""
    if key in _cache:
        entry = _cache[key]
        if time.time() < entry['expires']:
            return entry['data']
        else:
            # Expired, remove
            del _cache[key]
    return None

def clear_cache():
    """Clear all cache entries"""
    _cache.clear()