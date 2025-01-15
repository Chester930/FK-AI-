import os
from datetime import datetime, timedelta
import pytz
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    PushMessageRequest,
    TextMessage
)
import logging
from dotenv import load_dotenv
from utils.notification_manager import NotificationManager
import time

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

# LINE Bot 設定
configuration = Configuration(access_token=os.environ.get('LINE_CHANNEL_ACCESS_TOKEN'))

# 設定台灣時區
tw_timezone = pytz.timezone('Asia/Taipei')

# 定義通知配置
NOTIFICATION_CONFIGS = {
    'daily_notifications': [],
    'weekly_notifications': [],
    'specific_date_notifications': []
}

class MessageScheduler:
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.scheduler.start()
        self.jobs = {}
        
    def schedule_message(self, group_id: str, datetime_str: str, message: str) -> bool:
        """設置排程訊息"""
        try:
            from datetime import datetime
            schedule_time = datetime.strptime(datetime_str, '%Y%m%d-%H:%M')
            
            # 生成唯一的任務 ID
            job_id = f"schedule_{int(time.time())}"
            
            # 添加排程任務
            self.scheduler.add_job(
                self._send_scheduled_message,
                'date',
                run_date=schedule_time,
                args=[group_id, message],
                id=job_id
            )
            
            # 保存任務信息
            self.jobs[job_id] = {
                'group_id': group_id,
                'scheduled_time': datetime_str,
                'message': message
            }
            
            return True
                
        except Exception as e:
            logger.error(f"設置排程訊息時發生錯誤: {str(e)}", exc_info=True)
            return False 