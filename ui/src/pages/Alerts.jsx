import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { fetchAlerts } from '../api';
import StatusBadge from '../components/StatusBadge';

export default function Alerts() {
  const [alerts, setAlerts] = useState([]);
  const [tab, setTab] = useState('ACTIVE');
  const navigate = useNavigate();

  useEffect(() => {
    const loadAlerts = async () => {
      try {
        const data = await fetchAlerts();
        setAlerts(data);
      } catch (err) {
        console.error(err);
      }
    };
    loadAlerts();
    const interval = setInterval(loadAlerts, 2000);
    return () => clearInterval(interval);
  }, []);

  const activeAlerts = alerts.filter(a => a.status === 'ACTIVE');
  const historicalAlerts = alerts.filter(a => a.status !== 'ACTIVE');

  const displayedAlerts = tab === 'ACTIVE' ? activeAlerts : historicalAlerts;

  return (
    <div className="card">
      <div className="flex items-center mb-6" style={{ gap: '16px', borderBottom: '1px solid var(--color-border)', paddingBottom: '16px' }}>
        <button 
          onClick={() => setTab('ACTIVE')}
          style={{ 
            fontWeight: 600, 
            fontSize: '14px',
            color: tab === 'ACTIVE' ? 'var(--color-primary)' : 'var(--color-text-muted)',
            borderBottom: tab === 'ACTIVE' ? '2px solid var(--color-accent)' : 'none',
            paddingBottom: '16px',
            marginBottom: '-17px'
          }}
        >
          Active Alerts ({activeAlerts.length})
        </button>
        <button 
          onClick={() => setTab('HISTORY')}
          style={{ 
            fontWeight: 600, 
            fontSize: '14px',
            color: tab === 'HISTORY' ? 'var(--color-primary)' : 'var(--color-text-muted)',
            borderBottom: tab === 'HISTORY' ? '2px solid var(--color-accent)' : 'none',
            paddingBottom: '16px',
            marginBottom: '-17px'
          }}
        >
          Historical Alerts
        </button>
      </div>

      <table className="data-table">
        <thead>
          <tr>
            <th>Time</th>
            <th>Tank</th>
            <th>Event</th>
            <th>Severity</th>
            <th>Score</th>
            <th>Source</th>
            <th>Diagnosis</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {displayedAlerts.map(a => (
            <tr key={a.id} onClick={() => navigate(`/alerts/${a.alert_id}`)}>
              <td style={{color: 'var(--color-text-muted)', fontSize: '13px'}}>
                {new Date(a.timestamp).toLocaleTimeString()}
              </td>
              <td style={{fontWeight: 600}}>{a.tank_id}</td>
              <td>{a.event}</td>
              <td style={{fontWeight: 600}}>{a.severity}</td>
              <td>{a.anomaly_score.toFixed(2)}</td>
              <td style={{fontSize: '12px'}}>{a.source}</td>
              <td>{a.diagnosis}</td>
              <td><StatusBadge status={a.status} /></td>
            </tr>
          ))}
          {displayedAlerts.length === 0 && (
            <tr>
              <td colSpan="8" style={{textAlign: 'center', padding: '32px', color: 'var(--color-text-muted)'}}>
                No {tab.toLowerCase()} alerts found.
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
