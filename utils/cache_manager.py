class CacheManager:
    def __init__(self):
        self.cache = {}
    
    def get(self, role, text):
        """
        從快取中獲取回應
        
        Args:
            role (str): 當前角色
            text (str): 輸入文本
            
        Returns:
            str or None: 如果找到快取的回應則返回，否則返回 None
        """
        cache_key = f"{role}:{text}"
        return self.cache.get(cache_key)
    
    def set(self, role, text, response):
        """
        將回應存入快取
        
        Args:
            role (str): 當前角色
            text (str): 輸入文本
            response (str): 要快取的回應
        """
        cache_key = f"{role}:{text}"
        self.cache[cache_key] = response 