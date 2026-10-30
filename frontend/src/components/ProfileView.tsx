import React, { useState } from 'react';
import {
  Globe,
  FileText,
  CheckCircle2,
  AlertTriangle,
  ExternalLink,
  Target,
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
      setFeedback('Profile extracted from website. Review the facts before confirming.');
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
      setFeedback('Profile synthesized from description. Review the facts before confirming.');
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
      setFeedback('Business profile confirmed. You can now launch discovery campaigns.');
    } catch (err: any) {
      setFeedback(`Confirmation failed: ${err.message}`);
    }
  };

  return (
    <div className="page-shell">
      <div className="page-heading">
        <div>
          <h1>Business Profile & ICP</h1>
          <p>
            Extract your value proposition, customer pain points, and ideal customer profile from your website or product description.
          </p>
        </div>
      </div>

      {feedback && (
        <div
          className={`notice ${feedback.toLowerCase().includes('fail') || feedback.toLowerCase().includes('error') ? 'notice-error' : 'notice-info'}`}
          role="status"
        >
          <span>{feedback}</span>
          <button className="btn btn-secondary btn-sm" onClick={() => setFeedback(null)}>
            Dismiss
          </button>
        </div>
      )}

      {/* Top Banner / Onboarding Section */}
      <section className="panel" style={{ marginBottom: 'var(--sp-6)' }}>
        <div className="panel-header">
          <div>
            <h2>Extract or Update Business Understanding</h2>
            <p>Provide your live website URL or write a product overview to auto-discover customer pain patterns.</p>
          </div>

          {/* Toggle URL vs Manual */}
          <div className="version-toggle-bar" style={{ alignSelf: 'center' }}>
            <button
              type="button"
              className={`version-tab ${activeInputMode === 'url' ? 'active' : ''}`}
              onClick={() => setActiveInputMode('url')}
            >
              <Globe size={13} style={{ display: 'inline', marginRight: '4px' }} />
              Website URL
            </button>
            <button
              type="button"
              className={`version-tab ${activeInputMode === 'manual' ? 'active' : ''}`}
              onClick={() => setActiveInputMode('manual')}
            >
              <FileText size={13} style={{ display: 'inline', marginRight: '4px' }} />
              Manual Description
            </button>
          </div>
        </div>

        {activeInputMode === 'url' ? (
          <form onSubmit={handleExtractUrl} style={{ display: 'flex', gap: 'var(--sp-3)', flexWrap: 'wrap' }}>
            <div style={{ flex: 1, minWidth: '280px' }}>
              <input
                id="profile-url-input"
                aria-label="Website URL"
                type="url"
                className="input"
                placeholder="https://yourproduct.com (crawls features, pricing, and FAQ)"
                value={urlInput}
                onChange={(e) => setUrlInput(e.target.value)}
                disabled={loading}
                required
              />
            </div>
            <button type="submit" className="btn btn-primary" disabled={loading}>
              <Globe size={16} />
              <span>{loading ? 'Analyzing Pages…' : 'Analyze Website'}</span>
            </button>
          </form>
        ) : (
          <form onSubmit={handleExtractManual} style={{ display: 'flex', flexDirection: 'column', gap: 'var(--sp-3)' }}>
            <input
              id="profile-manual-name"
              aria-label="Product or Service Name"
              type="text"
              className="input"
              placeholder="Product or Service Name"
              value={nameInput}
              onChange={(e) => setNameInput(e.target.value)}
              disabled={loading}
            />
            <textarea
              id="profile-manual-desc"
              aria-label="Product or Service Description"
              className="textarea"
              rows={3}
              placeholder="Describe what your product does, problems it solves, target users, and key differentiators…"
              value={descInput}
              onChange={(e) => setDescInput(e.target.value)}
              disabled={loading}
              required
            />
            <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
              <button type="submit" className="btn btn-primary" disabled={loading}>
                <FileText size={16} />
                <span>{loading ? 'Extracting ICP…' : 'Extract Business Profile'}</span>
              </button>
            </div>
          </form>
        )}
      </section>

      {/* Confirmation & Status Bar if Profile exists */}
      {profile && (
        <section
          className="card"
          style={{
            padding: 'var(--sp-4) var(--sp-5)',
            marginBottom: 'var(--sp-6)',
            background: profile.confirmed ? 'var(--success-bg)' : 'var(--warning-bg)',
            borderColor: profile.confirmed ? 'var(--success-border)' : 'var(--warning-border)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: 'var(--sp-4)',
            flexWrap: 'wrap',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--sp-3)' }}>
            {profile.confirmed ? (
              <ShieldCheck size={22} color="var(--success)" />
            ) : (
              <AlertTriangle size={22} color="var(--warning)" />
            )}
            <div>
              <div
                style={{
                  fontWeight: 700,
                  fontSize: 'var(--fs-base)',
                  color: profile.confirmed ? 'var(--success-text)' : 'var(--warning-text)',
                }}
              >
                {profile.confirmed ? 'Profile Confirmed for Discovery' : 'Pending Review & Confirmation'}
              </div>
              <div
                style={{
                  fontSize: 'var(--fs-xs)',
                  color: profile.confirmed ? '#065f46' : '#78350f',
                  marginTop: '2px',
                }}
              >
                {profile.confirmed
                  ? 'AgentReach uses this ICP model to score community conversations.'
                  : 'Review the facts and parameters below, then click Confirm to unlock autonomous discovery.'}
              </div>
            </div>
          </div>

          <div style={{ display: 'flex', gap: 'var(--sp-2)' }}>
            <button className="btn btn-secondary btn-sm" onClick={handleSaveProfile}>
              <Save size={14} />
              <span>Save Edits</span>
            </button>
            {!profile.confirmed && (
              <button className="btn btn-primary btn-sm" onClick={handleConfirmProfile}>
                <CheckCircle2 size={14} />
                <span>Confirm Profile</span>
              </button>
            )}
          </div>
        </section>
      )}

      {/* Detail View Tabs */}
      {profile && (
        <div>
          {/* Sub Navigation */}
          <div
            role="tablist"
            aria-label="Profile Sections"
            style={{
              display: 'flex',
              gap: 'var(--sp-2)',
              borderBottom: '1px solid var(--border)',
              marginBottom: 'var(--sp-5)',
            }}
          >
            <button
              role="tab"
              aria-selected={activeTab === 'profile'}
              onClick={() => setActiveTab('profile')}
              style={{
                padding: 'var(--sp-2) var(--sp-4)',
                border: 'none',
                background: 'none',
                borderBottom: activeTab === 'profile' ? '2px solid var(--primary)' : '2px solid transparent',
                fontWeight: activeTab === 'profile' ? 700 : 500,
                color: activeTab === 'profile' ? 'var(--primary)' : 'var(--text-muted)',
                cursor: 'pointer',
                fontSize: 'var(--fs-sm)',
              }}
            >
              Core Profile & ICP
            </button>
            <button
              role="tab"
              aria-selected={activeTab === 'facts'}
              onClick={() => setActiveTab('facts')}
              style={{
                padding: 'var(--sp-2) var(--sp-4)',
                border: 'none',
                background: 'none',
                borderBottom: activeTab === 'facts' ? '2px solid var(--primary)' : '2px solid transparent',
                fontWeight: activeTab === 'facts' ? 700 : 500,
                color: activeTab === 'facts' ? 'var(--primary)' : 'var(--text-muted)',
                cursor: 'pointer',
                fontSize: 'var(--fs-sm)',
              }}
            >
              Extracted Facts ({profile.facts?.length || 0})
            </button>
            <button
              role="tab"
              aria-selected={activeTab === 'inferences'}
              onClick={() => setActiveTab('inferences')}
              style={{
                padding: 'var(--sp-2) var(--sp-4)',
                border: 'none',
                background: 'none',
                borderBottom: activeTab === 'inferences' ? '2px solid var(--primary)' : '2px solid transparent',
                fontWeight: activeTab === 'inferences' ? 700 : 500,
                color: activeTab === 'inferences' ? 'var(--primary)' : 'var(--text-muted)',
                cursor: 'pointer',
                fontSize: 'var(--fs-sm)',
              }}
            >
              Market Inferences ({profile.inferences?.length || 0})
            </button>
          </div>

          {activeTab === 'profile' && (
            <div className="form-grid-2">
              <div className="card" style={{ padding: 'var(--sp-5)', display: 'flex', flexDirection: 'column', gap: 'var(--sp-4)' }}>
                <div className="form-group">
                  <label htmlFor="prof-name" className="label">Product / Business Name</label>
                  <input
                    id="prof-name"
                    type="text"
                    className="input"
                    value={formData.name || ''}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="prof-niche" className="label">Niche & Category</label>
                  <input
                    id="prof-niche"
                    type="text"
                    className="input"
                    value={formData.niche || ''}
                    onChange={(e) => setFormData({ ...formData, niche: e.target.value })}
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="prof-icp" className="label">Ideal Customer Profile (ICP)</label>
                  <textarea
                    id="prof-icp"
                    className="textarea"
                    rows={3}
                    value={formData.icp || ''}
                    onChange={(e) => setFormData({ ...formData, icp: e.target.value })}
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="prof-main-product" className="label">Core Value Proposition</label>
                  <textarea
                    id="prof-main-product"
                    className="textarea"
                    rows={3}
                    value={formData.main_product_or_service || ''}
                    onChange={(e) => setFormData({ ...formData, main_product_or_service: e.target.value })}
                  />
                </div>
              </div>

              <div className="card" style={{ padding: 'var(--sp-5)', display: 'flex', flexDirection: 'column', gap: 'var(--sp-4)' }}>
                <div className="form-group">
                  <label htmlFor="prof-problems" className="label">Problems Solved (one per line)</label>
                  <textarea
                    id="prof-problems"
                    className="textarea"
                    rows={4}
                    value={(formData.problems_solved || []).join('\n')}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        problems_solved: e.target.value.split('\n').filter((x) => x.trim()),
                      })
                    }
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="prof-frustrations" className="label">Customer Frustrations & Vent Terms</label>
                  <textarea
                    id="prof-frustrations"
                    className="textarea"
                    rows={4}
                    value={(formData.customer_frustrations || []).join('\n')}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        customer_frustrations: e.target.value.split('\n').filter((x) => x.trim()),
                      })
                    }
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="prof-competitors" className="label">Known Competitors & Alternatives</label>
                  <input
                    id="prof-competitors"
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
            </div>
          )}

          {activeTab === 'facts' && (
            <div className="panel lead-table-panel">
              <div className="table-header">
                <div>
                  <h2>Extracted Facts with Source Citations</h2>
                  <span>Ground truth claims extracted directly from provided web pages</span>
                </div>
              </div>
              {profile.facts?.length === 0 ? (
                <div className="empty-state">
                  <div className="empty-icon">
                    <Globe size={20} />
                  </div>
                  <strong>No verified facts recorded yet</strong>
                  <span>Analyze your website above to extract verifiable product claims.</span>
                </div>
              ) : (
                <div className="priority-list">
                  {profile.facts.map((fact, idx) => (
                    <div
                      key={idx}
                      style={{
                        padding: 'var(--sp-4) var(--sp-5)',
                        borderBottom: '1px solid var(--border)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        gap: 'var(--sp-4)',
                      }}
                    >
                      <div>
                        <span className="badge badge-medium" style={{ marginRight: 'var(--sp-2)' }}>
                          {fact.category}
                        </span>
                        <span style={{ fontSize: 'var(--fs-base)', color: 'var(--text-main)' }}>
                          {fact.claim}
                        </span>
                      </div>
                      <a
                        href={fact.source_url}
                        target="_blank"
                        rel="noreferrer"
                        style={{
                          fontSize: 'var(--fs-xs)',
                          color: 'var(--primary)',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '4px',
                          whiteSpace: 'nowrap',
                        }}
                      >
                        <ExternalLink size={12} /> Source Page
                      </a>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {activeTab === 'inferences' && (
            <div className="panel lead-table-panel">
              <div className="table-header">
                <div>
                  <h2>Market & Buying Signals</h2>
                  <span>Synthesized ICP nuances, purchase triggers, and audience intent patterns</span>
                </div>
              </div>
              {profile.inferences?.length === 0 ? (
                <div className="empty-state">
                  <div className="empty-icon">
                    <Target size={20} />
                  </div>
                  <strong>No market inferences generated yet</strong>
                  <span>Provide more details or analyze additional pages to unlock market insights.</span>
                </div>
              ) : (
                <div className="priority-list">
                  {profile.inferences.map((inf, idx) => (
                    <div
                      key={idx}
                      style={{
                        padding: 'var(--sp-4) var(--sp-5)',
                        borderBottom: '1px solid var(--border)',
                      }}
                    >
                      <div
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'space-between',
                          marginBottom: '4px',
                        }}
                      >
                        <span style={{ fontWeight: 600, color: 'var(--text-main)', fontSize: 'var(--fs-base)' }}>
                          {inf.insight}
                        </span>
                        <span className="badge badge-high tabular">
                          {Math.round(inf.confidence * 100)}% Confidence
                        </span>
                      </div>
                      <div style={{ fontSize: 'var(--fs-xs)', color: 'var(--text-muted)' }}>
                        <strong>Evidence Basis:</strong> {inf.basis}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
