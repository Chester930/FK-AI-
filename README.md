# Fight.K AI Assistant

## 1. 系統概述

Fight.K AI 助手是一個多功能的 AI 對話系統，整合了以下主要功能：
- LINE Bot 介面
- Streamlit 網頁介面
- 管理員後台
- 自動排程通知
- 知識庫管理
- 多角色對話支援

## 2. 啟動說明

系統提供三種不同的啟動模式：

### 2.1 LINE Bot 模式

python run.py --mode line

- 啟動 LINE Bot 服務
- 自動建立 ngrok 通道
- 處理群組對話和管理員指令
- 支援排程通知功能

### 2.2 Streamlit 對話介面

python run.py --mode streamlit

- 啟動網頁版對話介面
- 提供直觀的操作界面
- 支援檔案上傳和對話記錄
- 適合測試和開發使用

### 2.3 後台管理介面

python run.py --mode admin

- 啟動管理員後台界面
- 管理 LINE 群組和排程通知
- 查看系統狀態和日誌
- 設定自動通知和系統參數

## 3. 系統架構

### 3.1 核心組件

#### AI 引擎 (`core/ai_engine.py`)
- 使用 Google Gemini 模型
- 處理自然語言生成
- 管理模型參數和配置

#### 知識庫 (`core/knowledge_base.py`)
- 支援多種文件格式 (DOCX, PDF, TXT, XLSX)
- 向量化搜索功能
- 角色特定的知識管理

#### 提示詞管理 (`core/prompts.py`)
- 管理不同角色的提示詞模板
- 支援通用提示詞和角色特定提示詞
- JSON 格式配置

### 3.2 使用者介面

#### LINE Bot (`ui/line_bot_ui.py`)
- 處理個人和群組訊息
- 支援檔案上傳和處理
- 管理員指令支援
- YouTube 影片處理功能

#### Streamlit 介面 (`ui/streamlit_ui.py`)
- 網頁聊天界面
- 檔案上傳功能
- 對話歷史顯示

#### 管理員後台 (`ui/admin_ui.py`)
- 排程管理
- 群組管理
- 通知設定

## 4. 管理員功能

### 4.1 群組 ID 列表
- 管理員群組: `Ca38140041deeb2d703b16cb45b8f3bf1`
- 測試群組: `C6ab768f2ac52e2e4fe4919191d8509b3`
- AI 新時代戰隊: `C1e53fadf3989586cd315c01925b77fb7`

### 4.2 管理員群組指令
1. `!help` - 顯示所有可用指令
2. `!schedule YYYYMMDD-HH:MM group_id message` - 設定新的排程通知
3. `!schedules` - 查看所有排程
4. `!remove_schedule schedule_id` - 刪除指定排程
5. `!groups` - 查看所有群組

範例：

設定排程
!schedule 20240101-09:30 C1e53fadf3989586cd315c01925b77fb7 早安！新的一天開始了

刪除排程
!remove_schedule schedule_123456


## 5. 環境設定

### 5.1 必要環境變數
- LINE_CHANNEL_SECRET
- LINE_CHANNEL_ACCESS_TOKEN
- NGROK_AUTH_TOKEN
- GEMINI_API_KEY

### 5.2 目錄結構
- `config/` - 配置檔案
- `core/` - 核心功能
- `ui/` - 使用者介面
- `data/` - 資料存放目錄
- `logs/` - 日誌存放目錄
- `models/` - 模型存放目錄
- `prompts/` - 提示詞存放目錄
- `knowledge_base/` - 知識庫存放目錄


├── core/             # 核心功能
│   ├── ai_engine.py  # AI 引擎
│   ├── knowledge_base.py  # 知識庫
│   ├── prompts.py  # 提示詞管理
│   └── ...
├── ui/               # 使用者介面
│   ├── line_bot_ui.py  # LINE Bot 介面
│   ├── streamlit_ui.py  # Streamlit 介面
│   ├── admin_ui.py  # 管理員後台
│   └── ...
├── data/             # 資料存放目錄
├── logs/             # 日誌存放目錄
├── models/           # 模型存放目錄
├── prompts/          # 提示詞存放目錄
├── knowledge_base/   # 知識庫存放目錄


## 6. 注意事項

1. 確保所有必要的資料目錄存在
2. 檢查知識庫文件的正確性和完整性
3. 注意時區設定（預設為 Asia/Taipei）
4. 確保網路連接穩定（特別是使用 ngrok 時）