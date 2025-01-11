import os
import json
import yaml
from datetime import datetime
import pytz
import logging

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NotificationManager:
    def __init__(self):
        self.data_dir = "data"
        self.groups_file = os.path.join(self.data_dir, "line_groups.json")
        self.schedules_file = os.path.join(self.data_dir, "schedules.json")
        self.notifications_file = os.path.join(self.data_dir, "notification_settings.yml")
        
        # 確保資料目錄存在
        os.makedirs(self.data_dir, exist_ok=True)
        
        # 初始化資料
        self.groups = self.load_groups()
        self.schedules = self.load_schedules()
        self.notifications = self.load_notifications()

    def load_groups(self):
        """載入群組資料"""
        try:
            if os.path.exists(self.groups_file):
                with open(self.groups_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {
                "C6ab768f2ac52e2e4fe4919191d8509b3": "Fight.K 測試群組",
                "C1e53fadf3989586cd315c01925b77fb7": "AI 新時代戰隊"
            }
        except Exception as e:
            logger.error(f"載入群組資料時發生錯誤: {e}")
            return {}

    def load_schedules(self):
        """載入排程資料"""
        try:
            if os.path.exists(self.schedules_file):
                with open(self.schedules_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return []
        except Exception as e:
            logger.error(f"載入排程資料時發生錯誤: {e}")
            return []

    def load_notifications(self):
        """載入通知設定"""
        try:
            if os.path.exists(self.notifications_file):
                with open(self.notifications_file, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f) or self._get_default_notifications()
            return self._get_default_notifications()
        except Exception as e:
            logger.error(f"載入通知設定時發生錯誤: {e}")
            return self._get_default_notifications()

    def _get_default_notifications(self):
        """獲取預設的通知設定結構"""
        return {
            'daily_notifications': [],
            'weekly_notifications': [],
            'specific_date_notifications': []
        }

    def save_groups(self):
        """儲存群組資料"""
        try:
            with open(self.groups_file, 'w', encoding='utf-8') as f:
                json.dump(self.groups, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logger.error(f"儲存群組資料時發生錯誤: {e}")
            return False

    def save_schedules(self):
        """儲存排程資料"""
        try:
            with open(self.schedules_file, 'w', encoding='utf-8') as f:
                json.dump(self.schedules, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logger.error(f"儲存排程資料時發生錯誤: {e}")
            return False

    def save_notifications(self):
        """儲存通知設定"""
        try:
            with open(self.notifications_file, 'w', encoding='utf-8') as f:
                yaml.dump(self.notifications, f, allow_unicode=True)
            return True
        except Exception as e:
            logger.error(f"儲存通知設定時發生錯誤: {e}")
            return False

    def add_group(self, group_id: str, group_name: str):
        """新增群組"""
        self.groups[group_id] = group_name
        return self.save_groups()

    def remove_group(self, group_id: str):
        """移除群組"""
        if group_id in self.groups:
            del self.groups[group_id]
            return self.save_groups()
        return False

    def add_schedule(self, schedule_data: dict):
        """新增排程"""
        self.schedules.append(schedule_data)
        return self.save_schedules()

    def remove_schedule(self, schedule_id: str):
        """移除排程"""
        self.schedules = [s for s in self.schedules if s['id'] != schedule_id]
        return self.save_schedules()

    def add_notification(self, notification_type: str, notification_data: dict):
        """新增通知設定"""
        if notification_type in self.notifications:
            self.notifications[notification_type].append(notification_data)
            return self.save_notifications()
        return False

    def get_all_active_notifications(self):
        """獲取所有活動中的通知設定"""
        return {
            'daily': self.notifications['daily_notifications'],
            'weekly': self.notifications['weekly_notifications'],
            'specific': self.notifications['specific_date_notifications']
        }

    def get_formatted_schedules(self):
        """獲取格式化的排程列表"""
        return [
            {
                'id': schedule['id'],
                'name': schedule.get('name', 'Unnamed Schedule'),
                'scheduled_time': schedule.get('scheduled_time', 'Unknown'),
                'group_id': schedule.get('group_id'),
                'message': schedule.get('message')
            }
            for schedule in self.schedules
        ] 