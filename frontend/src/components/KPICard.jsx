import React from 'react';

export default function KPICard({ label, value, subtext, icon: Icon, isCurrency = false }) {
  const displayValue = isCurrency
    ? new Intl.NumberFormat('en-IN', {
        style: 'currency',
        currency: 'INR',
        maximumFractionDigits: 0,
      }).format(value || 0)
    : (value ?? 0).toLocaleString();

  return (
    <div className="kpi-card">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <div className="kpi-label">{label}</div>
          <div className="kpi-value">{displayValue}</div>
        </div>
        {Icon && (
          <div style={{ color: 'var(--text-muted)', background: '#f8fafc', padding: 8, borderRadius: 6 }}>
            <Icon size={18} />
          </div>
        )}
      </div>
      {subtext && <div className="kpi-sub">{subtext}</div>}
    </div>
  );
}
