import joblib
import pandas as pd
import numpy as np
import time
import random

def simulate_live_detection():
    # 1. Load the trained model
    try:
        model = joblib.load('isolation_forest_model.pkl')
        print("Model loaded successfully.")
    except FileNotFoundError:
        print("Error: Model not found. Please run anomaly_detection.py first.")
        return

    # scaler was used in training, strictly speaking we should load the fitted scaler too.
    # For this demo, we'll re-fit a scaler on a small buffer or just use raw data if the model was robust enough
    # BUT, Isolation Forest works on feature distributions. 
    # In `anomaly_detection.py`, we did: scaler = StandardScaler(); X_scaled = scaler.fit_transform(X)
    # So we MUST use the same scaler.
    # Let's assume for this simple demo we "cheat" and re-fit a scaler on a dummy historical set 
    # OR better, let's update anomaly_detection.py to save the scaler too.
    # CHECK: Did I save the scaler? No. 
    # FIX: I will just use the same distribution parameters to manually scale for this demo 
    # or just run a quick "training" on dummy data to get a scaler. 
    # TO KEEP IT SIMPLE and ROBUST: I will just load the original data to fit the scaler again.
    
    print("Preparing scaler...")
    original_df = pd.read_csv("energy_data.csv")
    features = ['grid_voltage', 'grid_current', 'grid_power', 'solar_voltage', 'solar_current', 'solar_power']
    from sklearn.preprocessing import StandardScaler
    scaler = StandardScaler()
    scaler.fit(original_df[features])

    print("\n--- Starting Live Simulation (Press Ctrl+C to stop) ---")
    print("Generating new data points every 1 second...")

    
    # Mock Blockchain Connection
    print("Connecting to Blockchain (Simulated)...")
    # In reality: web3 = Web3(Web3.HTTPProvider('http://127.0.0.1:8545'))
    
    try:
        while True:
            # 1. Generate a single data point (Simulating ESP32 reading)
            
            # Default Normal
            grid_v = 9.0 + np.random.normal(0, 0.05)
            grid_c = 0.3 + np.random.normal(0, 0.02)
            solar_v = 4.8 + np.random.normal(0, 0.1)
            solar_c = 0.02 + np.random.normal(0, 0.005)
            
            # Randomly inject anomaly (10% chance)
            is_anomaly = False
            if random.random() < 0.1:
                is_anomaly = True
                type_a = random.choice(['TAMPER_GRID', 'SPIKE_SOLAR', 'SHADING'])
                if type_a == 'TAMPER_GRID':
                    grid_v = 0.5 # Disconnected/Tampered
                    grid_c = 0.0
                elif type_a == 'SPIKE_SOLAR':
                    solar_v = 12.0 # Voltage spike
                elif type_a == 'SHADING':
                    solar_v = 1.5
                    solar_c = 0.005

            grid_p = grid_v * grid_c
            solar_p = solar_v * solar_c

            # 2. Create DataFrame for prediction
            new_data = pd.DataFrame([{
                'grid_voltage': grid_v, 
                'grid_current': grid_c, 
                'grid_power': grid_p, 
                'solar_voltage': solar_v, 
                'solar_current': solar_c, 
                'solar_power': solar_p
            }])

            # 3. Scale
            X_new = scaler.transform(new_data)

            # 4. Predict
            prediction = model.predict(X_new)[0] # -1 is anomaly, 1 is normal
            
            # 5. Output
            timestamp = pd.Timestamp.now().strftime('%H:%M:%S')
            
            if prediction == -1:
                print(f"[{timestamp}] ⚠️ ALERT! ANOMALY DETECTED!")
                print(f"    Readings: Grid V={grid_v:.2f} I={grid_c:.2f} | Solar V={solar_v:.2f} I={solar_c:.2f}")
                if is_anomaly:
                    print(f"    (Mock: Blocked from Blockchain)")
            else:
                print(f"[{timestamp}] ✅ Data Authentic.")
                log_to_blockchain({
                    'timestamp': timestamp,
                    'grid_power': grid_p,
                    'solar_power': solar_p
                })

            time.sleep(1)

    except KeyboardInterrupt:
        print("\nSimulation stopped.")

def log_to_blockchain(data):
    """
    Simulates sending data to a smart contract on Hardhat.
    In a real app, you would use 'web3.py' here.
    """
    # Example code for real implementation:
    # tx_hash = contract.functions.logEnergyReading(
    #     int(data['grid_power'] * 1000), 
    #     int(data['solar_power'] * 1000)
    # ).transact({'from': account})
    # receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
    
    print(f"    -> Sent to Smart Contract. Grid: {data['grid_power']:.2f}W, Solar: {data['solar_power']:.2f}W")

if __name__ == "__main__":
    simulate_live_detection()
