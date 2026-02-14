import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta

def generate_synthetic_data(num_samples=1000):
    """
    Generates synthetic energy data for:
    1. Grid Source: 9V Battery + 5V DC Motor (Simulated)
    2. Green Source: 5V Solar Panel + LED Bulb (Simulated)
    """
    
    # Time setup
    start_time = datetime.now()
    timestamps = [start_time + timedelta(seconds=i*5) for i in range(num_samples)] # Every 5 seconds

    data = []

    # --- Grid Source (Battery + Motor) ---
    # Battery voltage drops slightly over time as it discharges
    # Motor current fluctuates based on load/noise
    # 9V battery starts around 9V, drops to maybe 7.5V
    grid_base_voltage = np.linspace(9.2, 7.5, num_samples) 
    
    # Motor current: ~0.2A - 0.5A typically for small DC motors
    grid_base_current = 0.3 # Amps

    # --- Green Source (Solar Panel + LED) ---
    # Solar voltage depends on light intensity. 
    # For a short duration, we can model it as constant or slowly varying if it's day.
    # Let's assume day time for now. 5V panel might output ~5-6V open circuit, ~4.5V under load.
    solar_base_voltage = 4.8 
    
    # LED current: ~20mA (0.02A) is typical for small LEDs, maybe up to 0.1A for high power
    solar_base_current = 0.02 # Amps

    for i in range(num_samples):
        # 1. Grid Reading (Battery + Motor)
        # Add noise
        grid_v = grid_base_voltage[i] + np.random.normal(0, 0.05)
        # Current fluctuates more due to motor brushes/load
        grid_c = grid_base_current + np.random.normal(0, 0.02)
        
        # Anomaly Injection - Grid
        is_grid_anomaly = 0
        if i > 200 and i < 220: # Tampering: Voltage drops to near 0 (disconnected)
            grid_v = np.random.normal(0.5, 0.1)
            grid_c = 0.0
            is_grid_anomaly = 1
        elif i > 600 and i < 610: # Spike: Motor stall current spike
            grid_c = 1.5 + np.random.normal(0, 0.1)
            is_grid_anomaly = 1
        
        # Calculate Power (P = V * I) in milliWatts typically for INA219, but let's stick to Watts for now or mW?
        # INA219 usually gives Bus Voltage (V), Shunt Voltage (mV), Current (mA), Power (mW).
        # Let's output generally in Volts, Amps, Watts.
        
        grid_p = grid_v * grid_c

        # 2. Green Reading (Solar + LED)
        # Solar varies with cloud cover (random drops)
        solar_v = solar_base_voltage + np.random.normal(0, 0.1)
        solar_c = solar_base_current + np.random.normal(0, 0.005)
        
        # Anomaly Injection - Solar
        is_solar_anomaly = 0
        if i > 400 and i < 430: # Cloud/Shading (Natural, effectively) or Tampering (Covering panel)
            solar_v = 1.5 + np.random.normal(0, 0.2) # Voltage drops significantly
            solar_c = 0.005 # Current drops
            # We might consider this an "anomaly" if the user wants to detect panel efficiency drops or tampering
            is_solar_anomaly = 1 
        elif i == 800: # Single point spike (Measurement error)
            solar_v = 12.0 
            is_solar_anomaly = 1

        solar_p = solar_v * solar_c

        data.append({
            "timestamp": timestamps[i],
            "grid_voltage": max(0, grid_v),
            "grid_current": max(0, grid_c),
            "grid_power": max(0, grid_p),
            "grid_label": is_grid_anomaly, # 0 = Normal, 1 = Anomaly
            "solar_voltage": max(0, solar_v),
            "solar_current": max(0, solar_c),
            "solar_power": max(0, solar_p),
            "solar_label": is_solar_anomaly
        })

    df = pd.DataFrame(data)
    
    # Save to CSV
    output_file = "energy_data.csv"
    df.to_csv(output_file, index=False)
    print(f"Generated {num_samples} samples. Saved to {output_file}")
    return df

if __name__ == "__main__":
    generate_synthetic_data()
