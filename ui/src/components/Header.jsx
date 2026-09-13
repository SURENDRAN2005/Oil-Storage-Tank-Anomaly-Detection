import React from 'react';
import { Bell, User } from 'lucide-react';
import { useLocation } from 'react-router-dom';
import './Header.css';

const pageTitles = {
  '/dashboard': { title: 'Dashboard', subtitle: 'Real-time overview of storage tank conditions' },
  '/tanks': { title: 'Storage Tanks', subtitle: 'All monitored storage tanks' },
  '/alerts': { title: 'Alerts', subtitle: 'Active and historical tank alerts' },
  '/analytics': { title: 'Analytics', subtitle: 'Model performance and tank insights' },
  '/settings': { title: 'Settings', subtitle: 'System configuration' },
};

export default function Header() {
  const location = useLocation();
  const currentPath = Object.keys(pageTitles).find(path => location.pathname.startsWith(path)) || '/dashboard';
  
  // Custom logic for tank details and alert details if needed
  let title = pageTitles[currentPath].title;
  let subtitle = pageTitles[currentPath].subtitle;

  if (location.pathname.startsWith('/tanks/') && location.pathname.length > 7) {
    title = 'Tank Details';
    subtitle = 'Detailed view of tank parameters and residual trend';
  } else if (location.pathname.startsWith('/alerts/') && location.pathname.length > 8) {
    title = 'Alert Details';
    subtitle = 'Investigation and action panel';
  }

  return (
    <div className="header">
      <div className="header-titles">
        <h1 className="header-title">{title}</h1>
        <div className="header-subtitle">{subtitle}</div>
      </div>
      <div className="header-actions">

        <button className="icon-btn">
          <Bell size={20} />
        </button>
        <button className="icon-btn">
          <User size={20} />
        </button>
      </div>
    </div>
  );
}
