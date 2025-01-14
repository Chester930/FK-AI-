import os
import logging
from typing import Dict, List, Optional
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
            role: 角色標識
            
        Returns:
            處理的文檔數量
        """
        try:
            count = 0
            path = Path(dir_path)
            
            if not path.exists():
                logger.warning(f"Directory not found: {dir_path}")
                return count
                
            # 處理所有文件
            for file_path in path.rglob('*'):
                if not file_path.is_file():
                    continue
                    
                # 檢查文件類型
                if file_path.suffix.lower() in ['.txt', '.docx', '.xlsx', '.pdf']:
                    # 生成文檔ID
                    doc_id = self._generate_doc_id(file_path, role)
                    
                    # 如果文件已處理且未修改，跳過
                    if doc_id in self.processed_files:
                        continue
                        
                    # 讀取並處理文件
                    content = self._read_file(file_path)
                    if content:
                        # 添加角色信息到內容中
                        if role:
                            content = f"[Role: {role}]\n{content}"
                            
                        self.vector_store.add_document(doc_id, content)
                        self.processed_files.add(doc_id)
                        count += 1
                
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
                if f"[Role: {role}]" in r['content']
            ]
            
        return results