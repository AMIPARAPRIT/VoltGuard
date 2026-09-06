import React from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';

interface PaginationProps {
  page: number;
  pageSize: number;
  total: number;
  hasNext: boolean;
  onPageChange: (page: number) => void;
}

export const Pagination: React.FC<PaginationProps> = ({ page, pageSize, total, hasNext, onPageChange }) => {
  const start = (page - 1) * pageSize + 1;
  const end = Math.min(page * pageSize, total);

  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '1rem',
        borderTop: '1px solid var(--border-color)',
        backgroundColor: 'var(--bg-secondary)',
        borderBottomLeftRadius: '6px',
        borderBottomRightRadius: '6px',
      }}
    >
      <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
        Showing <span style={{ color: 'var(--text-primary)', fontWeight: 600 }}>{total === 0 ? 0 : start}</span> to <span style={{ color: 'var(--text-primary)', fontWeight: 600 }}>{end}</span> of <span style={{ color: 'var(--text-primary)', fontWeight: 600 }}>{total}</span> entries
      </div>
      
      <div style={{ display: 'flex', gap: '0.5rem' }}>
        <button
          onClick={() => onPageChange(page - 1)}
          disabled={page === 1}
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '0.4rem 0.75rem',
            backgroundColor: page === 1 ? 'transparent' : 'var(--bg-primary)',
            border: `1px solid ${page === 1 ? 'transparent' : 'var(--border-color)'}`,
            borderRadius: '4px',
            color: page === 1 ? 'var(--text-muted)' : 'var(--text-primary)',
            cursor: page === 1 ? 'not-allowed' : 'pointer',
            fontSize: '0.85rem',
          }}
        >
          <ChevronLeft size={16} /> Prev
        </button>
        <button
          onClick={() => onPageChange(page + 1)}
          disabled={!hasNext}
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '0.4rem 0.75rem',
            backgroundColor: !hasNext ? 'transparent' : 'var(--bg-primary)',
            border: `1px solid ${!hasNext ? 'transparent' : 'var(--border-color)'}`,
            borderRadius: '4px',
            color: !hasNext ? 'var(--text-muted)' : 'var(--text-primary)',
            cursor: !hasNext ? 'not-allowed' : 'pointer',
            fontSize: '0.85rem',
          }}
        >
          Next <ChevronRight size={16} />
        </button>
      </div>
    </div>
  );
};
