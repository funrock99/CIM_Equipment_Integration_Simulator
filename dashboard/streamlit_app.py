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

# Sidebar
st.sidebar.title("Control Panel")
page = st.sidebar.selectbox("Navigation", ["Overview", "Alarms", "Sensors"])

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
