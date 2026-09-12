import React from 'react';
import { Doughnut, Bar } from 'react-chartjs-2';
import { Chart as ChartJS, ArcElement, Tooltip, Legend, CategoryScale, LinearScale, BarElement, Title } from 'chart.js';

ChartJS.register(ArcElement, Tooltip, Legend, CategoryScale, LinearScale, BarElement, Title);

export default function Analytics() {
  const donutData = {
    labels: ['Slow Leak', 'Water Ingress', 'Flow Meter Fault', 'Sensor Fault', 'Unauthorized Withdrawal'],
    datasets: [{
      data: [42, 28, 15, 10, 5],
      backgroundColor: ['#dc2626', '#2563eb', '#f59e0b', '#64748b', '#1e293b'],
      borderWidth: 0,
    }]
  };

  const donutOptions = {
    plugins: {
      legend: { position: 'right', labels: { font: { size: 12 }, usePointStyle: true, boxWidth: 8 } }
    },
    cutout: '70%'
  };

  const barData = {
    labels: ['T-101', 'T-102', 'T-103', 'T-104', 'T-105', 'T-106', 'T-107', 'T-108', 'T-109', 'T-110'],
    datasets: [{
      label: 'Anomaly Count',
      data: [12, 3, 45, 8, 2, 5, 18, 4, 1, 9],
      backgroundColor: '#2563eb',
      borderRadius: 4
    }]
  };

  const barOptions = {
    plugins: { legend: { display: false } },
    scales: {
      y: { grid: { color: '#e2e8f0', drawBorder: false }, ticks: { font: { size: 11 } } },
      x: { grid: { display: false, drawBorder: false }, ticks: { font: { size: 11 } } }
    }
  };

  return (
    <div className="analytics">

      <h2 className="section-title">MODEL PERFORMANCE</h2>
      <div className="grid grid-cols-4 mb-6">
        <div className="card"><div className="kpi-label">PRECISION</div><div className="kpi-value" style={{fontSize: '28px'}}>0.92</div></div>
        <div className="card"><div className="kpi-label">RECALL</div><div className="kpi-value" style={{fontSize: '28px'}}>0.89</div></div>
        <div className="card"><div className="kpi-label">F1 SCORE</div><div className="kpi-value" style={{fontSize: '28px'}}>0.90</div></div>
        <div className="card"><div className="kpi-label">FALSE POSITIVE RATE</div><div className="kpi-value" style={{fontSize: '28px'}}>0.04</div></div>
      </div>

      <div className="flex" style={{ gap: '24px' }}>
        <div className="card" style={{ flex: 1 }}>
          <h3 className="card-title mb-4">ANOMALIES BY TYPE</h3>
          <div style={{ height: '250px' }}>
            <Doughnut data={donutData} options={donutOptions} />
          </div>
        </div>
        <div className="card" style={{ flex: 2 }}>
          <h3 className="card-title mb-4">ANOMALIES BY TANK</h3>
          <div style={{ height: '250px' }}>
            <Bar data={barData} options={barOptions} />
          </div>
        </div>
      </div>
    </div>
  );
}
