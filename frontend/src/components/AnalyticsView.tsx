import React, { useState, useEffect } from 'react';
import { Lightbulb, BarChart3 } from 'lucide-react';
import type { AnalyticsSummary } from '../types';
import { api } from '../api';

export const AnalyticsView: React.FC = () => {
  const [analytics, setAnalytics] = useState<AnalyticsSummary | null>(null);
  const [loading, setLoading] = useState(true);

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

  useEffect(() => {
    void loadAnalytics();
  }, []);

  if (loading || !analytics) {
    return (
      <div className="page-shell">
        <div className="loading-state" style={{ minHeight: '320px' }}>
          <span>Loading customer pain analytics…</span>
        </div>
      </div>
    );
  }

  return (
    <div className="page-shell">
      <div className="page-heading">
        <div>
          <div className="eyebrow">
            <BarChart3 size={13} /> Aggregated Intelligence
          </div>
          <h1>Customer Insights & Market Patterns</h1>
          <p>
            Synthesized pain points, competitor dissatisfaction signals, and strategic recommendations across{' '}
            <strong className="tabular">{analytics.total_leads}</strong> analyzed community discussions.
          </p>
        </div>
      </div>

      {/* Actionable Strategy Recommendations */}
      {analytics.recommendations && analytics.recommendations.length > 0 && (
        <section style={{ marginBottom: 'var(--sp-6)' }}>
          <div className="eyebrow eyebrow-muted" style={{ marginBottom: 'var(--sp-3)' }}>
            Strategic Playbooks
          </div>
          <div className="form-grid-3">
            {analytics.recommendations.map((rec, idx) => (
              <div
                key={idx}
                className="card"
                style={{
                  padding: 'var(--sp-4)',
                  background:
                    rec.type === 'product'
                      ? 'var(--info-bg)'
                      : rec.type === 'marketing'
                      ? 'var(--success-bg)'
                      : 'var(--warning-bg)',
                  borderColor:
                    rec.type === 'product'
                      ? 'var(--info-border)'
                      : rec.type === 'marketing'
                      ? 'var(--success-border)'
                      : 'var(--warning-border)',
                  display: 'flex',
                  flexDirection: 'column',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--sp-2)', marginBottom: 'var(--sp-2)' }}>
                  <Lightbulb
                    size={16}
                    color={
                      rec.type === 'product'
                        ? 'var(--info)'
                        : rec.type === 'marketing'
                        ? 'var(--success)'
                        : 'var(--warning)'
                    }
                  />
                  <span
                    style={{
                      fontSize: 'var(--fs-2xs)',
                      fontWeight: 700,
                      textTransform: 'uppercase',
                      letterSpacing: '0.05em',
                      color:
                        rec.type === 'product'
                          ? 'var(--info-text)'
                          : rec.type === 'marketing'
                          ? 'var(--success-text)'
                          : 'var(--warning-text)',
                    }}
                  >
                    {rec.type} Strategy
                  </span>
                </div>
                <div style={{ fontWeight: 700, fontSize: 'var(--fs-base)', color: 'var(--text-main)', marginBottom: '4px' }}>
                  {rec.title}
                </div>
                <div style={{ fontSize: 'var(--fs-xs)', color: 'var(--text-muted)', lineHeight: '1.5', marginTop: 'auto' }}>
                  {rec.description}
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Main Grid: Complaints & Competitors */}
      <section className="form-grid-2" style={{ marginBottom: 'var(--sp-6)' }}>
        {/* Most Common Complaints */}
        <div className="panel lead-table-panel">
          <div className="table-header">
            <div>
              <h2>Top Recurring Customer Pain Points</h2>
              <span>Aggregated across all qualified discussions</span>
            </div>
          </div>
          {analytics.common_complaints.length === 0 ? (
            <div className="table-empty">
              <span>No recurring pain points recorded yet.</span>
            </div>
          ) : (
            analytics.common_complaints.map((item, idx) => (
              <div
                key={idx}
                style={{
                  padding: 'var(--sp-4) var(--sp-5)',
                  borderBottom: '1px solid var(--border)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  gap: 'var(--sp-3)',
                }}
              >
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: 'var(--fs-base)', fontWeight: 600, color: 'var(--text-main)' }}>
                    {item.problem}
                  </div>
                </div>
                <div>
                  <span className="badge badge-medium tabular">{item.count} Mentions</span>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Competitor Intelligence */}
        <div className="panel lead-table-panel">
          <div className="table-header">
            <div>
              <h2>Competitor Dissatisfaction Signals</h2>
              <span>Alternative products mentioned with user frustration</span>
            </div>
          </div>
          {analytics.competitor_intelligence.length === 0 ? (
            <div className="table-empty">
              <span>No competitor mentions found in this queue.</span>
            </div>
          ) : (
            analytics.competitor_intelligence.map((item, idx) => (
              <div
                key={idx}
                style={{
                  padding: 'var(--sp-4) var(--sp-5)',
                  borderBottom: '1px solid var(--border)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  gap: 'var(--sp-3)',
                }}
              >
                <div style={{ fontWeight: 600, fontSize: 'var(--fs-base)', color: 'var(--text-main)' }}>
                  {item.competitor}
                </div>
                <span className="badge badge-amber tabular">{item.mentions} Frustration Signals</span>
              </div>
            ))
          )}
        </div>
      </section>

      {/* Highest Urgency Conversations */}
      <section className="panel lead-table-panel">
        <div className="table-header">
          <div>
            <h2>Highest Urgency Problems Reported</h2>
            <span>Discussions where immediate solutions are requested</span>
          </div>
        </div>
        {analytics.high_urgency_problems.length === 0 ? (
          <div className="table-empty">
            <span>No high-urgency discussions identified in recent campaigns.</span>
          </div>
        ) : (
          analytics.high_urgency_problems.map((p, idx) => (
            <div
              key={idx}
              style={{
                padding: 'var(--sp-4) var(--sp-5)',
                borderBottom: '1px solid var(--border)',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--sp-2)', marginBottom: '4px' }}>
                <span className="badge badge-danger">Urgent Need</span>
                <span style={{ fontSize: 'var(--fs-xs)', color: 'var(--text-subtle)', fontWeight: 600 }}>
                  {p.community}
                </span>
              </div>
              <div style={{ fontWeight: 600, fontSize: 'var(--fs-base)', color: 'var(--text-main)', marginBottom: '4px' }}>
                {p.problem}
              </div>
              <div className="evidence-line">
                “{p.excerpt}”
              </div>
            </div>
          ))
        )}
      </section>
    </div>
  );
};
