import React, { useState, useEffect } from 'react';
import { fetchSimStatus, updateSimScenario } from '../api';

export default function Settings() {
  const [simStatus, setSimStatus] = useState(null);
  const [scenario, setScenario] = useState('normal');
  const [targetTank, setTargetTank] = useState('none');

  useEffect(() => {
    const loadStatus = async () => {
      try {
        const status = await fetchSimStatus();
        setSimStatus(status);
        setScenario(status.scenario);
        setTargetTank(status.target_tank);
      } catch (err) {
        console.error(err);
      }
    };
    loadStatus();
  }, []);

  const handleSaveScenario = async () => {
    try {
      await updateSimScenario(scenario, targetTank);
      alert('Simulator scenario updated successfully.');
    } catch (err) {
      console.error(err);
      alert('Failed to update simulator scenario.');
    }
  };

  return (
    <div className="settings">
      <div className="grid grid-cols-2" style={{ gap: '24px' }}>
        
        {/* Left Column */}
        <div className="flex-col" style={{ display: 'flex', gap: '24px' }}>
          
          <div className="card">
            <h3 className="card-title mb-4">ANOMALY DETECTION</h3>
            <div className="mb-4">
              <label style={{ display: 'block', fontSize: '13px', fontWeight: 600, color: 'var(--color-text-muted)', marginBottom: '8px' }}>
                Anomaly Threshold
              </label>
              <input type="text" defaultValue="0.75" style={{ width: '100%', padding: '8px 12px', border: '1px solid var(--color-border)', borderRadius: '4px' }} />
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '13px', fontWeight: 600, color: 'var(--color-text-muted)', marginBottom: '8px' }}>
                Persistence Intervals
              </label>
              <input type="number" defaultValue="3" style={{ width: '100%', padding: '8px 12px', border: '1px solid var(--color-border)', borderRadius: '4px' }} />
            </div>
          </div>

          <div className="card">
            <h3 className="card-title mb-4">RULE ENGINE</h3>
            <div className="mb-4">
              <label style={{ display: 'block', fontSize: '13px', fontWeight: 600, color: 'var(--color-text-muted)', marginBottom: '8px' }}>
                Water Ingress Limit (m)
              </label>
              <input type="text" defaultValue="0.20" style={{ width: '100%', padding: '8px 12px', border: '1px solid var(--color-border)', borderRadius: '4px' }} />
            </div>
            <div className="mb-4">
              <label style={{ display: 'block', fontSize: '13px', fontWeight: 600, color: 'var(--color-text-muted)', marginBottom: '8px' }}>
                Negative Residual Theft Limit (L)
              </label>
              <input type="text" defaultValue="-100" style={{ width: '100%', padding: '8px 12px', border: '1px solid var(--color-border)', borderRadius: '4px' }} />
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '13px', fontWeight: 600, color: 'var(--color-text-muted)', marginBottom: '8px' }}>
                Sensor Stuck Duration (min)
              </label>
              <input type="number" defaultValue="15" style={{ width: '100%', padding: '8px 12px', border: '1px solid var(--color-border)', borderRadius: '4px' }} />
            </div>
          </div>
          
        </div>

        {/* Right Column */}
        <div className="flex-col" style={{ display: 'flex', gap: '24px' }}>
          
          <div className="card" style={{ borderTop: '3px solid var(--color-accent)' }}>
            <h3 className="card-title mb-4">SIMULATOR CONTROLS</h3>
            <p style={{ fontSize: '13px', color: 'var(--color-text-muted)', marginBottom: '16px' }}>
              Inject physical anomalies into the live simulation environment.
            </p>
            
            <div className="mb-4">
              <label style={{ display: 'block', fontSize: '13px', fontWeight: 600, color: 'var(--color-text-muted)', marginBottom: '8px' }}>
                Target Tank
              </label>
              <select value={targetTank} onChange={e => setTargetTank(e.target.value)} style={{ width: '100%', padding: '8px 12px', border: '1px solid var(--color-border)', borderRadius: '4px' }}>
                <option value="none">None</option>
                <option value="T-101">T-101</option>
                <option value="T-102">T-102</option>
                <option value="T-103">T-103</option>
                <option value="T-104">T-104</option>
                <option value="T-105">T-105</option>
                <option value="T-106">T-106</option>
                <option value="T-107">T-107</option>
                <option value="T-108">T-108</option>
                <option value="T-109">T-109</option>
                <option value="T-110">T-110</option>
              </select>
            </div>
            
            <div className="mb-6">
              <label style={{ display: 'block', fontSize: '13px', fontWeight: 600, color: 'var(--color-text-muted)', marginBottom: '8px' }}>
                Anomaly Scenario
              </label>
              <select value={scenario} onChange={e => setScenario(e.target.value)} style={{ width: '100%', padding: '8px 12px', border: '1px solid var(--color-border)', borderRadius: '4px' }}>
                <option value="normal">Normal Operation</option>
                <option value="slow_leak">Slow Leak (Bottom Valve)</option>
                <option value="water_ingress">Water Ingress (Roof Drain)</option>
                <option value="sensor_drift">Level Sensor Drift</option>
                <option value="theft">Unauthorized Withdrawal</option>
              </select>
            </div>
            
            <button className="btn btn-primary w-full" onClick={handleSaveScenario}>APPLY SCENARIO</button>
          </div>

          <div className="card">
            <h3 className="card-title mb-4">SYSTEM INFO</h3>
            <div className="grid grid-cols-2" style={{ gap: '16px' }}>
              <div>
                <div style={{ fontSize: '11px', color: 'var(--color-text-muted)', fontWeight: 600 }}>Model Version</div>
                <div style={{ fontSize: '14px', fontWeight: 500 }}>V7.0</div>
              </div>
              <div>
                <div style={{ fontSize: '11px', color: 'var(--color-text-muted)', fontWeight: 600 }}>Dataset Version</div>
                <div style={{ fontSize: '14px', fontWeight: 500 }}>Baseline_2025_05</div>
              </div>
              <div>
                <div style={{ fontSize: '11px', color: 'var(--color-text-muted)', fontWeight: 600 }}>Last Model Training</div>
                <div style={{ fontSize: '14px', fontWeight: 500 }}>20 May 2025</div>
              </div>
              <div>
                <div style={{ fontSize: '11px', color: 'var(--color-text-muted)', fontWeight: 600 }}>ZEDEDA Status</div>
                <div style={{ fontSize: '14px', fontWeight: 500, color: 'var(--color-success)' }}>ONLINE</div>
              </div>
            </div>
          </div>
          
        </div>
      </div>
    </div>
  );
}
