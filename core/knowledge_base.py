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

class KnowledgeBase:
    def __init__(self, paths_config):
        self.paths_config = paths_config
        
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
            
            # 1. 本地知識庫搜索
            vector_results = self.vector_store.search(
                query,
                top_k=role_settings['top_k'],
                min_score=role_settings['min_score']
            )
            
            results = []
            # 添加本地搜索結果
            for result in vector_results:
                results.append({
                    'content': result['content'],
                    'score': result['score'],
                    'source': 'local',
                    'weight': role_settings['local_weight']  # 本地權重
                })
                
            # 2. 網路搜索結果
            if role_settings['web_weight'] > 0:
                web_results = self._get_web_results(query)
                for result in web_results:
                    results.append({
                        'content': result['content'],
                        'score': result.get('score', 0.5),
                        'source': 'web',
                        'weight': role_settings['web_weight']  # 網路權重
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
            formatted_text += f"=== {source_type} (相關度: {result['score']:.2f}) ===\n"
            formatted_text += f"{result['content']}\n\n"
        return formatted_text.strip()

    def _select_relevant_paths(self, query):
        """選擇與查詢相關的知識庫路徑"""
        relevant_paths = []
        
        # 先檢查共同資料
        if 'common' in self.paths_config:
            for category_name, info in self.paths_config['common'].items():
                if any(keyword in query.lower() for keyword in info['keywords']):
                    relevant_paths.append({
                        'path': info['path'],
                        'priority': info['priority'],
                        'description': info['description']
                    })
        
        # 再檢查角色特定資料
        for role_name, categories in self.paths_config.items():
            if role_name != 'common':  # 跳過共同資料
                for category_name, info in categories.items():
                    if any(keyword in query.lower() for keyword in info['keywords']):
                        relevant_paths.append({
                            'path': info['path'],
                            'priority': info['priority'],
                            'description': info['description']
                        })
        
        # 按優先級排序
        relevant_paths.sort(key=lambda x: x['priority'])
        return relevant_paths

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

