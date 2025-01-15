import os
import re
import docx
import openpyxl
import fitz  # PyMuPDF
import jieba
import json
import logging
from typing import List, Dict

# 設置日誌
logger = logging.getLogger(__name__)

# 將專案根目錄加入到 sys.path
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import KNOWLEDGE_BASE_PATHS, KNOWLEDGE_BASE_SETTINGS
from utils.vector_store import VectorStore

class KnowledgeBase:
    def __init__(self, paths_config):
        """初始化知識庫"""
        self.paths_config = paths_config
        logger.info(f"初始化知識庫，配置: {paths_config}")
        
        # 檢查文件是否存在
        for role, categories in paths_config.items():
            for category, info in categories.items():
                path = info['path']
                if not os.path.exists(path):
                    logger.warning(f"文件不存在: {path}")
                else:
                    logger.info(f"找到文件: {path}")
        
        # 初始化向量存儲
        self.vector_store = VectorStore()
        self._load_documents()
    
    def _load_documents(self):
        """載入所有文檔到向量存儲"""
        try:
            # 獲取所有相關路徑
            paths = self._select_relevant_paths("")
            logger.info(f"正在載入知識庫文件，共找到 {len(paths)} 個文件")
            
            for path_info in paths:
                path = path_info['path']
                if not os.path.exists(path):
                    logger.warning(f"文件不存在: {path}")
                    continue
                    
                logger.info(f"正在處理文件: {path}")
                content = self._read_document(path)
                if content:
                    doc_id = path
                    self.vector_store.add_document(doc_id, content)
                    logger.info(f"成功載入文件: {path}")
            
            logger.info("知識庫載入完成")
                    
        except Exception as e:
            logger.error(f"載入文檔時發生錯誤: {str(e)}", exc_info=True)

    def _read_document(self, path):
        """根據文件類型讀取文檔內容"""
        try:
            # 如果是目錄，掃描並讀取所有支援的文件
            if os.path.isdir(path):
                logger.info(f"掃描目錄: {path}")
                content = []
                for file_path in self._get_supported_files(path):
                    file_content = self._read_single_document(file_path)
                    if file_content:
                        content.append(file_content)
                return "\n\n".join(content)
            # 如果是文件列表
            elif isinstance(path, list):
                content = []
                for p in path:
                    if os.path.exists(p):
                        file_content = self._read_single_document(p)
                        if file_content:
                            content.append(file_content)
                return "\n\n".join(content)
            # 如果是單個文件
            else:
                return self._read_single_document(path)
            
        except Exception as e:
            logger.error(f"讀取文檔時發生錯誤: {str(e)}")
            return None

    def search(self, query: str, role: str = None):
        """根據查詢搜尋相關知識
        
        Args:
            query: 查詢文本
            role: 角色名稱，用於獲取角色特定的搜索設置
        """
        try:
            # 獲取角色特定的搜索設置
            role_settings = KNOWLEDGE_BASE_SETTINGS['role_search'].get(
                role, 
                KNOWLEDGE_BASE_SETTINGS['role_search']['FK helper']
            )
            
            # 進行向量搜索
            vector_results = self.vector_store.search(
                query,
                top_k=role_settings['top_k'],
                min_score=role_settings['min_score']
            )
            
            # 組合結果
            results = []
            for result in vector_results:
                results.append({
                    'content': result['content'],
                    'score': result['score'],
                    'source': 'local',
                    'weight': role_settings['local_weight']
                })
                
            # 如果是 FK helper 且需要網路搜索
            if role == 'FK helper' and role_settings['web_weight'] > 0:
                web_results = self._get_web_results(query)
                for result in web_results:
                    results.append({
                        'content': result['content'],
                        'score': result.get('score', 0.5),
                        'source': 'web',
                        'weight': role_settings['web_weight']
                    })
                    
            # 根據權重和分數排序
            results.sort(key=lambda x: x['score'] * x['weight'], reverse=True)
            
            return self._format_results(results)
            
        except Exception as e:
            logger.error(f"搜索知識庫時發生錯誤: {str(e)}", exc_info=True)
            return "搜索時發生錯誤"

    def _format_results(self, results):
        """格式化搜尋結果"""
        formatted_text = ""
        for result in results:
            source_type = "知識庫" if result['source'] == 'local' else "網路搜索"
            formatted_text += f"\n=== {source_type} (相關度: {result['score']:.2f}) ===\n"
            formatted_text += f"來源: {result.get('doc_id', '未知')}\n"
            formatted_text += f"{result['content']}\n"
        return formatted_text.strip()

    def _select_relevant_paths(self, query):
        """選擇與查詢相關的知識庫路徑"""
        try:
            relevant_paths = []
            logger.info(f"開始選擇相關路徑，當前設定: {self.paths_config}")
            
            # 先檢查共同資料
            if 'common' in self.paths_config:
                logger.info("檢查共同資料...")
                for category_name, info in self.paths_config['common'].items():
                    # 如果關鍵字包含 '*' 或符合查詢
                    if '*' in info['keywords'] or \
                       any(keyword in query.lower() for keyword in info['keywords']):
                        path = info['path']
                        logger.info(f"找到相關路徑: {path}")
                        relevant_paths.append({
                            'path': path,
                            'priority': info['priority'],
                            'description': info['description']
                        })
            
            # 檢查角色特定資料
            for role_name, categories in self.paths_config.items():
                if role_name != 'common':
                    logger.info(f"檢查角色 {role_name} 的資料...")
                    for category_name, info in categories.items():
                        if '*' in info['keywords'] or \
                           any(keyword in query.lower() for keyword in info['keywords']):
                            path = info['path']
                            logger.info(f"找到相關路徑: {path}")
                            relevant_paths.append({
                                'path': path,
                                'priority': info['priority'],
                                'description': info['description']
                            })
            
            # 按優先級排序
            relevant_paths.sort(key=lambda x: x['priority'])
            logger.info(f"共找到 {len(relevant_paths)} 個相關路徑")
            return relevant_paths
            
        except Exception as e:
            logger.error(f"選擇相關路徑時發生錯誤: {str(e)}", exc_info=True)
            return []

    def _read_excel(self, path):
        """讀取 Excel 文件"""
        wb = openpyxl.load_workbook(path)
        content = []
        for sheet in wb.worksheets:
            headers = None
            for row in sheet.iter_rows(values_only=True):
                if not headers:
                    headers = row  # 第一行作為標題
                    continue
                # 將標題和內容組合
                row_data = []
                for header, cell in zip(headers, row):
                    if cell:  # 只添加非空的單元格
                        row_data.append(f"{header}: {cell}")
                if row_data:
                    content.append(' | '.join(row_data))
        return '\n'.join(content)

    def _read_docx(self, path):
        """讀取 Word 文件"""
        doc = docx.Document(path)
        return '\n'.join(paragraph.text for paragraph in doc.paragraphs)

    def _read_text(self, path):
        """讀取文本文件"""
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()

    def _read_pdf(self, path):
        """讀取 PDF 文件"""
        doc = fitz.open(path)
        content = []
        for page in doc:
            content.append(page.get_text())
        return '\n'.join(content)

    def _get_web_results(self, query: str) -> List[Dict]:
        """獲取網路搜索結果"""
        try:
            from utils.web_search import WebSearcher
            web_searcher = WebSearcher()
            search_file = web_searcher.search_and_save(query, "temp", is_group=False)
            if search_file:
                content = web_searcher.read_search_results(search_file)
                return [{
                    'content': content,
                    'score': 0.5,  # 默認分數
                    'source': 'web'
                }]
            return []
        except Exception as e:
            logger.error(f"網路搜索時發生錯誤: {str(e)}", exc_info=True)
            return []

    def _get_supported_files(self, directory):
        """掃描目錄並返回所有支援的文件"""
        supported_extensions = {'.docx', '.txt', '.pdf', '.xlsx'}
        files = []
        
        try:
            # 遞迴掃描目錄
            for root, _, filenames in os.walk(directory):
                for filename in filenames:
                    ext = os.path.splitext(filename)[1].lower()
                    if ext in supported_extensions:
                        full_path = os.path.join(root, filename)
                        files.append(full_path)
                        logger.info(f"找到支援的文件: {full_path}")
        except Exception as e:
            logger.error(f"掃描目錄時發生錯誤 {directory}: {str(e)}")
        
        return files

    def _read_single_document(self, path):
        """讀取單個文件的內容"""
        try:
            ext = os.path.splitext(path)[1].lower()
            if ext == '.docx':
                return self._read_docx(path)
            elif ext == '.txt':
                return self._read_text(path)
            elif ext == '.pdf':
                return self._read_pdf(path)
            else:
                logger.warning(f"不支援的文件類型: {path}")
                return None
        except Exception as e:
            logger.error(f"讀取單個文件時發生錯誤: {str(e)}")
            return None

