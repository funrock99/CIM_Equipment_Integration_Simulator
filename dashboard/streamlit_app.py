import streamlit as st
import requests
import pandas as pd

API_URL = "http://localhost:8000/api"

st.set_page_config(page_title="CIM Equipment Dashboard", layout="wide")
st.title("CIM Equipment Integration Simulator Dashboard")

def get_equipments():
    try:
        res = requests.get(f"{API_URL}/equipment")
        if res.status_code == 200:
            return res.json()
    except:
        pass
    return []

def get_alarms(eqp_id):
    try:
        res = requests.get(f"{API_URL}/equipment/{eqp_id}/alarms?limit=50")
        if res.status_code == 200:
            return res.json()
    except:
        pass
    return []

def get_sensors(eqp_id):
    try:
        res = requests.get(f"{API_URL}/equipment/{eqp_id}/sensors?limit=100")
        if res.status_code == 200:
            return res.json()
    except:
        pass
    return []

def get_sim_status():
    try:
        res = requests.get(f"{API_URL}/simulator/control")
        if res.status_code == 200:
            return res.json().get("enabled", True)
    except:
        pass
    return True

def set_sim_status(enabled):
    try:
        requests.post(f"{API_URL}/simulator/control?enabled={str(enabled).lower()}")
    except:
        pass

def get_rules():
    try:
        res = requests.get(f"{API_URL}/rules")
        if res.status_code == 200:
            return res.json()
    except:
        pass
    return []

def create_rule(rule_data):
    try:
        res = requests.post(f"{API_URL}/rules", json=rule_data)
        return res.status_code == 200
    except:
        return False

def delete_rule(rule_id):
    try:
        res = requests.delete(f"{API_URL}/rules/{rule_id}")
        return res.status_code == 200
    except:
        return False

# Sidebar
st.sidebar.title("Control Panel")
page = st.sidebar.selectbox("Navigation", ["Overview", "Alarms", "Sensors", "Alarm Rules"])

st.sidebar.divider()
st.sidebar.subheader("Simulator System")
current_sim_status = get_sim_status()
new_sim_status = st.sidebar.toggle("Enable Data Reporting", value=current_sim_status)



if new_sim_status != current_sim_status:
    set_sim_status(new_sim_status)
    st.sidebar.success(f"Simulator {'Started' if new_sim_status else 'Paused'}")
    st.rerun()

equipments = get_equipments()

if page == "Overview":
    st.header("Equipment Overview")
    if not equipments:
        st.warning("No equipment data available.")
    else:
        df_eqp = pd.DataFrame(equipments)
        st.dataframe(df_eqp[['eqp_id', 'eqp_name', 'eqp_type', 'current_status', 'updated_at']], use_container_width=True)
        
        st.subheader("Status Distribution")
        status_counts = df_eqp['current_status'].value_counts()
        st.bar_chart(status_counts)

elif page == "Alarms":
    st.header("Alarm List")
    if not equipments:
        st.warning("No equipment data available.")
    else:
        eqp_id = st.selectbox("Select Equipment", [e["eqp_id"] for e in equipments])
        alarms = get_alarms(eqp_id)
        if alarms:
            df_alarms = pd.DataFrame(alarms)
            st.dataframe(df_alarms[['alarm_code', 'alarm_level', 'alarm_message', 'alarm_status', 'occurred_at']], use_container_width=True)
        else:
            st.info("No alarms found for this equipment.")

elif page == "Sensors":
    st.header("Sensor Trends")
    if not equipments:
        st.warning("No equipment data available.")
    else:
        eqp_id = st.selectbox("Select Equipment", [e["eqp_id"] for e in equipments])
        sensors = get_sensors(eqp_id)
        if sensors:
            df_sensors = pd.DataFrame(sensors)
            df_sensors['collected_at'] = pd.to_datetime(df_sensors['collected_at'])
            
            sensor_names = df_sensors['sensor_name'].unique()
            selected_sensor = st.selectbox("Select Sensor", sensor_names)
            
            df_filtered = df_sensors[df_sensors['sensor_name'] == selected_sensor]
            df_filtered = df_filtered.sort_values(by='collected_at')
            
            st.line_chart(data=df_filtered, x='collected_at', y='sensor_value')
        else:
            st.info("No sensor data found for this equipment.")

elif page == "Alarm Rules":
    st.header("Alarm Rule Settings")
    st.markdown("在此處管理由 CIM Host API 自動判斷並觸發的動態警報規則。")
    
    rules = get_rules()
    if rules:
        df_rules = pd.DataFrame(rules)
        st.subheader("Current Rules")
        st.dataframe(df_rules[['id', 'eqp_id', 'sensor_name', 'condition', 'threshold_value', 'alarm_code', 'alarm_level']], use_container_width=True)
        
        st.markdown("### 🗑️ Delete Rule")
        col_del, _ = st.columns([1, 2])
        with col_del:
            del_id = st.selectbox("Select Rule ID to delete", df_rules['id'].tolist())
            if st.button("Delete Selected Rule"):
                if delete_rule(del_id):
                    st.success(f"Rule {del_id} deleted successfully!")
                    st.rerun()
                else:
                    st.error("Failed to delete rule.")
    else:
        st.info("No active alarm rules found.")
    
    st.divider()
    st.subheader("➕ Create New Rule")
    with st.form("create_rule_form"):
        col_a, col_b = st.columns(2)
        with col_a:
            eqp_opts = ["All Equipment (Global)"] + [e["eqp_id"] for e in equipments]
            selected_eqp = st.selectbox("Target Equipment", eqp_opts)
            sensor_name = st.selectbox("Sensor Name", ["Temperature", "Pressure"])
            condition = st.selectbox("Condition", [">", "<", "==", ">=", "<="])
            threshold_value = st.number_input("Threshold Value", value=85.0)
        with col_b:
            alarm_code = st.text_input("Alarm Code", "ALM_NEW_RULE")
            alarm_level = st.selectbox("Alarm Level", ["WARNING", "CRITICAL", "INFO"])
            alarm_message = st.text_input("Alarm Message", "Custom rule triggered")
        
        submit_btn = st.form_submit_button("Save Rule")
        if submit_btn:
            new_rule = {
                "eqp_id": None if "All Equipment" in selected_eqp else selected_eqp,
                "sensor_name": sensor_name,
                "condition": condition,
                "threshold_value": float(threshold_value),
                "alarm_code": alarm_code,
                "alarm_level": alarm_level,
                "alarm_message": alarm_message
            }
            if create_rule(new_rule):
                st.success("Rule created successfully!")
                st.rerun()
            else:
                st.error("Failed to create rule. Please check API connection.")
