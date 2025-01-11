import streamlit as st
import sys
import os
import json
from datetime import datetime, timedelta
import pytz
import yaml

# 將專案根目錄加入到 sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.scheduled_messages import MessageScheduler
from linebot.v3.messaging import Configuration, ApiClient, MessagingApi
from utils.notification_manager import NotificationManager

# 設定台灣時區
TIMEZONE = 'Asia/Taipei'
tw_timezone = pytz.timezone(TIMEZONE)

# 初始化管理器
notification_manager = NotificationManager()
message_scheduler = MessageScheduler()

# 在 imports 之後，類別之前添加
NOTIFICATION_SETTINGS_FILE = 'data/notification_settings.yml'

def load_group_list():
    """載入群組列表"""
    return notification_manager.groups

def save_group_list(groups):
    """儲存群組列表"""
    notification_manager.groups = groups
    return notification_manager.save_groups()

def main():
    st.set_page_config(page_title="Fight.K 通知管理後台", page_icon="✝️", layout="wide")
    st.title("Fight.K 通知管理後台 ✝️")

    # 側邊欄選單
    menu = st.sidebar.selectbox(
        "功能選單",
        ["排程管理", "群組管理", "通知設定"]
    )

    if menu == "排程管理":
        show_schedule_management()
    elif menu == "群組管理":
        show_group_management()
    else:
        show_notification_settings()

def show_schedule_management():
    st.header("排程管理")
    
    # 顯示現有排程
    st.subheader("現有排程")
    schedules = message_scheduler.list_schedules()
    if schedules:
        for schedule in schedules:
            col1, col2 = st.columns([0.9, 0.1])
            with col1:
                st.write(f"ID: {schedule['id']}")
                st.write(f"名稱: {schedule['name']}")
                st.write(f"下次執行時間: {schedule['scheduled_time']}")
            with col2:
                if st.button("刪除", key=f"del_{schedule['id']}"):
                    message_scheduler.remove_schedule(schedule['id'])
                    st.success("排程已刪除")
                    st.experimental_rerun()
    else:
        st.info("目前沒有排程")

    # 新增排程
    st.subheader("新增排程")
    with st.form("add_schedule"):
        groups = load_group_list()
        selected_group = st.selectbox("選擇群組", options=list(groups.keys()), format_func=lambda x: groups[x])
        
        datetime_str = st.text_input(
            "輸入時間 (格式: YYYYMMDD-HH:MM)",
            help="例如：20240101-09:30"
        )
        
        message = st.text_area("訊息內容")
        submitted = st.form_submit_button("新增排程")
        
        if submitted:
            try:
                if not datetime_str:
                    st.error("請輸入時間")
                    return
                
                # 驗證時間格式並轉換
                try:
                    schedule_datetime = datetime.strptime(datetime_str, '%Y%m%d-%H:%M')
                    schedule_datetime = tw_timezone.localize(schedule_datetime)
                except ValueError:
                    st.error("時間格式錯誤，請使用正確的格式：YYYYMMDD-HH:MM")
                    return
                
                if schedule_datetime <= datetime.now(tw_timezone):
                    st.error("請選擇未來的時間")
                    return
                
                if not message:
                    st.error("請輸入訊息內容")
                    return
                
                result = message_scheduler.schedule_message(selected_group, datetime_str, message)
                
                if result:
                    st.success("排程新增成功！")
                    st.experimental_rerun()
            except Exception as e:
                st.error(f"發生錯誤：{str(e)}")

def show_group_management():
    st.header("群組管理")
    
    groups = load_group_list()
    
    # 顯示現有群組
    st.subheader("現有群組")
    for group_id, group_name in groups.items():
        col1, col2 = st.columns([0.9, 0.1])
        with col1:
            st.write(f"群組ID: {group_id}")
            st.write(f"群組名稱: {group_name}")
        with col2:
            if st.button("刪除", key=f"del_group_{group_id}"):
                del groups[group_id]
                save_group_list(groups)
                st.success("群組已刪除")
                st.experimental_rerun()
    
    # 新增群組
    st.subheader("新增群組")
    with st.form("add_group"):
        new_group_id = st.text_input("群組 ID")
        new_group_name = st.text_input("群組名稱")
        submitted = st.form_submit_button("新增群組")
        
        if submitted:
            if new_group_id and new_group_name:
                groups[new_group_id] = new_group_name
                save_group_list(groups)
                st.success("群組新增成功！")
                st.experimental_rerun()
            else:
                st.error("請填寫完整資訊")

def _handle_notification_form(form_type: str, settings: dict, groups: dict) -> None:
    """處理通知表單提交"""
    selected_group = st.selectbox(
        "選擇群組", 
        options=list(groups.keys()), 
        format_func=lambda x: groups[x],
        key=f"{form_type}_group"
    )
    
    if form_type == 'weekly':
        weekday = st.selectbox(
            "選擇星期", 
            options=['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun'],
            format_func=lambda x: {
                'mon': '星期一', 'tue': '星期二', 'wed': '星期三',
                'thu': '星期四', 'fri': '星期五', 'sat': '星期六',
                'sun': '星期日'
            }[x]
        )
    
    time_str = st.text_input(
        "通知時間 (格式: HH:MM)",
        help="例如：09:30",
        key=f"{form_type}_time_str"
    )
    
    message = st.text_area("通知內容", key=f"{form_type}_message")
    
    if st.form_submit_button(f"新增{form_type=='daily'and'每日'or'每週'}通知"):
        try:
            datetime.strptime(time_str, '%H:%M')
            hour, minute = time_str.split(':')
            
            new_notification = {
                'group_id': selected_group,
                'schedule': {
                    'hour': hour,
                    'minute': minute,
                    'timezone': TIMEZONE
                },
                'message': message
            }
            
            if form_type == 'weekly':
                new_notification['schedule']['day_of_week'] = weekday
                
            settings[f'{form_type}_notifications'].append(new_notification)
            
            with open(NOTIFICATION_SETTINGS_FILE, 'w', encoding='utf-8') as f:
                yaml.dump(settings, f, allow_unicode=True)
            
            st.success("設定已儲存")
            st.experimental_rerun()
        except ValueError:
            st.error("時間格式錯誤，請使用 HH:MM 格式")

def show_notification_settings():
    st.header("通知設定")
    
    try:
        with open(NOTIFICATION_SETTINGS_FILE, 'r', encoding='utf-8') as f:
            settings = yaml.safe_load(f) or {
                'daily_notifications': [],
                'weekly_notifications': [],
                'specific_date_notifications': []
            }
    except FileNotFoundError:
        settings = {
            'daily_notifications': [],
            'weekly_notifications': [],
            'specific_date_notifications': []
        }
    
    groups = load_group_list()
    
    # 每日通知設定
    st.subheader("每日通知設定")
    with st.form("daily_notification"):
        _handle_notification_form('daily', settings, groups)

    # 每週通知設定
    st.subheader("每週通知設定")
    with st.form("weekly_notification"):
        _handle_notification_form('weekly', settings, groups)

if __name__ == "__main__":
    main()