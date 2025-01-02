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

# --- UI 設定 ---
st.set_page_config(page_title="Fight.K AI助手", page_icon="✝️", layout="wide")

st.title("Fight.K AI助手 ✝️")
st.write("我是 Fight.K AI助手，幫助你了解Fight.K")

# --- 側邊欄 (Sidebar) ---
st.sidebar.header("設定")
prompt_category = st.sidebar.selectbox(
    "問題類別：",
    ("FK helper", "FK teacher", "FK Prophet", "FK Business"), # 新增 "test" 選項
    format_func=lambda x: {
        "FK helper": "Fight.K 小幫手",
        "FK teacher": "FK裝備課程",
        "FK Prophet": "Fight.K 策士",
        "FK Business": "Fight.K 商業專家"
    }.get(x, x)
)
show_knowledge = st.sidebar.checkbox("顯示相關知識", value=False)

# --- 主畫面 ---
user_input = st.text_input("請輸入你的問題：", key="user_input")

if st.button("送出"):
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
    else:
        st.warning("請輸入問題！")

# --- 頁尾 ---
st.write("---")
st.markdown("© 2025 Fight.K AI助手 ✝️")