import React from 'react';
import { X, CheckCircle, AlertTriangle, Info, XCircle } from 'lucide-react';
import { useToast, toast as toastManager } from '../../services/toast';

export const ToastContainer: React.FC = () => {
  const toasts = useToast();

  return (
    <div
      style={{
        position: 'fixed',
        bottom: '20px',
        right: '20px',
        display: 'flex',
        flexDirection: 'column',
        gap: '10px',
        zIndex: 9999,
      }}
    >
      {toasts.map((toast) => (
        <ToastItem key={toast.id} toast={toast} onClose={() => toastManager.remove(toast.id)} />
      ))}
    </div>
  );
};

const ToastItem: React.FC<{ toast: any; onClose: () => void }> = ({ toast, onClose }) => {
  const colors = {
    success: 'var(--color-safe)',
    error: 'var(--color-catastrophic)',
    warning: 'var(--color-warning)',
    info: 'var(--color-accent)',
  };

  const icons = {
    success: <CheckCircle size={18} color={colors.success} />,
    error: <XCircle size={18} color={colors.error} />,
    warning: <AlertTriangle size={18} color={colors.warning} />,
    info: <Info size={18} color={colors.info} />,
  };

  return (
    <div
      style={{
        backgroundColor: 'var(--bg-secondary)',
        borderLeft: `4px solid ${colors[toast.type as keyof typeof colors]}`,
        borderRadius: '4px',
        padding: '12px 16px',
        minWidth: '280px',
        maxWidth: '400px',
        boxShadow: '0 4px 12px rgba(0,0,0,0.5)',
        display: 'flex',
        alignItems: 'flex-start',
        gap: '12px',
        animation: 'slideIn 0.2s ease-out forwards',
      }}
    >
      <div style={{ marginTop: '2px' }}>{icons[toast.type as keyof typeof icons]}</div>
      <div style={{ flex: 1 }}>
        <div style={{ fontWeight: 600, fontSize: '0.9rem', color: 'var(--text-primary)' }}>{toast.title}</div>
        {toast.message && (
          <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '4px' }}>
            {toast.message}
          </div>
        )}
      </div>
      <button
        onClick={onClose}
        style={{
          background: 'none',
          border: 'none',
          color: 'var(--text-muted)',
          cursor: 'pointer',
          padding: '2px',
        }}
      >
        <X size={14} />
      </button>
    </div>
  );
};
