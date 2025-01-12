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
        self.max_content_length = 800  # 每個網頁的最大字數
        self.max_total_length = 2400   # 總字數限制 (3個網頁合計)
        
    def search_and_save(self, query: str) -> str:
        """
        搜尋 Google 並保存結果到臨時文件
        返回臨時文件路徑
        """
        try:
            logger.info(f"開始搜尋查詢: {query}")
            results = []
            total_length = 0
            
            # 修改搜尋參數，使用正確的參數名稱
            search_params = {
                'num': 3,              # 改用 'num' 而不是 'num_results'
                'lang': 'zh-TW',
                'stop': 3,            # 限制搜尋結果數量
                'pause': 2.0,         # 搜尋間隔
                'tld': 'com.tw',      # 使用台灣的 Google 網域
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
            
            logger.info("開始 Google 搜尋...")
            try:
                # 直接使用必要的參數
                search_results = list(search(
                    query,
                    num=search_params['num'],
                    stop=search_params['stop'],
                    pause=search_params['pause'],
                    lang=search_params['lang'],
                    tld=search_params['tld'],
                    user_agent=search_params['user_agent']
                ))
                logger.info(f"找到 {len(search_results)} 個搜尋結果")
            except Exception as search_error:
                logger.error(f"Google 搜尋失敗: {str(search_error)}")
                # 如果搜尋失敗，返回空結果
                return None
            
            # 獲取搜尋結果
            for url in search_results:
                try:
                    logger.info(f"正在處理 URL: {url}")
                    headers = {
                        'User-Agent': search_params['user_agent'],
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                        'Accept-Language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7',
                    }
                    
                    # 使用 session 來處理請求
                    with requests.Session() as session:
                        session.headers.update(headers)
                        response = session.get(url, timeout=10)
                        response.raise_for_status()  # 檢查回應狀態
                        response.encoding = 'utf-8'
                    
                    # 解析 HTML
                    logger.info("正在解析網頁內容...")
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # 移除腳本和樣式標籤
                    for script in soup(["script", "style"]):
                        script.decompose()
                    
                    # 獲取純文字內容
                    text = soup.get_text()
                    
                    # 清理文字
                    lines = (line.strip() for line in text.splitlines())
                    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                    text = ' '.join(chunk for chunk in chunks if chunk)
                    
                    # 限制每個網頁的文字長度
                    if len(text) > self.max_content_length:
                        text = text[:self.max_content_length] + "..."
                    
                    # 檢查總字數限制
                    if total_length + len(text) > self.max_total_length:
                        text = text[:self.max_total_length - total_length] + "..."
                        
                    total_length += len(text)
                    
                    logger.info(f"成功處理網頁，內容長度: {len(text)}")
                    results.append({
                        'url': url,
                        'content': text
                    })
                    
                except Exception as e:
                    logger.error(f"處理網頁時發生錯誤 {url}: {str(e)}", exc_info=True)
                    continue
            
            if results:
                # 保存結果到臨時文件
                timestamp = datetime.now(pytz.UTC).strftime('%Y%m%d_%H%M%S')
                temp_file = os.path.join(self.temp_dir, f"search_{timestamp}.json")
                
                logger.info(f"正在保存搜尋結果到: {temp_file}")
                with open(temp_file, 'w', encoding='utf-8') as f:
                    json.dump(results, f, ensure_ascii=False, indent=2)
                
                logger.info("搜尋過程完成")
                return temp_file
            else:
                logger.warning("沒有找到任何搜尋結果")
                return None
            
        except Exception as e:
            logger.error(f"搜尋過程中發生錯誤: {str(e)}", exc_info=True)
            return None
            
    def read_search_results(self, file_path: str) -> str:
        """讀取搜尋結果"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                results = json.load(f)
            
            # 組合所有結果
            combined_text = ""
            for i, result in enumerate(results, 1):
                combined_text += f"\n來源 {i}: {result['url']}\n"
                combined_text += f"內容摘要：{result['content']}\n"
            
            return combined_text
            
        except Exception as e:
            logger.error(f"讀取搜尋結果時發生錯誤: {str(e)}")
            return "" 