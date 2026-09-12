export const fetchTanks = async () => {
  const res = await fetch('/api/tanks');
  if (!res.ok) throw new Error('Failed to fetch tanks');
  return res.json();
};

export const fetchTankDetail = async (tankId) => {
  const res = await fetch(`/api/tanks/${tankId}`);
  if (!res.ok) throw new Error('Failed to fetch tank detail');
  return res.json();
};

export const fetchTankHistory = async (tankId, limit = 60) => {
  const res = await fetch(`/api/tanks/${tankId}/history?limit=${limit}`);
  if (!res.ok) throw new Error('Failed to fetch tank history');
  return res.json();
};

export const fetchAlerts = async (status = '') => {
  const url = status ? `/api/alerts?status=${status}` : '/api/alerts';
  const res = await fetch(url);
  if (!res.ok) throw new Error('Failed to fetch alerts');
  return res.json();
};

export const updateAlertStatus = async (alertId, status) => {
  const res = await fetch(`/api/alerts/${alertId}/status`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ status })
  });
  if (!res.ok) throw new Error('Failed to update alert');
  return res.json();
};

export const fetchSimStatus = async () => {
  const res = await fetch('/api/simulator/status');
  if (!res.ok) throw new Error('Failed to fetch simulator status');
  return res.json();
};

export const updateSimScenario = async (scenario, target_tank) => {
  const res = await fetch('/api/simulator/scenario', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ scenario, target_tank })
  });
  if (!res.ok) throw new Error('Failed to update scenario');
  return res.json();
};
