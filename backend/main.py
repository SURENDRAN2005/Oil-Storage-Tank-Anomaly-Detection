from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sqlite3
import json
from pathlib import Path
import sys
import datetime
sys.path.append(str(Path(__file__).resolve().parent.parent))
from backend.database import get_db, init_db

app = FastAPI(title="Oil Storage Tank Anomaly API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup
@app.on_event("startup")
def startup():
    init_db()

# --- API Endpoints ---

@app.get("/api/health")
def health_check():
    return {"status": "ok", "version": "1.0.0"}

@app.get("/api/tanks")
def get_tanks():
    conn = get_db()
    c = conn.cursor()
    # Get latest reading for each tank
    c.execute('''
        SELECT t1.* FROM telemetry t1
        JOIN (SELECT tank_id, MAX(timestamp) as max_ts FROM telemetry GROUP BY tank_id) t2
        ON t1.tank_id = t2.tank_id AND t1.timestamp = t2.max_ts
    ''')
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.get("/api/tanks/{tank_id}")
def get_tank_detail(tank_id: str):
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM telemetry WHERE tank_id=? ORDER BY timestamp DESC LIMIT 1', (tank_id,))
    row = c.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Tank not found")
    return dict(row)

@app.get("/api/tanks/{tank_id}/history")
def get_tank_history(tank_id: str, limit: int = 60):
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM telemetry WHERE tank_id=? ORDER BY timestamp DESC LIMIT ?', (tank_id, limit))
    rows = c.fetchall()
    conn.close()
    # return in chronological order (oldest first)
    return [dict(r) for r in reversed(rows)]

@app.get("/api/alerts")
def get_alerts(status: str = None):
    conn = get_db()
    c = conn.cursor()
    if status:
        c.execute('SELECT * FROM alerts WHERE status=? ORDER BY timestamp DESC', (status,))
    else:
        c.execute('SELECT * FROM alerts ORDER BY timestamp DESC')
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]

class AlertStatusUpdate(BaseModel):
    status: str

@app.post("/api/alerts/{alert_id}/status")
def update_alert_status(alert_id: str, req: AlertStatusUpdate):
    if req.status not in ["ACKNOWLEDGED", "RESOLVED"]:
        raise HTTPException(status_code=400, detail="Invalid status")
        
    conn = get_db()
    c = conn.cursor()
    
    now = datetime.datetime.utcnow().isoformat() + "Z"
    
    if req.status == "ACKNOWLEDGED":
        c.execute('UPDATE alerts SET status=?, acknowledged_at=? WHERE alert_id=?', (req.status, now, alert_id))
    elif req.status == "RESOLVED":
        c.execute('UPDATE alerts SET status=?, resolved_at=? WHERE alert_id=?', (req.status, now, alert_id))
        
    if c.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Alert not found")
        
    conn.commit()
    conn.close()
    return {"status": "success"}

class ScenarioRequest(BaseModel):
    scenario: str
    target_tank: str

@app.post("/api/simulator/scenario")
def set_scenario(req: ScenarioRequest):
    conn = get_db()
    c = conn.cursor()
    c.execute('UPDATE sim_state SET scenario=?, target_tank=? WHERE id=1', (req.scenario, req.target_tank))
    conn.commit()
    conn.close()
    return {"status": "success"}

@app.get("/api/simulator/status")
def get_sim_status():
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM sim_state WHERE id=1')
    row = c.fetchone()
    conn.close()
    return dict(row)

# Removed old frontend serving
