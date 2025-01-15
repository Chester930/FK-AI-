import sys
import os

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

# 定義角色對應的中文名稱和描述
ROLE_DESCRIPTIONS = {
    "FK helper": {
        "name": "Fight.K 小幫手",
        "description": "您是「Fight.K 小幫手」，你會依照提供的背景知識來回答問題..."
    },
    "FK teacher": {
        "name": "FK裝備課程",
        "description": "您是「Fight.K 教師」，一位精通聖經、Fight.K 理念和歷史的專家..."
    },
    "FK Prophet": {
        "name": "Fight.K 策士",
        "description": "Fight.K 策士」，知道Fight.K的目標與方向，現階段執行的計畫，並且提供使用者相關的資料。你會依照提供的背景知識來回答問題。："
    },
    "FK Business": {
        "name": "Fight.K 商業專家",
        "description": "您是「Fight.K 商業專家」，擅長引用聖經的經文與商業結合，探討商業的問題，並使用聖經的觀點。擅長使用比喻來提出簡潔且專業的回應。你會依照提供的背景知識來回答問題。："
    }
}

# --- UI 設定 ---
st.set_page_config(page_title="Fight.K AI助手", page_icon="✝️", layout="wide")

st.title("Fight.K AI助手 ✝️")

# 根據選擇的角色顯示對應描述
prompt_category = st.sidebar.selectbox(
    "問題類別：",
    list(ROLE_DESCRIPTIONS.keys()),
    format_func=lambda x: ROLE_DESCRIPTIONS[x]["name"]
)

# 顯示當前角色的描述
st.write(ROLE_DESCRIPTIONS[prompt_category]["description"])

show_knowledge = st.sidebar.checkbox("顯示相關知識", value=False)

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
    try:
        # 顯示上傳狀態
        with st.spinner(f"處理檔案 {uploaded_file.name} 中..."):
            # 讀取檔案內容
            file_content = uploaded_file.read()
            
            # 根據檔案類型處理內容
            file_type = uploaded_file.name.split('.')[-1].lower()
            
            if file_type == 'txt':
                # 處理文字檔
                content = file_content.decode('utf-8')
            elif file_type in ['pdf', 'doc', 'docx']:
                st.warning("PDF和Word文件的處理功能尚未實作")
                content = None
            
            if content:
                st.success(f"成功上傳：{uploaded_file.name}")
                with st.expander("查看檔案內容"):
                    st.text(content[:500] + "..." if len(content) > 500 else content)
            
    except Exception as e:
        st.error(f"檔案處理時發生錯誤：{str(e)}")

# 處理使用者輸入
if user_input:
    with st.spinner("思考中..."):
        try:
            # Initialize KnowledgeBase with the selected category
            knowledge_base = KnowledgeBase(KNOWLEDGE_BASE_PATHS[prompt_category])

            # Retrieve relevant knowledge (if any)
            relevant_knowledge = knowledge_base.search(user_input)
            
            # Get a prompt based on user input or a default one
            prompt = prompt_manager.get_prompt(prompt_category)
            
            if not prompt:
                st.error(f"找不到 {prompt_category} 的提示詞")
            else:
                # 修改提示詞組合方式
                full_prompt = f"{prompt}\n\n背景知識：\n{relevant_knowledge}\n\n問題：{user_input}\n回答："

            # Generate a response
            response = ai_engine.generate_response(full_prompt)
            
            st.write("---")
            st.markdown(f"**Fight.K AI助手 ✝️:** {response}")

            if show_knowledge and relevant_knowledge:
                with st.expander("顯示相關知識"):
                    st.text(relevant_knowledge)

            # 在初始化 KnowledgeBase 之前添加
            st.write("Debug: Selected category paths:")
            for path in KNOWLEDGE_BASE_PATHS[prompt_category]:
                st.write(f"Checking path: {path}")
                st.write(f"Path exists: {os.path.exists(path)}")

        except Exception as e:
            st.error(f"發生錯誤：{str(e)}")

# --- 頁尾 ---
st.write("---")
st.markdown("© 2025 Fight.K AI助手 ✝️")