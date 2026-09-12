// Navigation Logic
function navigateTo(pageId) {
    document.querySelectorAll('.page-container').forEach(el => el.classList.remove('active'));
    document.getElementById('page-' + pageId).classList.add('active');
    
    document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
    if (event && event.currentTarget) {
        event.currentTarget.classList.add('active');
    }
}

// Global State
const state = {
    tanks: {},
    alerts: []
};

let residualChart = null;
let currentDetailTankId = null;

// Fetch Live Data
async function fetchTelemetry() {
    try {
        const tanksRes = await fetch('/api/tanks');
        const tanksData = await tanksRes.json();
        
        const alertsRes = await fetch('/api/alerts');
        state.alerts = await alertsRes.json();
        
        // Convert array to object
        tanksData.forEach(t => {
            state.tanks[t.tank_id] = t;
        });
        
        renderDashboard();
        
        // Refresh details page if active
        if(document.getElementById('page-details').classList.contains('active') && currentDetailTankId) {
            refreshTankDetails(currentDetailTankId);
        }
        
    } catch (err) {
        console.error("API Error:", err);
    }
}

// Render logic
function renderDashboard() {
    const grid = document.getElementById('dashboard-tank-grid');
    const table = document.getElementById('tanks-table').querySelector('tbody');
    
    if(!grid || !table) return;
    
    grid.innerHTML = '';
    table.innerHTML = '';
    
    let anomalies = 0;
    
    Object.values(state.tanks).sort((a,b) => a.tank_id.localeCompare(b.tank_id)).forEach(t => {
        if(t.status === 'ANOMALY') anomalies++;
        
        const statusClass = t.status === 'ANOMALY' ? 'status-anomaly' : 'status-normal';
        const level = t.level_m || 0;
        
        // We divide level_m by an assumed max level (say 20m) for a % roughly, or just show m
        const levelPct = (level / 20.0) * 100;
        
        const maxFlow = Math.max(t.inflow_l_min, t.outflow_l_min);
        const residual = t.residual_l || 0;
        
        // Dashboard Card
        const cardHtml = `
            <div class="card tank-card" onclick="openTankDetails('${t.tank_id}')">
                <div class="tank-card-header">
                    <h3 class="card-title" style="color: var(--text-main);">${t.tank_id}</h3>
                    <div class="status-text ${statusClass}">${t.status}</div>
                </div>
                <div class="tank-card-stats">
                    <div><div class="stat-label">Level</div><div class="stat-value">${levelPct.toFixed(1)}%</div></div>
                    <div><div class="stat-label">Flow</div><div class="stat-value">${maxFlow.toFixed(0)} L/m</div></div>
                    <div style="grid-column: span 2; margin-top: 4px;">
                        <div class="stat-label">Residual</div>
                        <div class="stat-value">${residual > 0 ? '+' : ''}${residual.toFixed(1)} L</div>
                    </div>
                </div>
            </div>
        `;
        grid.innerHTML += cardHtml;
        
        // Tanks Table Row
        const trHtml = `
            <tr class="clickable" onclick="openTankDetails('${t.tank_id}')">
                <td style="font-weight: 600;">${t.tank_id}</td>
                <td class="${statusClass} status-text">${t.status}</td>
                <td>${levelPct.toFixed(1)}%</td>
                <td>${(t.temperature_c || 0).toFixed(1)}°C</td>
                <td>${maxFlow.toFixed(0)} L/m</td>
                <td>${(t.pressure_bar || 0).toFixed(2)} bar</td>
                <td>${residual > 0 ? '+' : ''}${residual.toFixed(1)} L</td>
            </tr>
        `;
        table.innerHTML += trHtml;
    });
    
    document.getElementById('kpi-normal').innerText = Object.keys(state.tanks).length - anomalies;
    document.getElementById('kpi-anomalies').innerText = anomalies;
    
    const activeAlerts = state.alerts.filter(a => a.status === 'ACTIVE');
    document.getElementById('kpi-alerts').innerText = activeAlerts.length;
    
    renderAlerts();
}

function renderAlerts() {
    const dashAlerts = document.getElementById('dashboard-alerts-table')?.querySelector('tbody');
    const pageAlerts = document.getElementById('alerts-active-table')?.querySelector('tbody');
    const histAlerts = document.getElementById('alerts-history-table')?.querySelector('tbody');
    
    if(!dashAlerts || !pageAlerts || !histAlerts) return;
    
    dashAlerts.innerHTML = '';
    pageAlerts.innerHTML = '';
    histAlerts.innerHTML = '';
    
    const activeAlerts = state.alerts.filter(a => a.status === 'ACTIVE' || a.status === 'ACKNOWLEDGED');
    const historicalAlerts = state.alerts.filter(a => a.status === 'RESOLVED');
    
    activeAlerts.slice(0,5).forEach(a => {
        const actionHtml = `
            <button onclick="event.stopPropagation(); updateAlertStatus('${a.alert_id}', 'ACKNOWLEDGED')" style="padding:4px 8px; font-size:12px; margin-right:4px;" ${a.status === 'ACKNOWLEDGED' ? 'disabled' : ''}>Ack</button>
            <button onclick="event.stopPropagation(); updateAlertStatus('${a.alert_id}', 'RESOLVED')" style="padding:4px 8px; font-size:12px;">Resolve</button>
        `;
        const severityClass = a.status === 'ACKNOWLEDGED' ? 'status-text' : 'status-anomaly';
        dashAlerts.innerHTML += `
            <tr onclick="openTankDetails('${a.tank_id}')" class="clickable">
                <td style="font-weight:600;">${a.tank_id}</td>
                <td>${a.event}</td>
                <td class="${severityClass}">${a.severity}</td>
                <td>${new Date(a.timestamp).toLocaleTimeString()}</td>
                <td>${actionHtml}</td>
            </tr>
        `;
    });
    
    activeAlerts.forEach(a => {
        const actionHtml = `
            <button onclick="event.stopPropagation(); updateAlertStatus('${a.alert_id}', 'ACKNOWLEDGED')" style="padding:4px 8px; font-size:12px; margin-right:4px;" ${a.status === 'ACKNOWLEDGED' ? 'disabled' : ''}>Acknowledge</button>
            <button onclick="event.stopPropagation(); updateAlertStatus('${a.alert_id}', 'RESOLVED')" style="padding:4px 8px; font-size:12px;">Resolve</button>
        `;
        const severityClass = a.status === 'ACKNOWLEDGED' ? 'status-text' : 'status-anomaly';
        const statusClass = a.status === 'ACKNOWLEDGED' ? 'status-text' : 'status-anomaly';
        pageAlerts.innerHTML += `
            <tr onclick="openTankDetails('${a.tank_id}')" class="clickable">
                <td>${new Date(a.timestamp).toLocaleTimeString()}</td>
                <td style="font-weight:600;">${a.tank_id}</td>
                <td>${a.event}</td>
                <td class="${severityClass}">${a.severity}</td>
                <td>${(a.anomaly_score || 0).toFixed(2)}</td>
                <td class="${statusClass}">${a.status}</td>
                <td>${actionHtml}</td>
            </tr>
        `;
    });
    
    historicalAlerts.slice(0,20).forEach(a => {
        histAlerts.innerHTML += `
            <tr onclick="openTankDetails('${a.tank_id}')" class="clickable">
                <td>${new Date(a.timestamp).toLocaleTimeString()}</td>
                <td style="font-weight:600;">${a.tank_id}</td>
                <td>${a.event}</td>
                <td>${a.severity}</td>
                <td class="status-normal">${a.status}</td>
                <td>${new Date(a.resolved_at).toLocaleTimeString()}</td>
            </tr>
        `;
    });
}

function openTankDetails(tankId) {
    currentDetailTankId = tankId;
    
    document.querySelectorAll('.page-container').forEach(el => el.classList.remove('active'));
    document.getElementById('page-details').classList.add('active');
    
    refreshTankDetails(tankId);
    fetchChartHistory(tankId);
}

function refreshTankDetails(tankId) {
    const t = state.tanks[tankId];
    if(!t) return;
    
    document.getElementById('detail-tank-id').innerText = t.tank_id;
    document.getElementById('detail-status').innerText = t.status;
    document.getElementById('detail-status').className = 'status-text ' + (t.status === 'ANOMALY' ? 'status-anomaly' : 'status-normal');
    
    document.getElementById('detail-score').innerText = (t.anomaly_score || 0).toFixed(2);
    
    const levelPct = ((t.level_m || 0) / 20.0) * 100;
    
    document.getElementById('detail-level').innerText = levelPct.toFixed(1) + '%';
    document.getElementById('detail-temp').innerText = (t.temperature_c || 0).toFixed(1) + ' °C';
    document.getElementById('detail-water').innerText = (t.water_interface_m || 0).toFixed(3) + ' m';
    document.getElementById('detail-pressure').innerText = (t.pressure_bar || 0).toFixed(2) + ' bar';
    
    document.getElementById('detail-inflow').innerText = (t.inflow_l_min || 0).toFixed(0) + ' L/min';
    document.getElementById('detail-outflow').innerText = (t.outflow_l_min || 0).toFixed(0) + ' L/min';
    document.getElementById('detail-netflow').innerText = (t.net_flow_l_min || 0).toFixed(0) + ' L/min';
    document.getElementById('detail-valve').innerText = t.valve_position_outlet_closed ? 'Closed' : 'Open';
    
    document.getElementById('detail-residual-text').innerText = `${t.residual_l > 0 ? '+' : ''}${(t.residual_l || 0).toFixed(1)} L`;
    document.getElementById('detail-state').innerText = t.operating_state;
    
    document.getElementById('detail-persistence').innerText = t.persistence ? `${t.persistence} intervals` : '0 intervals';
    
    if(t.status === 'ANOMALY') {
        const alert = state.alerts.find(a => a.tank_id === t.tank_id && a.status === 'ACTIVE');
        document.getElementById('detail-cause').innerText = alert ? alert.event : 'Unknown Anomaly';
        
        document.getElementById('diagnosis-card').innerHTML = `
            <div style="font-weight: 600; color: var(--color-anomaly); margin-bottom: 16px; font-size: 18px;">
                SUSPECTED: ${alert ? alert.event.toUpperCase() : 'ANOMALY'}
            </div>
            <ul class="diagnosis-list">
                <li><div class="diagnosis-label">Source:</div><div>${alert ? alert.source : 'MODEL'}</div></li>
                <li><div class="diagnosis-label">Score:</div><div style="color:red; font-weight:bold;">${(alert?.anomaly_score||0).toFixed(2)}</div></li>
                <li><div class="diagnosis-label">Evidence:</div><div>Material-balance mismatch detected by Isolation Forest</div></li>
            </ul>
        `;
    } else {
        document.getElementById('detail-cause').innerText = '';
        document.getElementById('diagnosis-card').innerHTML = `<div style="color: var(--text-secondary);">No active diagnosis. Tank behavior is normal.</div>`;
    }
}

async function fetchChartHistory(tankId) {
    try {
        const res = await fetch(`/api/tanks/${tankId}/history?limit=60`);
        const data = await res.json();
        
        // Extract residuals
        const residuals = data.map(d => d.residual_l);
        renderChart(residuals);
    } catch (err) {
        console.error("Failed to fetch history:", err);
    }
}

function renderChart(dataPoints) {
    const ctx = document.getElementById('residualChart').getContext('2d');
    
    if(residualChart) residualChart.destroy();
    
    residualChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: Array.from({length: dataPoints.length}, (_, i) => `-${dataPoints.length - i}`),
            datasets: [{
                label: 'Residual (L)',
                data: dataPoints,
                borderColor: '#3274d9',
                backgroundColor: 'rgba(50, 116, 217, 0.2)',
                borderWidth: 1.5,
                fill: true,
                pointRadius: 0,
                pointHoverRadius: 4,
                tension: 0
            }]
        },
        options: {
            animation: false,
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                intersect: false,
                mode: 'index',
            },
            plugins: { 
                legend: { display: false },
                tooltip: {
                    backgroundColor: '#181b1f',
                    titleFont: { size: 12 },
                    bodyFont: { size: 12 },
                    cornerRadius: 2
                }
            },
            scales: { 
                y: { 
                    title: { display: false },
                    grid: { color: '#e0e4e8', drawBorder: false },
                    ticks: { color: '#8e99a2', font: { size: 11 } }
                },
                x: {
                    grid: { display: false, drawBorder: false },
                    ticks: { color: '#8e99a2', font: { size: 11 }, maxTicksLimit: 10 }
                }
            }
        }
    });
}

// Start polling API every 2 seconds
setInterval(fetchTelemetry, 2000);
setInterval(() => {
    if(document.getElementById('page-details').classList.contains('active') && currentDetailTankId) {
        fetchChartHistory(currentDetailTankId);
    }
}, 2000);

async function updateAlertStatus(alertId, newStatus) {
    try {
        await fetch(`/api/alerts/${alertId}/status`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status: newStatus })
        });
        fetchTelemetry(); // Refresh data immediately
    } catch (err) {
        console.error("Failed to update alert status:", err);
    }
}

fetchTelemetry();
