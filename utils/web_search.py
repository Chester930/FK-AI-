import logging
from googlesearch import search
import requests
from bs4 import BeautifulSoup
import os
import json
from datetime import datetime
import pytz
from core.ai_engine import AIEngine

logger = logging.getLogger(__name__)

class WebSearcher:
    def __init__(self):
        self.temp_dir = "temp/web_search"
        os.makedirs(self.temp_dir, exist_ok=True)
        self.max_content_length = 500   # 每個網頁最大字數
        self.max_results_per_search = 3  # 每次搜尋的結果數
        self.ai_engine = AIEngine()  # 初始化 AI 引擎
        
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
    
    def extract_search_queries(self, query: str) -> tuple:
        """從問題中提取兩組不同的搜尋關鍵字"""
        try:
            # 直接分析關鍵字，不依賴 AI
            keywords = []
            
            # 第一組：新聞相關關鍵字
            if '最新' in query or '更新' in query or '現在' in query:
                keywords.append('最新消息')
            
            # 提取地點
            locations = []
            if '洛杉磯' in query:
                locations.append('洛杉磯')
            elif '台灣' in query:
                locations.append('台灣')
            # ... 其他地點判斷
            
            # 提取事件類型
            events = []
            if '野火' in query or '山火' in query:
                events.append('野火')
            elif '地震' in query:
                events.append('地震')
            # ... 其他事件類型判斷
            
            # 組合第一組搜尋詞
            query1 = f"{' '.join(locations)} {' '.join(events)} 最新情況"
            
            # 第二組：細節相關關鍵字
            query2 = f"{' '.join(locations)} {' '.join(events)} 影響範圍 傷亡"
            
            logger.info(f"生成搜尋關鍵字 - 第一組: {query1}")
            logger.info(f"生成搜尋關鍵字 - 第二組: {query2}")
            
            return query1.strip(), query2.strip()
            
        except Exception as e:
            logger.error(f"提取搜尋關鍵字時發生錯誤: {str(e)}")
            return "最新消息 " + query, "詳細資訊 " + query

    def get_search_keywords(self, query: str) -> tuple:
        """使用 AI 生成搜尋關鍵字"""
        try:
            prompt = (
                "你是一個搜尋關鍵字優化專家。請將以下問題轉換成兩組搜尋關鍵字：\n"
                "1. 第一組關鍵字應該著重在最新資訊\n"
                "2. 第二組關鍵字應該著重在深入細節\n"
                "3. 每組關鍵字使用 2-4 個字\n"
                "4. 關鍵字應該使用最常用的表達方式\n"
                "5. 不要加入無關的字詞\n\n"
                f"問題：{query}\n\n"
                "請使用以下格式回答：\n"
                "第一組：關鍵字1 關鍵字2\n"
                "第二組：關鍵字3 關鍵字4"
            )
            
            response = self.ai_engine.generate_response(prompt)
            
            # 解析 AI 回應
            lines = response.strip().split('\n')
            if len(lines) >= 2:
                query1 = lines[0].replace('第一組：', '').strip()
                query2 = lines[1].replace('第二組：', '').strip()
                
                logger.info(f"AI 生成搜尋關鍵字 - 第一組: {query1}")
                logger.info(f"AI 生成搜尋關鍵字 - 第二組: {query2}")
                
                return query1, query2
            else:
                raise ValueError("AI 回應格式不正確")
            
        except Exception as e:
            logger.error(f"AI 生成關鍵字時發生錯誤: {str(e)}")
            # 如果 AI 生成失敗，使用備用的關鍵字提取方法
            return self.extract_search_queries(query)

    def search_and_save(self, query: str, source_id: str, is_group: bool = False) -> str:
        """執行搜尋流程"""
        try:
            # 清除歷史記錄
            if is_group:
                self._clear_group_search_history(source_id)
            else:
                self._clear_user_search_history(source_id)
            
            # 使用 AI 生成搜尋關鍵字
            query1, query2 = self.get_search_keywords(query)
            logger.info(f"最終搜尋關鍵字 - 第一組: {query1}")
            logger.info(f"最終搜尋關鍵字 - 第二組: {query2}")
            
            results = []
            search_queries = [query1, query2]
            
            # 執行兩次搜尋
            for round_num, search_query in enumerate(search_queries, 1):
                logger.info(f"第 {round_num} 輪搜尋: {search_query}")
                
                # 搜尋參數
                search_params = {
                    'num': 3,              # 每次搜尋3個結果
                    'lang': 'zh-TW',
                    'stop': 3,
                    'pause': 2.0,
                    'tld': 'com.tw'
                }
                
                try:
                    search_results = list(search(search_query, **search_params))
                    
                    # 處理搜尋結果
                    for url in search_results:
                        content = self._get_page_content(url)
                        if content:
                            # 限制內容長度為500字
                            content = content[:500] + ("..." if len(content) > 500 else "")
                            results.append({
                                'url': url,
                                'content': content,
                                'search_round': round_num,
                                'keywords': search_query
                            })
                            
                except Exception as e:
                    logger.error(f"第 {round_num} 輪搜尋時發生錯誤: {str(e)}")
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

    def _get_page_content(self, url: str) -> str:
        """獲取網頁內容"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # 處理編碼
            if 'charset' not in response.headers.get('content-type', '').lower():
                response.encoding = response.apparent_encoding
            
            # 解析 HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 移除不需要的標籤
            for tag in soup(['script', 'style', 'nav', 'footer', 'iframe']):
                tag.decompose()
            
            # 獲取文字內容
            text = soup.get_text(separator=' ', strip=True)
            
            # 清理文字
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            return text
            
        except Exception as e:
            logger.error(f"獲取網頁內容時發生錯誤 {url}: {str(e)}")
            return "" 