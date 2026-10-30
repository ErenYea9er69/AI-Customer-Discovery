import React, { useState, useEffect } from 'react';
import {
  MessageSquare,
  Copy,
  ExternalLink,
  CheckCircle,
  ShieldCheck,
  Send,
} from 'lucide-react';
import type { GeneratedReply, LeadQualification } from '../types';
import { api } from '../api';

interface ReplyStudioViewProps {
  initialLeadId?: string;
  leads: LeadQualification[];
}

export const ReplyStudioView: React.FC<ReplyStudioViewProps> = ({ initialLeadId, leads }) => {
  const [selectedLeadId, setSelectedLeadId] = useState<string>(initialLeadId || (leads[0]?.id || ''));
  const [lead, setLead] = useState<LeadQualification | null>(null);
  const [reply, setReply] = useState<GeneratedReply | null>(null);
  const [selectedVersion, setSelectedVersion] = useState<'value_first' | 'product_aware' | 'custom'>('value_first');
  const [editedText, setEditedText] = useState('');
  const [copied, setCopied] = useState(false);
  const [loading, setLoading] = useState(false);
  const [publishStatus, setPublishStatus] = useState<string | null>(null);

  useEffect(() => {
    if (initialLeadId) {
      setSelectedLeadId(initialLeadId);
    } else if (!selectedLeadId && leads.length > 0) {
      setSelectedLeadId(leads[0].id);
    }
  }, [initialLeadId, leads]);

  useEffect(() => {
    if (!selectedLeadId) return;
    loadLeadAndReply(selectedLeadId);
  }, [selectedLeadId]);

  const loadLeadAndReply = async (id: string) => {
    setLoading(true);
    setPublishStatus(null);
    try {
      const data = await api.getLead(id);
      setLead(data.lead);

      if (data.reply) {
        setReply(data.reply);
        setSelectedVersion(data.reply.selected_version);
        setEditedText(data.reply.edited_reply || (data.reply.selected_version === 'product_aware' ? data.reply.product_aware : data.reply.value_first));
      } else {
        // Auto-generate reply if none exists
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
      setPublishStatus('Reply approved. It is ready to publish or copy.');
    } catch (err: any) {
      setPublishStatus(`Approval error: ${err.message}`);
    }
  };

  const handlePublish = async () => {
    if (!selectedLeadId) return;
    try {
      const res = await api.publishReply(selectedLeadId);
      if (res.success) {
        setPublishStatus(res.message || 'Reply copied. Confirm once you have submitted it.');
        if (reply) setReply({ ...reply, status: 'pending_manual_post' });
        // Also copy to clipboard for convenience
        navigator.clipboard.writeText(editedText);
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
      setPublishStatus(res.message || 'Publication confirmed and recorded.');
      if (reply) setReply({ ...reply, status: 'published' });
    } else {
      setPublishStatus(`Could not confirm: ${res.reason || 'Try again.'}`);
    }
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(editedText);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (leads.length === 0) {
    return (
      <div style={{ padding: '3rem', textAlign: 'center', color: '#94a3b8' }}>
        No leads discovered yet. Please run a discovery campaign to generate replies.
      </div>
    );
  }

  return (
    <div style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1.5rem', maxWidth: '1200px' }}>
      {/* Top selector */}
      <div className="card" style={{ padding: '0.75rem 1rem', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <MessageSquare size={18} color="var(--primary)" />
          <span style={{ fontWeight: 600, color: '#0f172a' }}>Select Opportunity to Reply:</span>
          <select
            className="select"
            style={{ width: '380px' }}
            value={selectedLeadId}
            onChange={(e) => setSelectedLeadId(e.target.value)}
          >
            {leads.map((l) => (
              <option key={l.id} value={l.id}>
                [{l.score}/100] {l.community} - {l.title.slice(0, 45)}...
              </option>
            ))}
          </select>
        </div>

        {reply && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
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
                Status: {reply.status === 'pending_manual_post' ? 'awaiting confirmation' : reply.status}
            </span>
          </div>
        )}
      </div>

      {loading || !lead ? (
        <div style={{ padding: '3rem', textAlign: 'center', color: '#94a3b8' }}>Loading lead intelligence...</div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1.2fr', gap: '1.5rem' }}>
          {/* Left Column: Original Conversation & Extracted Problem */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div className="card">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                <span className="badge badge-medium">{lead.platform}</span>
                <a
                  href={lead.url}
                  target="_blank"
                  rel="noreferrer"
                  style={{ fontSize: '0.75rem', color: 'var(--primary)', textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '4px' }}
                >
                  <ExternalLink size={12} /> View Original Discussion
                </a>
              </div>

              <h3 style={{ fontSize: '1rem', fontWeight: 700, color: '#0f172a', marginBottom: '0.5rem' }}>
                {lead.title}
              </h3>

              <div style={{ fontSize: '0.75rem', color: '#64748b', marginBottom: '0.75rem' }}>
                Posted by <strong>{lead.author}</strong> in <strong>{lead.community}</strong> on {lead.published_at}
              </div>

              <div
                style={{
                  fontSize: '0.8125rem',
                  color: '#334155',
                  background: '#f8fafc',
                  border: '1px solid var(--border)',
                  borderRadius: 'var(--radius)',
                  padding: '0.875rem',
                  lineHeight: 1.6,
                }}
              >
                "{lead.excerpt}"
              </div>
            </div>

            {/* Extracted Problem & Evidence */}
            <div className="card">
              <label className="label">Exact Problem Identified</label>
              <div style={{ fontSize: '0.875rem', fontWeight: 600, color: '#0f172a', marginBottom: '0.75rem' }}>
                {lead.customer_problem}
              </div>

              <label className="label">Recommended Product Angle</label>
              <div style={{ fontSize: '0.8125rem', color: '#047857', background: '#ecfdf5', padding: '0.625rem', borderRadius: 'var(--radius)', border: '1px solid #a7f3d0' }}>
                {lead.product_fit_explanation}
              </div>
            </div>
          </div>

          {/* Right Column: AI Reply Studio */}
          <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                <span style={{ fontWeight: 700, fontSize: '0.9375rem', color: '#0f172a' }}>
                  Response Strategy
                </span>

                {/* Variant Switcher */}
                <div style={{ display: 'flex', background: '#f1f5f9', padding: '0.25rem', borderRadius: 'var(--radius)' }}>
                  <button
                    className="btn btn-sm"
                    style={{
                      background: selectedVersion === 'value_first' ? '#ffffff' : 'transparent',
                      color: selectedVersion === 'value_first' ? 'var(--primary)' : '#64748b',
                      boxShadow: selectedVersion === 'value_first' ? '0 1px 2px rgba(0,0,0,0.05)' : 'none',
                    }}
                    onClick={() => handleSelectVersion('value_first')}
                  >
                    1. Value-First (No Pitch)
                  </button>
                  <button
                    className="btn btn-sm"
                    style={{
                      background: selectedVersion === 'product_aware' ? '#ffffff' : 'transparent',
                      color: selectedVersion === 'product_aware' ? 'var(--primary)' : '#64748b',
                      boxShadow: selectedVersion === 'product_aware' ? '0 1px 2px rgba(0,0,0,0.05)' : 'none',
                    }}
                    onClick={() => handleSelectVersion('product_aware')}
                  >
                    2. Product-Aware (Disclosed)
                  </button>
                </div>
              </div>

              <div style={{ fontSize: '0.75rem', color: '#64748b' }}>
                {selectedVersion === 'value_first'
                  ? 'Pure value. Direct technical and practical advice with zero product pitch. Best for strict anti-promotion subreddits.'
                  : 'Helpful answer with transparent product mention and affiliation disclosure. Complies with community rules.'}
              </div>
            </div>

            {/* Editable Reply Box */}
            <div style={{ display: 'flex', flexDirection: 'column', flex: 1 }}>
              <label className="label">Customizable Response Text</label>
              <textarea
                className="textarea"
                rows={10}
                style={{ fontSize: '0.875rem', lineHeight: 1.6 }}
                value={editedText}
                onChange={(e) => {
                  setEditedText(e.target.value);
                  setSelectedVersion('custom');
                }}
              />
            </div>

            {/* Affiliation Disclosure Note */}
            {reply && (
              <div style={{ fontSize: '0.6875rem', color: '#64748b', display: 'flex', alignItems: 'center', gap: '0.375rem' }}>
                <ShieldCheck size={14} color="#10b981" />
                <span>Includes mandatory disclosure: "{reply.affiliation_disclosure}"</span>
              </div>
            )}

            {/* Status message */}
            {publishStatus && (
              <div
                style={{
                  padding: '0.5rem 0.75rem',
                  borderRadius: 'var(--radius)',
                  fontSize: '0.75rem',
                  background: publishStatus.startsWith('Failed') ? '#fef2f2' : '#ecfdf5',
                  color: publishStatus.startsWith('Failed') ? '#b91c1c' : '#047857',
                  border: `1px solid ${publishStatus.startsWith('Failed') ? '#fecaca' : '#a7f3d0'}`,
                }}
              >
                {publishStatus}
              </div>
            )}

            {/* Actions Toolbar */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingTop: '0.75rem', borderTop: '1px solid var(--border)' }}>
              <button className="btn btn-secondary" onClick={handleCopy}>
                {copied ? <CheckCircle size={16} color="#10b981" /> : <Copy size={16} />}
                {copied ? 'Copied to Clipboard!' : 'Copy to Clipboard'}
              </button>

              <div style={{ display: 'flex', gap: '0.5rem' }}>
                <button className="btn btn-secondary" onClick={handleApprove}>
                  <CheckCircle size={16} /> Approve Reply
                </button>
                {reply?.status === 'pending_manual_post' ? (
                  <button className="btn btn-primary" onClick={handleConfirmPublished}>
                    <CheckCircle size={16} /> Confirm posted
                  </button>
                ) : (
                  <button className="btn btn-primary" onClick={handlePublish}>
                    <Send size={16} /> Approve & Publish
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
