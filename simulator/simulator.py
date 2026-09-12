import time
import random
import datetime
import sqlite3
import json
import uuid
import pickle
import numpy as np
import pandas as pd
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent))
from config.settings import TANKS, TANK_CAPACITIES_L, TANK_AREA_M2, BETA_CRUDE_OIL, MODELS_DIR
from backend.database import get_db, init_db
from ml.rules import evaluate_rules, PersistenceEngine

V7_MODELS_DIR = MODELS_DIR / "v7"

class TankSimulator:
    def __init__(self, tank_id):
        self.tank_id = tank_id
        self.capacity = TANK_CAPACITIES_L[tank_id]
        self.area = TANK_AREA_M2[tank_id]
        
        self.level_m = random.uniform(5.0, 15.0)
        self.temperature_c = 20.0
        self.water_interface_m = 0.1
        self.inflow = 0.0
        self.outflow = 0.0
        self.pressure = 1.0
        self.valve_closed = True
        
        self.state = 'IDLE'
        self.history = pd.DataFrame(columns=[
            'level_m', 'water_interface_m', 'residual_l', 'inflow_l_min', 'outflow_l_min'
        ])
        
    def step(self, scenario, is_target):
        # Base behavior
        self.inflow = 0
        self.outflow = 0
        self.valve_closed = True
        
        # State machine
        if random.random() < 0.05: # 5% chance to change state
            self.state = random.choice(['RECEIPT', 'DELIVERY', 'IDLE', 'IDLE'])
            
        if self.state == 'RECEIPT':
            self.inflow = random.uniform(100, 200)
            self.valve_closed = False
        elif self.state == 'DELIVERY':
            self.outflow = random.uniform(100, 200)
            self.valve_closed = False
            
        # Physical changes
        net_flow_interval = (self.inflow - self.outflow) * 0.5 # 30s interval
        
        # Temperature drift (diurnal cycle simplified)
        now = datetime.datetime.utcnow()
        hour = now.hour + now.minute / 60.0
        self.temperature_c = 25.0 + 10.0 * np.sin(2 * np.pi * (hour - 6) / 24) + random.gauss(0, 0.5)
        
        actual_volume_change = net_flow_interval
        
        # Initialize true standard volume if not exists
        if not hasattr(self, 'true_std_oil_vol_l'):
            water_vol = self.water_interface_m * self.area * 1000.0
            obs_oil_vol = (self.level_m * self.area * 1000.0) - water_vol
            vcf = 1.0 / (1.0 + BETA_CRUDE_OIL * (self.temperature_c - 15.0))
            self.true_std_oil_vol_l = obs_oil_vol * vcf
        
        # ANOMALY INJECTION
        if is_target:
            if scenario == 'slow_leak':
                actual_volume_change -= random.uniform(20, 40)
            elif scenario == 'unauthorized_withdrawal':
                actual_volume_change -= random.uniform(200, 300)
                self.valve_closed = True # Rule 1 trigger
            elif scenario == 'water_ingress':
                self.water_interface_m += 0.005
                actual_volume_change += 20
                
        self.true_std_oil_vol_l += actual_volume_change
        
        # Calculate new observed level reflecting thermal expansion
        vcf = 1.0 / (1.0 + BETA_CRUDE_OIL * (self.temperature_c - 15.0))
        obs_oil_vol = self.true_std_oil_vol_l / vcf
        true_water_vol = self.water_interface_m * self.area * 1000.0
        true_total_vol = obs_oil_vol + true_water_vol
        
        # Apply measurement noise (5.0 Liters level noise matching training)
        noisy_volume_l = true_total_vol + random.gauss(0, 5.0)
        
        # Flow meter noise
        measured_inflow = max(0, self.inflow + (random.gauss(0, 0.5) if self.inflow > 0 else 0))
        measured_outflow = max(0, self.outflow + (random.gauss(0, 0.5) if self.outflow > 0 else 0))
        
        if is_target:
            if scenario == 'level_sensor_fault':
                noisy_volume_l = getattr(self, 'stuck_volume', noisy_volume_l)
                self.stuck_volume = noisy_volume_l
            else:
                if hasattr(self, 'stuck_volume'): delattr(self, 'stuck_volume')
                
            if scenario == 'flow_meter_fault':
                if self.state == 'RECEIPT': measured_inflow *= 0.8
                elif self.state == 'DELIVERY': measured_outflow *= 0.8
        else:
            if hasattr(self, 'stuck_volume'): delattr(self, 'stuck_volume')
                
        self.level_m = noisy_volume_l / (self.area * 1000.0)
        
        return {
            'tank_id': self.tank_id,
            'timestamp': datetime.datetime.utcnow().isoformat() + "Z",
            'level_m': self.level_m,
            'temperature_c': self.temperature_c,
            'water_interface_m': self.water_interface_m,
            'inflow_l_min': measured_inflow,
            'outflow_l_min': measured_outflow,
            'net_flow_l_min': measured_inflow - measured_outflow,
            'pressure_bar': self.pressure + (0.5 if measured_inflow > 0 else 0),
            'valve_position_outlet_closed': self.valve_closed
        }

def run_simulator():
    print("Initializing Database...")
    init_db()
    
    print("Loading ML Models...")
    with open(V7_MODELS_DIR / "isolation_forest.pkl", "rb") as f:
        models = pickle.load(f)
    with open(V7_MODELS_DIR / "scaler.pkl", "rb") as f:
        scalers = pickle.load(f)
    with open(V7_MODELS_DIR / "threshold.json", "r") as f:
        thresholds = json.load(f)
    with open(V7_MODELS_DIR / "diagnosis_rf.pkl", "rb") as f:
        rf = pickle.load(f)
        
    features_list = ['level_rate_m_min', 'residual_l', 'residual_rate', 'residual_roll_mean_5m', 'residual_roll_std_15m', 'cumulative_residual_60m']
    
    tanks = {t: TankSimulator(t) for t in TANKS}
    persistence_engine = PersistenceEngine(min_intervals=3)
    
    conn = get_db()
    
    print("Starting simulation loop...")
    while True:
        try:
            c = conn.cursor()
            c.execute('SELECT scenario, target_tank FROM sim_state WHERE id=1')
            state_row = c.fetchone()
            scenario = state_row['scenario'] if state_row else 'normal'
            target_tank = state_row['target_tank'] if state_row else 'none'
            
            for t_id, tank in tanks.items():
                is_target = (scenario != 'normal' and target_tank == t_id)
                reading = tank.step(scenario, is_target)
                
                # --- ML PIPELINE execution ---
                
                # 1. Thermal Correction & Residual
                area_m2 = TANK_AREA_M2[t_id]
                total_vol_l = reading['level_m'] * area_m2 * 1000
                water_vol_l = reading['water_interface_m'] * area_m2 * 1000
                oil_vol_l = total_vol_l - water_vol_l
                
                vcf = 1.0 / (1.0 + BETA_CRUDE_OIL * (reading['temperature_c'] - 15.0))
                corrected_oil_vol_l = oil_vol_l * vcf
                
                if len(tank.history) > 0:
                    prev_vol = tank.history['corrected_vol'].iloc[-1]
                    delta_vol = corrected_oil_vol_l - prev_vol
                    prev_level = tank.history['level_m'].iloc[-1]
                    level_rate = (reading['level_m'] - prev_level) * 2
                    prev_water = tank.history['water_interface_m'].iloc[-1]
                    water_rate = (reading['water_interface_m'] - prev_water) * 2
                else:
                    delta_vol = 0
                    level_rate = 0
                    water_rate = 0
                    
                net_flow_vol = reading['net_flow_l_min'] * 0.5
                residual = delta_vol - net_flow_vol
                
                # Update history
                new_hist = pd.DataFrame([{
                    'level_m': reading['level_m'],
                    'water_interface_m': reading['water_interface_m'],
                    'residual_l': residual,
                    'corrected_vol': corrected_oil_vol_l,
                    'inflow_l_min': reading['inflow_l_min'],
                    'outflow_l_min': reading['outflow_l_min']
                }])
                tank.history = pd.concat([tank.history, new_hist]).tail(120)
                
                # 2. State inference
                if reading['net_flow_l_min'] > 5: op_state = 'RECEIPT'
                elif reading['net_flow_l_min'] < -5: op_state = 'DELIVERY'
                else: op_state = 'IDLE'
                reading['operating_state'] = op_state
                
                # 3. Feature extraction
                if len(tank.history) >= 2:
                    res_rate = tank.history['residual_l'].diff().iloc[-1]
                else:
                    res_rate = 0
                    
                res_mean_5m = tank.history['residual_l'].tail(10).mean()
                res_std_15m = tank.history['residual_l'].tail(30).std()
                res_sum_60m = tank.history['residual_l'].sum()
                
                features_vec = [level_rate, residual, res_rate, res_mean_5m, res_std_15m, res_sum_60m]
                features_vec = [0 if np.isnan(x) else x for x in features_vec]
                
                # 4. IF Model scoring
                score = 1.0
                if t_id in models and op_state in models[t_id]:
                    model = models[t_id][op_state]
                    scaler = scalers[t_id][op_state]
                    thresh = thresholds[t_id][op_state]
                    
                    x_scaled = scaler.transform([features_vec])
                    score = float(model.score_samples(x_scaled)[0])
                    is_if_anomaly = score < thresh
                else:
                    is_if_anomaly = False
                
                # 5. Rules Evaluation
                rule_row = {
                    'valve_position_outlet_closed': reading['valve_position_outlet_closed'],
                    'level_rate_m_min': level_rate,
                    'water_rate_m_min': water_rate,
                    'residual_l': residual,
                    'inflow_l_min': reading['inflow_l_min'],
                    'outflow_l_min': reading['outflow_l_min']
                }
                fired_rules = evaluate_rules(rule_row)
                
                is_rule_anomaly = len(fired_rules) > 0
                is_abnormal = is_if_anomaly or is_rule_anomaly
                
                # 6. Persistence Tracker
                alert_triggered, streak = persistence_engine.update(t_id, is_abnormal)
                
                status_color = 'ANOMALY' if alert_triggered else 'NORMAL'
                
                diagnosis = "Normal"
                
                # 7. Diagnosis
                if alert_triggered:
                    r1 = 1 if "RULE_1_UNEXPECTED_LEVEL_DROP" in fired_rules else 0
                    r2 = 1 if "RULE_2_WATER_INGRESS" in fired_rules else 0
                    r3 = 1 if "RULE_3_SEVERE_NEGATIVE_RESIDUAL" in fired_rules else 0
                    r4 = 1 if "RULE_4_STUCK_LEVEL_SENSOR" in fired_rules else 0
                    r5 = 1 if "RULE_5_FLOW_VOLUME_MISMATCH" in fired_rules else 0
                    
                    s_del = 1 if op_state == 'DELIVERY' else 0
                    s_idl = 1 if op_state == 'IDLE' else 0
                    s_rec = 1 if op_state == 'RECEIPT' else 0
                    
                    diag_x = [
                        res_sum_60m, level_rate, r1, r2, r3, r4, r5,
                        residual, res_rate, res_mean_5m, res_std_15m,
                        s_del, s_idl, s_rec
                    ]
                    diag_x = [0 if np.isnan(x) else x for x in diag_x]
                    
                    diag_pred = rf.predict([diag_x])[0]
                    diagnosis = str(diag_pred)
                    
                    source = "MODEL"
                    if is_rule_anomaly and is_if_anomaly: source = "MODEL + RULE"
                    elif is_rule_anomaly: source = "RULE"
                    
                    # 8. Check for existing active/acknowledged alert for this tank
                    c.execute('SELECT alert_id FROM alerts WHERE tank_id=? AND status IN ("ACTIVE", "ACKNOWLEDGED")', (t_id,))
                    existing_alert = c.fetchone()
                    
                    if not existing_alert:
                        alert_id = f"ALT-{t_id}-{datetime.datetime.utcnow().strftime('%H%M')}"
                        c.execute('''
                            INSERT INTO alerts 
                            (alert_id, timestamp, tank_id, event, severity, anomaly_score, source, diagnosis, confidence, status, persistence_duration)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            alert_id, reading['timestamp'], t_id, diagnosis, 'HIGH', 
                            round(score, 3), source, diagnosis, 0.95, 'ACTIVE', f"{streak} intervals"
                        ))
                    else:
                        c.execute('UPDATE alerts SET persistence_duration=? WHERE alert_id=?', (f"{streak} intervals", existing_alert['alert_id']))
                
                # Save Telemetry
                c.execute('''
                    INSERT INTO telemetry 
                    (tank_id, timestamp, level_m, temperature_c, water_interface_m, inflow_l_min, outflow_l_min, net_flow_l_min, pressure_bar, valve_position_outlet_closed, residual_l, operating_state, status, anomaly_score, diagnosis, persistence)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    t_id, reading['timestamp'], reading['level_m'], reading['temperature_c'], reading['water_interface_m'],
                    reading['inflow_l_min'], reading['outflow_l_min'], reading['net_flow_l_min'], reading['pressure_bar'],
                    reading['valve_position_outlet_closed'], residual, op_state, status_color, score, diagnosis, streak
                ))
            
            conn.commit()
            
        except Exception as e:
            print(f"Simulator Error: {e}")
            import traceback
            traceback.print_exc()
            
        time.sleep(2) # Run every 2 real seconds representing 30s intervals

if __name__ == "__main__":
    run_simulator()
