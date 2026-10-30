import React, { useState } from 'react';
import {
  Globe,
  FileText,
  CheckCircle2,
  AlertTriangle,
  ExternalLink,
  Sparkles,
  Save,
  ShieldCheck,
} from 'lucide-react';
import type { BusinessProfile } from '../types';
import { api } from '../api';

interface ProfileViewProps {
  profile: BusinessProfile | null;
  onProfileUpdated: (profile: BusinessProfile) => void;
}

export const ProfileView: React.FC<ProfileViewProps> = ({ profile, onProfileUpdated }) => {
  const [activeInputMode, setActiveInputMode] = useState<'url' | 'manual'>('url');
  const [urlInput, setUrlInput] = useState('');
  const [nameInput, setNameInput] = useState('');
  const [descInput, setDescInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [feedback, setFeedback] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'profile' | 'facts' | 'inferences'>('profile');

  // Form edit states
  const [formData, setFormData] = useState<Partial<BusinessProfile>>(profile || {});

  React.useEffect(() => {
    if (profile) setFormData(profile);
  }, [profile]);

  const handleExtractUrl = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!urlInput.trim()) return;
    setLoading(true);
    try {
      const extracted = await api.extractFromUrl(urlInput.trim());
      onProfileUpdated(extracted);
      setFeedback('Profile extracted. Review the facts before confirming it.');
    } catch (err: any) {
      setFeedback(`Extraction failed: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleExtractManual = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!descInput.trim()) return;
    setLoading(true);
    try {
      const extracted = await api.extractFromManual(nameInput.trim(), descInput.trim());
      onProfileUpdated(extracted);
      setFeedback('Profile analyzed. Review the facts before confirming it.');
    } catch (err: any) {
      setFeedback(`Analysis failed: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleSaveProfile = async () => {
    if (!formData) return;
    try {
      const updated = await api.updateProfile(formData as BusinessProfile);
      onProfileUpdated(updated);
      setFeedback('Business profile saved.');
    } catch (err: any) {
      setFeedback(`Save failed: ${err.message}`);
    }
  };

  const handleConfirmProfile = async () => {
    try {
      const confirmed = await api.confirmProfile();
      onProfileUpdated(confirmed);
      setFeedback('Business profile confirmed. You can now launch discovery.');
    } catch (err: any) {
      setFeedback(`Confirmation failed: ${err.message}`);
    }
  };

  return (
    <div style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1.5rem', maxWidth: '1200px' }}>
      {feedback && <div className={`notice ${feedback.includes('failed') || feedback.includes('Failed') ? 'notice-error' : 'notice-info'}`} role="status"><span>{feedback}</span><button className="btn btn-secondary btn-sm" onClick={() => setFeedback(null)}>Dismiss</button></div>}
      {/* Top Banner / Onboarding Section */}
      <div className="card" style={{ padding: '1.25rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem' }}>
          <div>
            <div style={{ fontWeight: 700, fontSize: '1.125rem', color: '#0f172a' }}>
              Business Understanding & ICP Modeling
            </div>
            <div style={{ fontSize: '0.8125rem', color: '#64748b' }}>
              Extract problems solved, ideal customer profile, and buying signals directly from your website or product description.
            </div>
          </div>

          {/* Toggle URL vs Manual */}
          <div style={{ display: 'flex', background: '#f1f5f9', padding: '0.25rem', borderRadius: 'var(--radius)' }}>
            <button
              className="btn btn-sm"
              style={{
                background: activeInputMode === 'url' ? '#ffffff' : 'transparent',
                boxShadow: activeInputMode === 'url' ? '0 1px 2px rgba(0,0,0,0.05)' : 'none',
                color: activeInputMode === 'url' ? 'var(--primary)' : '#64748b',
              }}
              onClick={() => setActiveInputMode('url')}
            >
              <Globe size={14} /> Website URL
            </button>
            <button
              className="btn btn-sm"
              style={{
                background: activeInputMode === 'manual' ? '#ffffff' : 'transparent',
                boxShadow: activeInputMode === 'manual' ? '0 1px 2px rgba(0,0,0,0.05)' : 'none',
                color: activeInputMode === 'manual' ? 'var(--primary)' : '#64748b',
              }}
              onClick={() => setActiveInputMode('manual')}
            >
              <FileText size={14} /> Manual Description
            </button>
          </div>
        </div>

        {activeInputMode === 'url' ? (
          <form onSubmit={handleExtractUrl} style={{ display: 'flex', gap: '0.5rem' }}>
            <input
              type="text"
              className="input"
              placeholder="https://yourcompany.com (crawls homepage, /pricing, /features, /faq)"
              value={urlInput}
              onChange={(e) => setUrlInput(e.target.value)}
              disabled={loading}
              required
            />
            <button type="submit" className="btn btn-primary" disabled={loading}>
              <Sparkles size={16} /> {loading ? 'Analyzing Pages...' : 'Analyze Website'}
            </button>
          </form>
        ) : (
          <form onSubmit={handleExtractManual} style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            <input
              type="text"
              className="input"
              placeholder="Product or Service Name (optional)"
              value={nameInput}
              onChange={(e) => setNameInput(e.target.value)}
              disabled={loading}
            />
            <textarea
              className="textarea"
              rows={3}
              placeholder="Describe what your product does, who it is for, the main problems it solves, pricing, and main competitors..."
              value={descInput}
              onChange={(e) => setDescInput(e.target.value)}
              disabled={loading}
              required
            />
            <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
              <button type="submit" className="btn btn-primary" disabled={loading}>
                <Sparkles size={16} /> {loading ? 'Extracting ICP...' : 'Extract Business Profile'}
              </button>
            </div>
          </form>
        )}
      </div>

      {/* Confirmation & Status Bar if Profile exists */}
      {profile && (
        <div
          className="card"
          style={{
            background: profile.confirmed ? '#ecfdf5' : '#fffbeb',
            borderColor: profile.confirmed ? '#a7f3d0' : '#fde68a',
            padding: '1rem',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            {profile.confirmed ? (
              <ShieldCheck size={20} color="#059669" />
            ) : (
              <AlertTriangle size={20} color="#d97706" />
            )}
            <div>
              <div style={{ fontWeight: 600, color: profile.confirmed ? '#065f46' : '#92400e' }}>
                {profile.confirmed
                  ? 'Profile Confirmed for Discovery'
                  : 'Pending Review & Confirmation'}
              </div>
              <div style={{ fontSize: '0.75rem', color: profile.confirmed ? '#047857' : '#b45309' }}>
                {profile.confirmed
                  ? 'The agent is actively using this confirmed ICP to discover customer opportunities.'
                  : 'Please review the fields below and click Confirm before launching research.'}
              </div>
            </div>
          </div>

          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <button className="btn btn-secondary btn-sm" onClick={handleSaveProfile}>
              <Save size={14} /> Save Edits
            </button>
            {!profile.confirmed && (
              <button className="btn btn-primary btn-sm" onClick={handleConfirmProfile}>
                <CheckCircle2 size={14} /> Confirm Profile
              </button>
            )}
          </div>
        </div>
      )}

      {/* Detail View Tabs */}
      {profile && (
        <div>
          {/* Sub Navigation */}
          <div style={{ display: 'flex', gap: '0.5rem', borderBottom: '1px solid var(--border)', marginBottom: '1rem' }}>
            <button
              onClick={() => setActiveTab('profile')}
              style={{
                padding: '0.5rem 1rem',
                border: 'none',
                background: 'none',
                borderBottom: activeTab === 'profile' ? '2px solid var(--primary)' : '2px solid transparent',
                fontWeight: activeTab === 'profile' ? 600 : 500,
                color: activeTab === 'profile' ? 'var(--primary)' : '#64748b',
                cursor: 'pointer',
              }}
            >
              Core Profile & ICP
            </button>
            <button
              onClick={() => setActiveTab('facts')}
              style={{
                padding: '0.5rem 1rem',
                border: 'none',
                background: 'none',
                borderBottom: activeTab === 'facts' ? '2px solid var(--primary)' : '2px solid transparent',
                fontWeight: activeTab === 'facts' ? 600 : 500,
                color: activeTab === 'facts' ? 'var(--primary)' : '#64748b',
                cursor: 'pointer',
              }}
            >
              Verified Facts ({profile.facts?.length || 0})
            </button>
            <button
              onClick={() => setActiveTab('inferences')}
              style={{
                padding: '0.5rem 1rem',
                border: 'none',
                background: 'none',
                borderBottom: activeTab === 'inferences' ? '2px solid var(--primary)' : '2px solid transparent',
                fontWeight: activeTab === 'inferences' ? 600 : 500,
                color: activeTab === 'inferences' ? 'var(--primary)' : '#64748b',
                cursor: 'pointer',
              }}
            >
              AI Inferences ({profile.inferences?.length || 0})
            </button>
          </div>

          {activeTab === 'profile' && (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '1rem' }}>
              <div className="card">
                <label className="label">Product / Business Name</label>
                <input
                  type="text"
                  className="input"
                  style={{ marginBottom: '1rem' }}
                  value={formData.name || ''}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                />

                <label className="label">Niche & Category</label>
                <input
                  type="text"
                  className="input"
                  style={{ marginBottom: '1rem' }}
                  value={formData.niche || ''}
                  onChange={(e) => setFormData({ ...formData, niche: e.target.value })}
                />

                <label className="label">Ideal Customer Profile (ICP)</label>
                <textarea
                  className="textarea"
                  rows={3}
                  style={{ marginBottom: '1rem' }}
                  value={formData.icp || ''}
                  onChange={(e) => setFormData({ ...formData, icp: e.target.value })}
                />

                <label className="label">Core Offering / Value Proposition</label>
                <textarea
                  className="textarea"
                  rows={3}
                  value={formData.main_product_or_service || ''}
                  onChange={(e) => setFormData({ ...formData, main_product_or_service: e.target.value })}
                />
              </div>

              <div className="card">
                <label className="label">Problems Solved (comma or newline separated)</label>
                <textarea
                  className="textarea"
                  rows={4}
                  style={{ marginBottom: '1rem' }}
                  value={(formData.problems_solved || []).join('\n')}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      problems_solved: e.target.value.split('\n').filter((x) => x.trim()),
                    })
                  }
                />

                <label className="label">Customer Frustrations & Vent Expressions</label>
                <textarea
                  className="textarea"
                  rows={4}
                  style={{ marginBottom: '1rem' }}
                  value={(formData.customer_frustrations || []).join('\n')}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      customer_frustrations: e.target.value.split('\n').filter((x) => x.trim()),
                    })
                  }
                />

                <label className="label">Known Competitors & Alternatives</label>
                <input
                  type="text"
                  className="input"
                  placeholder="e.g. Linear, Jira, Asana"
                  value={(formData.competitors_and_alternatives || []).join(', ')}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      competitors_and_alternatives: e.target.value.split(',').map((x) => x.trim()),
                    })
                  }
                />
              </div>
            </div>
          )}

          {activeTab === 'facts' && (
            <div className="card" style={{ padding: 0 }}>
              <div style={{ padding: '0.75rem 1rem', borderBottom: '1px solid var(--border)', fontSize: '0.75rem', fontWeight: 600, color: '#64748b' }}>
                DIRECT CLAIMS EXTRACTED WITH VERIFIABLE SOURCE LINKS
              </div>
              {profile.facts?.length === 0 ? (
                <div style={{ padding: '2rem', textAlign: 'center', color: '#94a3b8' }}>No verified facts extracted yet.</div>
              ) : (
                profile.facts.map((fact, idx) => (
                  <div key={idx} style={{ padding: '0.875rem 1rem', borderBottom: '1px solid var(--border)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <div>
                      <span className="badge badge-medium" style={{ marginRight: '0.5rem' }}>{fact.category}</span>
                      <span style={{ fontSize: '0.8125rem', color: '#0f172a' }}>{fact.claim}</span>
                    </div>
                    <a
                      href={fact.source_url}
                      target="_blank"
                      rel="noreferrer"
                      style={{ fontSize: '0.75rem', color: 'var(--primary)', textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '4px' }}
                    >
                      <ExternalLink size={12} /> Source Page
                    </a>
                  </div>
                ))
              )}
            </div>
          )}

          {activeTab === 'inferences' && (
            <div className="card" style={{ padding: 0 }}>
              <div style={{ padding: '0.75rem 1rem', borderBottom: '1px solid var(--border)', fontSize: '0.75rem', fontWeight: 600, color: '#64748b' }}>
                AI-DERIVED MARKET & BUYING SIGNAL INFERENCES
              </div>
              {profile.inferences?.length === 0 ? (
                <div style={{ padding: '2rem', textAlign: 'center', color: '#94a3b8' }}>No AI inferences recorded.</div>
              ) : (
                profile.inferences.map((inf, idx) => (
                  <div key={idx} style={{ padding: '1rem', borderBottom: '1px solid var(--border)' }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
                      <span style={{ fontWeight: 600, color: '#0f172a', fontSize: '0.875rem' }}>{inf.insight}</span>
                      <span className="badge badge-high">{Math.round(inf.confidence * 100)}% Confidence</span>
                    </div>
                    <div style={{ fontSize: '0.75rem', color: '#64748b' }}>
                      <strong>Evidence Basis:</strong> {inf.basis}
                    </div>
                  </div>
                ))
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
