import streamlit as st
import pandas as pd
import requests
import time

st.set_page_config(page_title="SNPSU Live IoT Guard", page_icon="📡", layout="wide")

# --- PASSCODE GATE ---
CLASS_PASSCODE = "SNPSU2026"
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    st.title("🔑 SNPSU Sensor Gateway")
    pwd = st.text_input("Enter Passcode:", type="password")
    if st.button("Unlock"):
        if pwd == CLASS_PASSCODE:
            st.session_state["logged_in"] = True
            st.rerun()
    st.stop()

st.title("📡 Live IoT Emission & Oxygen Sensor Stream")
st.caption("Saptagiri NPS University | Real-time Agarbatti Combustion Detection")

# --- SIDEBAR: LIVE FEED SETUP ---
st.sidebar.header("⚙️ Telemetry Source")
mode = st.sidebar.radio("Data Mode:", ["Live Physical Sensor Stream (ThingSpeak / API)", "Manual Interactive Sliders"])

# Auto-refresh loop toggle
auto_refresh = st.sidebar.checkbox("⚡ Enable Real-time Auto-Refresh (every 3s)", value=False)

if mode == "Live Physical Sensor Stream (ThingSpeak / API)":
    st.sidebar.subheader("📡 Channel Credentials")
    channel_id = st.sidebar.text_input("ThingSpeak Channel ID:", "YOUR_CHANNEL_ID")
    read_api_key = st.sidebar.text_input("Read API Key (if private):", "")
    
    # Fetch live sensor data from ThingSpeak
    try:
        url = f"https://api.thingspeak.com/channels/{channel_id}/feeds/last.json"
        if read_api_key:
            url += f"?api_key={read_api_key}"
        res = requests.get(url, timeout=3).json()
        
        # Read fields sent by your ESP32 / Arduino
        o2_val = float(res.get("field1", 20.9))
        pm25_val = float(res.get("field2", 25.0))
        co_val = float(res.get("field3", 2.0))
        st.sidebar.success(f"Last updated: {res.get('created_at', 'Now')}")
    except Exception:
        st.sidebar.warning("⚠️ No live stream detected yet. Showing default baseline.")
        o2_val, pm25_val, co_val = 20.9, 25.0, 2.0
else:
    st.sidebar.subheader("🎛️ Live Manual Sensor Dial")
    st.sidebar.info("Simulate live analog voltage changes manually:")
    o2_val = st.sidebar.slider("Measured Oxygen (% O2)", 17.0, 21.5, 20.9, 0.1)
    pm25_val = st.sidebar.slider("Smoke Particulate (PM2.5 µg/m³)", 5.0, 600.0, 25.0, 1.0)
    co_val = st.sidebar.slider("Combustion CO (ppm)", 0.0, 100.0, 2.0, 1.0)

# Calculate dynamic AQI based on particulate density
calc_aqi = int(pm25_val * 1.1)

# --- METRIC DISPLAY ---
col1, col2, col3 = st.columns(3)
col1.metric("Live Oxygen (O2)", f"{o2_val}%", delta=f"{round(o2_val - 20.9, 1)}%", delta_color="normal" if o2_val >= 20.5 else "inverse")
col2.metric("Smoke PM2.5", f"{pm25_val} µg/m³", delta="Elevated" if pm25_val > 100 else "Clean", delta_color="inverse")
col3.metric("Carbon Monoxide (CO)", f"{co_val} ppm", delta="Combustion Detected" if co_val > 15 else "Normal", delta_color="inverse")

st.divider()

# --- INSTANT HAZARD EVALUATION ---
if o2_val < 19.5 or pm25_val > 300:
    st.error("🚨 CRITICAL HAZARD: Dense combustion plume detected! Severe oxygen dilution and toxic particulate spike.")
    st.markdown("**AI Action Plan:** Evacuate enclosed area immediately and switch on intake air blowers.")
elif o2_val < 20.5 or pm25_val > 100:
    st.warning("⚠️ WARNING: Smoke concentration rising. Agarbatti emissions displacing breathable oxygen.")
    st.markdown("**AI Action Plan:** Open windows for cross-ventilation and activate localized exhaust.")
else:
    st.success("✅ Clean Ambient Air: Normal oxygen saturation and safe particulate levels.")

# Auto-refresh mechanism
if auto_refresh:
    time.sleep(3)
    st.rerun()
