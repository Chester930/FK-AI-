import numpy as np
from typing import List, Dict, Optional, Tuple
import logging
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import json
import os
from datetime import datetime
import pytz

logger = logging.getLogger(__name__)

class VectorStore:
    def __init__(self, 
                 model_name: str = 'paraphrase-multilingual-MiniLM-L12-v2',
                 cache_dir: str = 'data/vector_cache'):
        """
        初始化向量存儲
        
        Args:
            model_name: 使用的語言模型名稱
            cache_dir: 向量快取目錄
        """
        self.model = SentenceTransformer(model_name)
        self.embeddings: Dict[str, np.ndarray] = {}
        self.documents: Dict[str, Dict] = {}
        self.cache_dir = cache_dir
        
        # 確保快取目錄存在
        os.makedirs(cache_dir, exist_ok=True)
        
        # 載入快取的向量
        self._load_cache()
        
    def _load_cache(self):
        """載入快取的向量"""
        try:
            cache_file = os.path.join(self.cache_dir, 'vector_cache.json')
            if os.path.exists(cache_file):
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                    
                for doc_id, doc_info in cache_data.items():
                    self.documents[doc_id] = {
                        'content': doc_info['content'],
                        'metadata': doc_info['metadata'],
                        'embedding': np.array(doc_info['embedding'])
                    }
                logger.info(f"Loaded {len(self.documents)} documents from cache")
        except Exception as e:
            logger.error(f"Error loading vector cache: {e}")
            
    def _save_cache(self):
        """保存向量到快取"""
        try:
            cache_file = os.path.join(self.cache_dir, 'vector_cache.json')
            cache_data = {}
            
            for doc_id, doc_info in self.documents.items():
                cache_data[doc_id] = {
                    'content': doc_info['content'],
                    'metadata': doc_info['metadata'],
                    'embedding': doc_info['embedding'].tolist()
                }
                
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
                
            logger.info(f"Saved {len(cache_data)} documents to cache")
        except Exception as e:
            logger.error(f"Error saving vector cache: {e}")
            
    def add_document(self, 
                    doc_id: str, 
                    content: str, 
                    metadata: Optional[Dict] = None):
        """
        添加文檔到向量存儲
        
        Args:
            doc_id: 文檔ID
            content: 文檔內容
            metadata: 文檔元數據
        """
        try:
            # 生成文檔向量
            embedding = self.model.encode([content])[0]
            
            # 保存文檔信息
            self.documents[doc_id] = {
                'content': content,
                'metadata': metadata or {},
                'embedding': embedding
            }
            
            # 更新快取
            self._save_cache()
            
            logger.info(f"Added document {doc_id} to vector store")
        except Exception as e:
            logger.error(f"Error adding document {doc_id}: {e}")
            
    def search(self, 
              query: str, 
              top_k: int = 5,
              min_score: float = 0.3) -> List[Dict]:
        """
        搜索相似文檔
        
        Args:
            query: 查詢文本
            top_k: 返回結果數量
            min_score: 最小相似度閾值
            
        Returns:
            相似文檔列表
        """
        try:
            # 生成查詢向量
            query_embedding = self.model.encode([query])[0]
            
            # 計算相似度
            results = []
            for doc_id, doc_info in self.documents.items():
                similarity = cosine_similarity(
                    [query_embedding], 
                    [doc_info['embedding']]
                )[0][0]
                
                if similarity >= min_score:
                    results.append({
                        'doc_id': doc_id,
                        'content': doc_info['content'],
                        'metadata': doc_info['metadata'],
                        'score': float(similarity)
                    })
                    
            # 排序並返回結果
            results.sort(key=lambda x: x['score'], reverse=True)
            return results[:top_k]
            
        except Exception as e:
            logger.error(f"Error searching documents: {e}")
            return []
            
    def batch_add_documents(self, 
                          documents: List[Tuple[str, str, Optional[Dict]]]):
        """
        批量添加文檔
        
        Args:
            documents: [(doc_id, content, metadata), ...]
        """
        try:
            # 批量生成向量
            contents = [doc[1] for doc in documents]
            embeddings = self.model.encode(contents)
            
            # 保存文檔
            for (doc_id, content, metadata), embedding in zip(documents, embeddings):
                self.documents[doc_id] = {
                    'content': content,
                    'metadata': metadata or {},
                    'embedding': embedding
                }
                
            # 更新快取
            self._save_cache()
            
            logger.info(f"Added {len(documents)} documents in batch")
        except Exception as e:
            logger.error(f"Error in batch_add_documents: {e}")
            
    def remove_document(self, doc_id: str):
        """移除文檔"""
        if doc_id in self.documents:
            del self.documents[doc_id]
            self._save_cache()
            logger.info(f"Removed document {doc_id}")
            
    def clear(self):
        """清空向量存儲"""
        self.documents.clear()
        self._save_cache()
        logger.info("Cleared vector store")
        
    def get_document(self, doc_id: str) -> Optional[Dict]:
        """獲取文檔信息"""
        return self.documents.get(doc_id) 