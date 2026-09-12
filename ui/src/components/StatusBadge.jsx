import React from 'react';

export default function StatusBadge({ status }) {
  let badgeClass = 'badge-normal';
  
  const s = status ? status.toUpperCase() : 'UNKNOWN';
  
  if (s === 'NORMAL' || s === 'RESOLVED') {
    badgeClass = 'badge-normal';
  } else if (s === 'ANOMALY' || s === 'ACTIVE' || s === 'CRITICAL') {
    badgeClass = 'badge-anomaly';
  } else if (s === 'WARNING' || s === 'ACKNOWLEDGED') {
    badgeClass = 'badge-warning';
  }
  
  return (
    <span className={`badge ${badgeClass}`}>
      {s}
    </span>
  );
}
