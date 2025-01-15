import numpy as np
from typing import List, Dict, Optional
import logging
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from threading import Lock

logger = logging.getLogger(__name__)

class VectorStore:
    def __init__(self, model_name: str = 'paraphrase-multilingual-MiniLM-L12-v2'):
        """初始化向量存儲
        
        Args:
            model_name: 使用的 Sentence Transformer 模型名稱
        """
        self.model_name = model_name
        self.model = None
        self.embeddings: Dict[str, np.ndarray] = {}
        self.documents: Dict[str, str] = {}
        self.lock = Lock()
        
    def _ensure_model_loaded(self):
        """確保模型已加載"""
        if self.model is None:
            try:
                logger.info(f"Loading model: {self.model_name}")
                self.model = SentenceTransformer(self.model_name)
                logger.info("Model loaded successfully")
            except Exception as e:
                logger.error(f"Error loading model: {e}", exc_info=True)
                raise
        
    def add_document(self, doc_id: str, content: str):
        """添加文檔到向量存儲"""
        try:
            with self.lock:
                self._ensure_model_loaded()
                embedding = self.model.encode([content])[0]
                self.embeddings[doc_id] = embedding
                self.documents[doc_id] = content
                logger.info(f"Document added: {doc_id}")
        except Exception as e:
            logger.error(f"Error adding document: {e}", exc_info=True)
            raise
            
    def search(self, query: str, top_k: int = 5, min_score: float = 0.3) -> List[Dict[str, any]]:
        """搜索相似文檔
        
        Args:
            query: 查詢文本
            top_k: 返回結果數量
            min_score: 最小相似度閾值
            
        Returns:
            List[Dict]: 包含文檔內容和相似度分數的列表
        """
        try:
            with self.lock:
                self._ensure_model_loaded()
                if not self.embeddings:
                    return []
                    
                # 計算查詢向量
                query_embedding = self.model.encode([query])[0]
                
                # 計算相似度
                scores = {}
                for doc_id, doc_embedding in self.embeddings.items():
                    similarity = cosine_similarity(
                        [query_embedding], 
                        [doc_embedding]
                    )[0][0]
                    if similarity >= min_score:
                        scores[doc_id] = similarity
                
                # 排序並返回結果
                results = []
                for doc_id, score in sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]:
                    results.append({
                        'doc_id': doc_id,
                        'content': self.documents[doc_id],
                        'score': float(score)
                    })
                    
                return results
                
        except Exception as e:
            logger.error(f"Error searching documents: {e}", exc_info=True)
            return []
            
    def clear(self):
        """清空向量存儲"""
        with self.lock:
            self.embeddings.clear()
            self.documents.clear() 