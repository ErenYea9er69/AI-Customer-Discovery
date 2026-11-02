import React, { useState, useEffect, useCallback } from 'react';
import {
  Lightbulb,
  AlertTriangle,
  ShieldCheck,
  TrendingUp,
  Flame,
  CheckCircle2,
} from 'lucide-react';
import type { AnalyticsSummary } from '../types';
import { api } from '../api';

const PLATFORM_LABELS: Record<string, string> = {
  reddit: 'Reddit',
  hackernews: 'Hacker News',
  web: 'Public Web',
  quora: 'Quora',
  github: 'GitHub Issues',
  twitter: 'Twitter / X',
};

export const AnalyticsView: React.FC = () => {
  const [analytics, setAnalytics] = useState<AnalyticsSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadAnalytics = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getAnalytics();
      setAnalytics(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Could not load customer analytics.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadAnalytics();
  }, [loadAnalytics]);

  if (error) {
    return (
      <div className="page-shell">
        <div className="notice notice-error" role="alert" style={{ marginTop: 'var(--sp-6)' }}>
          <AlertTriangle size={16} />
          <span>{error}</span>
          <button className="btn btn-secondary btn-sm" onClick={() => void loadAnalytics()}>
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (loading || !analytics) {
    return (
      <div className="page-shell">
        <div className="loading-state" style={{ minHeight: '320px' }}>
          <span>Synthesizing customer pain analytics and market patterns…</span>
        </div>
      </div>
    );
  }

  const highIntentCount = analytics.intent_distribution?.High || 0;
  const replyMix = analytics.reply_mix;
  const productShare = replyMix?.product_share ?? 0;
  const isProductShareSafe = productShare <= 0.1;

  return (
    <div className="page-shell">
      <div className="page-heading">
        <div>
          <h1>Customer Insights & Market Patterns</h1>
          <p>
            Synthesized pain points, competitor dissatisfaction signals, and strategic recommendations across{' '}
            <strong className="tabular">{analytics.total_leads}</strong> analyzed community discussions.
          </p>
        </div>
      </div>

      {/* First Run / Zero State Banner */}
      {analytics.total_leads === 0 && (
        <section className="notice notice-info" style={{ marginBottom: 'var(--sp-6)' }}>
          <Lightbulb size={20} />
          <div>
            <strong>Ready for Autonomous Discovery</strong>
            <span>
              Once you set up your business profile and launch your first campaign in the Discovery Engine, aggregated customer pain points, community breakdown stats, and competitor dissatisfaction patterns will populate here automatically.
            </span>
          </div>
        </section>
      )}

      {/* Strategic Playbooks */}
      {analytics.recommendations && analytics.recommendations.length > 0 && (
        <section style={{ marginBottom: 'var(--sp-6)' }}>
          <h2 className="section-title">Strategic Action Playbooks</h2>
          <div className="form-grid-3">
            {analytics.recommendations.map((rec, idx) => {
              const isSafety = rec.type === 'safety';
              const isMarketing = rec.type === 'marketing';
              const isProduct = rec.type === 'product';

              return (
                <div
                  key={idx}
                  className="card"
                  style={{
                    padding: 'var(--sp-4)',
                    background: isSafety
                      ? 'var(--warning-bg)'
                      : isMarketing
                      ? 'var(--success-bg)'
                      : isProduct
                      ? 'var(--info-bg)'
                      : 'var(--surface)',
                    borderColor: isSafety
                      ? 'var(--warning-border)'
                      : isMarketing
                      ? 'var(--success-border)'
                      : isProduct
                      ? 'var(--info-border)'
                      : 'var(--border)',
                    display: 'flex',
                    flexDirection: 'column',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--sp-2)', marginBottom: 'var(--sp-2)' }}>
                    <Lightbulb
                      size={16}
                      color={
                        isSafety
                          ? 'var(--warning)'
                          : isMarketing
                          ? 'var(--success)'
                          : isProduct
                          ? 'var(--info)'
                          : 'var(--primary)'
                      }
                    />
                    <span
                      style={{
                        fontSize: 'var(--fs-2xs)',
                        fontWeight: 700,
                        textTransform: 'uppercase',
                        letterSpacing: '0.05em',
                        color: isSafety
                          ? 'var(--warning-text)'
                          : isMarketing
                          ? 'var(--success-text)'
                          : isProduct
                          ? 'var(--info-text)'
                          : 'var(--text-subtle)',
                      }}
                    >
                      {rec.type} Playbook
                    </span>
                  </div>
                  <div style={{ fontWeight: 700, fontSize: 'var(--fs-base)', color: 'var(--text-main)', marginBottom: '4px' }}>
                    {rec.title}
                  </div>
                  <div style={{ fontSize: 'var(--fs-xs)', color: 'var(--text-muted)', lineHeight: '1.5', marginTop: 'auto' }}>
                    {rec.description}
                  </div>
                </div>
              );
            })}
          </div>
        </section>
      )}

      {/* KPI Overview Grid */}
      <section className="metric-grid" aria-label="Customer discovery metrics" style={{ marginBottom: 'var(--sp-6)' }}>
        <article className="metric-card metric-card-primary">
          <div className="metric-label">Analyzed Discussions</div>
          <div className="metric-value">{analytics.total_leads}</div>
          <div className="metric-meta">
            <span className="status-dot status-dot-blue" />
            <span>Across {Object.keys(analytics.platform_distribution || {}).length} platforms</span>
          </div>
        </article>

        <article className="metric-card">
          <div className="metric-label">High-Intent Buyers</div>
          <div className="metric-value">{highIntentCount}</div>
          <div className="metric-meta">
            <TrendingUp size={14} color="var(--success)" />
            <span>Actively asking for tool recommendations</span>
          </div>
        </article>

        <article className="metric-card">
          <div className="metric-label">Competitor Dissatisfaction</div>
          <div className="metric-value">{analytics.competitor_intelligence?.length || 0}</div>
          <div className="metric-meta">
            <Flame size={14} color="var(--warning)" />
            <span>Alternatives mentioned with frustration</span>
          </div>
        </article>

        <article className="metric-card">
          <div className="metric-label">90-Day Reply Safety Mix</div>
          <div className="metric-value">
            {replyMix?.published_last_90_days ? `${Math.round(productShare * 100)}%` : '0%'}
          </div>
          <div className="metric-meta">
            {isProductShareSafe ? (
              <>
                <CheckCircle2 size={14} color="var(--success)" />
                <span>Safe (under 10% ceiling)</span>
              </>
            ) : (
              <>
                <ShieldCheck size={14} color="var(--warning)" />
                <span>Warning: Exceeds 10% target</span>
              </>
            )}
          </div>
        </article>
      </section>

      {/* Top Communities & Top Pain Points Grid */}
      <section className="form-grid-2" style={{ marginBottom: 'var(--sp-6)' }}>
        {/* Top Communities */}
        <div className="panel lead-table-panel">
          <div className="table-header">
            <div>
              <h2>Top Discussion Hubs & Subreddits</h2>
              <span>Communities generating the highest volume of qualified leads</span>
            </div>
          </div>
          {!analytics.top_communities || analytics.top_communities.length === 0 ? (
            <div className="table-empty">
              <span>No community discussions recorded yet.</span>
            </div>
          ) : (
            <div className="priority-list">
              {analytics.top_communities.map((c, idx) => (
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
                  <div>
                    <div style={{ fontWeight: 600, fontSize: 'var(--fs-base)', color: 'var(--text-main)' }}>
                      {c.community}
                    </div>
                    <div style={{ fontSize: 'var(--fs-xs)', color: 'var(--text-subtle)', marginTop: '2px' }}>
                      <span className="tabular">{c.leads}</span> leads identified
                    </div>
                  </div>

                  <div>
                    {c.high_potential > 0 ? (
                      <span className="badge badge-high tabular">
                        {c.high_potential} High Potential
                      </span>
                    ) : (
                      <span className="badge badge-low tabular">
                        {c.leads} Opportunities
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Competitor Intelligence */}
        <div className="panel lead-table-panel">
          <div className="table-header">
            <div>
              <h2>Competitor Dissatisfaction Signals</h2>
              <span>Alternative products mentioned by users reporting frustration</span>
            </div>
          </div>
          {!analytics.competitor_intelligence || analytics.competitor_intelligence.length === 0 ? (
            <div className="table-empty">
              <span>No competitor mentions identified in current discussions.</span>
            </div>
          ) : (
            <div className="priority-list">
              {analytics.competitor_intelligence.map((item, idx) => (
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
                  <div>
                    <div style={{ fontWeight: 600, fontSize: 'var(--fs-base)', color: 'var(--text-main)' }}>
                      {item.competitor}
                    </div>
                    <div style={{ fontSize: 'var(--fs-xs)', color: 'var(--text-subtle)', marginTop: '2px' }}>
                      Users venting about pricing, complexity, or missing workflows
                    </div>
                  </div>
                  <span className="badge badge-amber tabular">{item.mentions} Frustration Signals</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </section>

      {/* Common Complaints & Category Breakdown */}
      <section className="form-grid-2" style={{ marginBottom: 'var(--sp-6)' }}>
        {/* Most Common Complaints */}
        <div className="panel lead-table-panel">
          <div className="table-header">
            <div>
              <h2>Top Recurring Customer Pain Points</h2>
              <span>Most frequent problem patterns discovered across conversations</span>
            </div>
          </div>
          {!analytics.common_complaints || analytics.common_complaints.length === 0 ? (
            <div className="table-empty">
              <span>No recurring pain points recorded yet.</span>
            </div>
          ) : (
            <div className="priority-list">
              {analytics.common_complaints.map((item, idx) => (
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
                    <span className="badge badge-medium tabular">{item.count} Discussions</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Platform & Intent Distributions */}
        <div className="panel" style={{ padding: 'var(--sp-5)', display: 'flex', flexDirection: 'column', gap: 'var(--sp-5)' }}>
          <div>
            <h2 className="section-title" style={{ marginBottom: 'var(--sp-3)' }}>
              Distribution by Discovery Platform
            </h2>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--sp-2)' }}>
              {Object.entries(analytics.platform_distribution || {}).map(([platform, count]) => {
                const total = analytics.total_leads || 1;
                const pct = Math.round((count / total) * 100);
                return (
                  <div key={platform}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 'var(--fs-xs)', marginBottom: '3px' }}>
                      <span style={{ fontWeight: 600 }}>{PLATFORM_LABELS[platform] || platform}</span>
                      <span className="tabular">{count} ({pct}%)</span>
                    </div>
                    <div className="coverage-bar" style={{ height: '6px' }}>
                      <span style={{ width: `${Math.max(5, pct)}%` }} />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          <div>
            <h2 className="section-title" style={{ marginBottom: 'var(--sp-3)' }}>
              Distribution by Buying Intent
            </h2>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--sp-2)' }}>
              {['High', 'Medium', 'Low'].map((level) => {
                const count = analytics.intent_distribution?.[level] || 0;
                const total = analytics.total_leads || 1;
                const pct = Math.round((count / total) * 100);
                return (
                  <div key={level}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 'var(--fs-xs)', marginBottom: '3px' }}>
                      <span style={{ fontWeight: 600 }}>{level} Intent</span>
                      <span className="tabular">{count} ({pct}%)</span>
                    </div>
                    <div className="coverage-bar" style={{ height: '6px' }}>
                      <span
                        style={{
                          width: `${Math.max(count ? 5 : 0, pct)}%`,
                          background:
                            level === 'High'
                              ? 'var(--success)'
                              : level === 'Medium'
                              ? 'var(--primary)'
                              : 'var(--border-strong)',
                        }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </section>

      {/* Highest Urgency Conversations */}
      <section className="panel lead-table-panel">
        <div className="table-header">
          <div>
            <h2>Highest Urgency Problems Reported</h2>
            <span>Discussions where users are actively seeking immediate solutions or tool recommendations</span>
          </div>
        </div>
        {!analytics.high_urgency_problems || analytics.high_urgency_problems.length === 0 ? (
          <div className="table-empty">
            <span>No high-urgency discussions identified in recent campaigns.</span>
          </div>
        ) : (
          <div className="priority-list">
            {analytics.high_urgency_problems.map((p, idx) => (
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
                  &ldquo;{p.excerpt}&rdquo;
                </div>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
};

export default AnalyticsView;
