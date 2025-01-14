import sys
import os
import time
import yaml
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, request, abort
from linebot.v3 import WebhookHandler
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage
)
from linebot.v3.webhooks import (
    MessageEvent,
    TextMessageContent,
    FileMessageContent,
    ImageMessageContent,
    AudioMessageContent,
    GroupSource,
    JoinEvent,
    LeaveEvent
)
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging.models import (
    QuickReply,
    QuickReplyItem,
    MessageAction,
    TextMessage
)
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv
from config import KNOWLEDGE_BASE_PATHS

# 載入環境變數
load_dotenv()

# 創建 Flask app
app = Flask(__name__)

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_role_selection_message():
    """創建角色選擇訊息"""
    return TextMessage(
        text="歡迎使用 Fight.K AI 助手！\n請選擇諮詢對象：\n" + \
             "\n".join([f"🔹 !{key}: {ROLE_DESCRIPTIONS[key]}" for key in ROLE_OPTIONS.keys()]) + \
             "\n\n💡💡 提示：\n1. 直接輸入 !A、!B、!C、!D 切換角色\n2. 輸入「!切換身分」重新選擇"
    )

# 添加角色選項和描述
ROLE_OPTIONS = {
    'A': 'FK helper',
    'B': 'FK teacher',
    'C': 'FK pastor',
    'D': 'FK counselor'
}

ROLE_DESCRIPTIONS = {
    'A': '一般諮詢助理',
    'B': 'Fight.K 教師',
    'C': 'Fight.K 牧者',
    'D': 'Fight.K 輔導員'
}

def initialize_line_bot(app):
    """初始化 LINE Bot 和相關組件"""
    global line_bot_api, handler, cache_manager, web_searcher, chat_history
    global youtube_handler, ai_engine, prompt_manager, scheduler
    
    try:
        # 初始化 LINE Bot API
        configuration = Configuration(access_token=os.environ.get('LINE_CHANNEL_ACCESS_TOKEN'))
        handler = WebhookHandler(os.environ.get('LINE_CHANNEL_SECRET'))
        
        with ApiClient(configuration) as api_client:
            line_bot_api = MessagingApi(api_client)
        
        # 從 app.config 獲取組件
        cache_manager = app.config['cache_manager']
        web_searcher = app.config['web_searcher']
        chat_history = app.config['chat_history']
        youtube_handler = app.config['youtube_handler']
        ai_engine = app.config['ai_engine']
        prompt_manager = app.config['prompt_manager']
        
        # 初始化排程器
        scheduler = BackgroundScheduler()
        scheduler.add_job(cache_manager.check_and_clear_inactive_caches, 'interval', minutes=1)
        scheduler.add_job(cache_manager.periodic_cleanup, 'interval', minutes=30)
        scheduler.start()
        
        # 清空快取
        cache_manager.clear_all_cache()
        logger.info("快取系統初始化完成")
        
        # 註冊路由
        @app.route("/callback", methods=['POST'])
        def callback():
            signature = request.headers['X-Line-Signature']
            body = request.get_data(as_text=True)
            
            try:
                handler.handle(body, signature)
            except InvalidSignatureError:
                abort(400)
                
            return 'OK'
            
        # 註冊訊息處理器
        @handler.add(MessageEvent, message=TextMessageContent)
        def handle_text_message(event):
            if isinstance(event.source, GroupSource):
                handle_group_message(event, event.source.group_id, event.message.text)
            else:
                handle_personal_message(event, event.source.user_id, event.message.text)
                
        logger.info("LINE Bot 初始化完成")
        
    except Exception as e:
        logger.error(f"初始化 LINE Bot 時發生錯誤: {str(e)}")
        raise

def handle_personal_message(event, user_id: str, text: str):
    reply_token = event.reply_token
    try:
        # 檢查用戶狀態
        user_state = chat_history.get_state(user_id)
        
        # 移除驚嘆號並檢查是否為角色選擇
        clean_text = text.strip('!')
        
        # 確保新用戶或重啟後的用戶都會看到歡迎訊息
        if not user_state or 'role' not in user_state:
            chat_history.set_state(user_id, {"role": None})
            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[create_role_selection_message()]
                )
            )
            return
            
        # 檢查是否要求切換身分
        if text.lower() in ["!切換身分", "!切換角色", "!重新選擇"]:
            chat_history.set_state(user_id, {"role": None})
            cache_manager.clear_user_cache(user_id)
            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[create_role_selection_message()]
                )
            )
            return
            
        # 檢查是否直接選擇角色
        if clean_text in ROLE_OPTIONS:
            selected_role = ROLE_OPTIONS[clean_text]
            chat_history.set_state(user_id, {"role": selected_role})
            
            try:
                # 載入角色資料到快取
                cache_manager.load_common_data(user_id, KNOWLEDGE_BASE_PATHS)
                cache_manager.load_role_data(user_id, selected_role, KNOWLEDGE_BASE_PATHS)
                
                response = f"已切換到 {ROLE_DESCRIPTIONS[clean_text]} 模式，請問有什麼我可以協助的嗎？"
                line_bot_api.reply_message(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[TextMessage(text=response)]
                    )
                )
                return
                
            except Exception as e:
                logger.error(f"載入角色資料時發生錯誤: {str(e)}")
                line_bot_api.reply_message(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[TextMessage(text="選擇角色時發生錯誤，請稍後再試。")]
                    )
                )
                return
            
    except Exception as e:
        logger.error(f"處理個人訊息時發生錯誤: {str(e)}")
        try:
            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=reply_token,
                    messages=[TextMessage(text="抱歉，處理訊息時發生錯誤。")]
                )
            )
        except Exception as reply_error:
            logger.error(f"發送錯誤訊息失敗: {str(reply_error)}")

def handle_group_message(event, group_id: str, text: str):
    try:
        # 檢查群組狀態
        group_state = chat_history.get_state(group_id, is_group=True) or {}
        
        # 移除驚嘆號並檢查是否為角色選擇
        clean_text = text.strip('!')
        
        # 檢查是否要求切換身分
        if text.lower() in ["!切換身分", "!切換角色", "!重新選擇"]:
            chat_history.set_state(group_id, {"role": None}, is_group=True)
            cache_manager.clear_user_cache(group_id, is_group=True)
            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[create_role_selection_message()]
                )
            )
            return
            
        # 檢查是否直接選擇角色
        if clean_text in ROLE_OPTIONS:
            selected_role = ROLE_OPTIONS[clean_text]
            chat_history.set_state(group_id, {"role": selected_role}, is_group=True)
            
            try:
                cache_manager.load_common_data(group_id, KNOWLEDGE_BASE_PATHS, is_group=True)
                cache_manager.load_role_data(group_id, selected_role, KNOWLEDGE_BASE_PATHS, is_group=True)
                response = f"已切換到 {ROLE_DESCRIPTIONS[clean_text]} 模式，請問有什麼我可以協助的嗎？"
                line_bot_api.reply_message(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[TextMessage(text=response)]
                    )
                )
                return
            except Exception as e:
                logger.error(f"載入角色資料時發生錯誤: {str(e)}")
                line_bot_api.reply_message(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[TextMessage(text="選擇角色時發生錯誤，請稍後再試。")]
                    )
                )
                return
                
        # 處理一般對話
        current_role = group_state.get("role")
        if not current_role:
            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[create_role_selection_message()]
                )
            )
            return
            
        # 添加一般對話處理邏輯
        context = chat_history.format_context(group_id, is_group=True)
        prompt = f"你現在是 {current_role} 的角色。\n\n{context}問題：{text}\n回答："
        response = ai_engine.generate_response(prompt)
        
        chat_history.add_message(group_id, "user", text, is_group=True)
        chat_history.add_message(group_id, "assistant", response, is_group=True)
        
        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=response)]
            )
        )
            
    except Exception as e:
        logger.error(f"處理群組訊息時發生錯誤: {str(e)}")
        try:
            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text="抱歉，處理訊息時發生錯誤。")]
                )
            )
        except Exception as reply_error:
            logger.error(f"發送錯誤訊息失敗: {str(reply_error)}")