import React from 'react';
import './TankGraphic.css';

export default function TankGraphic({ level, status }) {
  const isAnomaly = status === 'ANOMALY';
  const fillColor = isAnomaly ? 'var(--color-danger)' : 'var(--color-success)';
  const clampedLevel = Math.max(0, Math.min(100, level));
  
  return (
    <div className="tank-graphic">
      <div className="tank-graphic-outline">
        <div 
          className="tank-graphic-fill" 
          style={{ 
            height: `${clampedLevel}%`,
            backgroundColor: fillColor 
          }} 
        />
        {/* Draw lines to mimic cylinder ribs */}
        <div className="tank-graphic-rib" style={{ top: '25%' }} />
        <div className="tank-graphic-rib" style={{ top: '50%' }} />
        <div className="tank-graphic-rib" style={{ top: '75%' }} />
      </div>
    </div>
  );
}
