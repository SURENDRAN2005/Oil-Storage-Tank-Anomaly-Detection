import pandas as pd
import numpy as np
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent))
from config.settings import DATA_DIR, TANKS, TANK_AREA_M2, BETA_CRUDE_OIL

def apply_thermal_correction_and_residual(df):
    """PHASE 4 & 5: Thermal correction and material-balance residual"""
    
    # Pre-allocate new columns
    df['thermally_corrected_volume_l'] = 0.0
    df['delta_corrected_volume_l'] = 0.0
    df['residual_l'] = 0.0
    
    for tank_id in TANKS:
        mask = df['tank_id'] == tank_id
        if not mask.any():
            continue
            
        tank_data = df.loc[mask].copy()
        
        # 1. Total raw measured volume
        area_m2 = TANK_AREA_M2[tank_id]
        total_vol_l = tank_data['level_m'] * area_m2 * 1000
        water_vol_l = tank_data['water_interface_m'] * area_m2 * 1000
        oil_vol_l = total_vol_l - water_vol_l
        
        # 2. Thermal correction (VCF)
        # Assuming Base Temp = 15 C
        vcf = 1.0 / (1.0 + BETA_CRUDE_OIL * (tank_data['temperature_c'] - 15.0))
        corrected_oil_vol_l = oil_vol_l * vcf
        
        # 3. Volume Change
        delta_vol = corrected_oil_vol_l.diff().fillna(0)
        
        # 4. Residual
        # Net metered flow = inflow - outflow
        # For 30s intervals, rates in L/min must be divided by 2 to get Volume per interval
        interval_factor = 0.5 
        net_flow = (tank_data['inflow_l_min'] - tank_data['outflow_l_min']) * interval_factor
        
        residual = delta_vol - net_flow
        
        df.loc[mask, 'thermally_corrected_volume_l'] = corrected_oil_vol_l
        df.loc[mask, 'delta_corrected_volume_l'] = delta_vol
        df.loc[mask, 'residual_l'] = residual
        
    return df

def infer_operating_state(df):
    """PHASE 6: Infer operating state from flow & valves"""
    # Assuming standard thresholds: if net flow is positive by significant margin -> RECEIPT
    # If net flow is negative -> DELIVERY
    # Else IDLE
    
    # We use L/min flows for this inference
    net_flow = df['inflow_l_min'] - df['outflow_l_min']
    
    # Create the state column if it doesn't exist (it exists in our synthetic as ground truth, 
    # but we will compute the "inferred" one just to be strictly correct with the pipeline)
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
    
    # Sort just in case
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values(by=['tank_id', 'timestamp']).reset_index(drop=True)
    
    # Only process VALID and WARNING records
    # If a record is INVALID, we might forward fill or drop it depending on strategy.
    # For now, we compute features on everything, but we will exclude INVALID during training.
    
    print("Applying Phase 4 & 5 (Thermal Correction & Residual)...")
    df = apply_thermal_correction_and_residual(df)
    
    print("Applying Phase 6 (State Detection)...")
    df = infer_operating_state(df)
    
    print("Applying Phase 7 (Feature Engineering)...")
    
    # Group by tank to compute rolling features
    engineered_dfs = []
    
    for tank_id, group in df.groupby('tank_id'):
        group = group.copy()
        
        # We need rolling windows. For 30s intervals:
        # 5 min = 10 intervals
        # 15 min = 30 intervals
        # 60 min = 120 intervals
        
        # Temporal behavior of residual
        group['residual_rate'] = group['residual_l'].diff().fillna(0)
        group['residual_roll_mean_5m'] = group['residual_l'].rolling(10, min_periods=1).mean()
        group['residual_roll_std_15m'] = group['residual_l'].rolling(30, min_periods=1).std().fillna(0)
        group['cumulative_residual_60m'] = group['residual_l'].rolling(120, min_periods=1).sum()
        
        # Dynamics
        group['level_rate_m_min'] = group['level_m'].diff().fillna(0) * 2 # Convert /interval to /min
        group['water_rate_m_min'] = group['water_interface_m'].diff().fillna(0) * 2
        
        # Tank Normalization (Residual divided by tank capacity to scale it)
        capacity = TANK_AREA_M2[tank_id] * 20000 # Rough capacity estimate just for feature scaling
        group['normalized_residual'] = group['residual_l'] / capacity
        
        engineered_dfs.append(group)
        
    final_df = pd.concat(engineered_dfs, ignore_index=True)
    final_df.to_csv(output_csv, index=False)
    print(f"Features saved to {output_csv}")

if __name__ == "__main__":
    input_file = DATA_DIR / "synthetic_validated.csv"
    output_file = DATA_DIR / "features.csv"
    engineer_features(input_file, output_file)
