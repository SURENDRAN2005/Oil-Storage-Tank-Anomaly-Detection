import pandas as pd
import numpy as np
import pickle
import json
from pathlib import Path
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import precision_score, recall_score, f1_score, confusion_matrix
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent))
from config.settings import DATA_DIR, MODELS_DIR, TANKS, CONTAMINATION_RATE

V7_MODELS_DIR = MODELS_DIR / "v7"
V7_MODELS_DIR.mkdir(parents=True, exist_ok=True)

# Selected Physics Features
FEATURES = [
    'level_rate_m_min', 
    'residual_l', 
    'residual_rate', 
    'residual_roll_mean_5m', 
    'residual_roll_std_15m', 
    'cumulative_residual_60m'
]

def split_data(df):
    """Chronological Split: 4 days Train, 1.5 days Val, 1.5 days Test"""
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    t_min = df['timestamp'].min()
    
    train_end = t_min + pd.Timedelta(days=4)
    val_end = train_end + pd.Timedelta(days=1.5)
    
    train_df = df[df['timestamp'] < train_end].copy()
    val_df = df[(df['timestamp'] >= train_end) & (df['timestamp'] < val_end)].copy()
    test_df = df[df['timestamp'] >= val_end].copy()
    
    return train_df, val_df, test_df

def train_and_calibrate():
    print(f"Reading {DATA_DIR / 'features.csv'}...")
    df = pd.read_csv(DATA_DIR / "features.csv")
    
    # Drop rows where rolling windows have NaNs (the first few rows)
    df = df.dropna(subset=FEATURES).copy()
    
    train_df, val_df, test_df = split_data(df)
    
    print(f"Train size: {len(train_df)} | Val size: {len(val_df)} | Test size: {len(test_df)}")
    
    models = {}
    scalers = {}
    thresholds = {}
    
    # PHASE 8: Train models (Tank + State specific)
    for tank_id in TANKS:
        models[tank_id] = {}
        scalers[tank_id] = {}
        thresholds[tank_id] = {}
        
        tank_train = train_df[train_df['tank_id'] == tank_id]
        
        for state in ['RECEIPT', 'DELIVERY', 'IDLE']:
            # We ONLY train on NORMAL data!
            state_train = tank_train[(tank_train['inferred_state'] == state) & (tank_train['event'] == 'normal')]
            
            if len(state_train) < 50:
                print(f"WARNING: Not enough normal training data for {tank_id} in state {state}")
                continue
                
            X_train = state_train[FEATURES].values
            
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            
            iso_forest = IsolationForest(
                n_estimators=100, 
                contamination=CONTAMINATION_RATE, 
                random_state=42
            )
            iso_forest.fit(X_train_scaled)
            
            models[tank_id][state] = iso_forest
            scalers[tank_id][state] = scaler
    
    print("Models trained successfully on NORMAL data.")
    
    # PHASE 9: Threshold Calibration on Validation Set
    print("Calibrating thresholds on Validation set...")
    
    # We will score the validation set to find the optimal threshold for anomaly score
    # Lower score = more anomalous
    val_df['predicted_anomaly'] = 0
    val_df['anomaly_score'] = 1.0 # Default normal
    
    # Score val set
    for tank_id in TANKS:
        for state in ['RECEIPT', 'DELIVERY', 'IDLE']:
            if state not in models[tank_id]: continue
                
            mask = (val_df['tank_id'] == tank_id) & (val_df['inferred_state'] == state)
            if not mask.any(): continue
                
            X_val = val_df.loc[mask, FEATURES].values
            X_val_scaled = scalers[tank_id][state].transform(X_val)
            
            # score_samples returns negative scores (lower is more anomalous)
            scores = models[tank_id][state].score_samples(X_val_scaled)
            val_df.loc[mask, 'anomaly_score'] = scores
            
            # Let's find the 1st percentile of normal validation data to use as threshold
            # to keep false positive rate low.
            mask_normal = mask & (val_df['event'] == 'normal')
            if mask_normal.any():
                normal_scores = val_df.loc[mask_normal, 'anomaly_score']
                # Threshold: Anything lower than this is an anomaly
                thresh = np.percentile(normal_scores, 0.5) # 0.5% False Positive rate target
                thresholds[tank_id][state] = float(thresh)
            else:
                thresholds[tank_id][state] = -0.5 # fallback

    # Apply thresholds to val set to see performance
    for tank_id in TANKS:
        for state in ['RECEIPT', 'DELIVERY', 'IDLE']:
            if state not in thresholds[tank_id]: continue
            thresh = thresholds[tank_id][state]
            
            mask = (val_df['tank_id'] == tank_id) & (val_df['inferred_state'] == state)
            
            # 1 for anomaly, 0 for normal
            is_anomaly = val_df.loc[mask, 'anomaly_score'] < thresh
            val_df.loc[mask, 'predicted_anomaly'] = is_anomaly.astype(int)

    # Evaluate Validation
    y_true_val = (val_df['event'] != 'normal').astype(int)
    y_pred_val = val_df['predicted_anomaly']
    
    precision = precision_score(y_true_val, y_pred_val, zero_division=0)
    recall = recall_score(y_true_val, y_pred_val, zero_division=0)
    f1 = f1_score(y_true_val, y_pred_val, zero_division=0)
    
    print("\n--- VALIDATION PERFORMANCE (Before Rules & Persistence) ---")
    print(f"Precision: {precision:.3f}")
    print(f"Recall:    {recall:.3f}")
    print(f"F1 Score:  {f1:.3f}")
    
    # Save artifacts
    with open(V7_MODELS_DIR / "isolation_forest.pkl", "wb") as f:
        pickle.dump(models, f)
    with open(V7_MODELS_DIR / "scaler.pkl", "wb") as f:
        pickle.dump(scalers, f)
    with open(V7_MODELS_DIR / "features.json", "w") as f:
        json.dump(FEATURES, f)
    with open(V7_MODELS_DIR / "threshold.json", "w") as f:
        json.dump(thresholds, f)
        
    print("\nSaved models, scalers, and thresholds to models/v7/")
    
    # We will test the Final Test Set later when we integrate Rules and Persistence.

if __name__ == "__main__":
    train_and_calibrate()
