import pandas as pd
import numpy as np
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent))
from config.settings import DATA_DIR, TANKS, TANK_AREA_M2, BETA_CRUDE_OIL

def apply_thermal_correction_and_residual(df):
    """PHASE 4 & 5: Thermal correction and material-balance residual"""
    
    df['thermally_corrected_volume_l'] = 0.0
    df['delta_corrected_volume_l'] = 0.0
    df['residual_l'] = 0.0
    
    for tank_id in TANKS:
        mask = df['tank_id'] == tank_id
        if not mask.any():
            continue
            
        tank_data = df.loc[mask].copy()
        
        area_m2 = TANK_AREA_M2[tank_id]
        total_vol_l = tank_data['level_m'] * area_m2 * 1000
        water_vol_l = tank_data['water_interface_m'] * area_m2 * 1000
        oil_vol_l = total_vol_l - water_vol_l
        
        vcf = 1.0 / (1.0 + BETA_CRUDE_OIL * (tank_data['temperature_c'] - 15.0))
        corrected_oil_vol_l = oil_vol_l * vcf
        
        delta_vol = corrected_oil_vol_l.diff().fillna(0)
        
        interval_factor = 0.5 
        net_flow = (tank_data['inflow_l_min'] - tank_data['outflow_l_min']) * interval_factor
        
        residual = delta_vol - net_flow
        
        df.loc[mask, 'thermally_corrected_volume_l'] = corrected_oil_vol_l
        df.loc[mask, 'delta_corrected_volume_l'] = delta_vol
        df.loc[mask, 'residual_l'] = residual
        
    return df

def infer_operating_state(df):
    """PHASE 6: Infer operating state from flow & valves"""
    net_flow = df['inflow_l_min'] - df['outflow_l_min']
    
    conditions = [
        (net_flow > 5),
        (net_flow < -5)
    ]
    choices = ['RECEIPT', 'DELIVERY']
    df['inferred_state'] = np.select(conditions, choices, default='IDLE')
    
    return df

def engineer_features(input_csv: Path, output_csv: Path):
    """PHASE 7: Engineering rolling windows and physics features"""
    print(f"Reading {input_csv}...")
    df = pd.read_csv(input_csv)
    
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values(by=['tank_id', 'timestamp']).reset_index(drop=True)
    
    print("Applying Phase 4 & 5 (Thermal Correction & Residual)...")
    df = apply_thermal_correction_and_residual(df)
    
    print("Applying Phase 6 (State Detection)...")
    df = infer_operating_state(df)
    
    print("Applying Phase 7 (Feature Engineering)...")
    
    engineered_dfs = []
    
    for tank_id, group in df.groupby('tank_id'):
        group = group.copy()
        
        # 1 interval = 30 seconds -> 0.5 min
        dt = 0.5
        
        # Means
        group['residual_mean_5'] = group['residual_l'].rolling(5, min_periods=1).mean()
        group['residual_mean_15'] = group['residual_l'].rolling(15, min_periods=1).mean()
        group['residual_mean_30'] = group['residual_l'].rolling(30, min_periods=1).mean()
        
        # Stds
        group['residual_std_15'] = group['residual_l'].rolling(15, min_periods=1).std().fillna(0)
        group['residual_std_30'] = group['residual_l'].rolling(30, min_periods=1).std().fillna(0)
        
        # Slopes: (R_t - R_{t-w}) / (w * dt)
        group['residual_slope_15'] = (group['residual_l'] - group['residual_l'].shift(15).fillna(0)) / (15 * dt)
        group['residual_slope_30'] = (group['residual_l'] - group['residual_l'].shift(30).fillna(0)) / (30 * dt)
        
        # Cumulative Residual (rolling sum over 1 hour = 120 intervals)
        group['cumulative_residual'] = group['residual_l'].rolling(120, min_periods=1).sum()
        
        # Dynamics
        group['level_rate_m_min'] = group['level_m'].diff().fillna(0) * 2 
        group['water_rate_m_min'] = group['water_interface_m'].diff().fillna(0) * 2
        
        capacity = TANK_AREA_M2[tank_id] * 20000 
        group['normalized_residual'] = group['residual_l'] / capacity
        
        engineered_dfs.append(group)
        
    final_df = pd.concat(engineered_dfs, ignore_index=True)
    final_df.to_csv(output_csv, index=False)
    print(f"Features saved to {output_csv}")

if __name__ == "__main__":
    input_file = DATA_DIR / "synthetic_validated.csv"
    output_file = DATA_DIR / "features.csv"
    engineer_features(input_file, output_file)
