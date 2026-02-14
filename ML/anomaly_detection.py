import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, confusion_matrix
import matplotlib.pyplot as plt

def train_anomaly_detection_model(input_file="energy_data.csv"):
    # 1. Load Data
    try:
        df = pd.read_csv(input_file)
    except FileNotFoundError:
        print(f"Error: {input_file} not found. Please run generate_data.py first.")
        return

    print("Data loaded successfully.")
    
    # 2. Features for training
    # We will train two separate models or one combined model? 
    # Let's train one model on the voltage, current, and power of both sources.
    # In a real scenario, you might want separate models per source.
    features = ['grid_voltage', 'grid_current', 'grid_power', 'solar_voltage', 'solar_current', 'solar_power']
    
    X = df[features]
    
    # 3. Preprocessing
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # 4. Train Isolation Forest
    # contamination: Expected proportion of outliers in the data set. 
    # We injected some, let's estimate or set it small.
    # In generate_data.py: 
    # Grid: 200-220 (20 pts), 600-610 (10 pts) -> 30 pts
    # Solar: 400-430 (30 pts), 800 (1 pt) -> 31 pts
    # Total ~60 anomalies out of 1000 => 0.06
    model = IsolationForest(contamination=0.06, random_state=42)
    model.fit(X_scaled)
    
    # 5. Predict
    # Isolation Forest returns -1 for outliers and 1 for inliers.
    predictions = model.predict(X_scaled)
    
    # Add predictions to dataframe
    df['anomaly_pred'] = predictions
    # Map -1 to 1 (anomaly) and 1 to 0 (normal) to match our label format
    df['is_anomaly_detected'] = df['anomaly_pred'].apply(lambda x: 1 if x == -1 else 0)
    
    # Create a true label column for validation (generated labels were separate)
    df['true_label'] = df.apply(lambda row: 1 if (row['grid_label'] == 1 or row['solar_label'] == 1) else 0, axis=1)
    
    # 6. Evaluation
    print("\n--- Model Evaluation ---")
    print(confusion_matrix(df['true_label'], df['is_anomaly_detected']))
    print(classification_report(df['true_label'], df['is_anomaly_detected'], target_names=['Normal', 'Anomaly']))
    
    # Save results
    result_file = "anomaly_results.csv"
    df.to_csv(result_file, index=False)
    print(f"\nResults saved to {result_file}")

    # Save the model
    import joblib
    joblib.dump(model, 'isolation_forest_model.pkl')
    print("Model saved to isolation_forest_model.pkl")
    # plt.figure(figsize=(10,6))
    # plt.plot(df['grid_voltage'], label='Grid Voltage')
    # plt.scatter(df[df['is_anomaly_detected']==1].index, df[df['is_anomaly_detected']==1]['grid_voltage'], color='red', label='Anomaly')
    # plt.legend()
    # plt.savefig('anomaly_plot.png')

if __name__ == "__main__":
    train_anomaly_detection_model()
