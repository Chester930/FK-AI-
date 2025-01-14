import os
import json
import logging
from typing import Dict, Any
from datetime import datetime, timedelta
import pytz
import pandas as pd
from docx import Document

logger = logging.getLogger(__name__)

class CacheManager:
    def __init__(self):
        self.user_caches = {}  # 用戶級別的快取 {user_id: UserCache}
        self.cache_dir = "temp/cache"
        self.web_search_dir = "temp/web_search"  # 網路搜尋暫存目錄
        self.timeout = timedelta(minutes=10)
        self.max_cache_size = 100 * 1024 * 1024  # 100MB
        self.max_users = 1000  # 最大用戶數
        self.cleanup_interval = timedelta(hours=1)  # 定期清理間隔
        self.last_cleanup = datetime.now(pytz.UTC)
        os.makedirs(self.cache_dir, exist_ok=True)
        os.makedirs(self.web_search_dir, exist_ok=True)

    class UserCache:
        def __init__(self):
            self.common_cache = {}    # 共用資料快取
            self.role_cache = {}      # 角色資料快取
            self.rag_cache = {}       # RAG 搜尋結果快取
            self.last_access = datetime.now(pytz.UTC)
            self.cache_size = 0  # 追蹤快取大小
            
        def update_access_time(self):
            """更新最後訪問時間"""
            self.last_access = datetime.now(pytz.UTC)
            
        def update_cache_size(self):
            """計算當前快取大小"""
            size = 0
            size += sum(len(str(v)) for v in self.common_cache.values())
            size += sum(len(str(v)) for v in self.role_cache.values())
            size += sum(len(str(v)) for v in self.rag_cache.values())
            self.cache_size = size
            return size

    def get_user_cache(self, user_id: str, is_group: bool = False) -> UserCache:
        """獲取用戶的快取，如果不存在則創建"""
        cache_id = f"{'group' if is_group else 'user'}_{user_id}"
        if cache_id not in self.user_caches:
            self.user_caches[cache_id] = self.UserCache()
        return self.user_caches[cache_id]
        
    def clear_user_cache(self, user_id: str, is_group: bool = False):
        """清除特定用戶的快取和搜尋紀錄"""
        # 清除快取
        cache_id = f"{'group' if is_group else 'user'}_{user_id}"
        if cache_id in self.user_caches:
            del self.user_caches[cache_id]
            
        # 清除網路搜尋紀錄
        prefix = f"search_{'group' if is_group else 'personal'}_{user_id}_"
        if os.path.exists(self.web_search_dir):
            for file in os.listdir(self.web_search_dir):
                if file.startswith(prefix):
                    file_path = os.path.join(self.web_search_dir, file)
                    try:
                        if os.path.isfile(file_path):
                            os.remove(file_path)
                            logger.info(f"已刪除搜尋記錄: {file}")
                    except Exception as e:
                        logger.error(f"刪除檔案時發生錯誤 {file_path}: {str(e)}")
                        
        logger.info(f"已清除 {cache_id} 的快取和搜尋紀錄")
            
    def check_and_clear_inactive_caches(self):
        """檢查並並清除不活躍的快取"""
        current_time = datetime.now(pytz.UTC)
        inactive_users = []
        
        for cache_id, user_cache in self.user_caches.items():
            if current_time - user_cache.last_access > self.timeout:
                inactive_users.append(cache_id)
                
        for cache_id in inactive_users:
            self.clear_user_cache(cache_id.split('_')[1], 
                                is_group=cache_id.startswith('group_'))
            logger.info(f"已清除不活躍用戶 {cache_id} 的快取")
            
    def load_common_data(self, user_id: str, knowledge_base_paths: dict, is_group: bool = False):
        """載入共用資料到用戶快取"""
        user_cache = self.get_user_cache(user_id, is_group)
        user_cache.common_cache.clear()
        
        try:
            if 'common' in knowledge_base_paths:
                for category, info in knowledge_base_paths['common'].items():
                    content = self._read_file_content(info['path'])
                    if content:
                        user_cache.common_cache[category] = {
                            'content': content,
                            'metadata': info
                        }
            user_cache.update_access_time()
            logger.info(f"已為 {'群組' if is_group else '用戶'} {user_id} 載入共用資料")
        except Exception as e:
            logger.error(f"載入共用資料時發生錯誤: {str(e)}")
            
    def load_role_data(self, user_id: str, role: str, knowledge_base_paths: dict, is_group: bool = False):
        """載入角色資料到用戶快取"""
        user_cache = self.get_user_cache(user_id, is_group)
        user_cache.role_cache.clear()
        
        try:
            if role in knowledge_base_paths:
                for category, info in knowledge_base_paths[role].items():
                    content = self._read_file_content(info['path'])
                    if content:
                        user_cache.role_cache[category] = {
                            'content': content,
                            'metadata': info
                        }
            user_cache.update_access_time()
            logger.info(f"已為 {'群組' if is_group else '用戶'} {user_id} 載入 {role} 角色資料")
        except Exception as e:
            logger.error(f"載入角色資料時發生錯誤: {str(e)}")
            
    def add_rag_result(self, user_id: str, query: str, result: Dict[str, Any], is_group: bool = False):
        """添加 RAG 搜尋結果到用戶快取"""
        user_cache = self.get_user_cache(user_id, is_group)
        user_cache.rag_cache[query] = {
            'result': result,
            'timestamp': datetime.now(pytz.UTC).isoformat()
        }
        user_cache.update_access_time()
        
    def get_rag_result(self, user_id: str, query: str, is_group: bool = False) -> Dict[str, Any]:
        """獲取用戶的 RAG 搜尋結果"""
        user_cache = self.get_user_cache(user_id, is_group)
        user_cache.update_access_time()
        return user_cache.rag_cache.get(query, {}).get('result')
        
    def _read_file_content(self, path: str) -> str:
        """讀取檔案內容"""
        try:
            if not os.path.isfile(path):
                return None
            
            # 根據檔案類型使用不同的讀取方式
            file_ext = path.lower().split('.')[-1]
            
            if file_ext == 'txt':
                with open(path, 'r', encoding='utf-8') as f:
                    return f.read()
                
            elif file_ext == 'docx':
                doc = Document(path)
                return '\n'.join(paragraph.text for paragraph in doc.paragraphs)
                
            elif file_ext == 'xlsx':
                df = pd.read_excel(path)
                return df.to_string()
                
            else:
                logger.warning(f"不支援的檔案類型: {file_ext}")
                return None
            
        except Exception as e:
            logger.error(f"讀取檔案失敗 {path}: {str(e)}")
            return None

    def check_cache_size(self):
        """檢查並管理快取大小"""
        total_size = sum(cache.cache_size for cache in self.user_caches.values())
        if total_size > self.max_cache_size:
            # 移除最舊的快取
            sorted_caches = sorted(
                self.user_caches.items(),
                key=lambda x: x[1].last_access
            )
            while total_size > self.max_cache_size * 0.8:  # 清理到80%
                if not sorted_caches:
                    break
                user_id, _ = sorted_caches.pop(0)
                self.clear_user_cache(user_id.split('_')[1], 
                                    user_id.startswith('group_'))
                total_size = sum(cache.cache_size 
                               for cache in self.user_caches.values())

    def periodic_cleanup(self):
        """定期清理"""
        current_time = datetime.now(pytz.UTC)
        if current_time - self.last_cleanup > self.cleanup_interval:
            self.check_cache_size()
            self.check_and_clear_inactive_caches()
            self.last_cleanup = current_time 

    def clear_all_cache(self):
        """清空所有快取"""
        try:
            # 清空記憶體中的快取
            self.user_caches.clear()
            
            # 清空快取目錄
            for directory in [self.cache_dir, self.web_search_dir]:
                if os.path.exists(directory):
                    for file in os.listdir(directory):
                        file_path = os.path.join(directory, file)
                        try:
                            if os.path.isfile(file_path):
                                os.remove(file_path)
                                logger.info(f"已刪除快取檔案: {file}")
                        except Exception as e:
                            logger.error(f"刪除檔案時發生錯誤 {file_path}: {str(e)}")
            
            logger.info("所有快取已清除")
        except Exception as e:
            logger.error(f"清除所有快取時發生錯誤: {str(e)}") 