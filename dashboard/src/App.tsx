import React, { useEffect, useState } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Header } from './components/layout/Header';
import { Sidebar } from './components/layout/Sidebar';
import { Dashboard } from './pages/Dashboard';
import { EventsPage } from './pages/Events';
import { AlertsPage } from './pages/Alerts';
import { DevicesPage } from './pages/Devices';
import { SimulationPage } from './pages/Simulation';
import { ReportsPage } from './pages/Reports';
import { ToastContainer } from './components/common/Toast';
import { SystemStatus } from './types';
import { api } from './services/api';
import { wsService } from './services/websocket';

export const App: React.FC = () => {
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null);

  useEffect(() => {
    // Check initial system status
    api.getSystemStatus()
      .then(setSystemStatus)
      .catch((err) => console.error('Failed to get system status:', err));

    // Connect WebSocket
    wsService.connect();

    return () => {
      wsService.disconnect();
    };
  }, []);

  return (
    <Router>
      <div className="app-container">
        <Header systemStatus={systemStatus} />
        <div className="main-body">
          <Sidebar />
          <main className="content-area">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/events" element={<EventsPage />} />
              <Route path="/alerts" element={<AlertsPage />} />
              <Route path="/devices" element={<DevicesPage />} />
              <Route path="/simulation" element={<SimulationPage />} />
              <Route path="/reports" element={<ReportsPage />} />
            </Routes>
          </main>
        </div>
      </div>
      {/* Global toast notification container */}
      <ToastContainer />
    </Router>
  );
};

export default App;
