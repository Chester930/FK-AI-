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
from config import KNOWLEDGE_BASE_PATHS, LINE_CHANNEL_SECRET, LINE_CHANNEL_ACCESS_TOKEN, FILE_SETTINGS
from utils.scheduled_messages import MessageScheduler
from utils.chat_history import ChatHistory

load_dotenv()  # 加載 .env 檔案中的環境變數

app = Flask(__name__)

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
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

# 初始化 ChatHistory
chat_history = ChatHistory(max_history=10)

# 自我介紹訊息
INTRODUCTION_MESSAGE = """
歡迎使用 Fight.K AI 助手！👋

我是您的智能助理，可以協助您了解 Fight.K 的各個面向。請選擇您想要諮詢的對象：

{role_options}

💡 提示：您隨時可以輸入「切換身分」來重新選擇諮詢對象
"""

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
    
    role_options_text = "\n".join([f"🔹 {key}: {ROLE_DESCRIPTIONS[key]}" for key in ROLE_OPTIONS.keys()])
    
    return TextMessage(
        text=INTRODUCTION_MESSAGE.format(role_options=role_options_text),
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

def handle_personal_message(event, user_id: str, text: str):
    """處理個人對話消息"""
    try:
        # 檢查是否要求切換身分
        if text.lower() in ["切換身分", "切換角色", "重新選擇"]:
            chat_history.set_state(user_id, {"role": None})
            # 使用預定義的歡迎訊息和角色選擇
            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[create_role_selection_message()]
                )
            )
            return

        # 檢查是否是新用戶或沒有角色
        user_state = chat_history.get_state(user_id)
        if not user_state or user_state.get("role") is None:
            chat_history.set_state(user_id, {"role": None})
            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[create_role_selection_message()]
                )
            )
            return

        # 處理角色選擇
        if text in ROLE_OPTIONS:
            selected_role = ROLE_OPTIONS[text]
            chat_history.set_state(user_id, {"role": selected_role})
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
            return

        # 處理一般對話
        current_role = user_state.get("role")
        if not current_role:
            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[create_role_selection_message()]
                )
            )
            return

        # 獲取對話歷史並生成回應
        context = chat_history.format_context(user_id)
        prompt = f"你現在是 {current_role} 的角色。\n\n{context}問題：{text}\n回答："
        
        response = ai_engine.generate_response(prompt)
        
        # 保存對話歷史
        chat_history.add_message(user_id, "user", text)
        chat_history.add_message(user_id, "assistant", response)
        
        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=response)]
            )
        )
        
    except Exception as e:
        logger.error(f"Error in handle_personal_message: {e}", exc_info=True)
        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text="系統發生錯誤，請稍後再試")]
            )
        )

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
                text="歡迎使用 Fight.K AI 助手！\n請使用 !A、!B、!C 或 !D 選擇諮詢對象：\n" + \
                     "\n".join([f"🔹 !{key}: {ROLE_DESCRIPTIONS[key]}" for key in ROLE_OPTIONS.keys()]) + \
                     "\n\n💡 提示：您可以隨時輸入「!切換身分」來重新選擇諮詢對象"
            )
            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[welcome_message]
                )
            )
            return

        # 檢查是否是新群組
        group_state = chat_history.get_state(group_id, is_group=True)
        if not group_state:
            chat_history.set_state(group_id, {"role": None}, is_group=True)
            welcome_message = TextMessage(
                text="歡迎使用 Fight.K AI 助手！\n請使用 !A、!B、!C 或 !D 選擇諮詢對象：\n" + \
                     "\n".join([f"🔹 !{key}: {ROLE_DESCRIPTIONS[key]}" for key in ROLE_OPTIONS.keys()]) + \
                     "\n\n💡 提示：您可以隨時輸入「!切換身分」來重新選擇諮詢對象"
            )
            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[welcome_message]
                )
            )
            return

        # 處理角色選擇 (移除前綴後的文字應該匹配 ROLE_OPTIONS 的鍵)
        if text in ROLE_OPTIONS:
            selected_role = ROLE_OPTIONS[text]
            chat_history.set_state(group_id, {"role": selected_role}, is_group=True)
            response = (
                f"已為此群組選擇 {ROLE_DESCRIPTIONS[text]}，請問有什麼我可以協助的嗎？\n\n"
                "💡 如果要更換諮詢對象，請輸入「!切換身分」"
            )
            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=response)]
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

# 修改主要的 handle_message 函數
@handler.add(MessageEvent)
def handle_message(event):
    """處理所有接收到的消息"""
    logger.info(f"Received message event: {event}")
    
    # 檢查是否為文字消息
    if not isinstance(event.message, TextMessageContent):
        logger.info("Not a text message")
        return
        
    text = event.message.text.strip()
    
    try:
        # 區分群組和個人消息
        if isinstance(event.source, GroupSource):
            group_id = event.source.group_id
            handle_group_message(event, group_id, text)
        else:
            user_id = event.source.user_id
            handle_personal_message(event, user_id, text)
            
    except Exception as e:
        logger.error(f"Error in handle_message: {e}", exc_info=True)
        try:
            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text="系統發生錯誤，請稍後再試")]
                )
            )
        except Exception as reply_error:
            logger.error(f"Error sending error message: {reply_error}", exc_info=True)

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

# 添加定期保存對話歷史的功能
def save_chat_history():
    """定期保存對話歷史"""
    try:
        chat_history.save_to_file('data/chat_history.json')
        logger.info("Chat history saved successfully")
    except Exception as e:
        logger.error(f"Error saving chat history: {e}", exc_info=True)

# 在應用啟動時載入歷史記錄
try:
    chat_history.load_from_file('data/chat_history.json')
    logger.info("Chat history loaded successfully")
except Exception as e:
    logger.error(f"Error loading chat history: {e}", exc_info=True)

# 設置定期保存
scheduler = BackgroundScheduler()
scheduler.add_job(save_chat_history, 'interval', minutes=30)
scheduler.start()

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