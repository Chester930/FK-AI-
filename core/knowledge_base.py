import os
import re
import docx
import openpyxl
import fitz  # PyMuPDF
import jieba
import json

# 將專案根目錄加入到 sys.path
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import KNOWLEDGE_BASE_PATHS

class KnowledgeBase:
    def __init__(self, paths_config):
        self.paths_config = paths_config
        
    def search(self, query: str):
        """根據查詢搜尋相關知識"""
        results = []
        
        # 根據關鍵字選擇合適的知識庫
        relevant_paths = self._select_relevant_paths(query)
        
        for path_info in relevant_paths:
            path = path_info['path']
            try:
                # 讀取文件內容
                if os.path.isfile(path):
                    with open(path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        results.append({
                            'content': content,
                            'path': path,
                            'description': path_info['description']
                        })
            except Exception as e:
                logger.error(f"讀取文件時發生錯誤 {path}: {str(e)}")
                continue
            
        return self._format_results(results)

    def _format_results(self, results):
        """格式化搜尋結果"""
        formatted_text = ""
        for result in results:
            formatted_text += f"=== {result['description']} ===\n"
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

