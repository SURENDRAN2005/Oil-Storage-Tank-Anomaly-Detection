import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import StorageTanks from './pages/StorageTanks';
import TankDetails from './pages/TankDetails';
import Alerts from './pages/Alerts';
import AlertDetails from './pages/AlertDetails';
import Analytics from './pages/Analytics';
import Settings from './pages/Settings';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="tanks" element={<StorageTanks />} />
          <Route path="tanks/:tankId" element={<TankDetails />} />
          <Route path="alerts" element={<Alerts />} />
          <Route path="alerts/:alertId" element={<AlertDetails />} />
          <Route path="analytics" element={<Analytics />} />
          <Route path="settings" element={<Settings />} />
        </Route>
      </Routes>
    </Router>
  );
}

export default App;
