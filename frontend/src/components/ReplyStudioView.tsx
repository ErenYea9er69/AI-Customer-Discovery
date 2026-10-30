import React, { useState, useEffect } from 'react';
import {
  Copy,
  ExternalLink,
  CheckCircle,
  ShieldCheck,
  Send,
  LoaderCircle,
  Compass,
} from 'lucide-react';
import type { GeneratedReply, LeadQualification } from '../types';
import { api } from '../api';

interface ReplyStudioViewProps {
  initialLeadId?: string;
  leads: LeadQualification[];
  onNavigateToDiscovery?: () => void;
}

export const ReplyStudioView: React.FC<ReplyStudioViewProps> = ({
  initialLeadId,
  leads,
  onNavigateToDiscovery,
}) => {
  const [selectedLeadId, setSelectedLeadId] = useState<string>(initialLeadId || (leads[0]?.id || ''));
  const [lead, setLead] = useState<LeadQualification | null>(null);
  const [reply, setReply] = useState<GeneratedReply | null>(null);
  const [selectedVersion, setSelectedVersion] = useState<'value_first' | 'product_aware' | 'custom'>('value_first');
  const [editedText, setEditedText] = useState('');
  const [copied, setCopied] = useState(false);
  const [loading, setLoading] = useState(false);
  const [publishStatus, setPublishStatus] = useState<string | null>(null);

  const loadLeadAndReply = async (id: string) => {
    setLoading(true);
    setPublishStatus(null);
    try {
      const data = await api.getLead(id);
      setLead(data.lead);

      if (data.reply) {
        setReply(data.reply);
        setSelectedVersion(data.reply.selected_version);
        setEditedText(
          data.reply.edited_reply ||
            (data.reply.selected_version === 'product_aware'
              ? data.reply.product_aware
              : data.reply.value_first)
        );
      } else {
        const generated = await api.generateReply(id);
        setReply(generated);
        setSelectedVersion(generated.selected_version);
        setEditedText(generated.value_first);
      }
    } catch (err: any) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (initialLeadId) {
      setSelectedLeadId(initialLeadId);
    } else if (!selectedLeadId && leads.length > 0) {
      setSelectedLeadId(leads[0].id);
    }
  }, [initialLeadId, leads]);

  useEffect(() => {
    if (!selectedLeadId) return;
    void loadLeadAndReply(selectedLeadId);
  }, [selectedLeadId]);

  const handleSelectVersion = (version: 'value_first' | 'product_aware') => {
    if (!reply) return;
    setSelectedVersion(version);
    setEditedText(version === 'product_aware' ? reply.product_aware : reply.value_first);
  };

  const handleApprove = async () => {
    if (!selectedLeadId) return;
    try {
      const updated = await api.approveReply(selectedLeadId, editedText, selectedVersion);
      setReply(updated);
      setPublishStatus('Reply approved. Ready to copy or publish.');
    } catch (err: any) {
      setPublishStatus(`Approval error: ${err.message}`);
    }
  };

  const handlePublish = async () => {
    if (!selectedLeadId) return;
    try {
      const res = await api.publishReply(selectedLeadId);
      if (res.success) {
        setPublishStatus(res.message || 'Reply copied to clipboard. Confirm once submitted.');
        if (reply) setReply({ ...reply, status: 'pending_manual_post' });
        await navigator.clipboard.writeText(editedText);
        setCopied(true);
        setTimeout(() => setCopied(false), 2500);
      } else {
        setPublishStatus(`Failed: ${res.reason}`);
      }
    } catch (err: any) {
      setPublishStatus(`Error: ${err.message}`);
    }
  };

  const handleConfirmPublished = async () => {
    if (!selectedLeadId) return;
    const res = await api.confirmPublished(selectedLeadId);
    if (res.success) {
      setPublishStatus(res.message || 'Publication confirmed and recorded in history.');
      if (reply) setReply({ ...reply, status: 'published' });
    } else {
      setPublishStatus(`Could not confirm: ${res.reason || 'Try again.'}`);
    }
  };

  const handleCopy = async () => {
    await navigator.clipboard.writeText(editedText);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (leads.length === 0) {
    return (
      <div className="page-shell">
        <div className="empty-state panel" style={{ marginTop: 'var(--sp-8)' }}>
          <div className="empty-icon">
            <Compass size={24} />
          </div>
          <strong>No leads in review queue</strong>
          <span>
            Run a customer discovery campaign to uncover discussions and auto-generate value-first reply drafts.
          </span>
          {onNavigateToDiscovery && (
            <button className="btn btn-primary" onClick={onNavigateToDiscovery} style={{ marginTop: 'var(--sp-2)' }}>
              <Compass size={16} />
              <span>Launch Discovery Engine</span>
            </button>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="page-shell">
      <div className="page-heading">
        <div>
          <h1>Reply Studio</h1>
          <p>
            Generate helpful, value-first replies with transparent affiliation disclosures and human approval gates.
          </p>
        </div>
      </div>

      {publishStatus && (
        <div
          className={`notice ${publishStatus.toLowerCase().includes('error') ? 'notice-error' : 'notice-info'}`}
          role="status"
        >
          <span>{publishStatus}</span>
          <button className="btn btn-secondary btn-sm" onClick={() => setPublishStatus(null)}>
            Dismiss
          </button>
        </div>
      )}

      {/* Target Selector Bar */}
      <section className="panel" style={{ padding: 'var(--sp-3) var(--sp-4)', marginBottom: 'var(--sp-5)' }}>
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: 'var(--sp-4)',
            flexWrap: 'wrap',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--sp-3)', flex: 1, minWidth: '280px' }}>
            <label htmlFor="reply-lead-selector" className="label" style={{ whiteSpace: 'nowrap' }}>
              Select Discussion:
            </label>
            <select
              id="reply-lead-selector"
              className="select"
              style={{ maxWidth: '480px' }}
              value={selectedLeadId}
              onChange={(e) => setSelectedLeadId(e.target.value)}
            >
              {leads.map((l) => (
                <option key={l.id} value={l.id}>
                  [{l.score}/100] {l.community} - {l.title.slice(0, 48)}…
                </option>
              ))}
            </select>
          </div>

          {reply && (
            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--sp-2)' }}>
              <span style={{ fontSize: 'var(--fs-xs)', color: 'var(--text-subtle)' }}>Workflow State:</span>
              <span
                className={`badge ${
                  reply.status === 'published'
                    ? 'badge-high'
                    : reply.status === 'pending_manual_post'
                    ? 'badge-amber'
                    : reply.status === 'approved'
                    ? 'badge-medium'
                    : 'badge-low'
                }`}
              >
                {reply.status === 'pending_manual_post' ? 'Awaiting Confirmation' : reply.status}
              </span>
            </div>
          )}
        </div>
      </section>

      {loading || !lead ? (
        <div className="panel" style={{ padding: 'var(--sp-12)', textAlign: 'center' }}>
          <LoaderCircle className="spin" size={24} style={{ margin: '0 auto var(--sp-2)', color: 'var(--primary)' }} />
          <div>Synthesizing context and drafting response…</div>
        </div>
      ) : (
        <section className="studio-grid">
          {/* Left Column: Original Context */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--sp-4)' }}>
            <div className="card" style={{ padding: 'var(--sp-5)' }}>
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  marginBottom: 'var(--sp-2)',
                }}
              >
                <span className="badge badge-medium">{lead.platform}</span>
                <a
                  href={lead.url}
                  target="_blank"
                  rel="noreferrer"
                  style={{
                    fontSize: 'var(--fs-xs)',
                    color: 'var(--primary)',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '4px',
                  }}
                >
                  <ExternalLink size={13} />
                  <span>View Original Thread</span>
                </a>
              </div>

              <h2 style={{ fontSize: 'var(--fs-md)', fontWeight: 700, color: 'var(--text-main)', marginBottom: 'var(--sp-1)' }}>
                {lead.title}
              </h2>

              <div style={{ fontSize: 'var(--fs-xs)', color: 'var(--text-subtle)', marginBottom: 'var(--sp-3)' }}>
                Posted by <strong>{lead.author}</strong> in <strong>{lead.community}</strong> · {lead.published_at || 'Recent'}
              </div>

              <div
                style={{
                  fontSize: 'var(--fs-sm)',
                  color: 'var(--text-muted)',
                  background: 'var(--surface-subtle)',
                  border: '1px solid var(--border)',
                  borderRadius: 'var(--r-md)',
                  padding: 'var(--sp-3)',
                  lineHeight: '1.5',
                  maxHeight: '220px',
                  overflowY: 'auto',
                }}
              >
                {lead.excerpt}
              </div>
            </div>

            {/* Extracted Problem & Product Angle */}
            <div className="card" style={{ padding: 'var(--sp-5)' }}>
              <h3 className="section-title">Identified Need & Opportunity</h3>
              <div style={{ fontSize: 'var(--fs-base)', fontWeight: 600, color: 'var(--text-main)', marginBottom: 'var(--sp-2)' }}>
                {lead.customer_problem}
              </div>
              <div className="fit-callout">
                <strong>Why your product fits:</strong> {lead.product_fit_explanation}
              </div>
            </div>
          </div>

          {/* Right Column: Reply Composition */}
          <div className="card" style={{ padding: 'var(--sp-5)', display: 'flex', flexDirection: 'column', gap: 'var(--sp-4)' }}>
            <div>
              <h3 className="section-title">Draft Strategy</h3>
              <div className="version-toggle-bar">
                <button
                  type="button"
                  className={`version-tab ${selectedVersion === 'value_first' ? 'active' : ''}`}
                  onClick={() => handleSelectVersion('value_first')}
                >
                  Value-First (Helpful Advice)
                </button>
                <button
                  type="button"
                  className={`version-tab ${selectedVersion === 'product_aware' ? 'active' : ''}`}
                  onClick={() => handleSelectVersion('product_aware')}
                >
                  Product-Aware (With Disclosure)
                </button>
              </div>
            </div>

            <div className="form-group" style={{ flex: 1 }}>
              <label htmlFor="reply-editor-textarea" className="label">
                Response Draft (Fully Editable)
              </label>
              <textarea
                id="reply-editor-textarea"
                className="textarea"
                rows={10}
                style={{ minHeight: '220px', lineHeight: '1.6' }}
                value={editedText}
                onChange={(e) => {
                  setEditedText(e.target.value);
                  setSelectedVersion('custom');
                }}
              />
            </div>

            {reply?.affiliation_disclosure && (
              <div
                style={{
                  padding: 'var(--sp-2) var(--sp-3)',
                  background: 'var(--surface-subtle)',
                  borderRadius: 'var(--r-sm)',
                  fontSize: 'var(--fs-2xs)',
                  color: 'var(--text-subtle)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 'var(--sp-2)',
                }}
              >
                <ShieldCheck size={14} color="var(--primary)" />
                <span>
                  <strong>Ethical Disclosure:</strong> {reply.affiliation_disclosure}
                </span>
              </div>
            )}

            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                gap: 'var(--sp-3)',
                paddingTop: 'var(--sp-3)',
                borderTop: '1px solid var(--border)',
                flexWrap: 'wrap',
              }}
            >
              <button className="btn btn-secondary btn-sm" onClick={handleCopy}>
                <Copy size={14} />
                <span>{copied ? 'Copied to Clipboard!' : 'Copy Text'}</span>
              </button>

              <div style={{ display: 'flex', gap: 'var(--sp-2)' }}>
                <button className="btn btn-secondary btn-sm" onClick={handleApprove}>
                  <CheckCircle size={14} />
                  <span>Approve Draft</span>
                </button>

                {reply?.status === 'pending_manual_post' ? (
                  <button className="btn btn-primary btn-sm" onClick={handleConfirmPublished}>
                    <CheckCircle size={14} />
                    <span>Confirm It Was Posted</span>
                  </button>
                ) : (
                  <button className="btn btn-primary btn-sm" onClick={handlePublish}>
                    <Send size={14} />
                    <span>Copy & Mark for Posting</span>
                  </button>
                )}
              </div>
            </div>
          </div>
        </section>
      )}
    </div>
  );
};
