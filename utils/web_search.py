import logging
from googlesearch import search
import requests
from bs4 import BeautifulSoup
import os
import json
from datetime import datetime
import pytz

logger = logging.getLogger(__name__)

class WebSearcher:
    def __init__(self):
        self.temp_dir = "temp/web_search"
        os.makedirs(self.temp_dir, exist_ok=True)
        self.max_content_length = 500   # 每個網頁最大字數
        self.max_results_per_search = 3  # 每次搜尋的結果數
        
    def _clear_user_search_history(self, user_id: str):
        """清除特定用戶的搜尋紀錄"""
        try:
            prefix = f"search_personal_{user_id}_"
            if os.path.exists(self.temp_dir):
                for file in os.listdir(self.temp_dir):
                    if file.startswith(prefix):
                        file_path = os.path.join(self.temp_dir, file)
                        try:
                            if os.path.isfile(file_path):
                                os.remove(file_path)
                                logger.info(f"已刪除用戶搜尋記錄: {file}")
                        except Exception as e:
                            logger.error(f"刪除檔案時發生錯誤 {file_path}: {str(e)}")
            logger.info(f"用戶 {user_id} 的搜尋歷史記錄已清除")
        except Exception as e:
            logger.error(f"清除用戶搜尋歷史時發生錯誤: {str(e)}")

    def _clear_group_search_history(self, group_id: str):
        """清除特定群組的搜尋紀錄"""
        try:
            prefix = f"search_group_{group_id}_"
            if os.path.exists(self.temp_dir):
                for file in os.listdir(self.temp_dir):
                    if file.startswith(prefix):
                        file_path = os.path.join(self.temp_dir, file)
                        try:
                            if os.path.isfile(file_path):
                                os.remove(file_path)
                                logger.info(f"已刪除群組搜尋記錄: {file}")
                        except Exception as e:
                            logger.error(f"刪除檔案時發生錯誤 {file_path}: {str(e)}")
            logger.info(f"群組 {group_id} 的搜尋歷史記錄已清除")
        except Exception as e:
            logger.error(f"清除群組搜尋歷史時發生錯誤: {str(e)}")
    
    def extract_keywords(self, query: str) -> list:
        """從查詢中提取關鍵字"""
        try:
            # 先用 AI 分析問題
            prompt = (
                "請從以下問題中提取3-5個最重要的關鍵字，以逗號分隔：\n"
                f"問題：{query}\n"
                "關鍵字："
            )
            keywords = ai_engine.generate_response(prompt).strip()
            return [k.strip() for k in keywords.split(',')]
        except Exception as e:
            logger.error(f"提取關鍵字時發生錯誤: {str(e)}")
            return [query]  # 如果失敗就返回原始查詢

    def search_and_save(self, query: str, source_id: str, is_group: bool = False) -> str:
        """執行兩次搜尋並保存結果"""
        try:
            # 清除歷史記錄
            if is_group:
                self._clear_group_search_history(source_id)
            else:
                self._clear_user_search_history(source_id)
            
            # 提取關鍵字
            keywords = self.extract_keywords(query)
            logger.info(f"提取的關鍵字: {keywords}")
            
            results = []
            total_length = 0
            
            # 執行兩次搜尋
            for search_round in range(2):
                # 根據搜尋輪次調整關鍵字
                if search_round == 0:
                    search_query = ' '.join(keywords[:2])  # 使用前兩個關鍵字
                else:
                    search_query = ' '.join(keywords[2:])  # 使用剩餘關鍵字
                
                logger.info(f"第 {search_round + 1} 輪搜尋: {search_query}")
                
                # 搜尋參數
                search_params = {
                    'num': self.max_results_per_search,
                    'lang': 'zh-TW',
                    'stop': self.max_results_per_search,
                    'pause': 2.0,
                    'tld': 'com.tw'
                }
                
                try:
                    search_results = list(search(
                        search_query,
                        **search_params
                    ))
                    logger.info(f"找到 {len(search_results)} 個搜尋結果")
                    
                    # 處理每個搜尋結果
                    for url in search_results:
                        content = self._get_page_content(url)
                        if content and len(content) > 0:
                            # 限制內容長度
                            if len(content) > self.max_content_length:
                                content = content[:self.max_content_length] + "..."
                            
                            results.append({
                                'url': url,
                                'content': content,
                                'search_round': search_round + 1
                            })
                            
                except Exception as e:
                    logger.error(f"搜尋過程發生錯誤: {str(e)}")
                    continue
            
            if results:
                # 保存結果
                timestamp = datetime.now(pytz.UTC).strftime('%Y%m%d_%H%M%S')
                prefix = f"search_{'group' if is_group else 'personal'}_{source_id}_"
                temp_file = os.path.join(self.temp_dir, f"{prefix}{timestamp}.json")
                
                with open(temp_file, 'w', encoding='utf-8') as f:
                    json.dump(results, f, ensure_ascii=False, indent=2)
                
                return temp_file
                
            return None
            
        except Exception as e:
            logger.error(f"搜尋過程中發生錯誤: {str(e)}")
            return None

    def read_search_results(self, file_path: str) -> str:
        """讀取並格式化搜尋結果"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                results = json.load(f)
            
            formatted_text = ""
            for round_num in [1, 2]:  # 分別處理兩輪搜尋結果
                round_results = [r for r in results if r['search_round'] == round_num]
                if round_results:
                    formatted_text += f"\n=== 第 {round_num} 輪搜尋結果 ===\n"
                    for i, result in enumerate(round_results, 1):
                        formatted_text += f"\n來源 {i}: {result['url']}\n"
                        formatted_text += f"內容摘要：{result['content']}\n"
            
            return formatted_text.strip()
            
        except Exception as e:
            logger.error(f"讀取搜尋結果時發生錯誤: {str(e)}")
            return "" 