import React from 'react';
import { NavLink } from 'react-router-dom';
import { LayoutDashboard, ShieldAlert, Server, Bell, PlaySquare } from 'lucide-react';

export const Sidebar: React.FC = () => {
  const navItems = [
    { to: '/', label: 'Dashboard', icon: LayoutDashboard },
    { to: '/events', label: 'Security Events', icon: ShieldAlert },
    { to: '/alerts', label: 'Alerts', icon: Bell },
    { to: '/devices', label: 'OT Devices', icon: Server },
    { to: '/simulation', label: 'Simulation Control', icon: PlaySquare },
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
              })}
            >
              <Icon size={18} />
              <span>{item.label}</span>
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
