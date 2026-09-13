import pandas as pd
import numpy as np
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent))
from config.settings import DATA_DIR, TANKS

def check_sensor_health(tank_df):
    """
    Formal Sensor Health Engine
    Evaluates each sensor individually for BAD/SUSPECT/GOOD quality.
    """
    tank_df = tank_df.copy()
    
    tank_df['level_sensor_quality'] = 'GOOD'
    tank_df['flow_sensor_quality'] = 'GOOD'
    tank_df['temp_sensor_quality'] = 'GOOD'
    tank_df['pressure_sensor_quality'] = 'GOOD'
    
    # 1. Level Sensor Health
    missing_level = tank_df['level_m'].isna()
    out_of_bounds_level = (tank_df['level_m'] < 0) | (tank_df['level_m'] > 30)
    spikes_level = tank_df['level_m'].diff().abs() > 1.0
    
    # Check for stuck values (std == 0 over a 15-min rolling window, while flow is non-zero)
    roll_std_level = tank_df['level_m'].rolling(30, min_periods=30).std()
    flow_activity = tank_df['net_metered_flow_l_min'].abs() > 10.0
    stuck_level = (roll_std_level < 1e-4) & flow_activity
    
    tank_df.loc[missing_level | out_of_bounds_level, 'level_sensor_quality'] = 'BAD'
    tank_df.loc[spikes_level | stuck_level, 'level_sensor_quality'] = 'SUSPECT'
    
    # 2. Flow Meter Health
    impossible_flow = (tank_df['inflow_l_min'] > 1000) | (tank_df['outflow_l_min'] > 1000)
    flow_stuck_zero = (tank_df['valve_position'] == 'open') & (tank_df['outflow_l_min'] == 0) & (tank_df['inflow_l_min'] == 0)
    missing_flow = tank_df['inflow_l_min'].isna() | tank_df['outflow_l_min'].isna()
    
    tank_df.loc[missing_flow | impossible_flow, 'flow_sensor_quality'] = 'BAD'
    tank_df.loc[flow_stuck_zero, 'flow_sensor_quality'] = 'SUSPECT'
    
    # 3. Temperature Sensor Health
    missing_temp = tank_df['temperature_c'].isna()
    impossible_temp = (tank_df['temperature_c'] < -50) | (tank_df['temperature_c'] > 150)
    spike_temp = tank_df['temperature_c'].diff().abs() > 5.0
    
    tank_df.loc[missing_temp | impossible_temp, 'temp_sensor_quality'] = 'BAD'
    tank_df.loc[spike_temp, 'temp_sensor_quality'] = 'SUSPECT'
    
    # 4. Overall Sensor Quality
    def aggregate_quality(row):
        qualities = [row['level_sensor_quality'], row['flow_sensor_quality'], row['temp_sensor_quality']]
        if 'BAD' in qualities: return 'BAD'
        if 'SUSPECT' in qualities: return 'SUSPECT'
        return 'GOOD'
        
    tank_df['sensor_quality'] = tank_df.apply(aggregate_quality, axis=1)
    
    return tank_df

def validate_data(input_csv: Path, output_csv: Path):
    print(f"Validating dataset & Running Sensor Health Engine: {input_csv}")
    df = pd.read_csv(input_csv)
    
    invalid_tanks = ~df['tank_id'].isin(TANKS)
    if invalid_tanks.any():
        print(f"Dropping {invalid_tanks.sum()} records for unknown tanks.")
        df = df[~invalid_tanks]
        
    validated_dfs = []
    
    for tank_id, tank_df in df.groupby('tank_id'):
        tank_df['timestamp'] = pd.to_datetime(tank_df['timestamp'])
        tank_df = tank_df.sort_values('timestamp').reset_index(drop=True)
        
        # Sensor Health Engine
        tank_df = check_sensor_health(tank_df)
        
        # Interpolate missing values so pipeline can continue
        tank_df['level_m'] = tank_df['level_m'].interpolate(method='linear', limit=3)
        tank_df['temperature_c'] = tank_df['temperature_c'].interpolate(method='linear', limit=3)
        tank_df['inflow_l_min'] = tank_df['inflow_l_min'].fillna(0)
        tank_df['outflow_l_min'] = tank_df['outflow_l_min'].fillna(0)
        
        validated_dfs.append(tank_df)
        
    final_df = pd.concat(validated_dfs, ignore_index=True)
    final_df.to_csv(output_csv, index=False)
    
    print("\nSensor Quality Summary:")
    print(final_df['sensor_quality'].value_counts().to_string())
    print(f"\nValidated dataset saved to: {output_csv}")

if __name__ == "__main__":
    input_file = DATA_DIR / "synthetic_raw.csv"
    output_file = DATA_DIR / "synthetic_validated.csv"
    validate_data(input_file, output_file)
