import sqlite3
import json
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "app.db"

def get_db():
    # Allow multithreading and use WAL mode for better concurrency
    conn = sqlite3.connect(DB_PATH, check_same_thread=False, timeout=10.0)
    conn.execute('PRAGMA journal_mode=WAL;')
    conn.execute('PRAGMA synchronous=NORMAL;')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    
    # Drop existing for clean run if we want to reset every run
    # (Or keep it persistent. Let's keep persistent but maybe clear telemetry to avoid huge growth)
    c.execute('DROP TABLE IF EXISTS telemetry')
    
    # telemetry
    c.execute('''CREATE TABLE IF NOT EXISTS telemetry (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tank_id TEXT,
        timestamp TEXT,
        level_m REAL,
        temperature_c REAL,
        water_interface_m REAL,
        inflow_l_min REAL,
        outflow_l_min REAL,
        net_flow_l_min REAL,
        pressure_bar REAL,
        valve_position_outlet_closed BOOLEAN,
        residual_l REAL,
        operating_state TEXT,
        status TEXT,
        anomaly_score REAL,
        diagnosis TEXT,
        persistence INTEGER
    )''')
    
    # Index for fast querying by tank and time
    c.execute('CREATE INDEX IF NOT EXISTS idx_tank_time ON telemetry (tank_id, timestamp)')
    
    # alerts
    c.execute('''CREATE TABLE IF NOT EXISTS alerts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        alert_id TEXT UNIQUE,
        timestamp TEXT,
        tank_id TEXT,
        event TEXT,
        severity TEXT,
        anomaly_score REAL,
        source TEXT,
        diagnosis TEXT,
        confidence REAL,
        status TEXT,
        persistence_duration TEXT,
        acknowledged_at TEXT,
        resolved_at TEXT
    )''')
    
    # simulator state
    c.execute('''CREATE TABLE IF NOT EXISTS sim_state (
        id INTEGER PRIMARY KEY CHECK (id = 1),
        scenario TEXT,
        target_tank TEXT,
        is_running BOOLEAN
    )''')
    
    c.execute('''INSERT OR IGNORE INTO sim_state (id, scenario, target_tank, is_running) VALUES (1, 'normal', 'none', 1)''')
    
    conn.commit()
    conn.close()
