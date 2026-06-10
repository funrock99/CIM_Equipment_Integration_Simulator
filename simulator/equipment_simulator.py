import time
import random
import requests
import datetime
import threading

API_BASE_URL = "http://localhost:8000/api"

EQUIPMENTS = [
    {"eqp_id": "EQP-ETCH-001", "eqp_name": "Etcher 1", "eqp_type": "ETCH", "location": "FAB1"},
    {"eqp_id": "EQP-CVD-001", "eqp_name": "CVD 1", "eqp_type": "CVD", "location": "FAB1"},
    {"eqp_id": "EQP-WET-001", "eqp_name": "Wet Bench 1", "eqp_type": "WET", "location": "FAB1"},
    {"eqp_id": "EQP-PVD-001", "eqp_name": "PVD 1", "eqp_type": "PVD", "location": "FAB1"},
]

STATUSES = ["RUN", "IDLE", "DOWN", "PM"]

def register_equipments():
    for eqp in EQUIPMENTS:
        try:
            res = requests.post(f"{API_BASE_URL}/equipment/register", json=eqp)
            print(f"Registered {eqp['eqp_id']}: {res.status_code}")
        except Exception as e:
            print(f"Failed to register {eqp['eqp_id']}: {e}")

def simulate_equipment(eqp):
    eqp_id = eqp["eqp_id"]
    current_status = "IDLE"
    lot_id = f"LOT{datetime.datetime.now().strftime('%Y%m%d')}001"
    recipe_id = f"RCP-{eqp['eqp_type']}-A01"
    
    while True:
        try:
            # Check if simulator is enabled via API
            control_res = requests.get(f"{API_BASE_URL}/simulator/control").json()
            if not control_res.get("enabled", True):
                # print(f"[{eqp_id}] Simulator is PAUSED. Waiting...")
                time.sleep(5)
                continue

            # Random Status Change (mostly stays same)
            if random.random() < 0.2:
                new_status = random.choices(STATUSES, weights=[60, 30, 8, 2])[0]
                if new_status != current_status:
                    status_payload = {
                        "eqp_id": eqp_id,
                        "status": new_status,
                        "previous_status": current_status,
                        "reason": "Simulated state change",
                        "event_time": datetime.datetime.now().isoformat()
                    }
                    requests.post(f"{API_BASE_URL}/equipment/status", json=status_payload)
                    
                    # S6F11 Event Report for Status Change
                    event_payload = {
                        "stream": 6,
                        "function": 11,
                        "message_name": "S6F11_EventReport",
                        "equipment_id": eqp_id,
                        "event_id": "CEID_STATUS_CHANGE",
                        "report": {
                            "status": new_status,
                            "lot_id": lot_id if new_status == "RUN" else "",
                            "recipe_id": recipe_id if new_status == "RUN" else ""
                        },
                        "event_time": datetime.datetime.now().isoformat()
                    }
                    requests.post(f"{API_BASE_URL}/secs/message", json=event_payload)
                    current_status = new_status
            
            # Simulate Sensor Data
            temp = round(random.uniform(20.0, 90.0), 2)
            pressure = round(random.uniform(0.5, 2.5), 2)
            
            requests.post(f"{API_BASE_URL}/equipment/sensor", json={
                "eqp_id": eqp_id, "sensor_name": "Temperature", "sensor_value": temp, "unit": "C"
            })
            requests.post(f"{API_BASE_URL}/equipment/sensor", json={
                "eqp_id": eqp_id, "sensor_name": "Pressure", "sensor_value": pressure, "unit": "atm"
            })
            
            # Simulate Alarms
            if temp > 85.0:
                alarm_payload = {
                    "eqp_id": eqp_id, "alarm_code": "ALM_HIGH_TEMP", "alarm_level": "WARNING",
                    "alarm_message": "Temperature exceeded 85C", "alarm_status": "ACTIVE"
                }
                requests.post(f"{API_BASE_URL}/equipment/alarm", json=alarm_payload)
                
                # S5F1 Alarm Report
                requests.post(f"{API_BASE_URL}/secs/message", json={
                    "stream": 5, "function": 1, "message_name": "S5F1_AlarmReport",
                    "equipment_id": eqp_id, "event_id": "ALM_HIGH_TEMP",
                    "report": {"level": "WARNING", "message": "Temperature exceeded 85C"}
                })
                
        except Exception as e:
            print(f"Error simulating {eqp_id}: {e}")
            
        time.sleep(5)

if __name__ == "__main__":
    print("Waiting for API to start...")
    time.sleep(5)
    register_equipments()
    
    threads = []
    for eqp in EQUIPMENTS:
        t = threading.Thread(target=simulate_equipment, args=(eqp,))
        t.daemon = True
        t.start()
        threads.append(t)
        
    print("Simulator running. Press Ctrl+C to exit.")
    while True:
        time.sleep(1)
