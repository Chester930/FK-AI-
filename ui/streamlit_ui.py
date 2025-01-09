import sys
import os
import logging

# 將專案根目錄加入到 sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from core.ai_engine import AIEngine
from core.knowledge_base import KnowledgeBase
from core.prompts import PromptManager
from config import KNOWLEDGE_BASE_PATHS

# Initialize the core components
ai_engine = AIEngine()
prompt_manager = PromptManager()

# Initialize session state for chat history if it doesn't exist
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

# --- UI 設定 ---
st.set_page_config(page_title="Fight.K AI助手", page_icon="✝️", layout="wide")

st.title("Fight.K AI助手 ✝️")
st.write("我是 Fight.K AI助手，幫助你了解Fight.K")

# --- 側邊欄 (Sidebar) ---
st.sidebar.header("設定")
prompt_category = st.sidebar.selectbox(
    "問題類別：",
    ("FK helper", "FK teacher", "FK Prophet", "FK Business"),
    format_func=lambda x: {
        "FK helper": "Fight.K 小幫手",
        "FK teacher": "Fight.K 裝備課程",
        "FK Prophet": "Fight.K 策士",
        "FK Business": "Fight.K 商業專家"
    }.get(x, x)
)

# --- 聊天區域 ---
# 顯示聊天歷史
for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 輸入區域 ---
# 使用兩個 columns 用於主要輸入區
col1, col2 = st.columns([0.925, 0.075])

with col1:
    user_input = st.chat_input("請輸入你的問題：")

with col2:
    if st.button("🧹", help="清除對話歷史"):
        st.session_state.chat_history = []
        st.rerun()

# 上傳區域使用自適應寬度
uploaded_file = st.file_uploader(
    "拖曳檔案到此處或點擊上傳",
    type=["txt", "pdf", "doc", "docx"],
    help="上傳文件 (最大 200MB)\n支援格式：TXT, PDF, DOC, DOCX"
)

if uploaded_file:
    st.info(f"已上傳：{uploaded_file.name}")

# 添加日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 處理使用者輸入
if user_input:
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    
    with st.spinner("思考中..."):
        try:
            # 添加日誌
            logger.info(f"Processing input for category: {prompt_category}")
            
            # Initialize KnowledgeBase with the selected category
            knowledge_base = KnowledgeBase(KNOWLEDGE_BASE_PATHS[prompt_category])
            relevant_knowledge = knowledge_base.search(user_input)
            
            # 添加檢查
            if not relevant_knowledge:
                logger.warning("No relevant knowledge found")
                relevant_knowledge = "無相關資料"
            
            prompt = prompt_manager.get_prompt(prompt_category)
            
            if not prompt:
                raise ValueError(f"找不到 {prompt_category} 的提示詞")
                
            full_prompt = f"{prompt}\n\n背景知識：\n{relevant_knowledge}\n\n問題：{user_input}\n回答："
            
            # 添加日誌
            logger.info("Generating AI response...")
            
            # Generate a response with timeout
            response = ai_engine.generate_response(full_prompt)
            
            if not response:
                raise ValueError("AI 未能生成回應")
                
            # 添加 AI 回應到歷史記錄
            st.session_state.chat_history.append({"role": "assistant", "content": response})
            
            # 顯示相關知識在可展開的區域中
            with st.expander("參考資料", expanded=False):
                st.text(relevant_knowledge)

        except Exception as e:
            logger.error(f"Error occurred: {str(e)}", exc_info=True)
            st.error(f"發生錯誤：{str(e)}")
            # 添加錯誤到聊天歷史
            st.session_state.chat_history.append({
                "role": "assistant", 
                "content": f"抱歉，處理您的請求時發生錯誤。錯誤訊息：{str(e)}"
            })
        
        # 確保 AIEngine 的資源被正確釋放
        finally:
            if 'ai_engine' in locals():
                try:
                    ai_engine.close()  # 假設有 close 方法
                except:
                    pass
    
    # 重新載入頁面以更新聊天記錄
    st.rerun()

# --- 頁尾 ---
st.write("---")
st.markdown("© 2025 Fight.K AI助手 ✝️")