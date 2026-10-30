import React, { useEffect, useState } from 'react';
import {
  ChevronLeft,
  ChevronRight,
  ExternalLink,
  Filter,
  MessageSquare,
  Search,
  X,
  Sparkles,
} from 'lucide-react';
import type { LeadQualification } from '../types';
import { api } from '../api';

interface LeadsViewProps {
  leads: LeadQualification[];
  onOpenReplyStudio: (leadId: string) => void;
}

const PAGE_SIZE = 25;

const scoreFilter = (value: string) =>
  value === 'high'
    ? { min_score: 75 }
    : value === 'relevant'
    ? { min_score: 50, classification: 'relevant_potential' }
    : value === 'insight'
    ? { classification: 'customer_insight' }
    : value === 'competitor'
    ? { classification: 'competitor_intel' }
    : {};

export const LeadsView: React.FC<LeadsViewProps> = ({ leads: initialLeads, onOpenReplyStudio }) => {
  const [leads, setLeads] = useState(initialLeads);
  const [filterScore, setFilterScore] = useState('all');
  const [filterPlatform, setFilterPlatform] = useState('all');
  const [filterIntent, setFilterIntent] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [page, setPage] = useState(0);
  const [selectedLead, setSelectedLead] = useState<LeadQualification | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLeads(initialLeads);
  }, [initialLeads]);

  useEffect(() => {
    let active = true;
    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await api.listLeads({
          ...scoreFilter(filterScore),
          platform: filterPlatform === 'all' ? undefined : filterPlatform,
          buying_intent: filterIntent === 'all' ? undefined : filterIntent,
          query: searchQuery.trim() || undefined,
          limit: PAGE_SIZE,
          offset: page * PAGE_SIZE,
        });
        if (active) setLeads(data);
      } catch (e) {
        if (active) setError(e instanceof Error ? e.message : 'Could not load leads.');
      } finally {
        if (active) setLoading(false);
      }
    };
    void load();
    return () => {
      active = false;
    };
  }, [filterScore, filterPlatform, filterIntent, searchQuery, page]);

  const resetPage = (setter: (value: string) => void, value: string) => {
    setter(value);
    setPage(0);
  };

  return (
    <div className="page-shell leads-page">
      <section className="page-heading">
        <div>
          <div className="eyebrow">
            <Filter size={13} /> Opportunities Inbox
          </div>
          <h1>Qualified Customer Discussions</h1>
          <p>
            Inspect customer evidence, review multi-dimensional qualification scores, and prepare high-value replies.
          </p>
        </div>
        <div className="queue-summary">
          <strong className="tabular">{loading ? '…' : leads.length}</strong>
          <span>opportunities visible</span>
        </div>
      </section>

      {/* Filter Toolbar */}
      <section className="filter-bar panel">
        <div className="search-field">
          <Search size={16} />
          <input
            id="leads-search-input"
            aria-label="Search leads by problem, title, or community"
            className="input"
            placeholder="Search problems, keywords, or subreddits…"
            value={searchQuery}
            onChange={(e) => {
              setSearchQuery(e.target.value);
              setPage(0);
            }}
          />
        </div>

        <select
          aria-label="Filter by classification"
          className="select"
          value={filterScore}
          onChange={(e) => resetPage(setFilterScore, e.target.value)}
        >
          <option value="all">All Classifications</option>
          <option value="high">High Potential (75+)</option>
          <option value="relevant">Relevant Leads (50–74)</option>
          <option value="insight">Customer Insights</option>
          <option value="competitor">Competitor Intel</option>
        </select>

        <select
          aria-label="Filter by platform"
          className="select"
          value={filterPlatform}
          onChange={(e) => resetPage(setFilterPlatform, e.target.value)}
        >
          <option value="all">All Sources</option>
          <option value="reddit">Reddit</option>
          <option value="web">Public Web</option>
          <option value="github">GitHub</option>
          <option value="v2ex">V2EX</option>
        </select>

        <select
          aria-label="Filter by intent"
          className="select"
          value={filterIntent}
          onChange={(e) => resetPage(setFilterIntent, e.target.value)}
        >
          <option value="all">All Intent Levels</option>
          <option value="High">High Intent</option>
          <option value="Medium">Medium Intent</option>
          <option value="Low">Low Intent</option>
        </select>
      </section>

      {error && (
        <div className="notice notice-error" role="alert">
          <span>{error}</span>
          <button className="btn btn-secondary btn-sm" onClick={() => setPage(page)}>
            Retry loading
          </button>
        </div>
      )}

      {/* Leads Table Panel */}
      <section className="panel lead-table-panel">
        <div className="table-header">
          <div>
            <h2>Discovered Opportunities</h2>
            <span>Page {page + 1} · Ranked by pain alignment</span>
          </div>
          <span style={{ fontSize: 'var(--fs-xs)', color: 'var(--text-subtle)' }}>
            Select any item to inspect qualification scoring
          </span>
        </div>

        {loading ? (
          <div className="table-empty">Loading matching opportunities…</div>
        ) : leads.length === 0 ? (
          <div className="table-empty">
            <div className="empty-icon">
              <Sparkles size={20} />
            </div>
            <strong>No leads match these filters</strong>
            <span>Try clearing search keywords, adjusting intent filters, or launching a new campaign.</span>
          </div>
        ) : (
          <div className="lead-list">
            {leads.map((lead) => (
              <div
                className="lead-row"
                key={lead.id}
                onClick={() => setSelectedLead(lead)}
                role="button"
                tabIndex={0}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    setSelectedLead(lead);
                  }
                }}
              >
                <div
                  className={`score-badge ${
                    lead.score >= 75
                      ? 'score-badge-high'
                      : lead.score >= 50
                      ? 'score-badge-mid'
                      : 'score-badge-low'
                  }`}
                >
                  <strong className="tabular">{lead.score}</strong>
                  <span>/100</span>
                </div>

                <div className="lead-main">
                  <div className="lead-meta">
                    <span className="badge badge-low">{lead.platform}</span>
                    <span style={{ fontWeight: 600 }}>{lead.community}</span>
                    <span>·</span>
                    <span>{lead.published_at || 'Recent'}</span>
                    {lead.competitor_mentioned && (
                      <span className="badge badge-amber">vs {lead.competitor_mentioned}</span>
                    )}
                  </div>
                  <h3>{lead.title}</h3>
                  <p>
                    <strong>{lead.customer_problem}</strong>
                  </p>
                  <div className="evidence-line">“{lead.excerpt}”</div>
                </div>

                <div className="lead-side">
                  <span
                    className={`intent-pill ${lead.urgency === 'High' ? 'intent-pill-urgent' : ''}`}
                  >
                    {lead.purchase_intent} intent
                  </span>
                  <button
                    className="btn btn-primary btn-sm"
                    onClick={(e) => {
                      e.stopPropagation();
                      onOpenReplyStudio(lead.id);
                    }}
                  >
                    <MessageSquare size={13} />
                    <span>Open reply</span>
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

        <div className="pagination">
          <button
            className="btn btn-secondary btn-sm"
            onClick={() => setPage((value) => Math.max(0, value - 1))}
            disabled={page === 0 || loading}
          >
            <ChevronLeft size={14} />
            <span>Previous</span>
          </button>
          <span style={{ fontWeight: 600, fontSize: 'var(--fs-xs)' }}>Page {page + 1}</span>
          <button
            className="btn btn-secondary btn-sm"
            onClick={() => setPage((value) => value + 1)}
            disabled={loading || leads.length < PAGE_SIZE}
          >
            <span>Next</span>
            <ChevronRight size={14} />
          </button>
        </div>
      </section>

      {/* Lead Detail Modal */}
      {selectedLead && (
        <div
          className="modal-backdrop"
          onClick={() => setSelectedLead(null)}
          role="dialog"
          aria-modal="true"
          aria-labelledby="modal-lead-title"
        >
          <div className="modal-panel" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <div>
                <div className="lead-meta">
                  <span
                    className={`badge ${
                      selectedLead.score >= 75 ? 'badge-high' : 'badge-medium'
                    }`}
                  >
                    Score {selectedLead.score}/100
                  </span>
                  <span className="badge badge-low">
                    {selectedLead.classification.replaceAll('_', ' ')}
                  </span>
                </div>
                <h2 id="modal-lead-title">{selectedLead.title}</h2>
              </div>
              <button
                className="btn btn-secondary btn-sm"
                onClick={() => setSelectedLead(null)}
                aria-label="Close details"
              >
                <X size={16} />
              </button>
            </div>

            <div className="score-breakdown">
              {[
                ['ICP Match', selectedLead.score_breakdown.icp_match, 25],
                ['Problem Fit', selectedLead.score_breakdown.problem_fit, 30],
                ['Intent', selectedLead.score_breakdown.buying_intent, 20],
                ['Urgency', selectedLead.score_breakdown.urgency, 15],
                ['Recency', selectedLead.score_breakdown.recency, 10],
              ].map(([label, value, max]) => (
                <div className="score-breakdown-item" key={String(label)}>
                  <span>{label}</span>
                  <strong className="tabular">
                    {value}/{max}
                  </strong>
                </div>
              ))}
              <p>{selectedLead.score_breakdown.explanation}</p>
            </div>

            <div className="detail-block">
              <label className="label">Customer Evidence Quote</label>
              <blockquote>“{selectedLead.excerpt}”</blockquote>
              <p style={{ marginTop: 'var(--sp-2)', fontSize: 'var(--fs-xs)', color: 'var(--text-muted)' }}>
                {selectedLead.evidence}
              </p>
            </div>

            <div className="detail-block">
              <label className="label">Product Value & Fit Explanation</label>
              <div className="fit-callout">{selectedLead.product_fit_explanation}</div>
            </div>

            <div className="modal-actions">
              <a
                className="btn btn-secondary"
                href={selectedLead.url}
                target="_blank"
                rel="noreferrer"
              >
                <ExternalLink size={14} />
                <span>Open original discussion</span>
              </a>
              <button
                className="btn btn-primary"
                onClick={() => {
                  const id = selectedLead.id;
                  setSelectedLead(null);
                  onOpenReplyStudio(id);
                }}
              >
                <MessageSquare size={15} />
                <span>Draft custom reply</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
