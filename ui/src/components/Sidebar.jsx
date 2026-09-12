import React, { useState, useEffect } from 'react';
import { NavLink } from 'react-router-dom';
import { LayoutDashboard, Database, AlertTriangle, BarChart2, Settings, Server, Wifi } from 'lucide-react';
import './Sidebar.css';

export default function Sidebar() {
  const navItems = [
    { name: 'Dashboard', path: '/dashboard', icon: LayoutDashboard },
    { name: 'Tanks', path: '/tanks', icon: Database },
    { name: 'Alerts', path: '/alerts', icon: AlertTriangle },
    { name: 'Analytics', path: '/analytics', icon: BarChart2 },
    { name: 'Settings', path: '/settings', icon: Settings },
  ];

  const [activeAlertsCount, setActiveAlertsCount] = useState(0);

  useEffect(() => {
    const fetchAlertsCount = async () => {
      try {
        const response = await fetch('/api/alerts?status=ACTIVE');
        if (response.ok) {
          const data = await response.json();
          setActiveAlertsCount(data.length);
        }
      } catch (err) {
        console.error('Error fetching alerts count for sidebar:', err);
      }
    };

    fetchAlertsCount();
    const interval = setInterval(fetchAlertsCount, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="sidebar">
      <div className="sidebar-brand">
        <h3>OIL</h3>
        <p>TANK MONITORING</p>
      </div>

      <nav className="sidebar-nav">
        {navItems.map((item) => (
          <NavLink
            key={item.name}
            to={item.path}
            className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
          >
            <item.icon size={20} className="nav-icon" />
            <span>{item.name}</span>
            {item.name === 'Alerts' && activeAlertsCount > 0 && (
              <span className="nav-badge">{activeAlertsCount}</span>
            )}
          </NavLink>
        ))}
      </nav>

      <div className="sidebar-footer">
        <div className="status-item">
          <Server size={14} className="status-icon" />
          <span>ZEDEDA EDGE</span>
          <span className="status-dot green"></span>
          <span className="status-text">ONLINE</span>
        </div>
        <div className="status-item">
          <Wifi size={14} className="status-icon" />
          <span>MQTT</span>
          <span className="status-dot green"></span>
          <span className="status-text">CONNECTED</span>
        </div>
      </div>
    </div>
  );
}
