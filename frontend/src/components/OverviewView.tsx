import React from 'react';
import {
  Sparkles,
  ArrowRight,
  TrendingUp,
  Target,
  MessageSquare,
  AlertCircle,
  ExternalLink,
} from 'lucide-react';
import type { BusinessProfile, LeadQualification } from '../types';

interface OverviewViewProps {
  profile: BusinessProfile | null;
  leads: LeadQualification[];
  leadCounts: Record<string, number>;
  onNavigate: (tab: string, leadId?: string) => void;
  onLaunchCampaign: () => void;
}

export const OverviewView: React.FC<OverviewViewProps> = ({
  profile,
  leads,
  leadCounts,
  onNavigate,
  onLaunchCampaign,
}) => {
  const highPotential = leads.filter((l) => l.classification === 'high_potential' || l.score >= 75);

  return (
    <div style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1.5rem', maxWidth: '1200px' }}>
      {/* Top Welcome / Profile Alert */}
      {!profile ? (
        <div className="card" style={{ background: '#fffbeb', borderColor: '#fde68a', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <AlertCircle size={20} color="#b45309" />
            <div>
              <div style={{ fontWeight: 600, color: '#92400e' }}>No Business Profile Configured</div>
              <div style={{ fontSize: '0.75rem', color: '#b45309' }}>Analyze your business website or submit a description to begin discovering qualified customers.</div>
            </div>
          </div>
          <button className="btn btn-primary" onClick={() => onNavigate('profile')}>
            Set Up Business Profile
          </button>
        </div>
      ) : !profile.confirmed ? (
        <div className="card" style={{ background: '#eff6ff', borderColor: '#bfdbfe', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <Target size={20} color="#1d4ed8" />
            <div>
              <div style={{ fontWeight: 600, color: '#1e40af' }}>Business Profile Extracted: {profile.name}</div>
              <div style={{ fontSize: '0.75rem', color: '#3b82f6' }}>Review the extracted ICP and verified facts before launching automated customer discovery.</div>
            </div>
          </div>
          <button className="btn btn-primary" onClick={() => onNavigate('profile')}>
            Review & Confirm Profile
          </button>
        </div>
      ) : null}

      {/* Main KPI Stats Row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1rem' }}>
        <div className="card">
          <div style={{ fontSize: '0.75rem', fontWeight: 600, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.025em' }}>Total Discovered</div>
          <div style={{ fontSize: '1.75rem', fontWeight: 700, color: '#0f172a', margin: '0.25rem 0' }}>
            {leadCounts.total || 0}
          </div>
          <div style={{ fontSize: '0.75rem', color: '#10b981', display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
            <TrendingUp size={14} /> Across Reddit, Web & GitHub
          </div>
        </div>

        <div className="card">
          <div style={{ fontSize: '0.75rem', fontWeight: 600, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.025em' }}>Qualified Leads</div>
          <div style={{ fontSize: '1.75rem', fontWeight: 700, color: 'var(--primary)', margin: '0.25rem 0' }}>
            {(leadCounts.high_potential || 0) + (leadCounts.relevant || 0)}
          </div>
          <div style={{ fontSize: '0.75rem', color: '#64748b' }}>Score &gt;= 50 with clear pain point</div>
        </div>

        <div className="card">
          <div style={{ fontSize: '0.75rem', fontWeight: 600, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.025em' }}>High Potential</div>
          <div style={{ fontSize: '1.75rem', fontWeight: 700, color: '#10b981', margin: '0.25rem 0' }}>
            {leadCounts.high_potential || 0}
          </div>
          <div style={{ fontSize: '0.75rem', color: '#059669' }}>High intent & urgent pain</div>
        </div>

        <div className="card">
          <div style={{ fontSize: '0.75rem', fontWeight: 600, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.025em' }}>Market Insights</div>
          <div style={{ fontSize: '1.75rem', fontWeight: 700, color: '#0284c7', margin: '0.25rem 0' }}>
            {(leadCounts.customer_insights || 0) + (leadCounts.competitor_intel || 0)}
          </div>
          <div style={{ fontSize: '0.75rem', color: '#0284c7' }}>Competitor gaps & complaints</div>
        </div>
      </div>

      {/* Quick Launch Action Banner */}
      <div className="card" style={{ background: 'linear-gradient(135deg, #4f46e5 0%, #4338ca 100%)', color: '#ffffff', padding: '1.5rem', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontWeight: 700, fontSize: '1.125rem' }}>
            <Sparkles size={20} />
            <span>Autonomous Customer Opportunity Discovery</span>
          </div>
          <p style={{ fontSize: '0.8125rem', opacity: 0.9, marginTop: '0.25rem', maxWidth: '600px' }}>
            Search online communities for founders, developers, and teams experiencing the exact problems your product solves, rank buying intent, and prepare personalized replies.
          </p>
        </div>
        <button
          className="btn"
          onClick={onLaunchCampaign}
          style={{ background: '#ffffff', color: 'var(--primary)', fontWeight: 600, padding: '0.625rem 1.25rem' }}
        >
          Launch Discovery Campaign
        </button>
      </div>

      {/* High-Potential Leads Feed */}
      <div className="card" style={{ padding: 0 }}>
        <div style={{ padding: '1rem', borderBottom: '1px solid var(--border)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div>
            <div style={{ fontWeight: 600, fontSize: '0.9375rem', color: '#0f172a' }}>Priority Opportunities (High Buying Intent)</div>
            <div style={{ fontSize: '0.75rem', color: '#64748b' }}>Conversations with urgent pain signals and strong product fit.</div>
          </div>
          <button className="btn btn-secondary btn-sm" onClick={() => onNavigate('leads')}>
            View All Leads <ArrowRight size={14} />
          </button>
        </div>

        {highPotential.length === 0 ? (
          <div style={{ padding: '2.5rem', textAlign: 'center', color: '#94a3b8' }}>
            <div style={{ marginBottom: '0.5rem' }}>No high-potential leads discovered yet.</div>
            <button className="btn btn-secondary btn-sm" onClick={onLaunchCampaign}>
              Launch Research to Discover Leads
            </button>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column' }}>
            {highPotential.slice(0, 5).map((lead) => (
              <div
                key={lead.id}
                style={{
                  padding: '1rem',
                  borderBottom: '1px solid var(--border)',
                  display: 'flex',
                  alignItems: 'flex-start',
                  justifyContent: 'space-between',
                  gap: '1rem',
                }}
              >
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}>
                    <span className="badge badge-high">{lead.score}/100</span>
                    <span className="badge badge-medium">{lead.platform}</span>
                    <span style={{ fontSize: '0.75rem', color: '#64748b', fontWeight: 500 }}>{lead.community}</span>
                    <span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>• {lead.published_at}</span>
                  </div>
                  <div style={{ fontWeight: 600, fontSize: '0.875rem', color: '#0f172a', marginBottom: '0.25rem' }}>
                    {lead.title}
                  </div>
                  <div style={{ fontSize: '0.8125rem', color: '#475569', lineClamp: 2, display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
                    {lead.excerpt}
                  </div>
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.375rem', flexShrink: 0 }}>
                  <button
                    className="btn btn-primary btn-sm"
                    onClick={() => onNavigate('reply_studio', lead.id)}
                  >
                    <MessageSquare size={14} /> Open Reply
                  </button>
                  <a
                    href={lead.url}
                    target="_blank"
                    rel="noreferrer"
                    className="btn btn-secondary btn-sm"
                    style={{ textDecoration: 'none' }}
                  >
                    <ExternalLink size={12} /> View Post
                  </a>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
