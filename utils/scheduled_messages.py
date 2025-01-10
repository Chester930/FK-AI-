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
    # 每日通知
    'daily_notifications': [
        {
            'group_id': 'C1e53fadf3989586cd315c01925b77fb7',  # Fight.K 測試群組
            'schedule': {
                'hour': '09',
                'minute': '00',
                'timezone': 'Asia/Taipei'
            },
            'message': '早安！願神祝福大家今天有美好的一天！'
        },
        {
            'group_id': 'C1e53fadf3989586cd315c01925b77fb7',
            'schedule': {
                'hour': '17',
                'minute': '12',
                'timezone': 'Asia/Taipei'
            },
            'message': '晚安！願神保守大家有個好夢！'
        }
    ],
    
    # 每週通知
    'weekly_notifications': [
        {
            'group_id': 'C1e53fadf3989586cd315c01925b77fb7',
            'schedule': {
                'day_of_week': 'mon',  # mon, tue, wed, thu, fri, sat, sun
                'hour': '10',
                'minute': '00',
                'timezone': 'Asia/Taipei'
            },
            'message': '本週讀經進度提醒：\n1. 創世記第一章\n2. 詩篇第一篇'
        }
    ],
    
    # 特定日期通知
    'specific_date_notifications': [
        {
            'group_id': 'C1e53fadf3989586cd315c01925b77fb7',
            'schedule': {
                'date': '2025-12-25',  # 改為未來日期
                'hour': '10',
                'minute': '00',
                'timezone': 'Asia/Taipei'
            },
            'message': '聖誕節快樂！願神祝福大家！'
        }
    ]
}

class MessageScheduler:
    def __init__(self):
        self.scheduler = BackgroundScheduler(timezone=tw_timezone)
        self.scheduler.start()
        self._setup_notifications()
        self._send_startup_test()  # 添加啟動測試
    
    def _setup_notifications(self):
        """設置所有預定的通知"""
        try:
            # 設置每日通知
            for config in NOTIFICATION_CONFIGS['daily_notifications']:
                self._add_daily_notification(config)

            # 設置每週通知
            for config in NOTIFICATION_CONFIGS['weekly_notifications']:
                self._add_weekly_notification(config)

            # 設置特定日期通知
            for config in NOTIFICATION_CONFIGS['specific_date_notifications']:
                self._add_specific_date_notification(config)

        except Exception as e:
            logger.error(f"Error in _setup_notifications: {str(e)}", exc_info=True)

    def _add_daily_notification(self, config):
        """添加每日通知"""
        try:
            self.scheduler.add_job(
                func=self.send_message,
                trigger='cron',
                hour=config['schedule']['hour'],
                minute=config['schedule']['minute'],
                args=[config['group_id'], config['message']],
                id=f"daily_{config['group_id']}_{config['schedule']['hour']}_{config['schedule']['minute']}",
                timezone=pytz.timezone(config['schedule']['timezone']),
                misfire_grace_time=None  # 不限制錯過的執行時間
            )
            logger.info(f"Added daily notification: {config['message'][:50]}...")
        except Exception as e:
            logger.error(f"Error adding daily notification: {str(e)}")

    def _add_weekly_notification(self, config):
        """添加每週通知"""
        try:
            self.scheduler.add_job(
                func=self.send_message,
                trigger='cron',
                day_of_week=config['schedule']['day_of_week'],
                hour=config['schedule']['hour'],
                minute=config['schedule']['minute'],
                args=[config['group_id'], config['message']],
                id=f"weekly_{config['group_id']}_{config['schedule']['day_of_week']}",
                timezone=pytz.timezone(config['schedule']['timezone']),
                misfire_grace_time=None
            )
            logger.info(f"Added weekly notification: {config['message'][:50]}...")
        except Exception as e:
            logger.error(f"Error adding weekly notification: {str(e)}")

    def _add_specific_date_notification(self, config):
        """添加特定日期通知"""
        try:
            date = datetime.strptime(config['schedule']['date'], '%Y-%m-%d')
            time = f"{config['schedule']['hour']}:{config['schedule']['minute']}"
            dt = datetime.strptime(f"{config['schedule']['date']} {time}", '%Y-%m-%d %H:%M')
            
            # 檢查日期是否已過期
            if dt < datetime.now(tw_timezone):
                logger.warning(f"Skipping expired notification scheduled for {dt}")
                return
                
            self.scheduler.add_job(
                func=self.send_message,
                trigger=DateTrigger(
                    run_date=dt,
                    timezone=pytz.timezone(config['schedule']['timezone'])
                ),
                args=[config['group_id'], config['message']],
                id=f"specific_{config['group_id']}_{config['schedule']['date']}",
                misfire_grace_time=None
            )
            logger.info(f"Added specific date notification: {config['message'][:50]}...")
        except Exception as e:
            logger.error(f"Error adding specific date notification: {str(e)}")

    def send_message(self, group_id: str, message: str, file_path: str = None):
        """發送訊息到指定群組"""
        try:
            with ApiClient(configuration) as api_client:
                line_bot_api = MessagingApi(api_client)
                
                # 添加時間戳記到消息中
                current_time = datetime.now(tw_timezone).strftime('%Y-%m-%d %H:%M:%S')
                message_with_time = f"[{current_time}]\n{message}"
                
                if file_path:
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            file_content = f.read()
                        message_with_time += f"\n\n文件內容：\n{file_content}"
                    except Exception as e:
                        logger.error(f"Error reading file {file_path}: {str(e)}")
                        message_with_time += f"\n\n(無法讀取文件：{file_path})"

                line_bot_api.push_message(
                    PushMessageRequest(
                        to=group_id,
                        messages=[TextMessage(text=message_with_time)]
                    )
                )
                logger.info(f"Successfully sent message to group {group_id}: {message_with_time[:100]}...")
        except Exception as e:
            logger.error(f"Error sending message: {str(e)}", exc_info=True)

    def schedule_message(self, group_id: str, datetime_str: str, message: str, file_path: str = None):
        """
        設定在指定時間發送消息
        :param group_id: LINE群組ID
        :param datetime_str: 日期時間字符串，格式：YYYYMMDD-HH:MM
        :param message: 要發送的消息
        :param file_path: 可選的文件路徑
        """
        try:
            # 解析日期時間字符串
            dt = datetime.strptime(datetime_str, '%Y%m%d-%H:%M')
            # 設定為台灣時區
            dt = tw_timezone.localize(dt)
            
            job_id = f"message_job_{group_id}_{datetime.now().timestamp()}"
            
            # 添加任務
            self.scheduler.add_job(
                func=self.send_message,
                trigger=DateTrigger(run_date=dt, timezone=tw_timezone),
                args=[group_id, message, file_path],
                id=job_id,
                name=f"Send message to {group_id} at {datetime_str}"
            )
            
            logger.info(f"Scheduled message for {datetime_str}")
            return {
                'job_id': job_id,
                'scheduled_time': dt.strftime('%Y-%m-%d %H:%M'),
                'message': message,
                'file_path': file_path
            }
            
        except ValueError as e:
            logger.error(f"Invalid datetime format: {str(e)}")
            raise ValueError("日期時間格式錯誤，請使用 YYYYMMDD-HH:MM 格式")
        except Exception as e:
            logger.error(f"Error scheduling message: {str(e)}")
            raise

    def list_schedules(self):
        """列出所有排程"""
        return [
            {
                'id': job.id,
                'name': job.name,
                'scheduled_time': job.next_run_time.strftime('%Y-%m-%d %H:%M') if job.next_run_time else 'N/A'
            }
            for job in self.scheduler.get_jobs()
        ]

    def remove_schedule(self, job_id: str):
        """移除特定排程"""
        try:
            self.scheduler.remove_job(job_id)
            logger.info(f"Removed scheduled job: {job_id}")
            return True
        except Exception as e:
            logger.error(f"Error removing job {job_id}: {str(e)}")
            return False

    def shutdown(self):
        """關閉排程器"""
        self.scheduler.shutdown() 

    def _send_startup_test(self):
        """發送啟動測試通知"""
        try:
            test_groups = [
                'C6ab768f2ac52e2e4fe4919191d8509b3',  # Fight.K 測試群組
                # 可以添加更多測試群組
            ]
            
            startup_time = datetime.now(tw_timezone).strftime('%Y-%m-%d %H:%M:%S')
            
            # 生成排程列表
            daily_schedules = "\n".join([
                f"  ⏰ {config['schedule']['hour']}:{config['schedule']['minute']} - {config['message'][:30]}..."
                for config in NOTIFICATION_CONFIGS['daily_notifications']
            ])
            
            weekly_schedules = "\n".join([
                f"  📅 每週{config['schedule']['day_of_week']} {config['schedule']['hour']}:{config['schedule']['minute']} - {config['message'][:30]}..."
                for config in NOTIFICATION_CONFIGS['weekly_notifications']
            ])
            
            specific_schedules = "\n".join([
                f"  📌 {config['schedule']['date']} {config['schedule']['hour']}:{config['schedule']['minute']} - {config['message'][:30]}..."
                for config in NOTIFICATION_CONFIGS['specific_date_notifications']
            ])
            
            test_message = (
                f"🤖 Fight.K AI 助手啟動測試\n"
                f"⏰ 啟動時間：{startup_time}\n"
                f"\n📋 排程通知列表：\n"
                f"\n🔄 每日通知：\n{daily_schedules}\n"
                f"\n📅 每週通知：\n{weekly_schedules}\n"
                f"\n📌 特定日期通知：\n{specific_schedules}\n"
                f"\n💡 排程系統正常運作中"
            )
            
            # 轉換星期顯示為中文
            test_message = (test_message
                .replace('mon', '一')
                .replace('tue', '二')
                .replace('wed', '三')
                .replace('thu', '四')
                .replace('fri', '五')
                .replace('sat', '六')
                .replace('sun', '日'))
            
            for group_id in test_groups:
                self.send_message(group_id, test_message)
                logger.info(f"Sent startup test message to group {group_id}")
                
        except Exception as e:
            logger.error(f"Error sending startup test: {str(e)}", exc_info=True) 