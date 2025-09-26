"""
Simple in-memory TTL cache for API responses
"""
import time
from typing import Any, Dict, Optional
from threading import Lock

class TTLCache:
    """Thread-safe TTL cache with simple LRU eviction"""
    
    def __init__(self, default_ttl: int = 120, max_size: int = 1000):
        self.default_ttl = default_ttl
        self.max_size = max_size
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._lock = Lock()
    
    def get(self, key: str) -> Optional[Any]:
        """Get item from cache if not expired"""
        with self._lock:
            if key not in self._cache:
                return None
                
            item = self._cache[key]
            if time.time() > item['expires_at']:
                del self._cache[key]
                return None
                
            # Update access time for LRU
            item['accessed_at'] = time.time()
            return item['value']
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set item in cache with TTL"""
        if ttl is None:
            ttl = self.default_ttl
            
        with self._lock:
            # Evict oldest if at capacity
            if len(self._cache) >= self.max_size:
                self._evict_oldest()
            
            now = time.time()
            self._cache[key] = {
                'value': value,
                'expires_at': now + ttl,
                'accessed_at': now
            }
    
    def _evict_oldest(self) -> None:
        """Evict the least recently accessed item"""
        if not self._cache:
            return
            
        oldest_key = min(
            self._cache.keys(),
            key=lambda k: self._cache[k]['accessed_at']
        )
        del self._cache[oldest_key]
    
    def clear(self) -> None:
        """Clear all cached items"""
        with self._lock:
            self._cache.clear()

# Global cache instance
cache = TTLCache()