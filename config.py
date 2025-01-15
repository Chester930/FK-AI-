# Configuration for the AI customer service
import os

BASE_DIR = os.path.dirname(__file__)

# 定義常用檔案路徑
CORE_DOC_PATH = 'data/Fight.K核心理念.docx'
INTRO_DOC_PATH = 'data/Fight.K簡介.docx'
HISTORY_DOC_PATH = 'data/Fight.K歷史.docx'
LINKS_DOC_PATH = 'data/Fight.K相關連結整理.xlsx'

# 共同參考資料路徑
COMMON_PATHS = [
    os.path.join(BASE_DIR, CORE_DOC_PATH),
    os.path.join(BASE_DIR, "data", "knowledge_base.txt"), 
    os.path.join(BASE_DIR, HISTORY_DOC_PATH),  # 所有角色都需要的基礎
    os.path.join(BASE_DIR, INTRO_DOC_PATH),  
    os.path.join(BASE_DIR, LINKS_DOC_PATH),  
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
    'common': {  # 共同參考資料
        'core': {
            'path': CORE_DOC_PATH,
            'description': 'Fight.K核心理念文件',
            'keywords': ['核心', '理念', '價值觀', '使命', 'Fight.K'],
            'priority': 1
        },
        'intro': {
            'path': INTRO_DOC_PATH,
            'description': 'Fight.K 基本介紹',
            'keywords': ['簡介', '介紹', '認識', 'Fight.K'],
            'priority': 2
        },
        'history': {
            'path': HISTORY_DOC_PATH,
            'description': 'Fight.K 歷史記錄',
            'keywords': ['歷史', '發展', '里程碑', 'Fight.K'],
            'priority': 3
        },
        'links': {
            'path': LINKS_DOC_PATH,
            'description': 'Fight.K 相關資源連結',
            'keywords': ['連結', '資源', '網站', 'Fight.K'],
            'priority': 4
        }
    },
    'FK helper': {
        'common': {
            'path': CORE_DOC_PATH,
            'description': 'Fight.K 核心理念文件',
            'keywords': ['核心', '理念', '價值觀', '使命', 'Fight.K'],
            'priority': 1
        },
        'partners': {
            'path': 'data/撒瑪利亞教會/夥伴單位簡介.xlsx',
            'description': 'Fight.K 夥伴單位資料',
            'keywords': ['夥伴', '單位', '合作', '協會', '商會', '組織', 'Fight.K'],
            'priority': 2
        }
    },
    'FK teacher': {
        'bible': {
            'path': 'data/聖經',
            'description': '聖經相關資料',
            'keywords': ['聖經', '經文', '章節'],
            'priority': 1
        },
        'dna': {
            'path': 'data/裝備課程/DNA',
            'description': 'DNA 課程資料',
            'keywords': ['DNA', '講義', '考卷', '解答'],
            'priority': 2
        },
        'cloud': {
            'path': 'data/裝備課程/雲端神學院',
            'description': '雲端神學院課程',
            'keywords': ['神學院', '課程', '裝備'],
            'priority': 3
        }
    },
    'FK Prophet': {
        'home_church': {
            'path': 'data/FK計畫與轉型/家教會',
            'description': '家教會相關資料',
            'keywords': ['家教會', 'QA', '簡介', '計畫'],
            'priority': 1
        },
        'partners': {
            'path': 'data/撒瑪利亞教會/夥伴單位簡介.xlsx',
            'description': '夥伴單位資料',
            'keywords': ['夥伴', '單位', '合作'],
            'priority': 2
        }
    },
    'FK Business': {
        'business': {
            'path': 'data/FK商業理念',
            'description': 'Fight.K 商業相關資料',
            'keywords': ['商業', '理念', '經營'],
            'priority': 1
        }
    }
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

# Vector Store Settings
VECTOR_STORE_SETTINGS = {
    'model_name': 'paraphrase-multilingual-MiniLM-L12-v2',
    'min_score': 0.3,
    'top_k': 5
}

# Role-specific Search Settings
ROLE_SEARCH_SETTINGS = {
    'FK helper': {
        'top_k': 3,
        'min_score': 0.3,
        'local_weight': 0.3,
        'web_weight': 0.5,
        'history_weight': 0.2
    },
    'FK teacher': {
        'top_k': 5,
        'min_score': 0.4,
        'local_weight': 0.6,
        'web_weight': 0.2,
        'history_weight': 0.2
    },
    'FK Prophet': {
        'top_k': 4,
        'min_score': 0.35,
        'local_weight': 0.5,
        'web_weight': 0.3,
        'history_weight': 0.2
    },
    'FK Business': {
        'top_k': 4,
        'min_score': 0.35,
        'local_weight': 0.4,
        'web_weight': 0.4,
        'history_weight': 0.2
    }
}

# Document Processing Settings
DOCUMENT_PROCESSING = {
    'chunk_size': 1000,  # 文檔分塊大小
    'chunk_overlap': 200,  # 分塊重疊大小
    'allowed_extensions': ['.txt', '.docx', '.xlsx', '.pdf'],
    'encoding': 'utf-8'
}

# 更新 KNOWLEDGE_BASE_SETTINGS
KNOWLEDGE_BASE_SETTINGS = {
    'max_results': 5,
    'min_similarity': 0.3,
    'context_length': 1000,
    'vector_store': VECTOR_STORE_SETTINGS,
    'role_search': ROLE_SEARCH_SETTINGS,
    'document_processing': DOCUMENT_PROCESSING
}