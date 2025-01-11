
# Fight.K AI Assistant

## 啟動說明

系統提供三種不同的啟動模式，每種模式有不同的功能：

### 1. LINE Bot 模式

啟動 line bot: 
python run.py --mode line

- 啟動 LINE Bot 服務
- 自動建立 ngrok 通道
- 處理群組對話和管理員指令
- 支援排程通知功能

### 2. Streamlit 對話介面

啟動 streamlit: 
python run.py --mode streamlit

- 啟動網頁版對話介面
- 提供直觀的操作界面
- 支援檔案上傳和對話記錄
- 適合測試和開發使用

### 3. 後台管理介面

啟動管理員: 
python run.py --mode admin

- 啟動管理員後台界面
- 管理 LINE 群組和排程通知
- 查看系統狀態和日誌
- 設定自動通知和系統參數

## 管理員群組指令說明

在管理員群組中可以使用以下指令：

1. !help - 顯示所有可用指令
2. !schedule YYYYMMDD-HH:MM group_id message - 設定新的排程通知
3. !schedules - 查看所有排程
4. !remove_schedule schedule_id - 刪除指定排程
5. !groups - 查看所有群組

範例：
- 設定排程：!schedule 20240101-09:30 C1e53fadf3989586cd315c01925b77fb7 早安！新的一天開始了
- 刪除排程：!remove_schedule schedule_123456

## Line bot 群組 ID

管理員群組: Ca38140041deeb2d703b16cb45b8f3bf1
測試群組: C6ab768f2ac52e2e4fe4919191d8509b3
AI 新時代戰隊: C1e53fadf3989586cd315c01925b77fb7