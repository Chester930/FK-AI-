import numpy as np
from typing import List, Dict, Optional
import logging
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)

class VectorStore:
    def __init__(self, model_name: str = 'paraphrase-multilingual-MiniLM-L12-v2'):
        self.model = SentenceTransformer(model_name)
        self.embeddings: Dict[str, np.ndarray] = {}
        self.documents: Dict[str, str] = {}
        
    def add_document(self, doc_id: str, content: str):
        """添加文檔到向量存儲"""
        try:
            embedding = self.model.encode([content])[0]
            self.embeddings[doc_id] = embedding
            self.documents[doc_id] = content
            logger.info(f"Added document {doc_id} to vector store")
        except Exception as e:
            logger.error(f"Error adding document {doc_id}: {e}")
            
    def search(self, query: str, top_k: int = 5) -> List[Dict[str, any]]:
        """搜索相似文檔"""
        try:
            query_embedding = self.model.encode([query])[0]
            
            # 計算相似度
            scores = {}
            for doc_id, doc_embedding in self.embeddings.items():
                similarity = cosine_similarity(
                    [query_embedding], 
                    [doc_embedding]
                )[0][0]
                scores[doc_id] = similarity
                
            # 排序並返回結果
            sorted_scores = sorted(
                scores.items(), 
                key=lambda x: x[1], 
                reverse=True
            )
            
            results = []
            for doc_id, score in sorted_scores[:top_k]:
                results.append({
                    'doc_id': doc_id,
                    'content': self.documents[doc_id],
                    'score': float(score)
                })
                
            return results
            
        except Exception as e:
            logger.error(f"Error searching documents: {e}")
            return []
            
    def clear(self):
        """清空向量存儲"""
        self.embeddings.clear()
        self.documents.clear() 