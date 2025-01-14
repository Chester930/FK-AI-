import os
import logging
from typing import Dict, List, Optional
from config import KNOWLEDGE_BASE_SETTINGS
from utils.vector_store import VectorStore
from utils.embedding_manager import EmbeddingManager
from utils.cache_manager import CacheManager
from utils.web_search import WebSearcher

logger = logging.getLogger(__name__)

class KnowledgeBase:
    def __init__(self, paths_config: dict):
        """
        初始化知識庫
        
        Args:
            paths_config: 知識庫路徑配置
        """
        self.paths_config = paths_config
        
        # 初始化向量存儲
        self.vector_store = VectorStore(
            model_name=KNOWLEDGE_BASE_SETTINGS['vector_store']['model_name']
        )
        
        # 初始化嵌入管理器
        self.embedding_manager = EmbeddingManager(
            vector_store=self.vector_store
        )
        
        # 初始化快取管理器
        self.cache_manager = CacheManager(
            cache_settings=KNOWLEDGE_BASE_SETTINGS['cache']
        )
        
        # 初始化網路搜索器
        self.web_searcher = WebSearcher()
        
        # 載入知識庫文檔
        self._load_documents()
        
    def _load_documents(self):
        """載入所有知識庫文檔"""
        try:
            # 處理每個角色的文檔
            for role, categories in self.paths_config.items():
                if role == 'common':
                    # 處理共用文檔
                    for category in categories.values():
                        path = category['path']
                        if os.path.exists(path):
                            self.embedding_manager.process_directory(path)
                else:
                    # 處理角色特定文檔
                    for category in categories.values():
                        path = category['path']
                        if os.path.exists(path):
                            self.embedding_manager.process_directory(path, role)
                            
        except Exception as e:
            logger.error(f"Error loading documents: {e}")
            
    def search(self, query: str, role: Optional[str] = None) -> str:
        """
        搜索相關知識
        
        Args:
            query: 查詢文本
            role: 角色標識
            
        Returns:
            格式化的搜索結果
        """
        try:
            # 1. 檢查快取
            cached_response = self.cache_manager.get_cached_response(role, query)
            if cached_response:
                logger.info("Cache hit")
                return cached_response
                
            # 2. 獲取角色特定的搜索設置
            search_settings = KNOWLEDGE_BASE_SETTINGS['role_search'].get(
                role,
                KNOWLEDGE_BASE_SETTINGS['role_search']['FK helper']  # 默認設置
            )
            
            # 3. 本地知識庫搜索
            local_results = self.embedding_manager.search_documents(
                query=query,
                role=role,
                top_k=search_settings['top_k']
            )
            
            # 4. 如果是 FK helper 且本地結果不足，進行網路搜索
            web_content = ""
            if role == 'FK helper' and len(local_results) < search_settings['top_k']:
                temp_file = self.web_searcher.search_and_save(query, "system")
                if temp_file:
                    web_content = self.web_searcher.read_search_results(temp_file)
                    
            # 5. 組合並格式化結果
            formatted_results = self._format_results(
                local_results=local_results,
                web_content=web_content,
                search_settings=search_settings
            )
            
            # 6. 快取結果
            self.cache_manager.cache_response(role, query, formatted_results)
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error in search: {e}")
            return f"搜索時發生錯誤: {str(e)}"
            
    def _format_results(self, 
                       local_results: List[Dict],
                       web_content: str,
                       search_settings: Dict) -> str:
        """格式化搜索結果"""
        formatted_text = ""
        
        # 添加本地知識庫結果
        if local_results:
            formatted_text += "=== 本地知識庫 ===\n"
            for result in local_results:
                score = result['score']
                if score >= search_settings['min_score']:
                    content = result['content'].replace("[Role: ", "來源: ")
                    formatted_text += f"{content}\n\n"
                    
        # 添加網路搜索結果
        if web_content:
            formatted_text += "=== 網路搜索結果 ===\n"
            formatted_text += f"{web_content}\n"
            
        return formatted_text.strip()

