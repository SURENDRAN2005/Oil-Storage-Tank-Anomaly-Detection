import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { fetchTanks, fetchAlerts } from '../api';
import StatusBadge from '../components/StatusBadge';
import TankGraphic from '../components/TankGraphic';
import { Doughnut } from 'react-chartjs-2';
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js';
import './Dashboard.css';

ChartJS.register(ArcElement, Tooltip, Legend);

export default function Dashboard() {
  const [tanks, setTanks] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const navigate = useNavigate();

  useEffect(() => {
    const loadData = async () => {
      try {
        const [tanksData, alertsData] = await Promise.all([
          fetchTanks(),
          fetchAlerts('ACTIVE')
        ]);
        // Sort tanks by id
        tanksData.sort((a, b) => a.tank_id.localeCompare(b.tank_id));
        setTanks(tanksData);
        setAlerts(alertsData);
      } catch (err) {
        console.error(err);
      }
    };
    
    loadData();
    const interval = setInterval(loadData, 2000);
    return () => clearInterval(interval);
  }, []);

  const totalTanks = tanks.length;
  const anomalies = tanks.filter(t => t.status === 'ANOMALY').length;
  const normalTanks = totalTanks - anomalies;
  
  const avgResidual = tanks.length > 0 
    ? (tanks.reduce((sum, t) => sum + t.residual_l, 0) / tanks.length).toFixed(1) 
    : 0;

  const donutData = {
    labels: ['Slow leak', 'Water ingress', 'Sensor Fault', 'Flow Meter Fault', 'Unauthorized Withdrawal'],
    datasets: [{
      data: [2, 1, 1, 1, 0],
      backgroundColor: ['#dc2626', '#2563eb', '#f59e0b', '#64748b', '#1e293b'],
      borderWidth: 0,
    }]
  };

  const donutOptions = {
    plugins: {
      legend: { position: 'right', labels: { font: { size: 10 }, usePointStyle: true, boxWidth: 6 } }
    },
    cutout: '70%',
    maintainAspectRatio: false,
  };

  return (
    <div className="dashboard-container">
      {/* KPI Section */}
      <div className="grid grid-cols-4 mb-6">
        <div className="card kpi-card">
          <div className="kpi-label">TOTAL TANKS</div>
          <div className="kpi-value">{totalTanks}</div>
          <div className="kpi-sublabel">All Tanks</div>
        </div>
        <div className="card kpi-card normal">
          <div className="kpi-label">NORMAL</div>
          <div className="kpi-value">{normalTanks}</div>
          <div className="kpi-sublabel">Tanks</div>
        </div>
        <div className="card kpi-card anomaly">
          <div className="kpi-label">ANOMALIES</div>
          <div className="kpi-value">{anomalies}</div>
          <div className="kpi-sublabel">Tanks</div>
        </div>
        <div className="card kpi-card anomaly">
          <div className="kpi-label">ACTIVE ALERTS</div>
          <div className="kpi-value">{alerts.length}</div>
          <div className="kpi-sublabel">Alerts</div>
        </div>
      </div>

      <div className="dashboard-main flex">
        {/* Tank Grid */}
        <div className="tank-section">
          <h2 className="section-title">TANK OVERVIEW</h2>
          <div className="tank-grid">
            {tanks.map(tank => (
              <div 
                key={tank.tank_id} 
                className={`card tank-card ${tank.status === 'ANOMALY' ? 'anomaly-border' : ''}`}
                onClick={() => navigate(`/tanks/${tank.tank_id}`)}
              >
                <div className="tank-card-header mb-4">
                  <span className="tank-id">{tank.tank_id}</span>
                  <StatusBadge status={tank.status} />
                </div>
                <div className="flex items-center">
                  <TankGraphic level={tank.level_m} status={tank.status} />
                  <div className="flex-col" style={{ flex: 1, gap: '8px', display: 'flex' }}>
                    <div className="metric flex justify-between w-full">
                      <span className="metric-label">Level</span>
                      <span className="metric-value">{tank.level_m.toFixed(1)}%</span>
                    </div>
                    <div className="metric flex justify-between w-full">
                      <span className="metric-label">Flow</span>
                      <span className="metric-value">{Math.round(tank.net_flow_l_min)} L/min</span>
                    </div>
                    <div className="metric flex justify-between w-full">
                      <span className="metric-label">Residual</span>
                      <span className="metric-value">{tank.residual_l > 0 ? '+' : ''}{tank.residual_l.toFixed(1)} L</span>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Right Sidebar - Alerts & Residual */}
        <div className="dashboard-sidebar">
          <div className="card alerts-panel mb-6">
            <h3 className="card-title mb-4">ACTIVE ALERTS</h3>
            <div className="alerts-list">
              {alerts.slice(0, 5).map(alert => (
                <div key={alert.id} className="compact-alert" onClick={() => navigate(`/alerts/${alert.alert_id}`)}>
                  <div className="flex justify-between items-center mb-2">
                    <span className="alert-tank">{alert.tank_id}</span>
                    <StatusBadge status={alert.severity} />
                  </div>
                  <div className="alert-event">{alert.diagnosis}</div>
                  <div className="alert-score">Score {alert.anomaly_score.toFixed(2)}</div>
                </div>
              ))}
              {alerts.length === 0 && <div className="text-muted">No active alerts.</div>}
            </div>
            <button className="btn btn-outline w-full mt-4" onClick={() => navigate('/alerts')}>View All →</button>
          </div>

          <div className="card mb-6">
            <h3 className="card-title mb-4">ALERTS BY TYPE</h3>
            <div style={{ height: '140px', position: 'relative' }}>
              <Doughnut data={donutData} options={donutOptions} />
              <div style={{ position: 'absolute', top: '50%', left: '25%', transform: 'translate(-50%, -50%)', textAlign: 'center' }}>
                <div style={{ fontSize: '24px', fontWeight: 700, color: 'var(--color-primary)', lineHeight: 1 }}>5</div>
                <div style={{ fontSize: '10px', color: 'var(--color-text-muted)' }}>Total</div>
              </div>
            </div>
          </div>

          <div className="card residual-panel">
            <h3 className="card-title mb-4">RESIDUAL SUMMARY</h3>
            <div className="residual-avg">{avgResidual > 0 ? '+' : ''}{avgResidual} L</div>
            <div className="residual-label">CURRENT AVG RESIDUAL</div>
            
            <div className="residual-range mt-6">
              <div className="range-label">NORMAL RANGE</div>
              <div className="range-value">-10 L to +10 L</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
