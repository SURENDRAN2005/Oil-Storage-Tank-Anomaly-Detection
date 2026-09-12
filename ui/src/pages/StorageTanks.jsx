import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { fetchTanks } from '../api';
import StatusBadge from '../components/StatusBadge';

export default function StorageTanks() {
  const [tanks, setTanks] = useState([]);
  const navigate = useNavigate();

  useEffect(() => {
    const loadTanks = async () => {
      try {
        const data = await fetchTanks();
        data.sort((a, b) => a.tank_id.localeCompare(b.tank_id));
        setTanks(data);
      } catch (err) {
        console.error(err);
      }
    };
    loadTanks();
    const interval = setInterval(loadTanks, 2000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="card">
      <div className="flex justify-between items-center mb-6">
        <h2 className="section-title" style={{marginBottom: 0}}>TANK OVERVIEW</h2>
        <div className="flex items-center" style={{gap: '12px'}}>
          <input 
            type="text" 
            placeholder="Search tank..." 
            style={{
              padding: '6px 12px', 
              border: '1px solid var(--color-border)', 
              borderRadius: '4px',
              fontSize: '13px'
            }} 
          />
          <select 
            style={{
              padding: '6px 12px', 
              border: '1px solid var(--color-border)', 
              borderRadius: '4px',
              fontSize: '13px'
            }}
          >
            <option>All</option>
            <option>Normal</option>
            <option>Anomaly</option>
          </select>
        </div>
      </div>
      
      <table className="data-table">
        <thead>
          <tr>
            <th>Tank ID</th>
            <th>Status</th>
            <th>Level (%)</th>
            <th>Temperature (°C)</th>
            <th>Flow (L/min)</th>
            <th>Pressure (bar)</th>
            <th>Residual (L)</th>
            <th>Operating State</th>
            <th>Last Update</th>
          </tr>
        </thead>
        <tbody>
          {tanks.map(t => (
            <tr key={t.tank_id} onClick={() => navigate(`/tanks/${t.tank_id}`)}>
              <td style={{fontWeight: 600}}>{t.tank_id}</td>
              <td><StatusBadge status={t.status} /></td>
              <td>{t.level_m.toFixed(1)}</td>
              <td>{t.temperature_c.toFixed(1)}</td>
              <td>{Math.round(t.net_flow_l_min)}</td>
              <td>{t.pressure_bar.toFixed(2)}</td>
              <td style={{color: t.status === 'ANOMALY' ? 'var(--color-danger)' : 'inherit', fontWeight: t.status === 'ANOMALY' ? 600 : 400}}>
                {t.residual_l > 0 ? '+' : ''}{t.residual_l.toFixed(1)}
              </td>
              <td>{t.operating_state}</td>
              <td style={{color: 'var(--color-text-muted)', fontSize: '12px'}}>
                {new Date(t.timestamp).toLocaleTimeString()}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
