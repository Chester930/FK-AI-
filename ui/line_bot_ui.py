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
    TextMessageContent,
    FileMessageContent,  # 添加檔案訊息類型
    ImageMessageContent,  # 添加圖片訊息類型
    AudioMessageContent,  # 添加音訊訊息類型
    GroupSource,  # 添加群組來源類型
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
import subprocess
import json
import os
from dotenv import load_dotenv
import logging
import pandas as pd
from docx import Document
from PIL import Image
import pytesseract
import PyPDF2
import io
import cv2
import numpy as np
import speech_recognition as sr
from pydub import AudioSegment
import tempfile
from apscheduler.schedulers.background import BackgroundScheduler

from core.ai_engine import AIEngine
from core.knowledge_base import KnowledgeBase
from core.prompts import PromptManager
from config import KNOWLEDGE_BASE_PATHS, LINE_CHANNEL_SECRET, LINE_CHANNEL_ACCESS_TOKEN, FILE_SETTINGS, ADMIN_GROUP_ID, ADMIN_COMMANDS
from utils.scheduled_messages import MessageScheduler
from utils.chat_history import ChatHistory
from utils.web_search import WebSearcher
from utils.youtube_handler import YouTubeHandler
from utils.simple_cache import SimpleCache

load_dotenv()  # 加載 .env 檔案中的環境變數

app = Flask(__name__)

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Store user states (可以之後改用 Redis 或資料庫)
user_states = {}

# LINE Bot 配置
configuration = Configuration(
    access_token=os.environ.get('LINE_CHANNEL_ACCESS_TOKEN')
)

# 創建 WebhookHandler
handler = WebhookHandler(os.environ.get('LINE_CHANNEL_SECRET'))

class LineBotUI:
    def __init__(self):
        self.configuration = configuration
        self.handler = handler
        # 修改 KnowledgeBase 初始化，傳入配置
        self.knowledge_base = KnowledgeBase(paths_config=KNOWLEDGE_BASE_PATHS)
        self.ai_engine = AIEngine()
        self.prompt_manager = PromptManager()
        self.chat_history = ChatHistory(max_history=10)
        self.web_searcher = WebSearcher()
        self.youtube_handler = YouTubeHandler()
        self.cache = SimpleCache(max_size=1000, ttl=3600)

    def handle_personal_message(self, event, user_id: str, text: str):
        """處理個人對話消息"""
        reply_token = event.reply_token
        try:
            # 獲取或初始化用戶狀態
            user_state = user_states.get(user_id, {})
            
            # 處理角色選擇
            if text in ['A', 'B', 'C', 'D']:
                role = ROLE_OPTIONS[text]
                user_state['role'] = role
                user_states[user_id] = user_state
                
                with ApiClient(self.configuration) as api_client:
                    line_bot_api = MessagingApi(api_client)
                    line_bot_api.reply_message(
                        ReplyMessageRequest(
                            reply_token=reply_token,
                            messages=[TextMessage(text=f"已切換到 {ROLE_DESCRIPTIONS[text]} 模式")]
                        )
                    )
                return
                
            # 檢查是否已選擇角色
            if 'role' not in user_state:
                with ApiClient(self.configuration) as api_client:
                    line_bot_api = MessagingApi(api_client)
                    line_bot_api.reply_message(
                        ReplyMessageRequest(
                            reply_token=reply_token,
                            messages=[create_role_selection_message()]
                        )
                    )
                return
                
            current_role = user_state['role']
            
            # 檢查快取
            cached_response = self.cache.get(current_role, text)
            if cached_response:
                with ApiClient(self.configuration) as api_client:
                    line_bot_api = MessagingApi(api_client)
                    line_bot_api.reply_message(
                        ReplyMessageRequest(
                            reply_token=reply_token,
                            messages=[TextMessage(text=cached_response)]
                        )
                    )
                return
            
            # 搜索知識庫
            knowledge_results = self.knowledge_base.search(text, current_role)
            
            # 進行網路搜索
            search_file = self.web_searcher.search_and_save(text, user_id, is_group=False)
            if search_file:
                web_results = self.web_searcher.read_search_results(search_file)
            else:
                web_results = "無法獲取網路搜索結果"
            
            # 組合搜索結果
            combined_results = f"""
知識庫結果：
{knowledge_results}

網路搜索結果：
{web_results}
"""
            
            # 獲取對話歷史
            chat_context = self.chat_history.format_context(user_id)
            
            # 生成 prompt
            prompt = self.prompt_manager.get_prompt(current_role)
            
            # 組合完整的 prompt
            full_prompt = (
                f"{prompt}\n\n"
                f"相關資訊：\n{combined_results}\n\n"
                f"歷史對話：\n{chat_context}\n\n"
                f"問題：{text}\n"
                f"回答："
            )
            
            # 生成回應
            response = self.ai_engine.generate_response(full_prompt)
            
            # 設置快取
            self.cache.set(current_role, text, response)
            
            # 更新對話歷史
            self.chat_history.add_message(user_id, "user", text)
            self.chat_history.add_message(user_id, "assistant", response)
            
            # 發送回應
            with ApiClient(self.configuration) as api_client:
                line_bot_api = MessagingApi(api_client)
                line_bot_api.reply_message(
                    ReplyMessageRequest(
                        reply_token=reply_token,
                        messages=[TextMessage(text=response)]
                    )
                )
            
        except Exception as e:
            logger.error(f"處理訊息時發生錯誤: {str(e)}", exc_info=True)
            try:
                with ApiClient(self.configuration) as api_client:
                    line_bot_api = MessagingApi(api_client)
                    line_bot_api.reply_message(
                        ReplyMessageRequest(
                            reply_token=reply_token,
                            messages=[TextMessage(text="抱歉，處理您的訊息時發生錯誤。")]
                        )
                    )
            except Exception as reply_error:
                logger.error(f"發送錯誤訊息失敗: {str(reply_error)}")

    def handle_group_message(self, event):
        """處理群組消息"""
        try:
            text = event.message.text
            group_id = event.source.group_id
            reply_token = event.reply_token
            
            # 檢查是否為管理員群組
            admin_group_id = "Ca38140041deeb2d703b16cb45b8f3bf1"  # 從 README 中看到的管理員群組 ID
            
            # 處理管理員群組的命令
            if group_id == admin_group_id and text.startswith('!'):
                command = text[1:].split(' ')[0]  # 獲取命令部分
                
                if command == 'help':
                    response = """可用指令：
1. !help - 顯示所有可用指令
2. !schedule YYYYMMDD-HH:MM group_id message - 設定新的排程通知
3. !schedules - 查看所有排程
4. !remove_schedule schedule_id - 刪除指定排程
5. !groups - 查看所有群組"""
                
                elif command == 'schedule':
                    # 解析排程命令
                    parts = text[1:].split(' ', 3)  # 分割成 ['schedule', 'datetime', 'group_id', 'message']
                    if len(parts) >= 4:
                        _, datetime_str, target_group_id, message = parts
                        result = self.message_scheduler.schedule_message(target_group_id, datetime_str, message)
                        response = "排程設定成功！" if result else "排程設定失敗"
                    else:
                        response = "格式錯誤。正確格式：!schedule YYYYMMDD-HH:MM group_id message"
                
                elif command == 'schedules':
                    schedules = self.message_scheduler.list_schedules()
                    if schedules:
                        response = "目前的排程：\n" + "\n".join([
                            f"ID: {s['id']}\n時間: {s['scheduled_time']}\n訊息: {s['message']}\n"
                            for s in schedules
                        ])
                    else:
                        response = "目前沒有排程"
                
                elif command == 'remove_schedule':
                    parts = text[1:].split()
                    if len(parts) == 2:
                        schedule_id = parts[1]
                        if self.message_scheduler.remove_schedule(schedule_id):
                            response = f"排程 {schedule_id} 已刪除"
                        else:
                            response = f"找不到排程 {schedule_id}"
                    else:
                        response = "格式錯誤。正確格式：!remove_schedule schedule_id"
                
                elif command == 'groups':
                    # 讀取群組資訊
                    with open('data/line_groups.json', 'r', encoding='utf-8') as f:
                        groups = json.load(f)
                    response = "群組列表：\n" + "\n".join([
                        f"ID: {group_id}\n名稱: {group_info if isinstance(group_info, str) else group_info.get('name', 'Unknown')}"
                        for group_id, group_info in groups.items()
                    ])
                
                else:
                    response = "未知的命令。使用 !help 查看可用命令。"
                
                # 發送回應
                with ApiClient(self.configuration) as api_client:
                    line_bot_api = MessagingApi(api_client)
                    line_bot_api.reply_message(
                        ReplyMessageRequest(
                            reply_token=reply_token,
                            messages=[TextMessage(text=response)]
                        )
                    )
            
            # 處理一般群組的消息
            else:
                # 檢查是否有人提到 bot
                if '@Fight.K AI' in text:
                    # 移除 @Fight.K AI 並處理剩餘文本
                    query = text.replace('@Fight.K AI', '').strip()
                    if query:
                        # 使用與個人對話相同的邏輯處理問題
                        knowledge_results = self.knowledge_base.search(query, "FK helper")
                        search_file = self.web_searcher.search_and_save(query, group_id, is_group=True)
                        if search_file:
                            web_results = self.web_searcher.read_search_results(search_file)
                        else:
                            web_results = "無法獲取網路搜索結果"
                        
                        # 組合結果並生成回應
                        combined_results = f"知識庫結果：\n{knowledge_results}\n\n網路搜索結果：\n{web_results}"
                        response = self.ai_engine.generate_response(combined_results)
                        
                        # 發送回應
                        with ApiClient(self.configuration) as api_client:
                            line_bot_api = MessagingApi(api_client)
                            line_bot_api.reply_message(
                                ReplyMessageRequest(
                                    reply_token=reply_token,
                                    messages=[TextMessage(text=response)]
                                )
                            )
                
        except Exception as e:
            logger.error(f"處理群組訊息時發生錯誤: {str(e)}", exc_info=True)

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
    
    # 修改歡迎訊息格式
    welcome_message = (
        "請先選擇諮詢對象：\n"
        f"🔹 A: {ROLE_DESCRIPTIONS['A']}\n"
        f"🔹 B: {ROLE_DESCRIPTIONS['B']}\n"
        f"🔹 C: {ROLE_DESCRIPTIONS['C']}\n"
        f"🔹 D: {ROLE_DESCRIPTIONS['D']}\n\n"
        "💡 提示：\n"
        "1. 直接輸入 A、B、C、D 切換角色\n"
        "2. 輸入「切換身分」重新選擇"
    )
    
    return TextMessage(
        text=welcome_message,
        quick_reply=QuickReply(items=quick_reply_items)
    )

# 在 app 初始化後添加
message_scheduler = MessageScheduler()

# 更新 FILE_SETTINGS
FILE_SETTINGS = {
    'max_file_size': 10 * 1024 * 1024,  # 10MB
    'allowed_extensions': ['txt', 'xlsx', 'docx', 'jpg', 'jpeg', 'png', 'pdf', 'm4a', 'mp3', 'wav'],
    'temp_folder': 'temp'
}

def is_fightk_related(text: str) -> bool:
    """檢查文字是否與 Fight.K 相關"""
    keywords = [
        'fight.k', 'fk', '張蒙恩', '蒙恩哥', 
        'fight k', 'fightk', '張使徒', 
        '國際心教育', '心教育'
    ]
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in keywords)

def handle_group_message(event, group_id: str, text: str):
    """處理群組對話消息"""
    try:
        # 檢查是否有前綴（支持中英文驚嘆號）
        is_command = text.startswith(('!', '！'))
        if not is_command:
            return  # 不處理沒有前綴的消息

        # 移除前綴
        original_text = text
        text = text[1:].strip()

        # 特殊命令處理
        if original_text.lower() in ['!groupid', '！groupid']:
            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=f"群組 ID: {group_id}")]
                )
            )
            return

        # 檢查是否要求切換身分
        if text.lower() in ["切換身分", "切換角色", "重新選擇"]:
            chat_history.set_state(group_id, {"role": None}, is_group=True)
            welcome_message = TextMessage(
                text="歡迎使用 Fight.K AI 助手！\n請選擇諮詢對象：\n" + \
                     "\n".join([f"🔹 !{key}: {ROLE_DESCRIPTIONS[key]}" for key in ROLE_OPTIONS.keys()]) + \
                     "\n\n💡 提示：\n1. 直接輸入 !A、!B、!C、!D 切換角色\n2. 輸入「!切換身分」重新選擇"
            )
            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[welcome_message]
                )
            )
            return

        # 檢查是否直接選擇角色
        if text in ROLE_OPTIONS:
            selected_role = ROLE_OPTIONS[text]
            chat_history.set_state(group_id, {"role": selected_role}, is_group=True)
            response = (
                f"已切換到 {ROLE_DESCRIPTIONS[text]}，請問有什麼我可以協助您的嗎？\n\n"
                "💡 您可以：\n"
                "1. 直接輸入 !A、!B、!C、!D 切換角色\n"
                "2. 輸入「!切換身分」重新選擇\n"
                "3. 在訊息前加上 ! 來詢問問題"
            )
            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=response)]
                )
            )
            return

        # 檢查是否是新群組或沒有角色
        group_state = chat_history.get_state(group_id, is_group=True)
        if not group_state or 'role' not in group_state:
            chat_history.set_state(group_id, {"role": None}, is_group=True)
            welcome_message = TextMessage(
                text="歡迎使用 Fight.K AI 助手！\n請選擇諮詢對象：\n" + \
                     "\n".join([f"🔹 !{key}: {ROLE_DESCRIPTIONS[key]}" for key in ROLE_OPTIONS.keys()]) + \
                     "\n\n💡 提示：\n1. 直接輸入 !A、!B、!C、!D 切換角色\n2. 輸入「!切換身分」重新選擇"
            )
            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[welcome_message]
                )
            )
            return

        # 如果沒有選擇角色，提示選擇
        if group_state.get('role') is None:
            welcome_message = TextMessage(
                text="請先選擇諮詢對象：\n" + \
                     "\n".join([f"🔹 !{key}: {ROLE_DESCRIPTIONS[key]}" for key in ROLE_OPTIONS.keys()]) + \
                     "\n\n💡 提示：\n1. 直接輸入 !A、!B、!C、!D 切換角色\n2. 輸入「!切換身分」重新選擇"
            )
            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[welcome_message]
                )
            )
            return

        # 處理一般對話
        current_role = group_state.get("role") if group_state else None
        if not current_role:
            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text="請先使用 !A、!B、!C 或 !D 選擇一個諮詢對象。")]
                )
            )
            return

        # 獲取對話歷史並生成回應
        context = chat_history.format_context(group_id, is_group=True)
        prompt = f"你現在是 {current_role} 的角色。\n\n{context}問題：{text}\n回答："
        
        response = ai_engine.generate_response(prompt)
        
        # 保存對話歷史
        chat_history.add_message(group_id, "user", text, is_group=True)
        chat_history.add_message(group_id, "assistant", response, is_group=True)
        
        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=response)]
            )
        )
        
    except Exception as e:
        logger.error(f"Error in handle_group_message: {e}", exc_info=True)
        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text="系統發生錯誤，請稍後再試")]
            )
        )

# 創建 LineBotUI 實例
line_bot_ui = LineBotUI()

# 修改 handle_message 裝飾器函數
@handler.add(MessageEvent)
def handle_message(event):
    try:
        if isinstance(event.source, GroupSource):
            # ... group message handling ...
            pass
        else:
            # 處理個人訊息
            user_id = event.source.user_id
            message_text = event.message.text
            line_bot_ui.handle_personal_message(event, user_id, message_text)
            
    except Exception as e:
        logger.error(f"處理訊息時發生錯誤: {str(e)}", exc_info=True)
        try:
            with ApiClient(configuration) as api_client:
                line_bot_api = MessagingApi(api_client)
            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text="抱歉，處理訊息時發生錯誤。")]
                )
            )
        except Exception as reply_error:
            logger.error(f"發送錯誤訊息失敗: {str(reply_error)}")

def handle_admin_command(event):
    """處理管理員指令"""
    try:
        command = event.message.text.split()
        cmd = command[0].lower().replace('！', '!')  # 統一轉換為半形驚嘆號
        
        if cmd == '!help':
            help_text = (
                "管理員指令列表：\n"
                "!schedule [時間] [群組NID] [訊息] - 設定新的排程通知\n"
                "!schedules - 查看所有排程\n"
                "!remove_schedule [排程ID] - 刪除指定排程\n"
                "!groups - 查看所有群組\n\n"
                "群組指定方式：\n"
                "- 使用群組NID (例如：1、2、3)\n\n"
                "時間格式說明：\n"
                "YYYYMMDD-HH:MM - 完整日期，如 20240101-09:30\n"
                "YYYYMM-HH:MM - 指定年月，如 202401-09:30\n"
                "YYYY-HH:MM - 指定年，如 2024-09:30\n"
                "-HH:MM - 今天，如 -09:30\n"
                "1-HH:MM - 明天，如 1-09:30\n"
                "2-HH:MM - 後天，如 2-09:30\n\n"
                "範例：\n"
                "!schedule -09:30 1 早安！\n"
                "!schedule 1-09:30 2 明天早安！\n"
                "!remove_schedule s1234"
            )
            response = help_text
            
        elif cmd == '!groups':
            groups = message_scheduler.notification_manager.get_formatted_groups()
            response = "群組列表：\n" + "\n".join(
                f"群組 {g['nid']}: {g['name']}"
                for g in groups
            )
            
        elif cmd == '!schedule':
            if len(command) >= 4:
                datetime_str = command[1]
                group_nid = command[2]
                message = ' '.join(command[3:])
                
                # 通過 NID 獲取群組 ID
                group_id = message_scheduler.notification_manager.get_group_id_by_nid(group_nid)
                
                if not group_id:
                    response = f"找不到群組 {group_nid}，請使用 !groups 查看可用的群組編號"
                    raise ValueError(response)
                
                result = message_scheduler.schedule_message(
                    group_id=group_id,
                    datetime_str=datetime_str,
                    message=message
                )
                
                response = "排程設定成功！" if result else "排程設定失敗"
            else:
                response = "格式錯誤！正確格式：!schedule YYYYMMDD-HH:MM [群組NID] message"
        
        elif cmd == '!schedules':
            schedules = message_scheduler.list_schedules()
            if schedules:
                formatted_schedules = []
                for s in schedules:
                    nid = message_scheduler.notification_manager.get_nid_by_group_id(s['group_id'])
                    schedule_id = message_scheduler.notification_manager.format_schedule_id(s['id'])
                    formatted_schedules.append(
                        f"ID: {schedule_id}\n"
                        f"群組: {nid}\n"
                        f"時間: {s['scheduled_time']}\n"
                        f"訊息: {s['message']}"
                    )
                response = "目前的排程：\n\n" + "\n\n".join(formatted_schedules)
            else:
                response = "目前沒有排程"
                
        elif cmd == '!remove_schedule':
            if len(command) == 2:
                schedule_id = command[1]
                if message_scheduler.remove_schedule(schedule_id):
                    response = f"已刪除排程 {schedule_id}"
                else:
                    response = "刪除失敗，找不到指定的排程"
            else:
                response = "格式錯誤！正確格式：!remove_schedule schedule_id"
                
        else:
            response = "未知的指令。輸入 !help 查看可用指令。"

        # 統一的回覆處理
        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=response)]
            )
        )
            
    except Exception as e:
        logger.error(f"處理管理員指令時發生錯誤: {str(e)}", exc_info=True)
        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=f"執行指令時發生錯誤: {str(e)}")]
            )
        )

@app.route("/callback", methods=['POST'])
def callback():
    # 處理 webhook
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    
    return 'OK'

@handler.add(MessageEvent, message=FileMessageContent)
def handle_file(event):
    """處理檔案訊息"""
    try:
        # 獲取檔案資訊
        file_id = event.message.id
        file_name = event.message.file_name
        file_size = event.message.file_size
        file_type = file_name.split('.')[-1].lower()
        
        # 檢查檔案類型
        if file_type not in FILE_SETTINGS['allowed_extensions']:
            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=f"不支援的檔案類型：{file_type}\n支援的類型：{', '.join(FILE_SETTINGS['allowed_extensions'])}")]
                )
            )
            return
            
        # 檢查檔案大小
        if file_size > FILE_SETTINGS['max_file_size']:
            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=f"檔案太大，限制為 {FILE_SETTINGS['max_file_size']/1024/1024}MB")]
                )
            )
            return
        
        # 下載檔案
        with ApiClient(configuration) as api_client:
            api = MessagingApi(api_client)
            file_content = api.get_message_content(file_id)
            
            # 暫存檔案
            temp_path = f"temp/{file_id}_{file_name}"
            os.makedirs("temp", exist_ok=True)
            
            with open(temp_path, 'wb') as f:
                for chunk in file_content:
                    f.write(chunk)
            
            try:
                # 根據檔案類型處理
                content = ""
                if file_type == 'txt':
                    with open(temp_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                
                elif file_type == 'xlsx':
                    df = pd.read_excel(temp_path)
                    content = df.to_string()
                
                elif file_type == 'docx':
                    doc = Document(temp_path)
                    content = '\n'.join([paragraph.text for paragraph in doc.paragraphs])
                
                elif file_type in ['jpg', 'jpeg', 'png']:
                    # 讀取圖片
                    image = cv2.imread(temp_path)
                    # 轉換為灰度圖
                    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                    # OCR辨識
                    content = pytesseract.image_to_string(gray, lang='chi_tra+eng')
                    if not content.strip():
                        content = "這是一張圖片，但無法辨識出文字內容。"
                
                elif file_type == 'pdf':
                    pdf_text = []
                    with open(temp_path, 'rb') as file:
                        pdf_reader = PyPDF2.PdfReader(file)
                        for page in pdf_reader.pages:
                            pdf_text.append(page.extract_text())
                    content = '\n'.join(pdf_text)
                
                # 生成提示詞
                prompt = (
                    f"請分析以下{file_type}檔案的內容，並提供重點摘要：\n\n"
                    f"檔案名稱：{file_name}\n"
                    f"檔案內容：\n{content[:3000]}"  # 限制內容長度
                )
                
                # 使用 AI 引擎分析
                response = ai_engine.generate_response(prompt)
                
                # 回覆分析結果
                line_bot_api.reply_message(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[TextMessage(text=response)]
                    )
                )
                
            finally:
                # 清理暫存檔案
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                    
    except Exception as e:
        logger.error(f"處理檔案時發生錯誤: {str(e)}", exc_info=True)
        try:
            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text="抱歉，處理檔案時發生錯誤。")]
                )
            )
        except Exception as reply_error:
            logger.error(f"發送錯誤訊息失敗: {str(reply_error)}")

@handler.add(MessageEvent, message=ImageMessageContent)
def handle_image(event):
    """處理圖片訊息"""
    logger.info("收到圖片訊息")
    try:
        image_id = event.message.id
        logger.info(f"圖片 ID: {image_id}")
        
        with ApiClient(configuration) as api_client:
            api = MessagingApi(api_client)
            logger.info("開始下載圖片")
            response = api.get_message_content(
                message_id=image_id
            )
            
            # 建立暫存檔案
            temp_path = f"temp/{image_id}.jpg"
            logger.info(f"準備儲存圖片至: {temp_path}")
            os.makedirs("temp", exist_ok=True)
            
            # 儲存圖片
            with open(temp_path, 'wb') as f:
                for chunk in response.iter_content():
                    f.write(chunk)
            logger.info("圖片儲存成功")
            
            try:
                # 讀取圖片
                image = cv2.imread(temp_path)
                # 轉換為灰度圖
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                # OCR辨識
                text = pytesseract.image_to_string(gray, lang='chi_tra+eng')
                
                if text.strip():
                    # 生成提示詞
                    prompt = (
                        f"請分析以下圖片中的文字內容，並提供重點摘要：\n\n"
                        f"圖片文字內容：\n{text}"
                    )
                    
                    # 使用 AI 引擎分析
                    response = ai_engine.generate_response(prompt)
                else:
                    response = "這張圖片中沒有辨識到文字內容。"
                
                # 回覆分析結果
                line_bot_api.reply_message(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[TextMessage(text=response)]
                    )
                )
                
            finally:
                # 清理暫存檔案
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                    
    except Exception as e:
        logger.error(f"處理圖片時發生錯誤: {str(e)}", exc_info=True)
        try:
            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text="抱歉，處理圖片時發生錯誤。")]
                )
            )
        except Exception as reply_error:
            logger.error(f"發送錯誤訊息失敗: {str(reply_error)}")

@handler.add(MessageEvent, message=AudioMessageContent)
def handle_audio(event):
    """處理音訊訊息"""
    logger.info("收到音訊訊息")
    try:
        audio_id = event.message.id
        logger.info(f"音訊 ID: {audio_id}")
        
        with ApiClient(configuration) as api_client:
            api = MessagingApi(api_client)
            audio_content = api.get_message_content_by_id(message_id=audio_id)
            
            # 建立暫存檔案
            temp_audio_path = f"temp/{audio_id}.m4a"
            temp_wav_path = f"temp/{audio_id}.wav"
            os.makedirs("temp", exist_ok=True)
            
            # 儲存音訊檔案
            with open(temp_audio_path, 'wb') as f:
                for chunk in audio_content:
                    f.write(chunk)
            
            try:
                # 轉換音訊格式為 WAV
                audio = AudioSegment.from_file(temp_audio_path)
                audio.export(temp_wav_path, format="wav")
                
                # 使用 Speech Recognition 進行語音辨識
                recognizer = sr.Recognizer()
                with sr.AudioFile(temp_wav_path) as source:
                    audio_data = recognizer.record(source)
                    # 嘗試使用不同的語音辨識服務
                    try:
                        # 優先使用 Google Cloud Speech API（需要金鑰）
                        text = recognizer.recognize_google_cloud(
                            audio_data, 
                            language='zh-TW',
                            credentials_json=os.environ.get('GOOGLE_CLOUD_CREDENTIALS')
                        )
                    except:
                        # 備用：使用 Google Speech Recognition（免費版）
                        text = recognizer.recognize_google(
                            audio_data, 
                            language='zh-TW'
                        )
                
                # 生成提示詞
                prompt = (
                    f"請分析以下音訊轉錄的內容，並提供重點摘要：\n\n"
                    f"音訊內容：\n{text}"
                )
                
                # 使用 AI 引擎分析
                response = ai_engine.generate_response(prompt)
                
                # 回覆分析結果
                line_bot_api.reply_message(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[
                            TextMessage(text=f"音訊轉錄內容：\n{text}\n\n分析結果：\n{response}")
                        ]
                    )
                )
                
            finally:
                # 清理暫存檔案
                if os.path.exists(temp_audio_path):
                    os.remove(temp_audio_path)
                if os.path.exists(temp_wav_path):
                    os.remove(temp_wav_path)
                    
    except Exception as e:
        logger.error(f"處理音訊時發生錯誤: {str(e)}", exc_info=True)
        try:
            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text="抱歉，處理音訊時發生錯誤。")]
                )
            )
        except Exception as reply_error:
            logger.error(f"發送錯誤訊息失敗: {str(reply_error)}")

@handler.add(JoinEvent)
def handle_join(event):
    """處理機器人加入群組事件"""
    try:
        if isinstance(event.source, GroupSource):
            group_id = event.source.group_id
            
            # 獲取群組資訊
            with ApiClient(configuration) as api_client:
                line_bot_api = MessagingApi(api_client)
                group_summary = line_bot_api.get_group_summary(group_id)
                group_name = group_summary.group_name
                
                # 新增群組記錄
                if message_scheduler.notification_manager.add_group(group_id, group_name):
                    logger.info(f"已新增群組：{group_name} (ID: {group_id})")
                    
                    # 發送歡迎訊息
                    welcome_message = (
                        f"謝謝您邀請我加入「{group_name}」！\n"
                        "在群組中要呼叫我，請在訊息前加上 ! 符號\n"
                        "例如：!你好"
                    )
                    line_bot_api.reply_message(
                        ReplyMessageRequest(
                            reply_token=event.reply_token,
                            messages=[TextMessage(text=welcome_message)]
                        )
                    )
                else:
                    logger.error(f"新增群組失敗：{group_name} (ID: {group_id})")
                    
    except Exception as e:
        logger.error(f"處理加入群組事件時發生錯誤: {str(e)}", exc_info=True)

@handler.add(LeaveEvent)
def handle_leave(event):
    """處理機器人離開群組事件"""
    try:
        if isinstance(event.source, GroupSource):
            group_id = event.source.group_id
            
            # 移除群組記錄
            if message_scheduler.notification_manager.remove_group(group_id):
                logger.info(f"已移除群組記錄 (ID: {group_id})")
            else:
                logger.error(f"移除群組記錄失敗 (ID: {group_id})")
                
    except Exception as e:
        logger.error(f"處理離開群組事件時發生錯誤: {str(e)}", exc_info=True)

if __name__ == "__main__":
    try:
        # 清除對話歷史
        chat_history_file = 'data/chat_history.json'
        with open(chat_history_file, 'w', encoding='utf-8') as f:
            json.dump({
                "personal_history": {},
                "group_history": {},
                "personal_states": {},
                "group_states": {}
            }, f, ensure_ascii=False, indent=4)
        
        # 初始化一個全新的 chat_history 物件
        chat_history = ChatHistory(max_history=10)
        
        # 初始化 WebSearcher (會自動清除搜尋紀錄)
        web_searcher = WebSearcher()
        
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
            # 確保使用 /callback 路徑
            app.run(host='0.0.0.0', port=5000)  # 添加 host 參數
            
        finally:
            # 確保程序結束時關閉 ngrok
            ngrok_process.terminate()
            
    except Exception as e:
        print(f"啟動時發生錯誤: {str(e)}")
    finally:
        if os.path.exists(config_path):
            os.remove(config_path)