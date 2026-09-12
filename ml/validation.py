import pandas as pd
import numpy as np
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent))
from config.settings import DATA_DIR, TANKS

def validate_data(input_csv: Path, output_csv: Path):
    print(f"Validating dataset: {input_csv}")
    df = pd.read_csv(input_csv)
    
    # Initialize quality status
    df['data_quality'] = 'VALID'
    
    # 1. Missing values
    missing_level = df['level_m'].isna()
    df.loc[missing_level, 'data_quality'] = 'INVALID'
    
    # 2. Invalid ranges (loss-of-echo or impossible values)
    # E.g. level < 0 or level > 25 meters (assuming 25m max for T-110)
    out_of_bounds = (df['level_m'] < 0) | (df['level_m'] > 30)
    df.loc[out_of_bounds, 'data_quality'] = 'INVALID'
    
    # 3. Tank ID validity
    invalid_tanks = ~df['tank_id'].isin(TANKS)
    df.loc[invalid_tanks, 'data_quality'] = 'INVALID'
    
    # Process per tank to check timestamps and spikes
    validated_dfs = []
    
    for tank_id, tank_df in df.groupby('tank_id'):
        tank_df = tank_df.copy()
        
        # 4. Timestamp ordering
        tank_df['timestamp'] = pd.to_datetime(tank_df['timestamp'])
        tank_df = tank_df.sort_values('timestamp')
        
        # 5. Duplicate timestamps
        duplicates = tank_df['timestamp'].duplicated(keep=False)
        tank_df.loc[duplicates, 'data_quality'] = 'INVALID'
        
        # 6. Spikes (abnormal rate of change in one interval > 1.0 meters)
        level_diff = tank_df['level_m'].diff().abs()
        spikes = level_diff > 1.0
        tank_df.loc[spikes, 'data_quality'] = 'WARNING'
        
        # 7. Stuck readings (sensor fault checking on raw level)
        # We will let the rule engine handle "stuck for too long" anomalies, 
        # but if it's perfectly flat for an extremely long time (e.g. 100 intervals) with flow, it's a WARNING.
        # This is a bit complex for simple validation, so we just stick to spikes/bounds for data quality.
        
        validated_dfs.append(tank_df)
        
    final_df = pd.concat(validated_dfs, ignore_index=True)
    
    # Interpolate missing values only for VALID or WARNING records so feature engineering doesn't crash
    # But leave INVALID as invalid. Actually, the instruction says "Flag bad records instead of silently deleting".
    # We will forward fill small gaps so the pipeline can continue if it's just a WARNING or missing.
    final_df['level_m'] = final_df.groupby('tank_id')['level_m'].transform(lambda x: x.interpolate(method='linear', limit=3))
    
    final_df.to_csv(output_csv, index=False)
    
    counts = final_df['data_quality'].value_counts()
    print("\nValidation Summary:")
    print(counts.to_string())
    print(f"\nValidated dataset saved to: {output_csv}")

if __name__ == "__main__":
    input_file = DATA_DIR / "synthetic_raw.csv"
    output_file = DATA_DIR / "synthetic_validated.csv"
    validate_data(input_file, output_file)
