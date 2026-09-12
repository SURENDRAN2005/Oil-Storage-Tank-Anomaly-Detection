import numpy as np
import pandas as pd
from pathlib import Path
import random

import sys
sys.path.append(str(Path(__file__).resolve().parent.parent))
from config.settings import TANKS, TANK_CAPACITIES_L, TANK_AREA_M2, BETA_CRUDE_OIL, DATA_DIR

SEED = 20260901
# We want 7 days of 30-second data
# 1 minute = 2 rows -> 1 hour = 120 rows -> 1 day = 2880 rows -> 7 days = 20160 rows
ROWS_PER_TANK = 20160
OUTPUT_PATH = DATA_DIR / "synthetic_raw.csv"

rng = np.random.default_rng(SEED)

def get_tank_config(tank_id):
    # Extract tank index (e.g. T-101 -> 1)
    tank_idx = int(tank_id.split("-")[1]) - 100
    return {
        "tank_id": tank_id,
        "capacity_l": TANK_CAPACITIES_L[tank_id],
        "initial_fill_pct": 0.45 + rng.uniform(-0.1, 0.1),
        "tank_area_m2": TANK_AREA_M2[tank_id],
        "base_inflow": 130 + tank_idx * 8, # liters per minute
        "base_outflow": 105 + tank_idx * 7,
        "level_noise": 5.0, # liters
        "flow_noise": 0.5, # liters/min
    }

def generate_regimes(n_rows):
    """Generate state machine for tank operations (receipt, delivery, idle)"""
    states = []
    current_state = "idle"
    counter = 0
    
    for _ in range(n_rows):
        if counter <= 0:
            rand = rng.random()
            if current_state == "idle":
                if rand < 0.3:
                    current_state = "receipt"
                    counter = int(rng.uniform(120, 360)) # 1 to 3 hours (120 to 360 intervals of 30s)
                elif rand < 0.6:
                    current_state = "delivery"
                    counter = int(rng.uniform(120, 360))
                else:
                    current_state = "idle"
                    counter = int(rng.uniform(240, 800))
            else:
                current_state = "idle"
                counter = int(rng.uniform(240, 1200))
                
        states.append(current_state)
        counter -= 1
        
    return np.array(states)

def generate_anomalies(n_rows, states):
    """Generate anomaly labels that don't overlap and persist"""
    events = np.array(["normal"] * n_rows, dtype=object)
    
    possible_anomalies = [
        "slow_leak", "theft", "water_ingress", 
        "level_sensor_fault", "flow_meter_fault"
    ]
    
    num_anomalies_to_inject = 6
    interval = n_rows // (num_anomalies_to_inject + 1)
    
    for i in range(num_anomalies_to_inject):
        anomaly = rng.choice(possible_anomalies)
        start_idx = (i + 1) * interval + int(rng.uniform(-400, 400))
        duration = int(rng.uniform(60, 180)) # 30 to 90 minutes
        
        if anomaly in ["theft", "slow_leak"]:
            # Prefer IDLE for theft
            while start_idx < n_rows and states[start_idx] != "idle":
                start_idx += 1
                
        events[start_idx:min(start_idx+duration, n_rows)] = anomaly
        
    return events

def generate_data():
    all_tanks_data = []
    print(f"Generating V7 Dataset for {len(TANKS)} tanks (30-second intervals)...")
    
    for tank_id in TANKS:
        config = get_tank_config(tank_id)
        print(f"Processing {tank_id}...")
        
        timestamps = pd.date_range("2026-09-01 00:00:00", periods=ROWS_PER_TANK, freq="30s")
        hour = timestamps.hour.to_numpy() + timestamps.minute.to_numpy() / 60.0
        
        # Temperature with diurnal cycle
        temp_c = 25.0 + 10.0 * np.sin(2 * np.pi * (hour - 6) / 24) + rng.normal(0, 0.5, ROWS_PER_TANK)
        
        states = generate_regimes(ROWS_PER_TANK)
        events = generate_anomalies(ROWS_PER_TANK, states)
        
        true_oil_volume_l = np.zeros(ROWS_PER_TANK)
        true_water_volume_l = np.zeros(ROWS_PER_TANK)
        
        true_oil_volume_l[0] = config["capacity_l"] * config["initial_fill_pct"]
        true_water_volume_l[0] = config["capacity_l"] * 0.02 # 2% water bottom
        
        metered_inflow = np.zeros(ROWS_PER_TANK)
        metered_outflow = np.zeros(ROWS_PER_TANK)
        valve_closed = np.ones(ROWS_PER_TANK, dtype=bool)
        
        # 30-sec intervals -> rate per interval is half the per-minute rate
        interval_factor = 0.5 
        
        for t in range(1, ROWS_PER_TANK):
            state = states[t]
            event = events[t]
            
            true_inflow_min = 0.0
            true_outflow_min = 0.0
            valve = True
            
            if state == "receipt":
                true_inflow_min = config["base_inflow"] + rng.normal(0, config["flow_noise"])
            elif state == "delivery":
                true_outflow_min = config["base_outflow"] + rng.normal(0, config["flow_noise"])
                valve = False
                
            leak_min = 0.0
            theft_min = 0.0
            water_rate_min = 0.0
            
            if event == "slow_leak":
                leak_min = 2.5 
            elif event == "theft":
                theft_min = 50.0 
            elif event == "water_ingress":
                water_rate_min = 1.5 
                
            true_oil_volume_l[t] = true_oil_volume_l[t-1] + (true_inflow_min - true_outflow_min - leak_min - theft_min) * interval_factor
            true_water_volume_l[t] = true_water_volume_l[t-1] + (water_rate_min * interval_factor)
            
            m_inflow = true_inflow_min + rng.normal(0, config["flow_noise"]) if true_inflow_min > 0 else 0.0
            m_outflow = true_outflow_min + rng.normal(0, config["flow_noise"]) if true_outflow_min > 0 else 0.0
            
            if event == "flow_meter_fault":
                if state == "receipt": m_inflow *= 0.8
                elif state == "delivery": m_outflow *= 0.8
                    
            metered_inflow[t] = max(0, m_inflow)
            metered_outflow[t] = max(0, m_outflow)
            valve_closed[t] = valve

        # Apply thermal physics to get raw measurements
        vcf_inverse = 1.0 + BETA_CRUDE_OIL * (temp_c - 15.0)
        raw_oil_volume_l = true_oil_volume_l * vcf_inverse
        total_raw_volume_l = raw_oil_volume_l + true_water_volume_l
        
        measured_total_volume_l = total_raw_volume_l + rng.normal(0, config["level_noise"], ROWS_PER_TANK)
        
        fault_mask = (events == "level_sensor_fault")
        if fault_mask.any():
            from itertools import groupby
            groups = []
            for k, g in groupby(enumerate(fault_mask), lambda x: x[1]):
                if k: groups.append(list(map(lambda x: x[0], g)))
            
            for g in groups:
                stuck_val = measured_total_volume_l[g[0] - 1] if g[0] > 0 else measured_total_volume_l[0]
                measured_total_volume_l[g] = stuck_val + rng.normal(0, 0.1, len(g))
                
        level_m = measured_total_volume_l / (config["tank_area_m2"] * 1000)
        water_interface_m = true_water_volume_l / (config["tank_area_m2"] * 1000)
        
        # To make it raw data, we ONLY output what a sensor would output.
        # Feature engineering will happen later in the pipeline.
        df = pd.DataFrame({
            "tank_id": tank_id,
            "timestamp": timestamps,
            "level_m": level_m,
            "temperature_c": temp_c,
            "water_interface_m": water_interface_m,
            "inflow_l_min": metered_inflow,
            "outflow_l_min": metered_outflow,
            "net_metered_flow_l_min": metered_inflow - metered_outflow,
            "pressure_bar": 1.0 + level_m * 0.098 + rng.normal(0, 0.01, ROWS_PER_TANK),
            "valve_position": ["closed" if v else "open" for v in valve_closed],
            "operating_state": states, # Include this for evaluation, though real API might need to infer it
            "event": events # ground truth
        })
        
        # Inject some missing values / invalid readings for validation phase to catch
        # Random missing levels
        if rng.random() > 0.5:
            idx_missing = rng.choice(ROWS_PER_TANK, size=10, replace=False)
            df.loc[idx_missing, "level_m"] = np.nan
            
        # Spikes
        if rng.random() > 0.5:
            idx_spike = rng.choice(ROWS_PER_TANK, size=2, replace=False)
            df.loc[idx_spike, "level_m"] += 5.0
            
        all_tanks_data.append(df)

    final_df = pd.concat(all_tanks_data, ignore_index=True)
    final_df.to_csv(OUTPUT_PATH, index=False)
    print(f"Generated successfully: {OUTPUT_PATH}")

if __name__ == "__main__":
    generate_data()
