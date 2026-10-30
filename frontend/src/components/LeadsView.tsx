import React, { useState } from 'react';
import {
  Search,
  ExternalLink,
  MessageSquare,
  X,
} from 'lucide-react';
import type { LeadQualification } from '../types';

interface LeadsViewProps {
  leads: LeadQualification[];
  onOpenReplyStudio: (leadId: string) => void;
}

export const LeadsView: React.FC<LeadsViewProps> = ({ leads, onOpenReplyStudio }) => {
  const [filterScore, setFilterScore] = useState<string>('all');
  const [filterPlatform, setFilterPlatform] = useState<string>('all');
  const [filterIntent, setFilterIntent] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [selectedLead, setSelectedLead] = useState<LeadQualification | null>(null);

  const filteredLeads = leads.filter((lead) => {
    if (filterScore === 'high' && lead.score < 75) return false;
    if (filterScore === 'relevant' && (lead.score < 50 || lead.score >= 75)) return false;
    if (filterScore === 'insight' && lead.classification !== 'customer_insight') return false;
    if (filterScore === 'competitor' && lead.classification !== 'competitor_intel') return false;

    if (filterPlatform !== 'all' && lead.platform !== filterPlatform) return false;
    if (filterIntent !== 'all' && lead.purchase_intent !== filterIntent) return false;

    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      const match =
        lead.title.toLowerCase().includes(q) ||
        lead.customer_problem.toLowerCase().includes(q) ||
        lead.community.toLowerCase().includes(q);
      if (!match) return false;
    }
    return true;
  });

  return (
    <div style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1rem', maxWidth: '1200px' }}>
      {/* Filter and Search Bar */}
      <div className="card" style={{ padding: '0.75rem 1rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
          {/* Search box */}
          <div style={{ position: 'relative', flex: 1, minWidth: '220px' }}>
            <Search
              size={14}
              color="#94a3b8"
              style={{ position: 'absolute', left: '0.625rem', top: '50%', transform: 'translateY(-50%)' }}
            />
            <input
              type="text"
              className="input"
              style={{ paddingLeft: '2rem' }}
              placeholder="Filter by problem, title, or community..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>

          {/* Classification / Score Filter */}
          <select
            className="select"
            style={{ width: 'auto' }}
            value={filterScore}
            onChange={(e) => setFilterScore(e.target.value)}
          >
            <option value="all">All Classifications</option>
            <option value="high">High Potential (75-100)</option>
            <option value="relevant">Relevant Leads (50-74)</option>
            <option value="insight">Customer Research Insights</option>
            <option value="competitor">Competitor Intelligence</option>
          </select>

          {/* Platform Filter */}
          <select
            className="select"
            style={{ width: 'auto' }}
            value={filterPlatform}
            onChange={(e) => setFilterPlatform(e.target.value)}
          >
            <option value="all">All Sources</option>
            <option value="reddit">Reddit</option>
            <option value="web">Web</option>
            <option value="github">GitHub</option>
            <option value="v2ex">V2EX</option>
          </select>

          {/* Intent Filter */}
          <select
            className="select"
            style={{ width: 'auto' }}
            value={filterIntent}
            onChange={(e) => setFilterIntent(e.target.value)}
          >
            <option value="all">All Intent Levels</option>
            <option value="High">High Buying Intent</option>
            <option value="Medium">Medium Intent</option>
            <option value="Low">Low Intent / Vent</option>
          </select>
        </div>
      </div>

      {/* Leads Table / List */}
      <div className="card" style={{ padding: 0 }}>
        <div
          style={{
            padding: '0.75rem 1rem',
            borderBottom: '1px solid var(--border)',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            fontSize: '0.75rem',
            fontWeight: 600,
            color: '#64748b',
          }}
        >
          <span>QUALIFIED OPPORTUNITIES ({filteredLeads.length})</span>
          <span>Click any row to inspect score breakdown & evidence</span>
        </div>

        {filteredLeads.length === 0 ? (
          <div style={{ padding: '3rem', textAlign: 'center', color: '#94a3b8' }}>
            No leads matching current filters.
          </div>
        ) : (
          filteredLeads.map((lead) => {
            const isHigh = lead.score >= 75;
            return (
              <div
                key={lead.id}
                onClick={() => setSelectedLead(lead)}
                style={{
                  padding: '1rem',
                  borderBottom: '1px solid var(--border)',
                  cursor: 'pointer',
                  transition: 'background 0.15s ease',
                  display: 'flex',
                  alignItems: 'flex-start',
                  justifyContent: 'space-between',
                  gap: '1rem',
                }}
                onMouseEnter={(e) => (e.currentTarget.style.background = '#f8fafc')}
                onMouseLeave={(e) => (e.currentTarget.style.background = '#ffffff')}
              >
                {/* Left info */}
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.375rem' }}>
                    <span className={`badge ${isHigh ? 'badge-high' : 'badge-medium'}`}>
                      {lead.score} / 100
                    </span>
                    <span className="badge badge-low">{lead.platform}</span>
                    <span style={{ fontSize: '0.75rem', fontWeight: 600, color: '#475569' }}>
                      {lead.community}
                    </span>
                    <span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>
                      • By {lead.author} on {lead.published_at}
                    </span>
                    {lead.competitor_mentioned && (
                      <span className="badge" style={{ background: '#fef3c7', color: '#b45309' }}>
                        vs {lead.competitor_mentioned}
                      </span>
                    )}
                  </div>

                  <div style={{ fontWeight: 600, fontSize: '0.9375rem', color: '#0f172a', marginBottom: '0.25rem' }}>
                    {lead.title}
                  </div>

                  <div style={{ fontSize: '0.8125rem', color: '#334155', marginBottom: '0.5rem' }}>
                    <strong style={{ color: '#0f172a' }}>Problem:</strong> {lead.customer_problem}
                  </div>

                  <div
                    style={{
                      fontSize: '0.75rem',
                      color: '#64748b',
                      lineClamp: 2,
                      display: '-webkit-box',
                      WebkitLineClamp: 2,
                      WebkitBoxOrient: 'vertical',
                      overflow: 'hidden',
                      background: '#f8fafc',
                      padding: '0.375rem 0.5rem',
                      borderRadius: '4px',
                    }}
                  >
                    "{lead.excerpt}"
                  </div>
                </div>

                {/* Right badges & action */}
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '0.5rem', flexShrink: 0 }}>
                  <div style={{ display: 'flex', gap: '0.375rem' }}>
                    <span
                      className={`badge ${lead.purchase_intent === 'High' ? 'badge-high' : lead.purchase_intent === 'Medium' ? 'badge-medium' : 'badge-low'}`}
                    >
                      Intent: {lead.purchase_intent}
                    </span>
                    <span
                      className={`badge ${lead.urgency === 'High' ? 'badge-urgent' : 'badge-low'}`}
                    >
                      Urgency: {lead.urgency}
                    </span>
                  </div>

                  <button
                    className="btn btn-primary btn-sm"
                    onClick={(e) => {
                      e.stopPropagation();
                      onOpenReplyStudio(lead.id);
                    }}
                  >
                    <MessageSquare size={14} /> Open Reply
                  </button>
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* Lead Detail & Explainable Score Modal */}
      {selectedLead && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(15, 23, 42, 0.4)',
            backdropFilter: 'blur(2px)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 50,
            padding: '1rem',
          }}
          onClick={() => setSelectedLead(null)}
        >
          <div
            className="card"
            style={{ width: '100%', maxWidth: '680px', maxHeight: '90vh', overflowY: 'auto', padding: '1.5rem' }}
            onClick={(e) => e.stopPropagation()}
          >
            {/* Header */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1rem' }}>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}>
                  <span className={`badge ${selectedLead.score >= 75 ? 'badge-high' : 'badge-medium'}`}>
                    Overall Score: {selectedLead.score}/100
                  </span>
                  <span className="badge badge-low">{selectedLead.classification.replace('_', ' ')}</span>
                </div>
                <h3 style={{ fontSize: '1.125rem', fontWeight: 700, color: '#0f172a' }}>{selectedLead.title}</h3>
              </div>
              <button
                className="btn btn-secondary btn-sm"
                onClick={() => setSelectedLead(null)}
              >
                <X size={16} />
              </button>
            </div>

            {/* Explainable Score Breakdown */}
            <div style={{ background: '#f8fafc', border: '1px solid var(--border)', borderRadius: 'var(--radius)', padding: '1rem', marginBottom: '1.25rem' }}>
              <div style={{ fontWeight: 600, fontSize: '0.8125rem', color: '#0f172a', marginBottom: '0.5rem' }}>
                EXPLAINABLE 100-POINT SCORING BREAKDOWN
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: '0.5rem', textAlign: 'center', marginBottom: '0.75rem' }}>
                <div style={{ background: '#ffffff', padding: '0.5rem', borderRadius: '4px', border: '1px solid #e2e8f0' }}>
                  <div style={{ fontSize: '0.6875rem', color: '#64748b' }}>ICP Match</div>
                  <div style={{ fontWeight: 700, color: 'var(--primary)' }}>{selectedLead.score_breakdown.icp_match}/25</div>
                </div>
                <div style={{ background: '#ffffff', padding: '0.5rem', borderRadius: '4px', border: '1px solid #e2e8f0' }}>
                  <div style={{ fontSize: '0.6875rem', color: '#64748b' }}>Problem Fit</div>
                  <div style={{ fontWeight: 700, color: 'var(--primary)' }}>{selectedLead.score_breakdown.problem_fit}/30</div>
                </div>
                <div style={{ background: '#ffffff', padding: '0.5rem', borderRadius: '4px', border: '1px solid #e2e8f0' }}>
                  <div style={{ fontSize: '0.6875rem', color: '#64748b' }}>Buying Intent</div>
                  <div style={{ fontWeight: 700, color: 'var(--primary)' }}>{selectedLead.score_breakdown.buying_intent}/20</div>
                </div>
                <div style={{ background: '#ffffff', padding: '0.5rem', borderRadius: '4px', border: '1px solid #e2e8f0' }}>
                  <div style={{ fontSize: '0.6875rem', color: '#64748b' }}>Urgency</div>
                  <div style={{ fontWeight: 700, color: 'var(--primary)' }}>{selectedLead.score_breakdown.urgency}/15</div>
                </div>
                <div style={{ background: '#ffffff', padding: '0.5rem', borderRadius: '4px', border: '1px solid #e2e8f0' }}>
                  <div style={{ fontSize: '0.6875rem', color: '#64748b' }}>Recency</div>
                  <div style={{ fontWeight: 700, color: 'var(--primary)' }}>{selectedLead.score_breakdown.recency}/10</div>
                </div>
              </div>
              <div style={{ fontSize: '0.75rem', color: '#475569', lineHeight: 1.5 }}>
                <strong>Reasoning:</strong> {selectedLead.score_breakdown.explanation}
              </div>
            </div>

            {/* Extracted Problem & Evidence */}
            <div style={{ marginBottom: '1rem' }}>
              <label className="label">Customer Problem</label>
              <div style={{ fontSize: '0.875rem', color: '#0f172a', fontWeight: 500, marginBottom: '0.75rem' }}>
                {selectedLead.customer_problem}
              </div>

              <label className="label">Supporting Evidence & Conversation Excerpt</label>
              <div
                style={{
                  fontSize: '0.8125rem',
                  color: '#334155',
                  background: '#f1f5f9',
                  padding: '0.75rem',
                  borderRadius: 'var(--radius)',
                  fontStyle: 'italic',
                  lineHeight: 1.6,
                }}
              >
                "{selectedLead.excerpt}"
              </div>
            </div>

            {/* Product Fit Explanation */}
            <div style={{ marginBottom: '1.25rem' }}>
              <label className="label">How Your Product Fits This Situation</label>
              <div style={{ fontSize: '0.8125rem', color: '#047857', background: '#ecfdf5', padding: '0.5rem 0.75rem', borderRadius: '4px', border: '1px solid #a7f3d0' }}>
                {selectedLead.product_fit_explanation}
              </div>
            </div>

            {/* Actions */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingTop: '1rem', borderTop: '1px solid var(--border)' }}>
              <a
                href={selectedLead.url}
                target="_blank"
                rel="noreferrer"
                className="btn btn-secondary"
                style={{ textDecoration: 'none' }}
              >
                <ExternalLink size={14} /> Open Original Post
              </a>
              <button
                className="btn btn-primary"
                onClick={() => {
                  const id = selectedLead.id;
                  setSelectedLead(null);
                  onOpenReplyStudio(id);
                }}
              >
                <MessageSquare size={16} /> Open in Reply Studio
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
