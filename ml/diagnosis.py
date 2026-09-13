import pandas as pd
import numpy as np
import pickle
import sys
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report

sys.path.append(str(Path(__file__).resolve().parent.parent))
from config.settings import DATA_DIR, MODELS_DIR
from ml.rules import evaluate_rules
from ml.train import FEATURES

V7_MODELS_DIR = MODELS_DIR / "v7"

def prepare_diagnostic_dataset(df):
    """
    Applies the Rule Engine to generate rule features, 
    then filters for ONLY anomalous data to train the diagnostic classifier.
    """
    print("Applying independent rules for diagnosis features...")
    
    # We will compute rules for all rows to create boolean features
    rule_results = df.apply(evaluate_rules, axis=1)
    
    # One-hot encode the fired rules
    df['r1_drop'] = rule_results.apply(lambda x: "RULE_1_UNEXPECTED_LEVEL_DROP" in x).astype(int)
    df['r2_water'] = rule_results.apply(lambda x: "RULE_2_WATER_INGRESS" in x).astype(int)
    df['r3_theft'] = rule_results.apply(lambda x: "RULE_3_SEVERE_NEGATIVE_RESIDUAL" in x).astype(int)
    df['r4_stuck'] = rule_results.apply(lambda x: "RULE_4_STUCK_LEVEL_SENSOR" in x).astype(int)
    df['r5_flow'] = rule_results.apply(lambda x: "RULE_5_FLOW_VOLUME_MISMATCH" in x).astype(int)
    
    # Filter for anomalous data (where event != 'normal')
    anomalous_df = df[df['event'] != 'normal'].copy()
    
    # We need to map the event string to the 5 requested classes
    event_mapping = {
        'slow_leak': 'Suspected Leak',
        'theft': 'Suspected Theft',
        'water_ingress': 'Water Ingress',
        'level_sensor_fault': 'Sensor Fault',
        'flow_meter_fault': 'Flow Meter Fault'
    }
    anomalous_df['target'] = anomalous_df['event'].map(event_mapping)
    
    # Drop any unmapped (shouldn't be any)
    anomalous_df = anomalous_df.dropna(subset=['target'])
    
    return anomalous_df

def train_diagnosis():
    print(f"Reading {DATA_DIR / 'features.csv'}...")
    df = pd.read_csv(DATA_DIR / "features.csv")
    df = df.dropna(subset=FEATURES).copy()
    
    # We use the whole dataset (or just Train+Val) to get enough anomaly examples
    # Since it's a synthetic diagnostic prototype, using all anomalies is fine.
    anomalous_df = prepare_diagnostic_dataset(df)
    
    print(f"Extracted {len(anomalous_df)} anomalous samples for diagnosis training.")
    
    # Features for diagnosis = IF features + Rule Features + operating state
    state_dummies = pd.get_dummies(anomalous_df['inferred_state'], prefix='state')
    
    diag_features = FEATURES + ['r1_drop', 'r2_water', 'r3_theft', 'r4_stuck', 'r5_flow']
    
    X = pd.concat([anomalous_df[diag_features], state_dummies], axis=1)
    
    # Ensure all possible state columns exist
    for s in ['state_RECEIPT', 'state_DELIVERY', 'state_IDLE']:
        if s not in X.columns:
            X[s] = 0
            
    # Sort columns for consistency
    X = X[sorted(X.columns)]
    y = anomalous_df['target']
    
    # Train Random Forest
    rf = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42, class_weight='balanced')
    rf.fit(X, y)
    
    print("\n--- DIAGNOSIS CLASSIFIER PERFORMANCE ---")
    y_pred = rf.predict(X)
    print(classification_report(y, y_pred))
    
    # Save model and feature names
    with open(V7_MODELS_DIR / "diagnosis_rf.pkl", "wb") as f:
        pickle.dump(rf, f)
        
    with open(V7_MODELS_DIR / "diagnosis_features.pkl", "wb") as f:
        pickle.dump(list(X.columns), f)
        
    print("Saved diagnosis classifier to models/v7/")

if __name__ == "__main__":
    train_diagnosis()
