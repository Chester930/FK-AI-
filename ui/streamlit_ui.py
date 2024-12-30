import sys
import os

# 將專案根目錄加入到 sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from core.ai_engine import AIEngine
from core.knowledge_base import KnowledgeBase
from core.prompts import PromptManager

# Initialize the core components
ai_engine = AIEngine()
knowledge_base = KnowledgeBase()
prompt_manager = PromptManager()

# --- UI 設定 ---
st.set_page_config(page_title="FK AI 神學博士", page_icon="✝️", layout="wide") # 設定網頁標題、圖示、版面

st.title("FK AI 神學博士 ✝️")
st.write("我是 FK AI 神學博士，你的 AI 神學夥伴。")

# --- 側邊欄 (Sidebar) ---
st.sidebar.header("設定")
prompt_category = st.sidebar.selectbox(
    "問題類別：",
    ("general_theology", "bible_interpretation", "church_history", "apologetics"),
    format_func=lambda x: {
        "general_theology": "一般神學問題",
        "bible_interpretation": "聖經經文解釋",
        "church_history": "教會歷史問題",
        "apologetics": "護教學問題"
    }.get(x, x)  # 將 key 映射為更友善的標籤
)
show_knowledge = st.sidebar.checkbox("顯示相關知識", value=False) # 可以根據需求增加選項

# --- 主畫面 ---
user_input = st.text_input("請輸入你的問題：", key="user_input")

if st.button("送出"):
    if user_input:
        with st.spinner("思考中..."):
            # Retrieve relevant knowledge (if any)
            relevant_knowledge = knowledge_base.search(user_input)

            # Get a prompt based on user input or a default one
            prompt = prompt_manager.get_prompt(prompt_category)

            # Combine the prompt, relevant knowledge, and user input for the AI
            if relevant_knowledge and show_knowledge:
                full_prompt = f"{prompt}\n\n相關知識：\n{relevant_knowledge}\n\n使用者：{user_input}\nAI："
            else:
                full_prompt = f"{prompt}\n使用者：{user_input}\nAI："

            # Generate a response
            response = ai_engine.generate_response(full_prompt, user_input)

        st.write("---")  # 分隔線
        
        # 使用 Markdown 格式化輸出
        st.markdown(f"**FK AI 神學博士:** {response}")

        if show_knowledge and relevant_knowledge:
            with st.expander("顯示相關知識"):
                st.text(relevant_knowledge)
    else:
        st.warning("請輸入問題！")

# --- 頁尾 ---
st.write("---")
st.markdown("© 2023 FK AI 神學博士")