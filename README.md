# Fight.K AI Assistant

## 1. 系統概述

Fight.K AI 助手是一個多功能的 AI 對話系統，整合了以下主要功能：
- LINE Bot 介面
- Streamlit 網頁介面
- 管理員後台
- 自動排程通知
- 知識庫管理
- 多角色對話支援

## 2. 環境設置

### 2.1 Python 虛擬環境設置

1. 確保已安裝 Python 3.8 或更高版本

python --version


2. 建立虛擬環境

Windows
python -m venv venv

Linux/Mac
python3 -m venv venv


3. 啟動虛擬環境

Windows
venv\Scripts\activate

Linux/Mac
source venv/bin/activate

更新 pip
pip install --upgrade pip
安裝基礎框架
pip install flask==2.0.1 werkzeug==2.0.1 line-bot-sdk==3.5.0 streamlit==1.22.0
安裝 AI 和 NLP 相關套件
pip install google-generativeai==0.3.1 sentence-transformers>=2.2.2 scikit-learn>=1.0.2 torch>=2.0.0 jieba
安裝文件處理套件
pip install python-docx openpyxl PyMuPDF python-dotenv==0.19.0 pyyaml==6.0.1
安裝網路和爬蟲相關套件
pip install google==3.0.0 beautifulsoup4 requests youtube-transcript-api==0.6.1 pytube==15.0.0
安裝多媒體處理套件
pip install pytesseract==0.3.10 SpeechRecognition==3.10.0 vosk==0.3.45 pyttsx3==2.90 opencv-python pydub
安裝排程和其他工具
pip install APScheduler pytz


### 2.2 外部依賴安裝

#### 2.2.1 ffmpeg 安裝
1. Windows:
   - 前往 https://ffmpeg.org/download.html
   - 下載 Windows 版本
   - 解壓縮到指定目錄（例如：C:\Program Files\ffmpeg）
   - 添加到系統環境變數 Path：C:\Program Files\ffmpeg\bin

2. Linux:
sudo apt-get update
sudo apt-get install ffmpeg

3. Mac:
brew install ffmpeg

#### 2.2.2 Tesseract OCR 安裝
1. Windows:
   - 前往 https://github.com/UB-Mannheim/tesseract/wiki
   - 下載最新版本（例如：tesseract-ocr-w64-setup-5.3.3.20231005.exe）
   - 執行安裝程式
   - 建議安裝到：C:\Program Files\Tesseract-OCR
   - 必須勾選「Add to system PATH」
   - 勾選「Additional language data」支援多語言

2. Linux:
sudo apt-get install tesseract-ocr

3. Mac:
brew install tesseract

#### 2.2.3 ngrok 安裝和設置
1. 下載 ngrok:
   - 前往 https://ngrok.com/download
   - 下載對應系統版本
   - Windows 用戶下載 Windows 64-bit

2. 安裝步驟:
   - 解壓縮下載的 zip 檔案
   - 將 ngrok.exe 移動到固定位置（例如：C:\Program Files\ngrok）
   - 添加到系統環境變數 Path

3. 註冊和設置:
   - 前往 https://dashboard.ngrok.com/signup 註冊
   - 獲取 authtoken
   - 打開終端機執行：
     ```bash
     ngrok config add-authtoken 你的_authtoken
     ```

4. 驗證安裝:
ngrok --version


### 2.3 環境變數設置
1. 創建必要目錄:

Windows PowerShell
mkdir config, core, ui, data, logs, models, prompts, knowledge_base, temp
mkdir "temp\web_search"
Linux/Mac
mkdir -p config core ui data logs models prompts knowledge_base temp/web_search

2. 創建必要檔案:

Windows PowerShell
New-Item "data\prompts.json" -ItemType File
New-Item "data\knowledge_base.txt" -ItemType File
New-Item "data\Fight.K核心理念.docx" -ItemType File
New-Item "data\Fight.K簡介.docx" -ItemType File
New-Item "data\Fight.K歷史.docx" -ItemType File
New-Item "data\Fight.K相關連結整理.xlsx" -ItemType File
New-Item "data\info.json" -ItemType File
Linux/Mac
touch data/prompts.json
touch data/knowledge_base.txt
touch "data/Fight.K核心理念.docx"
touch "data/Fight.K簡介.docx"
touch "data/Fight.K歷史.docx"
touch "data/Fight.K相關連結整理.xlsx"
touch data/info.json

### 2.4 環境變數設置 `.env` 檔案

Windows
copy nul .env
Linux/Mac
touch .env


2. 在 .env 中添加以下內容:

LINE_CHANNEL_SECRET=你的LINE_Channel_Secret
LINE_CHANNEL_ACCESS_TOKEN=你的LINE_Channel_Access_Token
NGROK_AUTH_TOKEN=你的Ngrok_Auth_Token
GEMINI_API_KEY=你的Gemini_API_Key


2. 確保所有必要的目錄結構存在：
├── config/
├── core/
├── ui/
├── data/
├── logs/
├── models/
├── prompts/
└── knowledge_base/


## 3. 啟動說明

系統提供三種不同的啟動模式：

### 3.1 LINE Bot 模式


# 確保在虛擬環境中，啟動虛擬環境

Windows
venv\Scripts\activate

Linux/Mac
source venv/bin/activate

# 啟動 LINE Bot
python run.py --mode line

- 啟動 LINE Bot 服務
- 自動建立 ngrok 通道
- 處理群組對話和管理員指令
- 支援排程通知功能

### 3.2 Streamlit 對話介面

確保在虛擬環境中 venv\Scripts\activate
python run.py --mode streamlit

- 啟動網頁版對話介面
- 提供直觀的操作界面
- 支援檔案上傳和對話記錄
- 適合測試和開發使用

### 3.3 後台管理介面

確保在虛擬環境中
python run.py --mode admin

- 啟動管理員後台界面
- 管理 LINE 群組和排程通知
- 查看系統狀態和日誌
- 設定自動通知和系統參數

## 4. 常見問題排解

### 4.1 虛擬環境相關
1. 如果無法建立虛擬環境：
   ```bash
   python -m pip install --upgrade virtualenv
   ```

2. 如果找不到 python 命令：
   - 確認 Python 已安裝
   - 確認系統環境變數設置正確

### 4.2 套件安裝相關
1. 如果安裝套件時出現錯誤：
   ```bash
   pip install package_name --no-cache-dir
   ```

2. 如果出現版本衝突：
   ```bash
   pip uninstall package_name
   pip install package_name==specific_version
   ```  
### 4.3 外部依賴相關
1. 如果 ngrok 無法執行：
   - 確認 authtoken 已正確設置
   - 確認防火牆設置
   - 檢查 4040 端口是否被佔用

2. 如果 Tesseract 無法識別：
   - 確認環境變數設置
   - 使用完整路徑執行測試


1. 如果遇到套件安裝錯誤：

嘗試更新 pip
pip install --upgrade pip

如果特定套件安裝失敗，可以嘗試：
pip install package_name --no-cache-dir


2. 如果遇到 ffmpeg 相關錯誤：
- 確認 ffmpeg 是否正確安裝：`ffmpeg -version`
- 確認系統環境變數是否正確設置

3. 如果遇到 Tesseract 相關錯誤：
- 確認 Tesseract 是否正確安裝：`tesseract --version`
- 確認系統環境變數是否正確設置

4. 退出虛擬環境：

deactivate

## 5. 注意事項

1. 確保所有必要的資料目錄存在
2. 檢查知識庫文件的正確性和完整性
3. 注意時區設定（預設為 Asia/Taipei）
4. 確保網路連接穩定（特別是使用 ngrok 時）
5. 定期備份重要資料
6. 在更新系統前先備份整個專案

## 6. 系統架構

### 6.1 核心模組
- `core/ai_engine.py`: AI 對話引擎
- `core/knowledge_base.py`: 知識庫管理
- `core/prompts.py`: 提示詞管理

### 6.2 介面模組
- `ui/line_bot_ui.py`: LINE Bot 介面
- `ui/streamlit_ui.py`: Streamlit 網頁介面
- `ui/admin_ui.py`: 管理員後台介面

### 6.3 工具模組
- `utils/chat_history.py`: 對話歷史管理
- `utils/notification_manager.py`: 通知管理
- `utils/scheduled_messages.py`: 排程訊息
- `utils/web_search.py`: 網路搜尋
- `utils/youtube_handler.py`: YouTube 影片處理

## 7. 功能說明

### 7.1 對話功能
- 多角色對話支援（小幫手、教師、策士、商業專家）
- 知識庫整合回答
- 上下文理解
- 多媒體訊息處理

### 7.2 知識庫功能
- 支援多種文件格式（PDF、DOCX、XLSX、TXT）
- 自動文件分析和索引
- 相似度搜尋
- 知識庫更新機制

### 7.3 排程功能
- 每日定時通知
- 每週定期通知
- 特定日期通知
- 群組通知管理

### 7.4 管理功能
- 群組管理
- 通知設定
- 系統監控
- 日誌查看

## 8. 開發指南

### 8.1 新增功能
1. 遵循現有的模組化結構
2. 在相應模組中實現新功能
3. 更新配置文件
4. 添加適當的日誌記錄
5. 更新文檔

### 8.2 測試流程
1. 在虛擬環境中進行單元測試
2. 使用測試群組進行功能測試
3. 確認日誌輸出正確
4. 驗證與現有功能的相容性

### 8.3 部署流程
1. 備份現有系統
2. 更新程式碼
3. 更新依賴套件
4. 重新啟動服務
5. 驗證功能正常

## 9. 維護指南

### 9.1 日常維護
1. 定期檢查日誌文件
2. 監控系統資源使用
3. 備份重要資料
4. 更新知識庫內容

### 9.2 故障處理
1. 檢查日誌文件定位問題
2. 確認網路連接狀態
3. 驗證外部服務可用性
4. 必要時重啟服務

### 9.3 系統更新
1. 在測試環境驗證更新
2. 建立更新計劃
3. 執行更新程序
4. 驗證更新結果

## 10. 安全性考慮

### 10.1 資料安全
- 定期備份重要資料
- 加密敏感資訊
- 控制存取權限
- 監控異常活動

### 10.2 系統安全
- 定期更新依賴套件
- 使用安全的環境變數
- 限制 API 存取
- 監控系統活動

## 11. 版本資訊

### 11.1 當前版本
- 版本號：1.0.0
- 更新日期：2025-01-16
- 主要功能：
  - LINE Bot 整合
  - 多角色對話
  - 知識庫管理
  - 排程通知

### 11.2 更新計劃
- 優化對話體驗
- 擴充知識庫功能
- 增強管理介面
- 改進排程系統

## 12. 聯絡資訊

### 12.1 技術支援
- Email: support@fight-k.com
- LINE: @fight.k
- 電話: (02) 1234-5678

### 12.2 問題回報
- GitHub Issues
- 技術支援信箱
- LINE 官方帳號

## 13. 授權資訊

本專案採用 MIT 授權條款，詳細內容請參考 LICENSE 文件。

---

© 2025 Fight.K AI Assistant. All Rights Reserved.
