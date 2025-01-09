# Configuration for the AI customer service
import os

BASE_DIR = os.path.dirname(__file__)

# 共同參考資料路徑
COMMON_PATHS = [
    os.path.join(BASE_DIR, "data", "FK核心理念.docx"),  # 共用的基礎資料
    os.path.join(BASE_DIR, "data", "FK歷史.docx"),  # 所有角色都需要的基礎
    os.path.join(BASE_DIR, "data", "FK簡介.docx"),  
    os.path.join(BASE_DIR, "data", "FK相關連結整理.xlsx"),  
    os.path.join(BASE_DIR, "data", "info.json"),  
    os.path.join(BASE_DIR, "data", "knowledge_base.txt"),  
]

# 個別角色的專屬資料路徑
ROLE_SPECIFIC_PATHS = {
    "FK helper": [
        os.path.join(BASE_DIR, "data", "撒瑪利亞教會", "夥伴單位簡介.xlsx"),
        os.path.join(BASE_DIR, "data", "撒瑪利亞教會", "撒瑪利亞教會說明文件.txt"),
    ],
    "FK teacher": [
        os.path.join(BASE_DIR, "data", "聖經"),
        os.path.join(BASE_DIR, "data", "裝備課程", "雲端神學院"),
        os.path.join(BASE_DIR, "data", "裝備課程", "DNA", "AI大意"),
        os.path.join(BASE_DIR, "data", "裝備課程", "DNA", "AI重點整理"),
    ],
    "FK Prophet": [
        os.path.join(BASE_DIR, "data/FK計畫與轉型/家教會/家教會簡介.docx"),
        os.path.join(BASE_DIR, "data/FK計畫與轉型/家教會/家教會QA.xlsx"),        
        os.path.join(BASE_DIR, "data/FK計畫與轉型/家教會/家教會 PDF"),
        os.path.join(BASE_DIR, "data/夥伴單位簡介.xlsx"),        
    ],
    "FK Business": [
        os.path.join(BASE_DIR, "data/FK商業理念"),
    ]
}

# 組合共同路徑和角色專屬路徑
KNOWLEDGE_BASE_PATHS = {
    role: COMMON_PATHS + paths 
    for role, paths in ROLE_SPECIFIC_PATHS.items()
}

# Retrieve API key from environment variable
GEMINI_API_KEY = os.environ.get("GOOGLE_API_KEY")

# Model settings
MODEL_NAME = "gemini-2.0-flash-exp"  # 可以更換為其他模型
MODEL_TEMPERATURE = 0.7    # 控制創意程度 (0.0-1.0)
MODEL_TOP_P = 0.8         # 控制輸出多樣性
MAX_OUTPUT_TOKENS = 2048  # 最大輸出長度

# Prompt settings
PROMPT_TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), "data/prompts.json")