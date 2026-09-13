import React, { useState, useEffect } from 'react';
import { NavLink } from 'react-router-dom';
import { LayoutDashboard, Database, AlertTriangle, BarChart2, Settings } from 'lucide-react';
import './Sidebar.css';

// Global shared audio context
let audioCtx = null;
let unlocked = false;

const initAudio = () => {
  if (unlocked) return;
  try {
    const AudioContext = window.AudioContext || window.webkitAudioContext;
    if (AudioContext && !audioCtx) {
      audioCtx = new AudioContext();
    }
    if (audioCtx && audioCtx.state === 'suspended') {
      audioCtx.resume();
    }
    // Play a silent sound to properly unlock Web Audio API (especially on Safari/mobile)
    if (audioCtx) {
      const osc = audioCtx.createOscillator();
      const gain = audioCtx.createGain();
      gain.gain.value = 0; // silent
      osc.connect(gain);
      gain.connect(audioCtx.destination);
      osc.start();
      osc.stop(audioCtx.currentTime + 0.1);
      unlocked = true;
    }
  } catch (e) {
    console.error("Audio unlock failed", e);
  }
};

// Listen for first interaction to unlock audio
if (typeof window !== 'undefined') {
  window.addEventListener('click', initAudio, { once: true });
  window.addEventListener('keydown', initAudio, { once: true });
}

const playBeep = () => {
  try {
    if (!unlocked) {
      console.warn("Audio play blocked: waiting for user interaction (click anywhere).");
      return;
    }
    if (audioCtx && audioCtx.state === 'suspended') {
      audioCtx.resume();
    }
    if (!audioCtx) return;
    
    const osc = audioCtx.createOscillator();
    const gainNode = audioCtx.createGain();
    
    osc.type = 'square';
    osc.frequency.setValueAtTime(800, audioCtx.currentTime);
    osc.frequency.setValueAtTime(1000, audioCtx.currentTime + 0.15);
    
    gainNode.gain.setValueAtTime(1.0, audioCtx.currentTime);
    
    osc.connect(gainNode);
    gainNode.connect(audioCtx.destination);
    
    osc.start();
    osc.stop(audioCtx.currentTime + 0.4);
  } catch (e) {
    console.error("Beep failed:", e);
  }
};

let alarmInterval = null;

export const startAlarm = () => {
  if (alarmInterval) return; // already playing
  alarmInterval = setInterval(() => {
    playBeep();
  }, 1000); // Beep every 1 second
};

export const stopAlarm = () => {
  if (alarmInterval) {
    clearInterval(alarmInterval);
    alarmInterval = null;
  }
};

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
    const fetchData = async () => {
      try {
        const [alertsRes, tanksRes] = await Promise.all([
          fetch('/api/alerts?status=ACTIVE'),
          fetch('/api/tanks')
        ]);
        
        if (alertsRes.ok) {
          const alertsData = await alertsRes.json();
          setActiveAlertsCount(alertsData.length);
        }
        
        if (tanksRes.ok) {
          const tanksData = await tanksRes.json();
          const anomaliesCount = tanksData.filter(t => t.status === 'ANOMALY').length;
          
          if (anomaliesCount > 0) {
            startAlarm();
          } else {
            stopAlarm();
          }
        }
      } catch (err) {
        console.error('Error fetching data for sidebar:', err);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 2000);
    return () => {
      clearInterval(interval);
      stopAlarm();
    };
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


    </div>
  );
}
