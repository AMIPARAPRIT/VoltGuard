import React from 'react';
import { Search } from 'lucide-react';

interface FilterOption {
  value: string;
  label: string;
}

interface FilterDef {
  key: string;
  label: string;
  options: FilterOption[];
  value: string;
  onChange: (val: string) => void;
}

interface FilterBarProps {
  filters: FilterDef[];
  searchValue: string;
  onSearchChange: (val: string) => void;
  placeholder?: string;
}

export const FilterBar: React.FC<FilterBarProps> = ({ filters, searchValue, onSearchChange, placeholder = 'Search...' }) => {
  return (
    <div
      style={{
        display: 'flex',
        flexWrap: 'wrap',
        gap: '1rem',
        alignItems: 'center',
        padding: '1rem',
        backgroundColor: 'var(--bg-secondary)',
        borderRadius: '6px',
        border: '1px solid var(--border-color)',
        marginBottom: '1.25rem',
      }}
    >
      {filters.map((filter) => (
        <div key={filter.key} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{filter.label}:</span>
          <select
            className="scada-select"
            style={{ minWidth: '140px', padding: '0.4rem 0.75rem', fontSize: '0.85rem' }}
            value={filter.value}
            onChange={(e) => filter.onChange(e.target.value)}
          >
            {filter.options.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>
      ))}

      <div style={{ flex: 1, minWidth: '200px', display: 'flex', justifyContent: 'flex-end' }}>
        <div style={{ position: 'relative', width: '100%', maxWidth: '300px' }}>
          <div style={{ position: 'absolute', left: '10px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }}>
            <Search size={16} />
          </div>
          <input
            type="text"
            className="scada-input"
            placeholder={placeholder}
            value={searchValue}
            onChange={(e) => onSearchChange(e.target.value)}
            style={{ width: '100%', paddingLeft: '32px', padding: '0.4rem 0.75rem 0.4rem 32px', fontSize: '0.85rem' }}
          />
        </div>
      </div>
    </div>
  );
};
