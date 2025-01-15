import time
from typing import Dict, Any, Optional
import logging
from functools import lru_cache
from threading import Lock

logger = logging.getLogger(__name__)

class SimpleCache:
    def __init__(self, max_size: int = 1000, ttl: int = 3600):
        """初始化快取系統
        
        Args:
            max_size (int): 快取最大容量
            ttl (int): 快取存活時間（秒）
        """
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.max_size = max_size
        self.ttl = ttl  # Time to live in seconds
        self.lock = Lock()  # 線程安全鎖
        
    def _make_key(self, role: str, query: str) -> str:
        """生成快取鍵值
        
        Args:
            role (str): 角色名稱
            query (str): 查詢內容
            
        Returns:
            str: 組合後的鍵值
        """
        return f"{role}:{query.strip().lower()}"
        
    def get(self, role: str, query: str) -> Optional[str]:
        """獲取快取的回應
        
        Args:
            role (str): 角色名稱
            query (str): 查詢內容
            
        Returns:
            Optional[str]: 快取的回應，如果不存在或過期則返回 None
        """
        try:
            with self.lock:
                key = self._make_key(role, query)
                if key in self.cache:
                    item = self.cache[key]
                    if time.time() - item['timestamp'] < self.ttl:
                        logger.info(f"Cache hit for {key}")
                        return item['response']
                    else:
                        # 過期了，刪除
                        del self.cache[key]
                        logger.info(f"Cache expired for {key}")
                return None
        except Exception as e:
            logger.error(f"Error getting from cache: {e}", exc_info=True)
            return None
            
    def set(self, role: str, query: str, response: str) -> bool:
        """設置快取
        
        Args:
            role (str): 角色名稱
            query (str): 查詢內容
            response (str): 回應內容
            
        Returns:
            bool: 是否成功設置快取
        """
        try:
            with self.lock:
                # 如果快取太大，清除最舊的項目
                if len(self.cache) >= self.max_size:
                    oldest_key = min(
                        self.cache.keys(), 
                        key=lambda k: self.cache[k]['timestamp']
                    )
                    del self.cache[oldest_key]
                    logger.info(f"Removed oldest cache entry: {oldest_key}")
                    
                key = self._make_key(role, query)
                self.cache[key] = {
                    'response': response,
                    'timestamp': time.time(),
                    'hits': 0  # 添加命中計數
                }
                logger.info(f"Cached response for {key}")
                return True
        except Exception as e:
            logger.error(f"Error setting cache: {e}", exc_info=True)
            return False
            
    def clear(self) -> None:
        """清除所有快取"""
        try:
            with self.lock:
                self.cache.clear()
                logger.info("Cache cleared successfully")
        except Exception as e:
            logger.error(f"Error clearing cache: {e}", exc_info=True)
            
    def get_stats(self) -> Dict[str, Any]:
        """獲取快取統計信息
        
        Returns:
            Dict[str, Any]: 包含快取使用統計的字典
        """
        try:
            with self.lock:
                return {
                    'size': len(self.cache),
                    'max_size': self.max_size,
                    'usage_percent': (len(self.cache) / self.max_size) * 100,
                    'ttl': self.ttl
                }
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}", exc_info=True)
            return {}

# 使用 lru_cache 裝飾器的輔助函數，用於更高效的快取
@lru_cache(maxsize=1000)
def get_cached_response(role: str, query: str) -> Optional[str]:
    """使用 LRU 快取獲取回應
    
    Args:
        role (str): 角色名稱
        query (str): 查詢內容
        
    Returns:
        Optional[str]: 快取的回應
    """
    return None  # 實際使用時會被更新
