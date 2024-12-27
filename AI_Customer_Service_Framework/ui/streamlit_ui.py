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

st.title("FK AI 神學博士")

# Get user input
user_input = st.text_input("請輸入你的問題：")

if st.button("送出"):
    # Retrieve relevant knowledge (if any)
    relevant_knowledge = knowledge_base.search(user_input)

    # Get a prompt based on user input or a default one
    prompt = prompt_manager.get_prompt("general_theology")

    # Combine the prompt, relevant knowledge, and user input for the AI
    if relevant_knowledge:
        full_prompt = f"{prompt}\n{relevant_knowledge}\nUser: {user_input}\nAI:"
    else:
        full_prompt = f"{prompt}\nUser: {user_input}\nAI:"

    # Generate a response
    response = ai_engine.generate_response(full_prompt, user_input)

    # Display the response
    st.write(f"AI: {response}")
    