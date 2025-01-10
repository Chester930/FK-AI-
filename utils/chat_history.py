from typing import Dict, List, Optional
from datetime import datetime
import json

class ChatHistory:
    def __init__(self, max_history: int = 10):
        self.max_history = max_history
        self.personal_history: Dict[str, List[Dict]] = {}
        self.group_history: Dict[str, List[Dict]] = {}
        self.personal_states: Dict[str, Dict] = {}
        self.group_states: Dict[str, Dict] = {}

    def add_message(self, id: str, role: str, message: str, is_group: bool = False):
        """添加新消息到歷史記錄"""
        history_dict = self.group_history if is_group else self.personal_history
        
        if id not in history_dict:
            history_dict[id] = []
            
        history_dict[id].append({
            'timestamp': datetime.now().isoformat(),
            'role': role,
            'message': message
        })
        
        # 保持歷史記錄在最大限制內
        if len(history_dict[id]) > self.max_history:
            history_dict[id].pop(0)

    def get_history(self, id: str, is_group: bool = False) -> List[Dict]:
        """獲取特定ID的歷史記錄"""
        history_dict = self.group_history if is_group else self.personal_history
        return history_dict.get(id, [])

    def get_state(self, id: str, is_group: bool = False) -> Optional[Dict]:
        """獲取特定ID的狀態"""
        states_dict = self.group_states if is_group else self.personal_states
        return states_dict.get(id)

    def set_state(self, id: str, state: Dict, is_group: bool = False):
        """設置特定ID的狀態"""
        states_dict = self.group_states if is_group else self.personal_states
        states_dict[id] = state

    def clear_history(self, id: str, is_group: bool = False):
        """清除特定ID的歷史記錄"""
        history_dict = self.group_history if is_group else self.personal_history
        if id in history_dict:
            del history_dict[id]

    def format_context(self, id: str, is_group: bool = False) -> str:
        """格式化上下文供AI使用"""
        history = self.get_history(id, is_group)
        if not history:
            return ""
            
        context = "\n".join([
            f"{'Bot' if msg['role'] == 'assistant' else 'User'}: {msg['message']}"
            for msg in history[-self.max_history:]
        ])
        return f"Previous conversation:\n{context}\n"

    def save_to_file(self, filepath: str):
        """保存歷史記錄到文件"""
        data = {
            'personal_history': self.personal_history,
            'group_history': self.group_history,
            'personal_states': self.personal_states,
            'group_states': self.group_states
        }
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load_from_file(self, filepath: str):
        """從文件加載歷史記錄"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.personal_history = data.get('personal_history', {})
                self.group_history = data.get('group_history', {})
                self.personal_states = data.get('personal_states', {})
                self.group_states = data.get('group_states', {})
        except FileNotFoundError:
            pass 