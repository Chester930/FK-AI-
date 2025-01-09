import sys
import os
import time  # 添加 time 模組
import yaml  # 添加 yaml 模組
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, request, abort
# 更新 LINE Bot SDK 導入
from linebot.v3 import (
    WebhookHandler
)
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage
)
from linebot.v3.webhooks import (
    MessageEvent,
    TextMessageContent
)
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging.models import (
    QuickReply,
    QuickReplyItem,
    MessageAction,
    TextMessage
)
import subprocess
import json
import os
from dotenv import load_dotenv
import logging

from core.ai_engine import AIEngine
from core.knowledge_base import KnowledgeBase
from core.prompts import PromptManager
from config import KNOWLEDGE_BASE_PATHS, LINE_CHANNEL_SECRET, LINE_CHANNEL_ACCESS_TOKEN

load_dotenv()  # 加載 .env 檔案中的環境變數

app = Flask(__name__)

# 設置日誌
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# 初始化 LINE Bot API
configuration = Configuration(access_token=os.environ.get('LINE_CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.environ.get('LINE_CHANNEL_SECRET'))

with ApiClient(configuration) as api_client:
    line_bot_api = MessagingApi(api_client)

# Initialize core components
ai_engine = AIEngine()
prompt_manager = PromptManager()

# Store user states (可以之後改用 Redis 或資料庫)
user_states = {}

# 定義角色選項
ROLE_OPTIONS = {
    'A': 'FK helper',
    'B': 'FK teacher',
    'C': 'FK Prophet',
    'D': 'FK Business'
}

ROLE_DESCRIPTIONS = {
    'A': 'Fight.K 小幫手',
    'B': 'Fight.K 裝備課程',
    'C': 'Fight.K 策士',
    'D': 'Fight.K 商業專家'
}

def create_role_selection_message():
    """建立角色選擇的快速回覆選單"""
    quick_reply_items = [
        QuickReplyItem(
            action=MessageAction(
                label=f"{key}: {ROLE_DESCRIPTIONS[key]}", 
                text=key
            )
        ) for key in ROLE_OPTIONS.keys()
    ]
    
    return TextMessage(
        text="歡迎使用 Fight.K AI 助手！\n\n" + \
             "請選擇您想要諮詢的對象：\n" + \
             "\n".join([f"{key}: {ROLE_DESCRIPTIONS[key]}" for key in ROLE_OPTIONS.keys()]) + \
             "\n\n💡 提示：您隨時可以輸入「切換身分」來重新選擇諮詢對象",
        quick_reply=QuickReply(items=quick_reply_items)
    )

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    logger.info("Request body: %s", body)
    
    try:
        handler.handle(body, signature)
        logger.info("Message handled successfully")
    except InvalidSignatureError:
        logger.error("Invalid signature")
        abort(400)
    except Exception as e:
        logger.error(f"Error handling message: {e}")
        abort(500)
    return 'OK'

@handler.add(MessageEvent)
def handle_message(event):
    logger.info(f"Received message event: {event}")
    if not isinstance(event.message, TextMessageContent):
        logger.info("Not a text message")
        return
        
    user_id = event.source.user_id
    text = event.message.text.strip()
    logger.info(f"Processing message: {text} from user: {user_id}")
    
    try:
        # 如果使用者尚未選擇角色或輸入 "切換身分"
        if user_id not in user_states or text.lower() == "切換身分":
            user_states[user_id] = {"role": None}
            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[create_role_selection_message()]
                )
            )
            logger.info("Sent role selection message")
            return

        # 處理角色選擇
        if text in ROLE_OPTIONS:
            user_states[user_id]["role"] = ROLE_OPTIONS[text]
            response = (
                f"您已選擇 {ROLE_DESCRIPTIONS[text]}，請問有什麼我可以協助您的嗎？\n\n"
                "💡 如果要更換諮詢對象，隨時可以輸入「切換身分」"
            )
            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=response)]
                )
            )
            logger.info(f"User selected role: {ROLE_OPTIONS[text]}")
            return

        # 處理一般對話
        current_role = user_states[user_id]["role"]
        logger.info(f"Current role for user {user_id}: {current_role}")
        
        if not current_role:
            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text="請先選擇一個諮詢對象。")]
                )
            )
            logger.info("Asked user to select role first")
            return
            
        prompt = f"你現在是 {current_role} 的角色。\n\n問題：{text}\n回答："
        response = ai_engine.generate_response(prompt)
        logger.info(f"AI response generated: {response[:100]}...")
        
        if not response:
            response = "抱歉，我現在無法回答。請稍後再試。"
            
        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=response)]
            )
        )
        logger.info("Response sent successfully")
        
    except Exception as e:
        logger.error(f"Error in handle_message: {e}", exc_info=True)
        error_message = "系統發生錯誤，請稍後再試"
        try:
            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=error_message)]
                )
            )
        except Exception as reply_error:
            logger.error(f"Error sending error message: {reply_error}", exc_info=True)

if __name__ == "__main__":
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
        
        # 啟動 ngrok
        ngrok_process = subprocess.Popen(["ngrok", "start", "line-bot", "--config", config_path])
        
        # 等待 ngrok 啟動
        time.sleep(3)
        
        try:
            print('LINE Bot 已啟動於 port 5000')
            app.run(port=5000)
        finally:
            # 確保程序結束時關閉 ngrok
            ngrok_process.terminate()
            
    except Exception as e:
        print(f"啟動時發生錯誤: {str(e)}")
    finally:
        if os.path.exists(config_path):
            os.remove(config_path)