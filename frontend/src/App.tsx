import React, { useState, useEffect } from 'react';
import { Sidebar } from './components/Sidebar';
import { OverviewView } from './components/OverviewView';
import { ProfileView } from './components/ProfileView';
import { DiscoveryView } from './components/DiscoveryView';
import { LeadsView } from './components/LeadsView';
import { ReplyStudioView } from './components/ReplyStudioView';
import { AnalyticsView } from './components/AnalyticsView';
import { SettingsView } from './components/SettingsView';
import type { BusinessProfile, LeadQualification } from './types';
import { api } from './api';

export const App: React.FC = () => {
  const [currentTab, setCurrentTab] = useState<string>('overview');
  const [profile, setProfile] = useState<BusinessProfile | null>(null);
  const [leads, setLeads] = useState<LeadQualification[]>([]);
  const [leadCounts, setLeadCounts] = useState<Record<string, number>>({});
  const [emergencyStop, setEmergencyStop] = useState<boolean>(false);
  const [replyStudioLeadId, setReplyStudioLeadId] = useState<string | undefined>(undefined);

  const refreshData = async () => {
    try {
      const [prof, leadList, counts, settingsData] = await Promise.all([
        api.getProfile(),
        api.listLeads(),
        api.getLeadCounts(),
        api.getSettings(),
      ]);
      setProfile(prof);
      setLeads(leadList);
      setLeadCounts(counts);
      setEmergencyStop(settingsData.posting_settings?.emergency_stop || false);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    refreshData();
  }, []);

  const handleNavigate = (tab: string, leadId?: string) => {
    if (leadId) {
      setReplyStudioLeadId(leadId);
    }
    setCurrentTab(tab);
  };

  return (
    <div className="app-container">
      {/* Precision Navigation Sidebar */}
      <Sidebar
        currentTab={currentTab}
        onSelectTab={setCurrentTab}
        leadCounts={leadCounts}
        emergencyStop={emergencyStop}
      />

      {/* Main Content Pane */}
      <main className="main-content">
        {/* Compact App Header */}
        <header
          style={{
            height: '48px',
            background: '#ffffff',
            borderBottom: '1px solid var(--border)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '0 1.5rem',
            flexShrink: 0,
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <span style={{ fontWeight: 700, fontSize: '0.9375rem', color: '#0f172a' }}>
              {currentTab === 'overview' && 'Dashboard Overview'}
              {currentTab === 'profile' && 'Business Profile & ICP Model'}
              {currentTab === 'discovery' && 'Customer Discovery Engine'}
              {currentTab === 'leads' && 'Qualified Opportunities Inbox'}
              {currentTab === 'reply_studio' && 'AI Reply Studio'}
              {currentTab === 'analytics' && 'Customer Pain Analytics'}
              {currentTab === 'settings' && 'Platform Settings & Guardrails'}
            </span>

            {profile && (
              <span
                style={{
                  fontSize: '0.6875rem',
                  fontWeight: 600,
                  padding: '0.125rem 0.5rem',
                  borderRadius: '4px',
                  background: 'var(--primary-light)',
                  color: 'var(--primary)',
                }}
              >
                {profile.name}
              </span>
            )}
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', fontSize: '0.75rem', color: '#64748b' }}>
            <span>
              Total Leads: <strong style={{ color: '#0f172a' }}>{leadCounts.total || 0}</strong>
            </span>
            <span>
              High Potential: <strong style={{ color: '#10b981' }}>{leadCounts.high_potential || 0}</strong>
            </span>
          </div>
        </header>

        {/* View Switcher */}
        <div style={{ flex: 1, overflowY: 'auto' }}>
          {currentTab === 'overview' && (
            <OverviewView
              profile={profile}
              leads={leads}
              leadCounts={leadCounts}
              onNavigate={handleNavigate}
              onLaunchCampaign={() => setCurrentTab('discovery')}
            />
          )}

          {currentTab === 'profile' && (
            <ProfileView
              profile={profile}
              onProfileUpdated={(updated) => {
                setProfile(updated);
                refreshData();
              }}
            />
          )}

          {currentTab === 'discovery' && (
            <DiscoveryView
              profile={profile}
              onCampaignFinished={refreshData}
            />
          )}

          {currentTab === 'leads' && (
            <LeadsView
              leads={leads}
              onOpenReplyStudio={(id) => handleNavigate('reply_studio', id)}
            />
          )}

          {currentTab === 'reply_studio' && (
            <ReplyStudioView
              initialLeadId={replyStudioLeadId}
              leads={leads}
            />
          )}

          {currentTab === 'analytics' && <AnalyticsView />}

          {currentTab === 'settings' && <SettingsView />}
        </div>
      </main>
    </div>
  );
};

export default App;
