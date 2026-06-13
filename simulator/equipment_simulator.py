import time
import random
import requests
import datetime
import threading

API_BASE_URL = "http://localhost:8000/api"

EQUIPMENTS = [
    {"eqp_id": "EQP-ETCH-001", "eqp_name": "Etcher 1", "eqp_type": "ETCH", "location": "FAB1"},
    {"eqp_id": "EQP-ETCH-002", "eqp_name": "Etcher 2", "eqp_type": "ETCH", "location": "FAB1"},
    {"eqp_id": "EQP-ETCH-003", "eqp_name": "Etcher 3", "eqp_type": "ETCH", "location": "FAB2"},
    {"eqp_id": "EQP-CVD-001", "eqp_name": "CVD 1", "eqp_type": "CVD", "location": "FAB1"},
    {"eqp_id": "EQP-CVD-002", "eqp_name": "CVD 2", "eqp_type": "CVD", "location": "FAB1"},
    {"eqp_id": "EQP-CVD-003", "eqp_name": "CVD 3", "eqp_type": "CVD", "location": "FAB2"},
    {"eqp_id": "EQP-WET-001", "eqp_name": "Wet Bench 1", "eqp_type": "WET", "location": "FAB1"},
    {"eqp_id": "EQP-WET-002", "eqp_name": "Wet Bench 2", "eqp_type": "WET", "location": "FAB2"},
    {"eqp_id": "EQP-PVD-001", "eqp_name": "PVD 1", "eqp_type": "PVD", "location": "FAB1"},
    {"eqp_id": "EQP-PVD-002", "eqp_name": "PVD 2", "eqp_type": "PVD", "location": "FAB2"},
]

STATUSES = ["RUN", "IDLE", "DOWN", "PM"]

def register_equipments():
    for eqp in EQUIPMENTS:
        try:
            res = requests.post(f"{API_BASE_URL}/equipment/register", json=eqp)
            print(f"Registered {eqp['eqp_id']}: {res.status_code}")
        except Exception as e:
            print(f"Failed to register {eqp['eqp_id']}: {e}")

def register_default_rules():
    try:
        res = requests.get(f"{API_BASE_URL}/rules")
        rules = res.json() if res.status_code == 200 else []
        if not any(r.get("sensor_name") == "Temperature" for r in rules):
            rule = {
                "eqp_id": None,
                "sensor_name": "Temperature",
                "condition": ">",
                "threshold_value": 85.0,
                "alarm_code": "0001",
                "alarm_level": "WARNING",
                "alarm_message": "Temperature exceeded 85.0"
            }
            requests.post(f"{API_BASE_URL}/rules", json=rule)
            print("Default Alarm Rule registered.")
    except Exception as e:
        print(f"Failed to register default rule: {e}")

def simulate_equipment(eqp):
    eqp_id = eqp["eqp_id"]
    current_status = "IDLE"
    lot_id = f"LOT{datetime.datetime.now().strftime('%Y%m%d')}001"
    recipe_id = f"RCP-{eqp['eqp_type']}-A01"
    
    # 啟動時向 Host 取得最後狀態，確保重新啟動不會重置狀態
    try:
        init_res = requests.get(f"{API_BASE_URL}/equipment/{eqp_id}")
        if init_res.status_code == 200:
            init_data = init_res.json()
            current_status = init_data.get("current_status") or "IDLE"
            recipe_id = init_data.get("current_recipe_id") or recipe_id
            lot_id = init_data.get("current_lot_id") or lot_id
    except Exception as e:
        print(f"Failed to fetch initial state for {eqp_id}: {e}")
        
    while True:
        try:
            # Check if global simulator is enabled via API
            control_res = requests.get(f"{API_BASE_URL}/simulator/control").json()
            if not control_res.get("enabled", True):
                time.sleep(5)
                continue
                
            # Check if THIS equipment is enabled
            eqp_res = requests.get(f"{API_BASE_URL}/equipment/{eqp_id}")
            if eqp_res.status_code == 200:
                eqp_data = eqp_res.json()
                if not eqp_data.get("enabled", True):
                    time.sleep(5)
                    continue

            # Fetch pending commands
            pending_res = requests.get(f"{API_BASE_URL}/equipment/{eqp_id}/commands/pending")
            if pending_res.status_code == 200:
                for cmd in pending_res.json():
                    cmd_id = cmd["id"]
                    cmd_name = cmd["command_name"]
                    reply_status = "ACK"
                    
                    if cmd_name == "START":
                        current_status = "RUN"
                    elif cmd_name == "STOP":
                        current_status = "IDLE"
                    elif cmd_name == "CHANGE_RECIPE":
                        params = cmd.get("parameters", {}) or {}
                        if "recipe_id" in params:
                            recipe_id = params["recipe_id"]
                        else:
                            reply_status = "NACK"
                    
                    requests.post(f"{API_BASE_URL}/equipment/commands/{cmd_id}/reply", json={"status": reply_status})

            # Randomly start Lot
            if current_status == "IDLE" and random.random() < 0.05:
                use_wrong_recipe = random.random() < 0.1 # 10% chance to mismatch
                lot_recipe = recipe_id if not use_wrong_recipe else f"{recipe_id}-WRONG"
                new_lot = f"LOT{datetime.datetime.now().strftime('%H%M%S')}"
                lot_payload = {
                    "lot_id": new_lot,
                    "quantity": 25,
                    "recipe_id": lot_recipe
                }
                lot_res = requests.post(f"{API_BASE_URL}/equipment/{eqp_id}/lots/{new_lot}/start", json=lot_payload)
                if lot_res.status_code == 200:
                    current_status = "RUN"
                    lot_id = new_lot
                    
            # Randomly end Lot
            elif current_status == "RUN" and random.random() < 0.1:
                new_status = "IDLE"
                status_payload = {
                    "eqp_id": eqp_id,
                    "status": new_status,
                    "previous_status": current_status,
                    "reason": "Lot completed",
                    "event_time": datetime.datetime.now().isoformat()
                }
                requests.post(f"{API_BASE_URL}/equipment/status", json=status_payload)
                current_status = new_status

            # Random Anomaly (DOWN/PM)
            if current_status in ["RUN", "IDLE"] and random.random() < 0.02:
                new_status = random.choices(["DOWN", "PM"], weights=[80, 20])[0]
                status_payload = {
                    "eqp_id": eqp_id,
                    "status": new_status,
                    "previous_status": current_status,
                    "reason": "Simulated hardware anomaly",
                    "event_time": datetime.datetime.now().isoformat()
                }
                requests.post(f"{API_BASE_URL}/equipment/status", json=status_payload)
                current_status = new_status
                
            # S6F11 Event Report for Status Change (omitted here since API handles most, but we can keep it if needed. Actually we'll skip S6F11 here to keep the code clean, or just trust the backend)
                    
            # Simulate Sensor Data
            temp = round(random.uniform(20.0, 90.0), 2)
            pressure = round(random.uniform(0.5, 2.5), 2)
            
            requests.post(f"{API_BASE_URL}/equipment/sensor", json={
                "eqp_id": eqp_id, "sensor_name": "Temperature", "sensor_value": temp, "unit": "C"
            })
            requests.post(f"{API_BASE_URL}/equipment/sensor", json={
                "eqp_id": eqp_id, "sensor_name": "Pressure", "sensor_value": pressure, "unit": "atm"
            })
            
            # Alarm 邏輯已移至 CIM Host API 端 (Alarm Rule Engine)
                
        except Exception as e:
            print(f"Error simulating {eqp_id}: {e}")
            
        time.sleep(5)

if __name__ == "__main__":
    print("Waiting for API to start...")
    time.sleep(5)
    register_equipments()
    register_default_rules()
    
    threads = []
    for eqp in EQUIPMENTS:
        t = threading.Thread(target=simulate_equipment, args=(eqp,))
        t.daemon = True
        t.start()
        threads.append(t)
        
    print("Simulator running. Press Ctrl+C to exit.")
    while True:
        time.sleep(1)
