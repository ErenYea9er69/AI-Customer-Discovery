import React from 'react';
import {
  LayoutDashboard,
  Building2,
  Compass,
  Inbox,
  MessageSquare,
  BarChart3,
  Settings,
  ShieldAlert,
  Flame,
} from 'lucide-react';

interface SidebarProps {
  currentTab: string;
  onSelectTab: (tab: string) => void;
  leadCounts: Record<string, number>;
  emergencyStop: boolean;
}

export const Sidebar: React.FC<SidebarProps> = ({
  currentTab,
  onSelectTab,
  leadCounts,
  emergencyStop,
}) => {
  const navItems = [
    { id: 'overview', label: 'Overview', icon: LayoutDashboard },
    { id: 'profile', label: 'Business Profile', icon: Building2 },
    { id: 'discovery', label: 'Discovery Engine', icon: Compass },
    {
      id: 'leads',
      label: 'Leads Inbox',
      icon: Inbox,
      badge: leadCounts.total ? leadCounts.total.toString() : undefined,
      badgeColor: leadCounts.high_potential > 0 ? '#10b981' : '#64748b',
    },
    { id: 'reply_studio', label: 'Reply Studio', icon: MessageSquare },
    { id: 'analytics', label: 'Customer Insights', icon: BarChart3 },
    { id: 'settings', label: 'Settings & Safety', icon: Settings },
  ];

  return (
    <aside className="sidebar">
      {/* Brand Header */}
      <div style={{ padding: '1rem', borderBottom: '1px solid var(--border)', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
        <div style={{ width: '28px', height: '28px', borderRadius: '6px', background: 'var(--primary)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', fontWeight: 'bold' }}>
          <Flame size={18} />
        </div>
        <div>
          <div style={{ fontWeight: 700, fontSize: '0.875rem', letterSpacing: '-0.01em', color: '#0f172a' }}>AgentReach</div>
          <div style={{ fontSize: '0.6875rem', color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.04em' }}>Customer Discovery</div>
        </div>
      </div>

      {/* Emergency Stop Banner if active */}
      {emergencyStop && (
        <div style={{ margin: '0.5rem', padding: '0.5rem', background: '#fef2f2', border: '1px solid #fecaca', borderRadius: '4px', display: 'flex', alignItems: 'center', gap: '0.375rem', color: '#b91c1c', fontSize: '0.6875rem', fontWeight: 600 }}>
          <ShieldAlert size={14} />
          <span>STOP ACTIVE</span>
        </div>
      )}

      {/* Nav List */}
      <nav style={{ padding: '0.75rem 0.5rem', display: 'flex', flexDirection: 'column', gap: '0.25rem', flex: 1 }}>
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = currentTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onSelectTab(item.id)}
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                width: '100%',
                padding: '0.5rem 0.75rem',
                borderRadius: 'var(--radius)',
                border: 'none',
                background: isActive ? 'var(--primary-light)' : 'transparent',
                color: isActive ? 'var(--primary)' : '#475569',
                fontWeight: isActive ? 600 : 500,
                fontSize: '0.8125rem',
                cursor: 'pointer',
                textAlign: 'left',
                transition: 'all 0.15s ease',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.625rem' }}>
                <Icon size={16} color={isActive ? 'var(--primary)' : '#64748b'} />
                <span>{item.label}</span>
              </div>
              {item.badge && (
                <span
                  style={{
                    fontSize: '0.6875rem',
                    fontWeight: 700,
                    padding: '0.1rem 0.35rem',
                    borderRadius: '4px',
                    background: item.badgeColor || '#e2e8f0',
                    color: '#ffffff',
                  }}
                >
                  {item.badge}
                </span>
              )}
            </button>
          );
        })}
      </nav>

      {/* Footer Info */}
      <div style={{ padding: '0.75rem', borderTop: '1px solid var(--border)', fontSize: '0.6875rem', color: '#94a3b8', display: 'flex', justifyContent: 'space-between' }}>
        <span>Engine v2.0.0</span>
        <span style={{ color: '#10b981', display: 'flex', alignItems: 'center', gap: '4px' }}>
          <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#10b981' }}></span>
          Ready
        </span>
      </div>
    </aside>
  );
};

