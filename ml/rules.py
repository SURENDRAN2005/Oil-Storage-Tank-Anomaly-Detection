import numpy as np
import pandas as pd
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent))
from config.settings import (
    THEFT_THRESHOLD_L_PER_INTERVAL, 
    WATER_INGRESS_THRESHOLD_M_PER_INTERVAL, 
    LEAK_LEVEL_DROP_M_PER_INTERVAL,
    MIN_PERSISTENCE_INTERVALS
)

def evaluate_rules(row, residual_history=None):
    """
    Phase 11: Independent Rule Engine
    Evaluates physical rules against a single row or dataframe.
    Returns a dictionary of fired rules.
    """
    fired_rules = []
    
    # Check if we are dealing with a DataFrame row or dict
    if isinstance(row, pd.Series):
        row = row.to_dict()
        
    valve_closed = row.get('valve_position_outlet_closed', True)
    if isinstance(valve_closed, str):
        valve_closed = valve_closed.lower() == 'closed'
        
    level_rate = row.get('level_rate_m_min', 0)
    water_rate = row.get('water_rate_m_min', 0)
    residual = row.get('residual_l', 0)
    
    # RULE 1: Level falling while all outlet valves are closed
    if valve_closed and level_rate < LEAK_LEVEL_DROP_M_PER_INTERVAL:
        fired_rules.append("RULE_1_UNEXPECTED_LEVEL_DROP")
        
    # RULE 2: Water interface rising beyond configured limit
    if water_rate > WATER_INGRESS_THRESHOLD_M_PER_INTERVAL:
        fired_rules.append("RULE_2_WATER_INGRESS")
        
    # RULE 3: Negative residual exceeds theft threshold
    if residual < THEFT_THRESHOLD_L_PER_INTERVAL:
        fired_rules.append("RULE_3_SEVERE_NEGATIVE_RESIDUAL")
        
    # RULE 4: Sensor stuck for too long
    # Requires history, checked in persistence engine usually, 
    # but for simplicity if level rate is exactly 0.0 during flow, it's stuck.
    inflow = row.get('inflow_l_min', 0)
    outflow = row.get('outflow_l_min', 0)
    if (inflow > 10 or outflow > 10) and abs(level_rate) < 0.0001:
        fired_rules.append("RULE_4_STUCK_LEVEL_SENSOR")
        
    # RULE 5: Flow and physical volume change strongly disagree
    # If residual is extremely high while there is active flow
    if (inflow > 10 or outflow > 10) and abs(residual) > 40:
        fired_rules.append("RULE_5_FLOW_VOLUME_MISMATCH")
        
    return fired_rules

class PersistenceEngine:
    """Phase 10: Persistence Logic Tracker"""
    
    def __init__(self, min_intervals=MIN_PERSISTENCE_INTERVALS):
        self.min_intervals = min_intervals
        self.streaks = {}
        
    def update(self, tank_id, is_abnormal):
        """
        Updates the streak for a tank.
        Returns (alert_triggered, current_streak)
        """
        if tank_id not in self.streaks:
            self.streaks[tank_id] = 0
            
        if is_abnormal:
            self.streaks[tank_id] += 1
        else:
            # Optionally decay instead of immediate reset to handle noisy anomalies
            self.streaks[tank_id] = max(0, self.streaks[tank_id] - 1)
            
        alert_triggered = self.streaks[tank_id] >= self.min_intervals
        return alert_triggered, self.streaks[tank_id]
