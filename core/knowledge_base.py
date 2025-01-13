import os
import re
import docx
import openpyxl
import fitz  # PyMuPDF
import jieba
import json
import logging

# 設置日誌
logger = logging.getLogger(__name__)

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
                content = ""
                if os.path.isfile(path):
                    # 根據檔案類型讀取內容
                    if path.endswith('.xlsx'):
                        content = self._read_excel(path)
                    elif path.endswith('.docx'):
                        content = self._read_docx(path)
                    elif path.endswith('.txt'):
                        content = self._read_text(path)
                    elif path.endswith('.pdf'):
                        content = self._read_pdf(path)
                        
                    if content:
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

