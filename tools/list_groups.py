import json
import os

def load_json(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return {}

def list_groups():
    data_dir = "data"
    groups = load_json(os.path.join(data_dir, "line_groups.json"))
    nids = load_json(os.path.join(data_dir, "group_nids.json"))

    print("\n=== 群組列表 ===")
    print("NID | 群組名稱 | 群組 ID")
    print("-" * 80)
    
    for group_id, name in groups.items():
        # 找出對應的 NID
        nid = next((n for n, gid in nids.items() if gid == group_id), "N/A")
        print(f"{nid} | {name} | {group_id}")

if __name__ == "__main__":
    list_groups() 