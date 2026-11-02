import React, { useState, useEffect, useCallback } from 'react';
import {
  Copy,
  ExternalLink,
  CheckCircle,
  ShieldCheck,
  Send,
  LoaderCircle,
  Compass,
  AlertTriangle,
  Lock,
  Sparkles,
  ShieldAlert,
  AlertCircle,
  Check,
} from 'lucide-react';
import type { GeneratedReply, LeadQualification } from '../types';
import { api } from '../api';

interface ReplyStudioViewProps {
  initialLeadId?: string;
  leads: LeadQualification[];
  onNavigateToDiscovery?: () => void;
}

const PLATFORM_MAX_WORDS: Record<string, number> = {
  twitter: 45,
  github: 120,
  reddit: 150,
  quora: 150,
  web: 150,
  hackernews: 0,
};

const PITCH_LABELS: Record<number, { label: string; desc: string }> = {
  0: { label: 'Pure Value (Level 0)', desc: 'Helpful expert advice, zero product mentions' },
  1: { label: 'Soft Mention (Level 1)', desc: 'Helpful advice with passive solution reference' },
  2: { label: 'Product-Aware (Level 2)', desc: 'Named once with honest first-person disclosure' },
  3: { label: 'Direct Pitch (Level 3)', desc: 'Direct solution recommendation for explicit requests' },
};

function countWords(text: string): number {
  return text.trim() ? text.trim().split(/\s+/).length : 0;
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
  const [publishStatus, setPublishStatus] = useState<{
    type: 'info' | 'error' | 'success';
    message: string;
  } | null>(null);

  const loadLeadAndReply = useCallback(async (id: string) => {
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
        // If Hacker News, the platform bans AI drafts
        if (data.lead.platform === 'hackernews' || data.lead.reply_policy === 'human_only') {
          setReply(null);
          setSelectedVersion('custom');
          setEditedText('');
        } else {
          const generated = await api.generateReply(id);
          setReply(generated);
          setSelectedVersion(generated.selected_version);
          setEditedText(generated.value_first);
        }
      }
    } catch (err: any) {
      setPublishStatus({
        type: 'error',
        message: err instanceof Error ? err.message : 'Could not load discussion and reply draft.',
      });
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (initialLeadId) {
      setSelectedLeadId(initialLeadId);
    } else if (!selectedLeadId && leads.length > 0) {
      setSelectedLeadId(leads[0].id);
    }
  }, [initialLeadId, leads, selectedLeadId]);

  useEffect(() => {
    if (!selectedLeadId) return;
    void loadLeadAndReply(selectedLeadId);
  }, [selectedLeadId, loadLeadAndReply]);

  const handleSelectVersion = (version: 'value_first' | 'product_aware') => {
    if (!reply) return;
    setSelectedVersion(version);
    setEditedText(version === 'product_aware' ? reply.product_aware : reply.value_first);
  };

  const handleApprove = async () => {
    if (!selectedLeadId) return;
    if (selectedVersion === 'custom' && !editedText.trim()) {
      setPublishStatus({
        type: 'error',
        message: 'Please write your reply text before approving.',
      });
      return;
    }
    try {
      const updated = await api.approveReply(selectedLeadId, editedText, selectedVersion);
      setReply(updated);
      setPublishStatus({
        type: 'success',
        message: 'Reply draft approved! You can now proceed to copy and mark for posting.',
      });
    } catch (err: any) {
      setPublishStatus({
        type: 'error',
        message: err instanceof Error ? err.message : 'Approval failed. Please review text rules.',
      });
    }
  };

  const handlePublish = async () => {
    if (!selectedLeadId) return;
    try {
      const res = await api.publishReply(selectedLeadId);
      if (res.success) {
        setPublishStatus({
          type: 'success',
          message: res.message || 'Reply copied to clipboard and discussion link ready. Post on the platform, then click Confirm It Was Posted.',
        });
        if (reply) setReply({ ...reply, status: 'pending_manual_post' });
        await navigator.clipboard.writeText(editedText);
        setCopied(true);
        setTimeout(() => setCopied(false), 3000);
      } else {
        setPublishStatus({
          type: 'error',
          message: res.reason || 'Publishing check prevented posting. Please inspect settings and rules.',
        });
      }
    } catch (err: any) {
      setPublishStatus({
        type: 'error',
        message: err instanceof Error ? err.message : 'Could not proceed with publishing.',
      });
    }
  };

  const handleConfirmPublished = async () => {
    if (!selectedLeadId) return;
    try {
      const res = await api.confirmPublished(selectedLeadId);
      if (res.success) {
        setPublishStatus({
          type: 'success',
          message: res.message || 'Publication successfully confirmed and recorded in history.',
        });
        if (reply) setReply({ ...reply, status: 'published' });
      } else {
        setPublishStatus({
          type: 'error',
          message: res.reason || 'Could not record publication confirmation.',
        });
      }
    } catch (err: any) {
      setPublishStatus({
        type: 'error',
        message: err instanceof Error ? err.message : 'Confirmation request failed.',
      });
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

  const th = lead?.thread_health;
  const isLocked = th?.commentable === false;
  const isCrowded = th?.crowded === true;
  const isHN = lead?.platform === 'hackernews';
  const isHumanOnly = lead?.reply_policy === 'human_only' || isHN;
  const wordCount = countWords(editedText);
  const maxWords = lead ? PLATFORM_MAX_WORDS[lead.platform] || 150 : 150;
  const isOverWordLimit = maxWords > 0 && wordCount > maxWords;

  return (
    <div className="page-shell">
      <div className="page-heading">
        <div>
          <h1>Reply Studio</h1>
          <p>
            Review, personalize, and approve helpful value-first responses with ethical disclosures, automated linting, and platform safety gates.
          </p>
        </div>
      </div>

      {publishStatus && (
        <div
          className={`notice ${
            publishStatus.type === 'error'
              ? 'notice-error'
              : publishStatus.type === 'success'
              ? 'notice-success'
              : 'notice-info'
          }`}
          role="status"
        >
          <span>{publishStatus.message}</span>
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
              style={{ maxWidth: '520px' }}
              value={selectedLeadId}
              onChange={(e) => setSelectedLeadId(e.target.value)}
            >
              {leads.map((l) => (
                <option key={l.id} value={l.id}>
                  [{l.score}/100] {l.platform} · {l.community} - {l.title.slice(0, 48)}…
                </option>
              ))}
            </select>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--sp-2)' }}>
            <span style={{ fontSize: 'var(--fs-xs)', color: 'var(--text-subtle)' }}>Workflow State:</span>
            <span
              className={`badge ${
                reply?.status === 'published'
                  ? 'badge-high'
                  : reply?.status === 'pending_manual_post'
                  ? 'badge-amber'
                  : reply?.status === 'approved'
                  ? 'badge-medium'
                  : 'badge-low'
              }`}
            >
              {reply?.status === 'pending_manual_post'
                ? 'Pending Manual Post'
                : reply?.status === 'published'
                ? 'Published'
                : reply?.status === 'approved'
                ? 'Approved'
                : 'Draft'}
            </span>
          </div>
        </div>
      </section>

      {loading || !lead ? (
        <div className="panel" style={{ padding: 'var(--sp-12)', textAlign: 'center' }}>
          <LoaderCircle className="spin" size={24} style={{ margin: '0 auto var(--sp-2)', color: 'var(--primary)' }} />
          <div>Synthesizing context and drafting compliant response…</div>
        </div>
      ) : (
        <section className="studio-grid">
          {/* Left Column: Context & Evidence */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--sp-4)' }}>
            <div className="card" style={{ padding: 'var(--sp-5)' }}>
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  marginBottom: 'var(--sp-2)',
                  flexWrap: 'wrap',
                  gap: 'var(--sp-2)',
                }}
              >
                <div style={{ display: 'flex', gap: 'var(--sp-2)', alignItems: 'center' }}>
                  <span className="badge badge-medium">{lead.platform}</span>
                  {lead.judged_by === 'llm' && (
                    <span className="badge badge-high">
                      <Sparkles size={11} style={{ display: 'inline', marginRight: '3px' }} />
                      AI Scored
                    </span>
                  )}
                  {lead.competitor_mentioned && (
                    <span className="badge badge-amber">vs {lead.competitor_mentioned}</span>
                  )}
                </div>

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
                    fontWeight: 600,
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
                Posted by <strong>{lead.author || 'Author'}</strong> in <strong>{lead.community}</strong> · {lead.published_at || 'Recent'}
              </div>

              {/* Thread Health Pill */}
              {th && (
                <div
                  style={{
                    background: isLocked ? 'var(--danger-bg)' : 'var(--surface-subtle)',
                    border: `1px solid ${isLocked ? 'var(--danger-border)' : 'var(--border)'}`,
                    borderRadius: 'var(--r-sm)',
                    padding: 'var(--sp-2) var(--sp-3)',
                    marginBottom: 'var(--sp-3)',
                    display: 'flex',
                    gap: 'var(--sp-3)',
                    alignItems: 'center',
                    fontSize: 'var(--fs-2xs)',
                    flexWrap: 'wrap',
                  }}
                >
                  {isLocked ? (
                    <span style={{ color: 'var(--danger-text)', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '4px' }}>
                      <Lock size={12} />
                      Archived / Locked on Platform
                    </span>
                  ) : (
                    <span style={{ color: 'var(--success-text)', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '4px' }}>
                      <Check size={12} />
                      Open for Replies
                    </span>
                  )}

                  {th.num_comments !== undefined && th.num_comments !== null && (
                    <span style={{ color: 'var(--text-subtle)' }}>
                      {th.num_comments} replies
                    </span>
                  )}

                  {isCrowded && (
                    <span className="badge badge-amber" style={{ fontSize: '10px' }}>
                      Crowded thread (&gt;80 replies)
                    </span>
                  )}

                  {th.age_days !== undefined && th.age_days !== null && (
                    <span style={{ color: 'var(--text-subtle)' }}>
                      {th.age_days}d old
                    </span>
                  )}
                </div>
              )}

              {/* Platform Policy Alert */}
              {isHumanOnly && (
                <div className="notice notice-warning" style={{ margin: '0 0 var(--sp-3) 0', padding: 'var(--sp-3)' }}>
                  <ShieldAlert size={16} />
                  <div>
                    <strong>Platform Policy Notice</strong>
                    <span>
                      {isHN
                        ? 'Hacker News rules ban generated or AI-edited comments (March 2026). Hand-crafted human replies only.'
                        : 'This platform forbids automated bot drafts. Hand-craft your response or use this context for customer research.'}
                    </span>
                  </div>
                </div>
              )}

              {/* Targeting specific comment */}
              {reply?.target_kind === 'comment' && reply.target_author && (
                <div
                  style={{
                    marginBottom: 'var(--sp-3)',
                    padding: 'var(--sp-2) var(--sp-3)',
                    background: 'var(--info-bg)',
                    border: '1px solid var(--info-border)',
                    borderRadius: 'var(--r-sm)',
                    fontSize: 'var(--fs-2xs)',
                    color: 'var(--info-text)',
                  }}
                >
                  <strong>Targeting Comment by {reply.target_author}:</strong> &ldquo;{reply.target_text}&rdquo;
                  {reply.target_reason && (
                    <div style={{ marginTop: '2px', opacity: 0.85 }}>Reason: {reply.target_reason}</div>
                  )}
                </div>
              )}

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
              <h3 className="section-title">Customer Problem & Product Value Match</h3>
              <div style={{ fontSize: 'var(--fs-base)', fontWeight: 600, color: 'var(--text-main)', marginBottom: 'var(--sp-2)' }}>
                {lead.customer_problem}
              </div>
              <div className="fit-callout">
                <strong>Why your solution fits:</strong> {lead.product_fit_explanation}
              </div>
            </div>
          </div>

          {/* Right Column: Reply Composition */}
          <div className="card" style={{ padding: 'var(--sp-5)', display: 'flex', flexDirection: 'column', gap: 'var(--sp-4)' }}>
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--sp-2)' }}>
                <h3 className="section-title" style={{ margin: 0 }}>Reply Strategy</h3>
                {reply?.pitch_level !== undefined && (
                  <span className="badge badge-low" title={PITCH_LABELS[reply.pitch_level]?.desc}>
                    {PITCH_LABELS[reply.pitch_level]?.label || `Pitch Level ${reply.pitch_level}`}
                  </span>
                )}
              </div>

              {!isHumanOnly && (
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
              )}
            </div>

            {/* Warning if thread is locked */}
            {isLocked && (
              <div className="notice notice-warning" style={{ margin: 0 }}>
                <AlertTriangle size={15} />
                <span>
                  This thread is locked or archived. You can copy the reply for notes or follow-ups, but replies cannot be submitted to this URL.
                </span>
              </div>
            )}

            {/* Linter warnings / issues if any */}
            {reply?.needs_human_edit && (
              <div className="notice notice-warning" style={{ margin: 0 }}>
                <AlertCircle size={15} />
                <div>
                  <strong>Human Polish Recommended</strong>
                  <span>The AI draft flagged rule exceptions. Please review and adjust the text before approving.</span>
                </div>
              </div>
            )}

            {reply?.lint && reply.lint.issues && reply.lint.issues.length > 0 && (
              <div
                style={{
                  padding: 'var(--sp-2) var(--sp-3)',
                  background: 'var(--warning-bg)',
                  border: '1px solid var(--warning-border)',
                  borderRadius: 'var(--r-sm)',
                  fontSize: 'var(--fs-2xs)',
                  color: 'var(--warning-text)',
                }}
              >
                <strong>Linter Observations:</strong>
                <ul style={{ paddingLeft: 'var(--sp-4)', marginTop: '2px' }}>
                  {reply.lint.issues.map((iss: string, idx: number) => (
                    <li key={idx}>{iss}</li>
                  ))}
                </ul>
              </div>
            )}

            <div className="form-group" style={{ flex: 1 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <label htmlFor="reply-editor-textarea" className="label">
                  Response Draft (Fully Editable)
                </label>
                <span
                  style={{
                    fontSize: 'var(--fs-2xs)',
                    color: isOverWordLimit ? 'var(--danger-text)' : 'var(--text-subtle)',
                    fontWeight: 600,
                  }}
                >
                  {wordCount} words {maxWords > 0 ? `/ ${maxWords} max` : ''}
                </span>
              </div>
              <textarea
                id="reply-editor-textarea"
                className="textarea"
                rows={9}
                style={{ minHeight: '200px', lineHeight: '1.6' }}
                placeholder={
                  isHumanOnly
                    ? 'Write your original helpful response here. Platform policy requires manual, genuine human text.'
                    : 'Craft your response here…'
                }
                value={editedText}
                onChange={(e) => {
                  setEditedText(e.target.value);
                  setSelectedVersion('custom');
                }}
              />
            </div>

            {/* Ethical Disclosure Preview */}
            {reply?.affiliation_disclosure && selectedVersion === 'product_aware' && (
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

            {/* Workflow Action Bar */}
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
                <button
                  className="btn btn-secondary btn-sm"
                  onClick={handleApprove}
                  disabled={!editedText.trim()}
                >
                  <CheckCircle size={14} />
                  <span>Approve Draft</span>
                </button>

                {reply?.status === 'pending_manual_post' ? (
                  <button className="btn btn-primary btn-sm" onClick={handleConfirmPublished}>
                    <CheckCircle size={14} />
                    <span>Confirm It Was Posted</span>
                  </button>
                ) : (
                  <button
                    className="btn btn-primary btn-sm"
                    onClick={handlePublish}
                    disabled={!editedText.trim()}
                  >
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

export default ReplyStudioView;
