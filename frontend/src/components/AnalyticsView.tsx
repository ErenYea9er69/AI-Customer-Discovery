import React, { useState, useEffect } from 'react';
import {
  Lightbulb,
} from 'lucide-react';
import type { AnalyticsSummary } from '../types';
import { api } from '../api';

export const AnalyticsView: React.FC = () => {
  const [analytics, setAnalytics] = useState<AnalyticsSummary | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadAnalytics();
  }, []);

  const loadAnalytics = async () => {
    setLoading(true);
    try {
      const data = await api.getAnalytics();
      setAnalytics(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  if (loading || !analytics) {
    return <div style={{ padding: '3rem', textAlign: 'center', color: '#94a3b8' }}>Loading customer pain analytics...</div>;
  }

  return (
    <div style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1.5rem', maxWidth: '1200px' }}>
      {/* Header */}
      <div>
        <h2 style={{ fontSize: '1.25rem', fontWeight: 700, color: '#0f172a' }}>Customer Intelligence & Market Patterns</h2>
        <div style={{ fontSize: '0.8125rem', color: '#64748b' }}>
          Aggregated insights across {analytics.total_leads} discovered community discussions.
        </div>
      </div>

      {/* Actionable Suggestions */}
      {analytics.recommendations && analytics.recommendations.length > 0 && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem' }}>
          {analytics.recommendations.map((rec, idx) => (
            <div
              key={idx}
              className="card"
              style={{
                background: rec.type === 'product' ? '#eff6ff' : rec.type === 'marketing' ? '#ecfdf5' : '#fffbeb',
                borderColor: rec.type === 'product' ? '#bfdbfe' : rec.type === 'marketing' ? '#a7f3d0' : '#fde68a',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.375rem' }}>
                <Lightbulb
                  size={16}
                  color={rec.type === 'product' ? '#1d4ed8' : rec.type === 'marketing' ? '#047857' : '#b45309'}
                />
                <span
                  style={{
                    fontSize: '0.6875rem',
                    fontWeight: 700,
                    textTransform: 'uppercase',
                    color: rec.type === 'product' ? '#1e40af' : rec.type === 'marketing' ? '#065f46' : '#92400e',
                  }}
                >
                  {rec.type} Strategy
                </span>
              </div>
              <div style={{ fontWeight: 600, fontSize: '0.875rem', color: '#0f172a', marginBottom: '0.25rem' }}>
                {rec.title}
              </div>
              <div style={{ fontSize: '0.75rem', color: '#475569', lineHeight: 1.5 }}>
                {rec.description}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Main Grid: Complaints & Competitors */}
      <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: '1.5rem' }}>
        {/* Most Common Complaints */}
        <div className="card" style={{ padding: 0 }}>
          <div style={{ padding: '0.75rem 1rem', borderBottom: '1px solid var(--border)', fontSize: '0.75rem', fontWeight: 600, color: '#64748b' }}>
            TOP RECURRING CUSTOMER PAIN POINTS
          </div>
          {analytics.common_complaints.length === 0 ? (
            <div style={{ padding: '2rem', textAlign: 'center', color: '#94a3b8' }}>No complaints recorded yet.</div>
          ) : (
            analytics.common_complaints.map((item, idx) => (
              <div
                key={idx}
                style={{
                  padding: '0.875rem 1rem',
                  borderBottom: '1px solid var(--border)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                }}
              >
                <div style={{ flex: 1, paddingRight: '1rem' }}>
                  <div style={{ fontSize: '0.8125rem', fontWeight: 600, color: '#0f172a' }}>{item.problem}</div>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <span className="badge badge-medium">{item.count} Mentions</span>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Competitor Intelligence */}
        <div className="card" style={{ padding: 0 }}>
          <div style={{ padding: '0.75rem 1rem', borderBottom: '1px solid var(--border)', fontSize: '0.75rem', fontWeight: 600, color: '#64748b' }}>
            COMPETITORS WITH DISSATISFACTION SIGNALS
          </div>
          {analytics.competitor_intelligence.length === 0 ? (
            <div style={{ padding: '2rem', textAlign: 'center', color: '#94a3b8' }}>No competitor mentions found.</div>
          ) : (
            analytics.competitor_intelligence.map((item, idx) => (
              <div
                key={idx}
                style={{
                  padding: '0.875rem 1rem',
                  borderBottom: '1px solid var(--border)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                }}
              >
                <div style={{ fontWeight: 600, fontSize: '0.8125rem', color: '#0f172a' }}>{item.competitor}</div>
                <span className="badge badge-urgent">{item.mentions} Frustration Signals</span>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Highest Urgency Conversations */}
      <div className="card" style={{ padding: 0 }}>
        <div style={{ padding: '0.75rem 1rem', borderBottom: '1px solid var(--border)', fontSize: '0.75rem', fontWeight: 600, color: '#64748b' }}>
          HIGHEST URGENCY PROBLEMS REPORTED BY USERS
        </div>
        {analytics.high_urgency_problems.length === 0 ? (
          <div style={{ padding: '2rem', textAlign: 'center', color: '#94a3b8' }}>No high-urgency issues identified yet.</div>
        ) : (
          analytics.high_urgency_problems.map((p, idx) => (
            <div key={idx} style={{ padding: '1rem', borderBottom: '1px solid var(--border)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}>
                <span className="badge badge-urgent">Urgent</span>
                <span style={{ fontSize: '0.75rem', color: '#64748b', fontWeight: 600 }}>{p.community}</span>
              </div>
              <div style={{ fontWeight: 600, fontSize: '0.875rem', color: '#0f172a', marginBottom: '0.25rem' }}>
                {p.problem}
              </div>
              <div style={{ fontSize: '0.75rem', color: '#475569', fontStyle: 'italic' }}>
                "{p.excerpt}"
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};
