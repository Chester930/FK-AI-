import os
import logging
import subprocess
import time
import yaml
import requests
from flask import Flask
from utils.cache_manager import CacheManager
from utils.web_search import WebSearcher
from utils.chat_history import ChatHistory
from utils.youtube_handler import YouTubeHandler
from core.ai_engine import AIEngine
from core.prompts import PromptManager
from config import KNOWLEDGE_BASE_PATHS

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_app():
    # 創建 Flask app
    app = Flask(__name__)
    
    # 初始化所有組件
    app.config['cache_manager'] = CacheManager()
    app.config['web_searcher'] = WebSearcher(app.config['cache_manager'])
    app.config['chat_history'] = ChatHistory(max_history=10)
    app.config['youtube_handler'] = YouTubeHandler()
    app.config['ai_engine'] = AIEngine()
    app.config['prompt_manager'] = PromptManager()
    
    # 導入視圖函數
    from ui.line_bot_ui import initialize_line_bot
    initialize_line_bot(app)
    
    return app

def start_line_bot():
    try:
        logger.info("Starting LINE Bot service...")
        print("-" * 50)
        
        # 建立 ngrok 設定檔
        ngrok_config = {
            "version": "2",
            "authtoken": os.environ.get("NGROK_AUTH_TOKEN"),
            "tunnels": {
                "line-bot": {
                    "proto": "http",
                    "addr": "5000"
                }
            }
        }
        
        config_path = "ngrok.yml"
        with open(config_path, "w") as f:
            yaml.dump(ngrok_config, f)
        
        # 啟動 ngrok
        ngrok_process = subprocess.Popen(["ngrok", "start", "line-bot", "--config", config_path])
        
        # 等待 ngrok 啟動
        time.sleep(5)
        
        # 獲取 ngrok 公開網址
        try:
            response = requests.get("http://localhost:4040/api/tunnels")
            ngrok_url = response.json()["tunnels"][0]["public_url"]
            logger.info(f"Ngrok URL: {ngrok_url}")
            
            webhook_url = f"{ngrok_url}/callback"
            logger.info(f"LINE Bot Webhook URL: {webhook_url}")
            
            print(f"\n✅ Ngrok 轉發網址: {ngrok_url}")
            print(f"✅ LINE Bot Webhook URL: {webhook_url}")
            print("\n請將上述 Webhook URL 設定到 LINE Developers Console")
            print("網址: https://developers.line.biz/console/")
            print(f"\n📝 Ngrok 狀態面板: http://localhost:4040")
            print("-" * 50)
            
            # 創建並啟動 Flask 應用
            app = create_app()
            app.run(host='0.0.0.0', port=5000)
            
        except Exception as e:
            logger.error(f"Error getting ngrok URL: {str(e)}")
            ngrok_process.terminate()
            raise
            
    except Exception as e:
        logger.error(f"Error starting LINE Bot: {str(e)}")
    finally:
        if os.path.exists(config_path):
            os.remove(config_path)

if __name__ == "__main__":
    start_line_bot()
