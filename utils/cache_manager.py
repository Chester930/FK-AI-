from collections import OrderedDict
import time
from typing import Any, Optional
import logging

logger = logging.getLogger(__name__)

class BaseCache:
    """基礎快取類"""
    def __init__(self, max_size: int):
        self.max_size = max_size
        self.cache = OrderedDict()
        
    def get(self, key: str) -> Optional[Any]:
        """獲取快取值"""
        return self.cache.get(key)
        
    def set(self, key: str, value: Any):
        """設置快取值"""
        if len(self.cache) >= self.max_size:
            self.cache.popitem(last=False)
        self.cache[key] = value

class LRUCache(BaseCache):
    """最近最少使用快取"""
    def get(self, key: str) -> Optional[Any]:
        if key in self.cache:
            # 移動到最後(最近使用)
            value = self.cache.pop(key)
            self.cache[key] = value
            return value
        return None

class TTLCache(BaseCache):
    """帶過期時間的快取"""
    def __init__(self, max_size: int, ttl: int = 3600):
        super().__init__(max_size)
        self.ttl = ttl
        self.timestamps = {}
        
    def get(self, key: str) -> Optional[Any]:
        if key in self.cache:
            if time.time() - self.timestamps[key] > self.ttl:
                # 過期了,刪除
                self.cache.pop(key)
                self.timestamps.pop(key)
                return None
            return self.cache[key]
        return None
        
    def set(self, key: str, value: Any):
        super().set(key, value)
        self.timestamps[key] = time.time()

class CacheManager:
    """快取管理器"""
    def __init__(self, cache_settings: dict):
        self.caches = {
            role: self._create_cache(settings)
            for role, settings in cache_settings.items()
        }
        
    def _create_cache(self, settings: dict) -> BaseCache:
        """根據設置創建對應的快取"""
        cache_type = settings.get('type', 'lru')
        if cache_type == 'ttl':
            return TTLCache(
                max_size=settings['max_size'],
                ttl=settings['cache_duration']
            )
        return LRUCache(max_size=settings['max_size'])
        
    def get_role_cache(self, role: str) -> BaseCache:
        """獲取角色對應的快取"""
        return self.caches.get(role)
        
    def get_cached_response(self, role: str, query: str) -> Optional[str]:
        """獲取快取的回應"""
        cache = self.get_role_cache(role)
        if cache:
            return cache.get(query)
        return None
        
    def cache_response(self, role: str, query: str, response: str):
        """快取回應"""
        cache = self.get_role_cache(role)
        if cache:
            cache.set(query, response)
            logger.info(f"Cached response for role {role}") 