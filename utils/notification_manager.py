import os
import json
import yaml
from datetime import datetime
import pytz
import logging
import time

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
        self.groups = self._load_groups()
        self.schedules = self.load_schedules()
        self.notifications = self.load_notifications()
        self.nids = self._load_nids()

    def load_groups(self):
        """載入群組資料"""
        try:
            if os.path.exists(self.groups_file):
                with open(self.groups_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {
                "C6ab768f2ac52e2e4fe4919191d8509b3": "我的測試群組",
                "C1e53fadf3989586cd315c01925b77fb7": "AI 新時代戰隊",
                "Ca38140041deeb2d703b16cb45b8f3bf1": "Fight.K AI助理管理員"
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
        try:
            # 使用統一格式
            self.groups[group_id] = self._format_group_info(group_name)
            
            # 如果群組還沒有 NID，分配一個新的
            if not self.get_nid_by_group_id(group_id):
                new_nid = str(len(self.nids) + 1)
                self.nids[new_nid] = group_id
                self.save_nids()
            
            return self.save_groups()
        except Exception as e:
            logger.error(f"新增群組時發生錯誤: {e}")
            return False

    def remove_group(self, group_id: str):
        """移除群組"""
        try:
            # 從群組列表中移除
            if group_id in self.groups:
                del self.groups[group_id]
            
            # 從 NID 對應中移除
            nid = self.get_nid_by_group_id(group_id)
            if nid and nid in self.nids:
                del self.nids[nid]
                self.save_nids()
            
            return self.save_groups()
        except Exception as e:
            logger.error(f"移除群組時發生錯誤: {e}")
            return False

    def update_group_name(self, group_id: str, new_name: str):
        """更新群組名稱"""
        try:
            if group_id in self.groups:
                # 保持其他資訊不變，只更新名稱
                current_info = self.groups[group_id]
                if isinstance(current_info, str):
                    current_info = self._format_group_info(current_info)
                current_info['name'] = new_name
                self.groups[group_id] = current_info
                return self.save_groups()
            return False
        except Exception as e:
            logger.error(f"更新群組名稱時發生錯誤: {e}")
            return False

    def save_nids(self):
        """儲存 NID 對應資料"""
        try:
            with open('data/group_nids.json', 'w', encoding='utf-8') as f:
                json.dump(self.nids, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logger.error(f"儲存 NID 對應資料時發生錯誤: {e}")
            return False

    def add_schedule(self, schedule_data: dict):
        """新增排程"""
        try:
            # 確保排程有唯一ID
            if 'id' not in schedule_data:
                schedule_data['id'] = f"s{int(time.time())}"
            
            # 添加建立時間
            schedule_data['created_at'] = datetime.now(pytz.UTC).isoformat()
            
            # 添加到排程列表
            self.schedules.append(schedule_data)
            
            # 立即保存
            success = self.save_schedules()
            if success:
                logger.info(f"成功新增排程: {schedule_data}")
                # 重新載入排程確保資料同步
                self.schedules = self.load_schedules()
            return success
        except Exception as e:
            logger.error(f"新增排程時發生錯誤: {e}")
            return False

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
        try:
            # 重新載入確保資料最新
            self.schedules = self.load_schedules()
            
            formatted_schedules = []
            for schedule in self.schedules:
                try:
                    # 獲取群組名稱
                    group_id = schedule.get('group_id')
                    group_info = self.groups.get(group_id, {})
                    group_name = group_info.get('name', '未知群組') if isinstance(group_info, dict) else group_info
                    
                    formatted_schedule = {
                        'id': schedule.get('id', 'unknown'),
                        'scheduled_time': schedule.get('scheduled_time', 'Unknown'),
                        'group_id': group_id,
                        'group_name': group_name,
                        'message': schedule.get('message', ''),
                        'created_at': schedule.get('created_at', 'Unknown')
                    }
                    formatted_schedules.append(formatted_schedule)
                except Exception as e:
                    logger.error(f"格式化排程時發生錯誤: {e}")
                    continue
                    
            # 按時間排序
            formatted_schedules.sort(key=lambda x: x['scheduled_time'])
            
            return formatted_schedules
        except Exception as e:
            logger.error(f"獲取排程列表時發生錯誤: {e}")
            return []

    def _load_groups(self):
        """載入群組資訊"""
        try:
            if os.path.exists(self.groups_file):
                with open(self.groups_file, 'r', encoding='utf-8') as f:
                    groups = json.load(f)
                    # 統一格式化所有群組資訊
                    formatted_groups = {}
                    for group_id, info in groups.items():
                        formatted_groups[group_id] = self._format_group_info(info)
                    return formatted_groups
            return {}
        except Exception as e:
            logger.error(f"載入群組資料時發生錯誤: {e}")
            return {}

    def _format_group_info(self, info):
        """統一格式化群組資訊"""
        if isinstance(info, str):
            return {
                'name': info,
                'joined_at': datetime.now(pytz.UTC).isoformat()
            }
        elif isinstance(info, dict):
            if 'name' not in info:
                info['name'] = '未命名群組'
            if 'joined_at' not in info:
                info['joined_at'] = datetime.now(pytz.UTC).isoformat()
            return info
        else:
            return {
                'name': '未命名群組',
                'joined_at': datetime.now(pytz.UTC).isoformat()
            }

    def _load_nids(self):
        """載入群組 NID 對應"""
        try:
            with open('data/group_nids.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
            
    def get_group_id_by_nid(self, nid):
        """通過 NID 獲取群組 ID"""
        try:
            nid = str(nid)  # 確保 nid 是字串
            return self.nids.get(nid)
        except:
            return None
            
    def get_nid_by_group_id(self, group_id):
        """通過群組 ID 獲取 NID"""
        for nid, gid in self.nids.items():
            if gid == group_id:
                return nid
        return None
        
    def get_formatted_groups(self):
        """獲取格式化的群組列表"""
        formatted_groups = []
        for nid, group_id in self.nids.items():
            group_info = self.groups.get(group_id, {})
            if isinstance(group_info, str):
                group_info = self._format_group_info(group_info)
            
            formatted_groups.append({
                'nid': nid,
                'name': group_info.get('name', f'群組 {nid}')
            })
        return formatted_groups 