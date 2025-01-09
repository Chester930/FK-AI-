import argparse
import sys
import os
import subprocess
import time
import yaml
import requests
import json

def get_ngrok_url():
    try:
        # 獲取 ngrok 的 API 資訊
        response = requests.get('http://localhost:4040/api/tunnels')
        tunnels = json.loads(response.text)['tunnels']
        # 獲取 https 的 URL
        return next((tunnel['public_url'] for tunnel in tunnels if tunnel['proto'] == 'https'), None)
    except:
        return None

def run_streamlit():
    import streamlit.web.cli as stcli
    sys.argv = ["streamlit", "run", "ui/streamlit_ui.py"]
    sys.exit(stcli.main())

def run_line_bot():
    try:
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
        
        print("正在啟動 LINE Bot 服務...")
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
            print(f"\n✅ Ngrok 轉發網址: {ngrok_url}")
            print(f"✅ LINE Bot Webhook URL: {ngrok_url}/callback")
            print("\n請將上述 Webhook URL 設定到 LINE Developers Console")
            print("網址: https://developers.line.biz/console/")
            print("\n📝 Ngrok 狀態面板: http://localhost:4040")
        else:
            print("❌ 無法獲取 Ngrok URL")
        
        print("-" * 50)
        
        try:
            from ui.line_bot_ui import app
            print('\n🚀 LINE Bot 服務已啟動於 port 5000')
            print('按下 Ctrl+C 可以停止服務\n')
            app.run(port=5000)
        finally:
            ngrok_process.terminate()
            
    except Exception as e:
        print(f"\n❌ 啟動時發生錯誤: {str(e)}")
    finally:
        if os.path.exists(config_path):
            os.remove(config_path)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run Fight.K AI Assistant')
    parser.add_argument('--mode', type=str, choices=['streamlit', 'line'], 
                       required=True, help='Choose the UI mode: streamlit or line')
    
    args = parser.parse_args()
    
    if args.mode == 'streamlit':
        run_streamlit()
    elif args.mode == 'line':
        run_line_bot()
