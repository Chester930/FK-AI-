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
    def __init__(self, paths=None):
        """
        初始化知識庫
        Args:
            paths: 可以是單一路徑字串或路徑列表
        """
        if isinstance(paths, str):
            self.paths = [paths]
        elif isinstance(paths, list):
            self.paths = paths
        else:
            self.paths = []
        
        # 驗證路徑是否存在
        self.valid_paths = []
        for path in self.paths:
            if os.path.exists(path):
                self.valid_paths.append(path)
            else:
                print(f"Warning: Path does not exist: {path}")
        
        self.data = self.load_data()

    def load_data(self):
        """從多個路徑載入資料"""
        all_text = []
        for path in self.valid_paths:  # 只使用有效的路徑
            if os.path.isdir(path):
                all_text.append(self.read_folder(path))
            elif os.path.isfile(path):
                all_text.append(self.read_file(path))
        return "\n".join(all_text)

    def read_file(self, filepath):
        """根據檔案類型讀取檔案"""
        try:
            if filepath.endswith(".txt"):
                return self.read_txt(filepath)
            elif filepath.endswith(".docx"):
                return self.read_docx(filepath)
            elif filepath.endswith(".xlsx"):
                return self.read_xlsx(filepath)
            elif filepath.endswith(".pdf"):
                return self.read_pdf(filepath)
            elif filepath.endswith(".json"):
                return self.read_json(filepath)
            else:
                return ""
        except Exception as e:
            print(f"Error reading file {filepath}: {e}")
            return ""

    def read_txt(self, filepath):
        """Reads text from a .txt file."""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            print(f"Error reading TXT file {filepath}: {e}")
            return ""

    def read_docx(self, filepath):
        """Reads text from a .docx file."""
        try:
            doc = docx.Document(filepath)
            full_text = []
            for para in doc.paragraphs:
                full_text.append(para.text)
            return "\n".join(full_text)
        except Exception as e:
            print(f"Error reading DOCX file {filepath}: {e}")
            return ""

    def read_xlsx(self, filepath):
        """Reads text from a .xlsx file."""
        try:
            workbook = openpyxl.load_workbook(filepath, read_only=True)
            all_text = []
            
            # 先讀取說明文件（如果存在）
            description_file = filepath.rsplit('.', 1)[0] + '_description.txt'
            if os.path.exists(description_file):
                all_text.append(f"=== 檔案說明 ===\n{self.read_txt(description_file)}\n")
            
            # 讀取每個工作表
            for sheet in workbook:
                all_text.append(f"\n=== 工作表：{sheet.title} ===")
                
                # 獲取標題行
                headers = []
                for cell in next(sheet.iter_rows()):
                    headers.append(str(cell.value) if cell.value else '')
                
                # 讀取資料行
                for row in sheet.iter_rows(min_row=2):
                    row_data = []
                    for i, cell in enumerate(row):
                        if cell.value:
                            # 將標題和值配對
                            if i < len(headers) and headers[i]:
                                row_data.append(f"{headers[i]}: {cell.value}")
                            else:
                                row_data.append(str(cell.value))
                    if row_data:
                        all_text.append(" | ".join(row_data))
                        
            return "\n".join(all_text)
        except Exception as e:
            print(f"Error reading XLSX file {filepath}: {e}")
            return ""

    def read_pdf(self, filepath):
        """Reads text from a PDF file."""
        try:
            all_text = []
            # 使用 PyMuPDF
            with fitz.open(filepath) as doc:
                for page in doc:
                    all_text.append(page.get_text())
            return "\n".join(all_text)
        except Exception as e:
            print(f"Error reading PDF file {filepath}: {e}")
            return ""
    
    def read_json(self, filepath):
        """Reads data from a JSON file."""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                # 使用 json.dumps() 將字典轉換成字串
                return json.dumps(json.load(f), ensure_ascii=False, indent=4) + "\n"
        except Exception as e:
            print(f"Error reading JSON file {filepath}: {e}")
            return ""

    def read_folder(self, folderpath):
        """Recursively reads text from all files in a folder."""
        all_text = []
        
        # 先讀取資料夾說明文件（如果存在）
        folder_description = os.path.join(folderpath, "_folder_description.txt")
        if os.path.exists(folder_description):
            all_text.append(f"\n=== 資料夾：{os.path.basename(folderpath)} ===")
            all_text.append(self.read_txt(folder_description))
        
        try:
            for item in os.listdir(folderpath):
                filepath = os.path.join(folderpath, item)
                
                # 跳過說明文件和隱藏檔案
                if item.startswith('.') or item.startswith('_'):
                    continue
                    
                if os.path.isfile(filepath):
                    if filepath.endswith(('.txt', '.docx', '.xlsx', '.pdf', '.json')):
                        content = self.read_file(filepath)
                        if content:
                            all_text.append(f"\n=== 檔案：{item} ===")
                            all_text.append(content)
                elif os.path.isdir(filepath):
                    subfolder_content = self.read_folder(filepath)
                    if subfolder_content:
                        all_text.append(subfolder_content)
                        
            return "\n".join(all_text)
        except Exception as e:
            print(f"Error reading folder {folderpath}: {e}")
            return ""

    def search(self, query):
        """Searches the knowledge base for a query.

        Args:
            query (str): The search query.

        Returns:
            str: A relevant portion of the knowledge base.
        """
        if not self.data:
            return "目前沒有相關資料。"

        # 使用 jieba 進行分詞
        query_words = jieba.lcut(query)

        # 將資料分成段落
        paragraphs = self.data.split('\n\n')
        
        # 計算每個段落的相關性分數
        scored_paragraphs = []
        for para in paragraphs:
            if len(para.strip()) < 10:  # 跳過太短的段落
                continue
            score = sum(1 for word in query_words if word.lower() in para.lower())
            if score > 0:
                scored_paragraphs.append((score, para))
        
        # 根據分數排序並選擇最相關的段落
        scored_paragraphs.sort(reverse=True)
        relevant_paragraphs = [p[1] for p in scored_paragraphs[:3]]
        
        if not relevant_paragraphs:
            return "找不到相關資訊。"
        
        return "\n\n".join(relevant_paragraphs)

