import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { fetchAlerts, updateAlertStatus } from '../api';
import StatusBadge from '../components/StatusBadge';

export default function AlertDetails() {
  const { alertId } = useParams();
  const navigate = useNavigate();
  const [alert, setAlert] = useState(null);

  useEffect(() => {
    const loadData = async () => {
      try {
        const allAlerts = await fetchAlerts();
        const found = allAlerts.find(a => a.alert_id === alertId);
        setAlert(found);
      } catch (err) {
        console.error(err);
      }
    };
    loadData();
    const interval = setInterval(loadData, 2000);
    return () => clearInterval(interval);
  }, [alertId]);

  const handleAction = async (action) => {
    try {
      await updateAlertStatus(alertId, action);
      // It will auto-refresh via interval, but let's navigate back to alerts
      navigate('/alerts');
    } catch (err) {
      console.error(err);
    }
  };

  if (!alert) return <div>Loading...</div>;

  return (
    <div className="alert-details">
      <div className="mb-6 flex items-center">
        <button onClick={() => navigate('/alerts')} style={{ color: 'var(--color-accent)', fontWeight: 600, marginRight: '16px' }}>
          ← Back to Alerts
        </button>
      </div>

      <div className="flex items-center mb-6" style={{ gap: '16px' }}>
        <h1 className="page-title" style={{ margin: 0 }}>{alert.alert_id}</h1>
        <StatusBadge status={alert.status} />
      </div>

      <div className="grid grid-cols-2 mb-6" style={{ gap: '24px' }}>
        <div className="card">
          <div className="flex justify-between items-center mb-6">
            <h3 className="card-title" style={{ margin: 0 }}>{alert.tank_id}</h3>
            <span style={{ fontSize: '14px', fontWeight: 600, color: 'var(--color-danger)' }}>{alert.severity} SEVERITY</span>
          </div>
          
          <h2 style={{ fontSize: '24px', fontWeight: 700, color: 'var(--color-primary)', textTransform: 'uppercase', marginBottom: '24px' }}>
            {alert.diagnosis}
          </h2>
          
          <div className="grid grid-cols-2" style={{ gap: '16px' }}>
            <div>
              <div style={{ fontSize: '11px', color: 'var(--color-text-muted)', fontWeight: 600 }}>Detected At</div>
              <div style={{ fontSize: '14px', fontWeight: 500 }}>{new Date(alert.timestamp).toLocaleString()}</div>
            </div>
            <div>
              <div style={{ fontSize: '11px', color: 'var(--color-text-muted)', fontWeight: 600 }}>Anomaly Score</div>
              <div style={{ fontSize: '14px', fontWeight: 500 }}>{alert.anomaly_score.toFixed(2)}</div>
            </div>
            <div>
              <div style={{ fontSize: '11px', color: 'var(--color-text-muted)', fontWeight: 600 }}>Persistence</div>
              <div style={{ fontSize: '14px', fontWeight: 500 }}>{alert.persistence_duration || 'Unknown'}</div>
            </div>
            <div>
              <div style={{ fontSize: '11px', color: 'var(--color-text-muted)', fontWeight: 600 }}>Confidence</div>
              <div style={{ fontSize: '14px', fontWeight: 500 }}>{(alert.confidence * 100).toFixed(0)}%</div>
            </div>
          </div>
        </div>

        <div className="card">
          <h3 className="card-title mb-4">OPERATOR ACTION</h3>
          
          <div className="mb-4">
            <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: 'var(--color-text-muted)', marginBottom: '8px' }}>
              Action Type
            </label>
            <select style={{ width: '100%', padding: '8px', border: '1px solid var(--color-border)', borderRadius: '4px', fontSize: '14px' }}>
              <option>Select action</option>
              <option>Dispatch Field Technician</option>
              <option>Close Isolation Valve</option>
              <option>False Alarm - Ignore</option>
            </select>
          </div>
          
          <div className="mb-6">
            <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: 'var(--color-text-muted)', marginBottom: '8px' }}>
              Comments
            </label>
            <textarea 
              rows="3" 
              placeholder="Enter investigation notes..."
              style={{ width: '100%', padding: '8px', border: '1px solid var(--color-border)', borderRadius: '4px', fontSize: '14px', resize: 'none' }}
            />
          </div>
          
          <div className="flex" style={{ gap: '12px' }}>
            {alert.status === 'ACTIVE' && (
              <button className="btn" style={{ backgroundColor: 'var(--color-warning)', color: 'white', flex: 1 }} onClick={() => handleAction('ACKNOWLEDGED')}>
                ACKNOWLEDGE
              </button>
            )}
            <button className="btn btn-success" style={{ flex: 1 }} onClick={() => handleAction('RESOLVED')}>
              RESOLVE
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
