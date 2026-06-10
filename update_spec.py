import os
import re

filename = None
for f in os.listdir('.'):
    if f.startswith('CIM_Equipment_Integration_Simulator_') and f.endswith('.md'):
        filename = f
        break

if filename:
    with open(filename, 'r', encoding='big5', errors='ignore') as f:
        content = f.read()

    # 尋找可以插入 Alarm Rule Engine 的段落
    # 如果有 "API 端點設計" 或 "系統架構"，可以加在裡面。
    # 簡單的做法是在文件最後，或在 Features 的地方加上去。
    
    addition = """
### 6. 動態警報規則引擎 (Alarm Rule Engine)
- **功能描述**：允許 CIM Host API 根據使用者設定的門檻值，動態判定是否產生警報，拔除原本寫死在模擬器內的判斷邏輯。
- **資料表結構 (AlarmRule)**：
  - `rule_id`: 規則編號
  - `sensor_name`: 感測器名稱 (如 Temperature)
  - `condition`: 觸發條件 (如 >, <, ==)
  - `threshold_value`: 觸發門檻
  - `alarm_code` & `alarm_message`: 觸發時要記錄的錯誤代碼與訊息
- **運作流程**：
  1. 使用者可透過 `/api/equipment/rules` 端點增刪查改這些規則。
  2. 當設備上拋 Sensor Data 時，API 端點會主動與 `AlarmRule` 進行比對。
  3. 若數值違反規則，API 則主動建立一筆 Alarm Log 儲存於資料庫，後續可連動 Line Bot 等推播機制。
"""
    
    if "Alarm Rule Engine" not in content:
        content = content + "\n\n" + addition
        with open(filename, 'w', encoding='big5', errors='ignore') as f:
            f.write(content)
        print("Updated spec with Alarm Rule Engine.")
    else:
        print("Already updated.")
else:
    print("Spec file not found.")
