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
        
        # 修改限制
        self.max_content_length = 500   # 每個網頁最大字數改為 500
        self.max_total_length = 2500    # 總字數限制 (5個網頁合計)
        
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
    
    def search_and_save(self, query: str, source_id: str, is_group: bool = False) -> str:
        """
        搜尋 Google 並保存結果到臨時文件
        source_id: 用戶ID或群組ID
        is_group: 是否為群組搜尋
        """
        try:
            # 先清除該來源的歷史記錄
            if is_group:
                self._clear_group_search_history(source_id)
            else:
                self._clear_user_search_history(source_id)
            
            logger.info(f"開始搜尋查詢: {query}")
            results = []
            total_length = 0
            
            # 修改搜尋參數
            search_params = {
                'num': 5,              # 改為搜尋 5 個結果
                'lang': 'zh-TW',
                'stop': 5,             # 限制搜尋結果數量
                'pause': 2.0,
                'tld': 'com.tw',
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
                # 保存結果到臨時文件，使用不同的檔名前綴
                timestamp = datetime.now(pytz.UTC).strftime('%Y%m%d_%H%M%S')
                prefix = f"search_{'group' if is_group else 'personal'}_{source_id}_"
                temp_file = os.path.join(self.temp_dir, f"{prefix}{timestamp}.json")
                
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