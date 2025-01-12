# Configuration for the AI customer service
import os

BASE_DIR = os.path.dirname(__file__)

# 共同參考資料路徑
COMMON_PATHS = [
    os.path.join(BASE_DIR, "data", "Fight.K核心理念.docx"),  # 共用的基礎資料
    os.path.join(BASE_DIR, "data", "knowledge_base.txt"), 
    os.path.join(BASE_DIR, "data", "Fight.K歷史.docx"),  # 所有角色都需要的基礎
    os.path.join(BASE_DIR, "data", "Fight.K簡介.docx"),  
    os.path.join(BASE_DIR, "data", "Fight.K相關連結整理.xlsx"),  
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

# LINE Bot Settings
LINE_CHANNEL_SECRET = os.environ.get('LINE_CHANNEL_SECRET')
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN')

# 確保在找不到環境變數時給出警告
if not LINE_CHANNEL_SECRET or not LINE_CHANNEL_ACCESS_TOKEN:
    print("警告: 未設置 LINE Bot 相關的環境變數")

# File handling settings
FILE_SETTINGS = {
    'max_file_size': 10 * 1024 * 1024,  # 10MB
    'allowed_extensions': ['txt', 'xlsx', 'docx', 'jpg', 'jpeg', 'png', 'pdf', 'm4a', 'mp3', 'wav'],
    'temp_folder': 'temp'
}

# LINE Bot Admin Settings
ADMIN_GROUP_ID = "Ca38140041deeb2d703b16cb45b8f3bf1"  # Fight.K AI助理管理員
ADMIN_COMMANDS = {
    "!schedule": "設定新的排程通知",
    "!schedules": "查看所有排程",
    "!remove_schedule": "刪除指定排程",
    "!groups": "查看所有群組",
    "!add_group": "新增群組",
    "!remove_group": "移除群組",
    "!help": "顯示管理員指令說明"
}