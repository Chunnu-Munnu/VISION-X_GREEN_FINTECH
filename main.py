
import streamlit as st
import serial
import pandas as pd
import time
import numpy as np
from ml_model import SolarAnomalyModel
from database import init_db, create_user, get_user, update_coins, log_reading, get_history

# ---------------- INITIALIZE ----------------
init_db()
st.set_page_config(layout="wide", page_title="VISION-X Green FinTech")

# ---------------- STYLES (Clean & Professional) ----------------
# Force Dark/Light adaptability without imposing weird colors
st.markdown("""
<style>
    /* Metric Card Styling */
    .stMetric {
        background-color: transparent !important;
        border: 1px solid rgba(128, 128, 128, 0.2);
        padding: 10px;
        border-radius: 8px;
    }
    
    /* Remove Header Decoration */
    header {visibility: hidden;}
    
    /* Login Form Centering */
    div.stButton > button {
        width: 100%;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

st.title("🌱 VISION-X Green FinTech")
st.caption("AI-Powered Renewable Energy Verification & Incentive Engine")

# ---------------- SESSION STATE ----------------
for key in ["user_id", "coins", "model", "data_buffer", "ser", "running", "penalty_until", "simulate_grid"]:
    if key not in st.session_state:
        if key == "model": st.session_state[key] = SolarAnomalyModel()
        elif key == "data_buffer": st.session_state[key] = []
        elif key in ["coins", "penalty_until"]: st.session_state[key] = 0.0
        else: st.session_state[key] = None

if "simulate_grid" not in st.session_state: st.session_state.simulate_grid = False
if "running" not in st.session_state: st.session_state.running = False


# ---------------- AUTHENTICATION ----------------
if st.session_state.user_id is None:
    
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        with st.form("login_form"):
            uid_input = st.text_input("Enter User ID", placeholder="e.g. 1")
            login_submitted = st.form_submit_button("Access Dashboard")
            
            if login_submitted:
                if uid_input:
                    try:
                        user = get_user(int(uid_input))
                        if user:
                            st.session_state.user_id = user[0]
                            st.session_state.coins = user[3]
                            st.rerun()
                        else:
                            st.error("User ID not found.")
                    except ValueError:
                        st.error("Please enter a valid numeric ID.")

    with tab2:
        with st.form("register_form"):
            name = st.text_input("Full Name")
            phone = st.text_input("Phone Number")
            reg_submitted = st.form_submit_button("Create Account")
            
            if reg_submitted:
                if name and phone:
                    user_id = create_user(name, phone)
                    st.session_state.user_id = user_id
                    st.success(f"User Created. Your ID: {user_id}")
                    st.rerun()
                else:
                    st.warning("Please enter name and phone.")

# ---------------- MAIN DASHBOARD ----------------
else:
    user = get_user(st.session_state.user_id)
    if not user:
        st.session_state.user_id = None
        st.rerun()

    user_id, name, phone, coins_db = user
    
    # Sidebar
    with st.sidebar:
        st.header(f"👤 {name}")
        st.caption(f"ID: {user_id}")
        
        if st.button("Logout"):
            if st.session_state.ser:
                st.session_state.ser.close()
            st.session_state.user_id = None
            st.session_state.running = False
            st.rerun()
            
        st.divider()
        st.markdown("### ⚙ Connection")
        port = st.text_input("COM Port", value="COM7")
        
        c1, c2 = st.columns(2)
        if c1.button("Start", type="primary"):
            try:
                if not st.session_state.running:
                    st.session_state.ser = serial.Serial(port, 115200, timeout=1)
                    st.session_state.running = True
                    st.toast("Connected!", icon="🔌")
                    st.rerun()
            except Exception as e:
                st.error(f"Failed: {e}")

        if c2.button("Stop"):
            if st.session_state.ser:
                st.session_state.ser.close()
            st.session_state.running = False
            st.toast("Stopped")
            st.rerun()

        st.divider()
        st.markdown("### 🧪 Testing")
        
        def toggle_sim():
            st.session_state.simulate_grid = not st.session_state.simulate_grid
            
        st.checkbox("Simulate Fake Grid", value=st.session_state.simulate_grid, on_change=toggle_sim)


    # Main Layout
    
    # 1. METRICS ROW
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Green Coins", f"{st.session_state.coins:.4f}")
    
    # Placeholders for dynamic updates
    status_ph = m2.empty()
    power_ph = m3.empty()
    curr_ph = m4.empty()
    
    # Graph Placeholders
    st.divider()
    g1, g2, g3 = st.columns(3)
    graph_ph_v = g1.empty()
    graph_ph_c = g2.empty()
    graph_ph_p = g3.empty()

    
    # ---------------- REAL-TIME LOOP ----------------
    if st.session_state.running:
        
        # Read Data
        voltage, current, power = 0.0, 0.0, 0.0
        
        # Try Read Serial
        if st.session_state.ser and st.session_state.ser.in_waiting > 0:
            try:
                line = st.session_state.ser.readline().decode(errors="ignore").strip()
                if line and "," in line:
                    parts = line.split(",")
                    if len(parts) == 3:
                        voltage = float(parts[0])
                        current = abs(float(parts[1]))
                        power = voltage * current
            except:
                pass

        # Simulation Override
        if st.session_state.simulate_grid:
            voltage = 5.0 
            current = 200.0
            power = voltage * current

        # Buffer Update
        temp_data = [voltage, current, power]
        st.session_state.data_buffer.append(temp_data)
        if len(st.session_state.data_buffer) > 50:
            st.session_state.data_buffer.pop(0)

        # Train Logic
        if len(st.session_state.data_buffer) >= 20 and not st.session_state.model.trained:
            training_data = list(st.session_state.data_buffer)[-20:] 
            st.session_state.model.train(training_data)
            st.toast("Model Calibrated", icon="🧠")

        # Prediction Logic
        status_text = "Waiting..."
        is_anomaly = 0
        coins_earned = 0.0
        
        if st.session_state.model.trained:
            prediction = st.session_state.model.predict(temp_data)
            now = time.time()
            time_left = max(0, st.session_state.penalty_until - now)
            
            if prediction == -1: # Anomaly
                is_anomaly = 1
                status_text = "🚨 ANOMALY"
                st.session_state.penalty_until = now + 30
                status_ph.error(status_text)
            
            elif time_left > 0: # Penalty
                status_text = f"🚫 PENALTY ({int(time_left)}s)"
                is_anomaly = 0 
                status_ph.warning(status_text)
            
            else: # Normal
                status_text = "✅ VERIFIED"
                is_anomaly = 0
                coins_earned = power * 0.0001
                st.session_state.coins += coins_earned
                update_coins(user_id, st.session_state.coins)
                status_ph.success(status_text)
        else:
             status_ph.info("Calibrating...")

        # Update Metrics
        p_str = f"{(power*1000):.1f} µW" if power < 1.0 else f"{power:.2f} mW"
        c_str = f"{(current*1000):.1f} µA" if current < 1.0 else f"{current:.2f} mA"
        
        power_ph.metric("Power", p_str)
        curr_ph.metric("Current", c_str)
        
        # Update Graphs (using st.line_chart directly on placeholders doesn't work well in loop, simpler to redraw)
        df_chart = pd.DataFrame(st.session_state.data_buffer, columns=["Voltage", "Current", "Power"])
        
        with graph_ph_v:
            st.subheader("Voltage")
            st.line_chart(df_chart["Voltage"], height=200, color="#FF4B4B")
            
        with graph_ph_c:
            st.subheader("Current")
            st.line_chart(df_chart["Current"], height=200, color="#29B5E8")
            
        with graph_ph_p:
            st.subheader("Power")
            st.line_chart(df_chart["Power"], height=200, color="#17C37B")

        # Log DB
        log_reading(user_id, voltage, current, power, is_anomaly, coins_earned)
        
        # Rerun loop
        time.sleep(0.1 if st.session_state.simulate_grid else 0.5)
        st.rerun()

    else:
        # Static View (Not Running)
        st.info("Click Start to begin monitoring.")
        
        st.divider()
        st.subheader("Audit Log")
        history_raw = get_history(user_id, limit=20)
        hist_data = []
        for row in history_raw:
             ts, v, c, p, anom = row
             status_str = "FRAUD" if anom else "VERIFIED"
             t_str = time.strftime('%H:%M:%S', time.localtime(ts))
             hist_data.append([t_str, f"{v:.2f} V", f"{p:.2f} mW", status_str])
        
        st.table(pd.DataFrame(hist_data, columns=["Time", "Voltage", "Power", "Status"]))
