import argparse
import sys
import os
import subprocess
import time
import yaml
import requests
import json
import logging
from pathlib import Path
import shutil

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

def get_ngrok_url():
    """獲取 ngrok 的公開 URL"""
    try:
        response = requests.get('http://localhost:4040/api/tunnels')
        tunnels = json.loads(response.text)['tunnels']
        return next((tunnel['public_url'] for tunnel in tunnels if tunnel['proto'] == 'https'), None)
    except Exception as e:
        logger.error(f"Error getting ngrok URL: {e}")
        return None

def ensure_dependencies():
    """確保必要的依賴都已安裝"""
    try:
        # 檢查 ffmpeg
        ffmpeg_path = None
        if sys.platform.startswith('win'):
            # Windows: 檢查環境變數
            ffmpeg_path = shutil.which('ffmpeg.exe')
        else:
            # Linux/Mac: 檢查常見路徑
            ffmpeg_path = shutil.which('ffmpeg')
            
        if not ffmpeg_path:
            logger.warning("""
            未找到 ffmpeg，語音功能可能無法正常工作。
            請安裝 ffmpeg:
            - Windows: https://ffmpeg.org/download.html
            - Linux: sudo apt-get install ffmpeg
            - Mac: brew install ffmpeg
            """)
    except Exception as e:
        logger.error(f"檢查依賴時發生錯誤: {e}")

def ensure_directories():
    """確保必要的目錄存在"""
    directories = ['data', 'temp', 'logs']
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
    ensure_dependencies()  # 添加依賴檢查

def run_streamlit():
    """運行 Streamlit 界面"""
    try:
        import streamlit.web.cli as stcli
        sys.argv = ["streamlit", "run", "ui/streamlit_ui.py"]
        logger.info("Starting Streamlit interface...")
        sys.exit(stcli.main())
    except Exception as e:
        logger.error(f"Error running Streamlit: {e}")
        sys.exit(1)

def run_line_bot():
    """運行 LINE Bot 服務"""
    try:
        # 檢查環境變數
        required_env_vars = ['LINE_CHANNEL_SECRET', 'LINE_CHANNEL_ACCESS_TOKEN', 'NGROK_AUTH_TOKEN']
        missing_vars = [var for var in required_env_vars if not os.environ.get(var)]
        if missing_vars:
            logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
            sys.exit(1)

        # 檢查必要的套件
        try:
            import torch
            import sentence_transformers
            logger.info(f"PyTorch version: {torch.__version__}")
            logger.info(f"Sentence-transformers version: {sentence_transformers.__version__}")
        except ImportError as e:
            logger.error(f"Required package not found: {e}")
            logger.error("Please run: pip install torch sentence-transformers")
            sys.exit(1)

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
        
        # 清除終端機畫面
        os.system('cls' if os.name == 'nt' else 'clear')
        
        logger.info("Starting LINE Bot service...")
        print("-" * 50)
        
        # 啟動 ngrok
        ngrok_process = subprocess.Popen(
            ["ngrok", "start", "line-bot", "--config", config_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # 等待 ngrok 啟動
        time.sleep(3)
        
        # 獲取並顯示 ngrok URL
        ngrok_url = get_ngrok_url()
        if ngrok_url:
            logger.info(f"Ngrok URL: {ngrok_url}")
            logger.info(f"LINE Bot Webhook URL: {ngrok_url}/callback")
            print(f"\n✅ Ngrok 轉發網址: {ngrok_url}")
            print(f"✅ LINE Bot Webhook URL: {ngrok_url}/callback")
            print("\n請將上述 Webhook URL 設定到 LINE Developers Console")
            print("網址: https://developers.line.biz/console/")
            print("\n📝 Ngrok 狀態面板: http://localhost:4040")
        else:
            logger.error("Could not get ngrok URL")
            raise Exception("Failed to get ngrok URL")
        
        print("-" * 50)
        
        try:
            from ui.line_bot_ui import app
            logger.info("LINE Bot service started on port 5000")
            print('\n🚀 LINE Bot 服務已啟動於 port 5000')
            print('按下 Ctrl+C 可以停止服務\n')
            app.run(port=5000)
        finally:
            ngrok_process.terminate()
            
    except Exception as e:
        logger.error(f"Error starting LINE Bot: {e}", exc_info=True)
        sys.exit(1)
    finally:
        if os.path.exists(config_path):
            os.remove(config_path)

if __name__ == "__main__":
    # 確保必要的目錄存在
    ensure_directories()
    
    parser = argparse.ArgumentParser(description='Run Fight.K AI Assistant')
    parser.add_argument('--mode', type=str, choices=['streamlit', 'line', 'admin'], 
                       required=True, help='Choose the UI mode: streamlit, line, or admin')
    
    args = parser.parse_args()
    
    try:
        if args.mode == 'streamlit':
            run_streamlit()
        elif args.mode == 'line':
            run_line_bot()
        elif args.mode == 'admin':
            try:
                import streamlit.web.cli as stcli
                sys.argv = ["streamlit", "run", "ui/admin_ui.py"]
                logger.info("Starting admin interface...")
                sys.exit(stcli.main())
            except Exception as e:
                logger.error(f"Error running admin interface: {e}")
                sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Application stopped by user")
    except Exception as e:
        logger.error(f"Application error: {e}")
        sys.exit(1)
