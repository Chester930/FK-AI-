import os
import logging
from typing import Dict, List, Optional, Tuple
import hashlib
from datetime import datetime
import pytz
from pathlib import Path
import docx
import pandas as pd
import PyPDF2
from .vector_store import VectorStore

logger = logging.getLogger(__name__)

class EmbeddingManager:
    def __init__(self, 
                 vector_store: VectorStore,
                 base_dir: str = 'data'):
        """
        初始化嵌入管理器
        
        Args:
            vector_store: 向量存儲實例
            base_dir: 基礎數據目錄
        """
        self.vector_store = vector_store
        self.base_dir = base_dir
        self.processed_files = set()
        
    def process_directory(self, 
                         dir_path: str, 
                         role: Optional[str] = None) -> int:
        """
        處理目錄下的所有文檔
        
        Args:
            dir_path: 目錄路徑
            role: 角色標識(用於元數據)
            
        Returns:
            處理的文檔數量
        """
        try:
            count = 0
            path = Path(dir_path)
            
            if not path.exists():
                logger.warning(f"Directory not found: {dir_path}")
                return count
                
            # 收集所有要處理的文件
            documents = []
            for file_path in path.rglob('*'):
                if not file_path.is_file():
                    continue
                    
                # 檢查文件類型
                if file_path.suffix.lower() in ['.txt', '.docx', '.xlsx', '.pdf']:
                    # 生成文檔ID
                    doc_id = self._generate_doc_id(file_path, role)
                    
                    # 如果文件已處理且未修改，跳過
                    if not self._should_process_file(file_path, doc_id):
                        continue
                        
                    # 讀取並處理文件
                    content = self._read_file(file_path)
                    if content:
                        metadata = {
                            'path': str(file_path),
                            'role': role,
                            'type': file_path.suffix[1:],
                            'processed_at': datetime.now(pytz.UTC).isoformat()
                        }
                        documents.append((doc_id, content, metadata))
                        count += 1
                        
            # 批量添加文檔
            if documents:
                self.vector_store.batch_add_documents(documents)
                self.processed_files.update(doc_id for doc_id, _, _ in documents)
                
            return count
            
        except Exception as e:
            logger.error(f"Error processing directory {dir_path}: {e}")
            return 0
            
    def _generate_doc_id(self, file_path: Path, role: Optional[str] = None) -> str:
        """生成文檔唯一ID"""
        components = [str(file_path), str(file_path.stat().st_mtime)]
        if role:
            components.append(role)
        content = '|'.join(components)
        return hashlib.md5(content.encode()).hexdigest()
        
    def _should_process_file(self, file_path: Path, doc_id: str) -> bool:
        """判斷文件是否需要處理"""
        # 如果文件已經處理過且未修改，返回False
        if doc_id in self.processed_files:
            existing_doc = self.vector_store.get_document(doc_id)
            if existing_doc and existing_doc['metadata']['path'] == str(file_path):
                return False
        return True
        
    def _read_file(self, file_path: Path) -> Optional[str]:
        """讀取文件內容"""
        try:
            if file_path.suffix == '.txt':
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
                    
            elif file_path.suffix == '.docx':
                doc = docx.Document(file_path)
                return '\n'.join(p.text for p in doc.paragraphs)
                
            elif file_path.suffix == '.xlsx':
                df = pd.read_excel(file_path)
                return df.to_string()
                
            elif file_path.suffix == '.pdf':
                with open(file_path, 'rb') as f:
                    pdf = PyPDF2.PdfReader(f)
                    return '\n'.join(page.extract_text() for page in pdf.pages)
                    
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            return None
            
    def search_documents(self, 
                        query: str,
                        role: Optional[str] = None,
                        top_k: int = 5) -> List[Dict]:
        """
        搜索文檔
        
        Args:
            query: 查詢文本
            role: 限定角色
            top_k: 返回結果數量
            
        Returns:
            相關文檔列表
        """
        results = self.vector_store.search(query, top_k=top_k)
        
        # 如果指定了角色，過濾結果
        if role:
            results = [
                r for r in results 
                if r['metadata'].get('role') == role
            ]
            
        return results
        
    def get_role_documents(self, role: str) -> List[Dict]:
        """獲取指定角色的所有文檔"""
        return [
            doc for doc_id, doc in self.vector_store.documents.items()
            if doc['metadata'].get('role') == role
        ] 