import streamlit as st
import serial
import pandas as pd
import time
from ml_model import SolarAnomalyModel
from database import init_db, create_user, get_user, update_coins

# ---------------- INITIALIZE ----------------
init_db()
st.set_page_config(layout="wide")
st.title("🌱 Green Energy AI Monitoring System")

# ---------------- SESSION STATE ----------------
if "user_id" not in st.session_state:
    st.session_state.user_id = None

if "coins" not in st.session_state:
    st.session_state.coins = 0.0

if "model" not in st.session_state:
    st.session_state.model = SolarAnomalyModel()

if "data_buffer" not in st.session_state:
    st.session_state.data_buffer = []

if "ser" not in st.session_state:
    st.session_state.ser = None

if "running" not in st.session_state:
    st.session_state.running = False

if "inject" not in st.session_state:
    st.session_state.inject = False


# ---------------- USER REGISTRATION ----------------
if st.session_state.user_id is None:

    st.subheader("Create User")
    name = st.text_input("Name")
    phone = st.text_input("Phone")

    if st.button("Register"):
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
    user_id, name, phone, coins = user
    st.session_state.coins = coins

    st.success(f"Welcome {name}")
    st.metric("Green Coins", round(st.session_state.coins, 2))

    port = st.text_input("Enter COM Port (e.g., COM7)")

    col1, col2, col3 = st.columns(3)

    # -------- START MONITORING --------
    if col1.button("Start Monitoring"):
        try:
            st.session_state.ser = serial.Serial(port, 115200, timeout=1)
            st.session_state.running = True
            st.success("Serial Connected")
        except Exception as e:
            st.error(f"Unable to open COM port: {e}")

    # -------- STOP MONITORING --------
    if col2.button("Stop Monitoring"):
        if st.session_state.ser:
            st.session_state.ser.close()
        st.session_state.running = False
        st.success("Monitoring Stopped")

    # -------- INJECT ANOMALY --------
    if col3.button("Inject Anomaly"):
        st.session_state.inject = True

    # -------- LIVE MONITORING LOOP --------
    if st.session_state.running and st.session_state.ser:

        try:
            line = st.session_state.ser.readline().decode(errors="ignore").strip()

            if line and "," in line:
                parts = line.split(",")

                if len(parts) == 3:
                    try:
                        voltage = float(parts[0])
                        current = float(parts[1])
                        power = float(parts[2])
                    except:
                        voltage = current = power = 0.0
                else:
                    voltage = current = power = 0.0
            else:
                voltage = current = power = 0.0

            # -------- Inject Fake Grid Data --------
            if st.session_state.inject:
                voltage = 5.0
                current = 50.0
                power = 250.0
                st.session_state.inject = False
                st.warning("⚠ Grid Anomaly Injected")

            # -------- Add To Buffer --------
            st.session_state.data_buffer.append([voltage, current, power])

            # -------- Train Model After 20 Samples --------
            if len(st.session_state.data_buffer) >= 20 and not st.session_state.model.trained:
                st.session_state.model.train(st.session_state.data_buffer)
                st.success("Model trained on solar data")

            # -------- Prediction --------
            if st.session_state.model.trained:
                prediction = st.session_state.model.predict([voltage, current, power])

                if prediction == 1:
                    st.session_state.coins += power * 0.01
                    status = "Normal (Green)"
                else:
                    st.session_state.coins -= 2
                    status = "⚠ Anomaly Detected"

                update_coins(user_id, st.session_state.coins)

                st.metric("Green Coins", round(st.session_state.coins, 2))
                st.write("Status:", status)

            # -------- Show Live Chart --------
            df = pd.DataFrame(
                st.session_state.data_buffer[-50:],
                columns=["Voltage", "Current", "Power"]
            )
            st.line_chart(df)

        except Exception as e:
            st.error(f"Serial error: {e}")

        time.sleep(1)
        st.rerun()
