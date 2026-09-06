import React, { useEffect, useState } from 'react';
import { NavLink } from 'react-router-dom';
import { LayoutDashboard, ShieldAlert, Server, Bell, PlaySquare } from 'lucide-react';
import { api } from '../../services/api';
import { useWebSocketAlerts } from '../../hooks/useWebSocketAlerts';

export const Sidebar: React.FC = () => {
  const [activeAlertCount, setActiveAlertCount] = useState<number>(0);

  // Initial load of alert summary
  const fetchSummary = () => {
    api.getAlertSummary()
      .then(s => setActiveAlertCount(s.active))
      .catch(() => {});
  };

  useEffect(() => {
    fetchSummary();
    // Poll every 30s as backstop
    const interval = setInterval(fetchSummary, 30000);
    return () => clearInterval(interval);
  }, []);

  // Increment badge count in real-time when a new alert arrives via WebSocket
  useWebSocketAlerts({
    onNewAlert: () => {
      setActiveAlertCount(prev => prev + 1);
    },
  });

  const navItems = [
    { to: '/', label: 'Dashboard', icon: LayoutDashboard, badge: null, exact: true },
    { to: '/events', label: 'Security Events', icon: ShieldAlert, badge: null, exact: false },
    { to: '/alerts', label: 'Alerts', icon: Bell, badge: activeAlertCount > 0 ? activeAlertCount : null, exact: false },
    { to: '/devices', label: 'OT Devices', icon: Server, badge: null, exact: false },
    { to: '/simulation', label: 'Simulation Control', icon: PlaySquare, badge: null, exact: false },
  ];

  return (
    <aside
      style={{
        width: '220px',
        backgroundColor: 'var(--bg-secondary)',
        borderRight: '1px solid var(--border-color)',
        display: 'flex',
        flexDirection: 'column',
        padding: '1rem 0.75rem',
      }}
    >
      <nav style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.exact}
              style={({ isActive }) => ({
                display: 'flex',
                alignItems: 'center',
                gap: '0.75rem',
                padding: '0.65rem 0.85rem',
                borderRadius: 'var(--radius-sm)',
                color: isActive ? '#ffffff' : 'var(--text-secondary)',
                backgroundColor: isActive ? 'var(--bg-card-hover)' : 'transparent',
                fontWeight: isActive ? 600 : 400,
                textDecoration: 'none',
                fontSize: '0.875rem',
                transition: 'all 0.15s ease',
                borderLeft: isActive ? '3px solid var(--color-accent)' : '3px solid transparent',
                position: 'relative',
              })}
            >
              <Icon size={18} />
              <span style={{ flex: 1 }}>{item.label}</span>
              {item.badge != null && (
                <span
                  style={{
                    backgroundColor: 'var(--color-catastrophic)',
                    color: '#fff',
                    fontSize: '0.65rem',
                    fontWeight: 700,
                    borderRadius: '999px',
                    padding: '0.1rem 0.42rem',
                    minWidth: '18px',
                    textAlign: 'center',
                    lineHeight: 1.4,
                    animation: 'pulse 2s infinite',
                  }}
                >
                  {item.badge > 99 ? '99+' : item.badge}
                </span>
              )}
            </NavLink>
          );
        })}
      </nav>

      <div style={{ marginTop: 'auto', paddingTop: '1rem', borderTop: '1px solid var(--border-color)', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
        <div>VOLTGUARD v0.5.0</div>
        <div>PHYSICS-AWARE IDS/IPS</div>
      </div>
    </aside>
  );
};
