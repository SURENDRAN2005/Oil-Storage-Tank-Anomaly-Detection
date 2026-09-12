import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { fetchTankDetail, fetchTankHistory } from '../api';
import StatusBadge from '../components/StatusBadge';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend
} from 'chart.js';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend);

export default function TankDetails() {
  const { tankId } = useParams();
  const navigate = useNavigate();
  const [tank, setTank] = useState(null);
  const [history, setHistory] = useState([]);

  useEffect(() => {
    const loadData = async () => {
      try {
        const t = await fetchTankDetail(tankId);
        const h = await fetchTankHistory(tankId);
        setTank(t);
        setHistory(h);
      } catch (err) {
        console.error(err);
      }
    };
    loadData();
    const interval = setInterval(loadData, 2000);
    return () => clearInterval(interval);
  }, [tankId]);

  if (!tank) return <div>Loading...</div>;

  const chartData = {
    labels: history.map(h => new Date(h.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })),
    datasets: [
      {
        label: 'Residual (L)',
        data: history.map(h => h.residual_l),
        borderColor: '#2563eb',
        backgroundColor: 'rgba(37, 99, 235, 0.1)',
        borderWidth: 2,
        pointRadius: 4,
        pointHoverRadius: 6,
        tension: 0.1,
        pointBackgroundColor: history.map(h => h.residual_l < -10 ? '#dc2626' : '#16a34a'),
        pointBorderColor: history.map(h => h.residual_l < -10 ? '#dc2626' : '#16a34a'),
      },
      {
        label: 'Threshold',
        data: history.map(() => -10),
        borderColor: '#dc2626',
        borderWidth: 1,
        borderDash: [5, 5],
        pointRadius: 0,
        fill: false,
      }
    ]
  };

  const chartOptions = {
    animation: false,
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { position: 'top', align: 'end', labels: { usePointStyle: true, boxWidth: 6, font: { size: 11 } } },
      tooltip: {
        backgroundColor: '#1e293b',
        titleFont: { size: 12 },
        bodyFont: { size: 12 }
      }
    },
    scales: {
      y: {
        grid: { color: '#e2e8f0', drawBorder: false },
        ticks: { color: '#64748b', font: { size: 11 } }
      },
      x: {
        grid: { display: false, drawBorder: false },
        ticks: { color: '#64748b', font: { size: 11 }, maxTicksLimit: 8, maxRotation: 0 }
      }
    }
  };

  return (
    <div className="tank-details">
      <div className="mb-6 flex items-center">
        <button onClick={() => navigate('/tanks')} style={{ color: 'var(--color-accent)', fontWeight: 600, marginRight: '16px' }}>
          ← Back to Tanks
        </button>
      </div>

      <div className="flex items-center mb-6" style={{ gap: '16px' }}>
        <h1 className="page-title" style={{ margin: 0 }}>{tank.tank_id}</h1>
        <StatusBadge status={tank.status} />
        {tank.status === 'ANOMALY' && (
          <span style={{ fontSize: '14px', fontWeight: 600, color: 'var(--color-danger)', textTransform: 'uppercase' }}>
            {tank.diagnosis}
          </span>
        )}
      </div>

      <div className="grid grid-cols-4 mb-6">
        {tank.status === 'ANOMALY' && (
          <>
            <div className="card">
              <div className="kpi-label">Anomaly Score</div>
              <div className="kpi-value" style={{ fontSize: '24px' }}>{tank.anomaly_score.toFixed(2)}</div>
            </div>
            <div className="card">
              <div className="kpi-label">Duration</div>
              <div className="kpi-value" style={{ fontSize: '24px' }}>{tank.persistence * 2} minutes</div>
            </div>
          </>
        )}
        <div className="card">
          <div className="kpi-label">Operating State</div>
          <div className="kpi-value" style={{ fontSize: '24px' }}>{tank.operating_state}</div>
        </div>
      </div>

      <h2 className="section-title">CURRENT PARAMETERS</h2>
      <div className="grid" style={{ gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px', marginBottom: '24px' }}>
        {[
          { label: 'LEVEL', value: `${tank.level_m.toFixed(1)}%` },
          { label: 'TEMPERATURE', value: `${tank.temperature_c.toFixed(1)} °C` },
          { label: 'WATER INTERFACE', value: `${tank.water_interface_m.toFixed(2)} m` },
          { label: 'INFLOW', value: `${Math.round(tank.inflow_l_min)} L/min` },
          { label: 'OUTFLOW', value: `${Math.round(tank.outflow_l_min)} L/min` },
          { label: 'NET FLOW', value: <span style={{ color: tank.net_flow_l_min < 0 ? 'var(--color-danger)' : 'inherit' }}>{Math.round(tank.net_flow_l_min)} L/min</span> },
          { label: 'PRESSURE', value: `${tank.pressure_bar.toFixed(2)} bar` },
          { label: 'VALVE POSITION', value: tank.valve_position_outlet_closed ? '0%' : '65%' },
          { label: 'DENSITY', value: `845 kg/m³` }
        ].map(param => (
          <div key={param.label} className="card flex items-center justify-between" style={{ padding: '16px 24px', border: 'none', borderBottom: '1px solid var(--color-border)', borderRadius: 0, backgroundColor: 'transparent' }}>
            <div style={{ fontSize: '11px', color: 'var(--color-text-muted)', fontWeight: 700 }}>{param.label}</div>
            <div style={{ fontSize: '16px', fontWeight: 700, color: 'var(--color-primary)' }}>{param.value}</div>
          </div>
        ))}
      </div>

      <div className="flex mb-6" style={{ gap: '24px' }}>
        <div className="card" style={{ flex: 2 }}>
          <h3 className="card-title mb-4">RESIDUAL TREND</h3>
          <div style={{ height: '300px' }}>
            <Line data={chartData} options={chartOptions} />
          </div>
        </div>

        {tank.status === 'ANOMALY' && (
          <div className="flex-col" style={{ flex: 1, gap: '24px', display: 'flex' }}>
            <div className="card">
              <h3 className="card-title mb-4">PERSISTENCE</h3>
              <div style={{ fontSize: '24px', fontWeight: 700, color: 'var(--color-danger)' }}>
                {tank.persistence * 2} minutes
              </div>
              <div style={{ fontSize: '13px', color: 'var(--color-text-muted)' }}>
                {tank.persistence} abnormal intervals
              </div>
            </div>

            <div className="card" style={{ borderLeft: '4px solid var(--color-danger)' }}>
              <h3 className="card-title mb-4">WHY WAS THIS FLAGGED?</h3>
              <div className="grid grid-cols-2" style={{ gap: '16px', fontSize: '12px', color: 'var(--color-text-main)' }}>
                <div>
                  <div style={{ fontWeight: 700, marginBottom: '4px' }}>Residual</div>
                  <div style={{ color: 'var(--color-text-muted)' }}>Negative deviation persisted</div>
                </div>
                <div>
                  <div style={{ fontWeight: 700, marginBottom: '4px' }}>Level</div>
                  <div style={{ color: 'var(--color-text-muted)' }}>Continuous decrease</div>
                </div>
                <div>
                  <div style={{ fontWeight: 700, marginBottom: '4px' }}>Flow</div>
                  <div style={{ color: 'var(--color-text-muted)' }}>No corresponding expected withdrawal</div>
                </div>
                <div>
                  <div style={{ fontWeight: 700, marginBottom: '4px' }}>Valve</div>
                  <div style={{ color: 'var(--color-text-muted)' }}>Outlet condition abnormal</div>
                </div>
              </div>
              
              <div className="mt-6 pt-4" style={{ borderTop: '1px solid var(--color-border)' }}>
                <div style={{ fontSize: '11px', color: 'var(--color-text-muted)', fontWeight: 600, marginBottom: '4px' }}>DIAGNOSIS</div>
                <div style={{ fontSize: '16px', fontWeight: 700, color: 'var(--color-danger)', textTransform: 'uppercase' }}>
                  {tank.diagnosis}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
