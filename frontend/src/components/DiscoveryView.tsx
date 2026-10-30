import React, { useState, useEffect } from 'react';
import {
  Compass,
  Play,
  RotateCcw,
  CheckCircle,
  HelpCircle,
} from 'lucide-react';
import type { BusinessProfile, Campaign } from '../types';
import { api } from '../api';

interface DiscoveryViewProps {
  profile: BusinessProfile | null;
  onCampaignFinished: () => void;
}

export const DiscoveryView: React.FC<DiscoveryViewProps> = ({ profile, onCampaignFinished }) => {
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [campaignName, setCampaignName] = useState('Quarterly Opportunity Hunt');
  const [selectedPlatforms, setSelectedPlatforms] = useState<string[]>(['reddit', 'web']);
  const [maxLeads, setMaxLeads] = useState(15);
  const [running, setRunning] = useState(false);
  const [activeCampaign, setActiveCampaign] = useState<Campaign | null>(null);
  const [feedback, setFeedback] = useState<string | null>(null);

  const loadCampaigns = async () => {
    try {
      const list = await api.listCampaigns();
      setCampaigns(list);
      if (list.length > 0 && list[0].status === 'running') {
        setActiveCampaign(list[0]);
        setRunning(true);
      }
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    void loadCampaigns();
  }, []);

  // Poll progress when running
  useEffect(() => {
    if (!running || !activeCampaign) return;
    const interval = setInterval(async () => {
      try {
        const updated = await api.getCampaign(activeCampaign.id);
        setActiveCampaign(updated);
        if (updated.status === 'completed' || updated.status === 'failed') {
          setRunning(false);
          await loadCampaigns();
          onCampaignFinished();
        }
      } catch {
        setRunning(false);
      }
    }, 1500);
    return () => clearInterval(interval);
  }, [running, activeCampaign]);

  const togglePlatform = (p: string) => {
    if (selectedPlatforms.includes(p)) {
      if (selectedPlatforms.length > 1) {
        setSelectedPlatforms(selectedPlatforms.filter((x) => x !== p));
      }
    } else {
      setSelectedPlatforms([...selectedPlatforms, p]);
    }
  };

  const handleLaunch = async () => {
    if (!profile) {
      setFeedback('Please analyze and confirm your business profile first.');
      return;
    }
    setRunning(true);
    try {
      const campId = await api.launchCampaign(campaignName, selectedPlatforms, maxLeads);
      const camp = await api.getCampaign(campId);
      setActiveCampaign(camp);
      setFeedback('Discovery started. This page will update as results arrive.');
    } catch (err: any) {
      setFeedback(`Launch error: ${err.message}`);
      setRunning(false);
    }
  };

  return (
    <div className="page-shell">
      <div className="page-heading">
        <div>
          <h1>Discovery Engine</h1>
          <p>
            Scan online communities for users actively reporting pain points that match your ICP.
          </p>
        </div>
      </div>

      {feedback && (
        <div
          className={`notice ${feedback.toLowerCase().includes('error') ? 'notice-error' : 'notice-info'}`}
          role="status"
        >
          <span>{feedback}</span>
          <button className="btn btn-secondary btn-sm" onClick={() => setFeedback(null)}>
            Dismiss
          </button>
        </div>
      )}

      {/* Launch Configuration Panel */}
      <section className="panel" style={{ marginBottom: 'var(--sp-6)' }}>
        <div className="panel-header" style={{ marginBottom: 'var(--sp-5)' }}>
          <div>
            <h2>Launch New Discovery Campaign</h2>
            <p>Select target sources and depth. The engine generates natural problem-hunting queries.</p>
          </div>
          <button
            className="btn btn-primary"
            onClick={handleLaunch}
            disabled={running || !profile}
          >
            {running ? <RotateCcw size={16} className="spin" /> : <Play size={16} />}
            <span>{running ? 'Research in Progress…' : 'Launch Customer Discovery'}</span>
          </button>
        </div>

        <div className="form-grid-3">
          <div className="form-group">
            <label htmlFor="discovery-campaign-name" className="label">
              Campaign Name
            </label>
            <input
              id="discovery-campaign-name"
              type="text"
              className="input"
              value={campaignName}
              onChange={(e) => setCampaignName(e.target.value)}
              disabled={running}
            />
          </div>

          <div className="form-group">
            <label className="label">Discovery Sources</label>
            <div style={{ display: 'flex', gap: 'var(--sp-2)', flexWrap: 'wrap' }}>
              {[
                { id: 'reddit', label: 'Reddit' },
                { id: 'web', label: 'Public Web' },
                { id: 'github', label: 'GitHub Issues' },
                { id: 'v2ex', label: 'V2EX' },
              ].map((p) => {
                const isSelected = selectedPlatforms.includes(p.id);
                return (
                  <button
                    key={p.id}
                    type="button"
                    className={`btn btn-sm ${isSelected ? 'btn-primary' : 'btn-secondary'}`}
                    aria-pressed={isSelected}
                    onClick={() => togglePlatform(p.id)}
                    disabled={running}
                  >
                    {isSelected && <CheckCircle size={13} />}
                    <span>{p.label}</span>
                  </button>
                );
              })}
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="discovery-max-leads" className="label">
              Max Leads to Qualify
            </label>
            <select
              id="discovery-max-leads"
              className="select"
              value={maxLeads}
              onChange={(e) => setMaxLeads(parseInt(e.target.value))}
              disabled={running}
            >
              <option value="5">Quick Scan (5 Leads)</option>
              <option value="15">Standard Campaign (15 Leads)</option>
              <option value="30">Deep Harvest (30 Leads)</option>
            </select>
          </div>
        </div>

        {/* Live Progress Bar if Active */}
        {activeCampaign && running && (
          <div
            style={{
              marginTop: 'var(--sp-6)',
              padding: 'var(--sp-4)',
              background: 'var(--surface-subtle)',
              border: '1px solid var(--border)',
              borderRadius: 'var(--r-md)',
            }}
          >
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                fontSize: 'var(--fs-sm)',
                fontWeight: 600,
                marginBottom: 'var(--sp-2)',
              }}
            >
              <span style={{ color: 'var(--primary)' }}>{activeCampaign.current_step}</span>
              <span className="tabular">{activeCampaign.progress_percentage}%</span>
            </div>
            <div className="coverage-bar" style={{ height: '8px' }}>
              <span
                style={{
                  width: `${activeCampaign.progress_percentage}%`,
                  transition: 'width 0.3s ease',
                }}
              />
            </div>
            <div
              style={{
                display: 'flex',
                gap: 'var(--sp-4)',
                marginTop: 'var(--sp-3)',
                fontSize: 'var(--fs-xs)',
                color: 'var(--text-muted)',
              }}
            >
              <span>Discovered: <strong className="tabular">{activeCampaign.total_found}</strong> conversations</span>
              <span>Qualified: <strong className="tabular">{activeCampaign.total_qualified}</strong> leads</span>
              <span>High Potential: <strong className="tabular">{activeCampaign.high_potential_count}</strong></span>
            </div>
          </div>
        )}
      </section>

      {/* Discovery Strategy Explainer */}
      <section
        className="card"
        style={{
          padding: 'var(--sp-5)',
          background: 'var(--surface-subtle)',
          marginBottom: 'var(--sp-6)',
        }}
      >
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 'var(--sp-2)',
            fontWeight: 700,
            fontSize: 'var(--fs-base)',
            color: 'var(--text-main)',
            marginBottom: 'var(--sp-3)',
          }}
        >
          <HelpCircle size={16} /> Autonomous Query Generation Logic
        </div>
        <div className="form-grid-3">
          <div>
            <strong style={{ fontSize: 'var(--fs-sm)', color: 'var(--text-main)' }}>1. Pain & Vent Queries</strong>
            <p style={{ marginTop: '4px', fontSize: 'var(--fs-xs)', color: 'var(--text-muted)', lineHeight: '1.45' }}>
              Identifies natural phrases like "frustrated having to...", "is there an easier way to...", "struggling with...".
            </p>
          </div>
          <div>
            <strong style={{ fontSize: 'var(--fs-sm)', color: 'var(--text-main)' }}>2. Competitor Dissatisfaction</strong>
            <p style={{ marginTop: '4px', fontSize: 'var(--fs-xs)', color: 'var(--text-muted)', lineHeight: '1.45' }}>
              Finds users unhappy with alternatives ("looking for alternative to...", "...is way too expensive or clunky").
            </p>
          </div>
          <div>
            <strong style={{ fontSize: 'var(--fs-sm)', color: 'var(--text-main)' }}>3. Active Recommendation Requests</strong>
            <p style={{ marginTop: '4px', fontSize: 'var(--fs-xs)', color: 'var(--text-muted)', lineHeight: '1.45' }}>
              Detects users directly asking communities: "what tool do you recommend for...", "ready to pay for...".
            </p>
          </div>
        </div>
      </section>

      {/* Campaign History */}
      <section className="panel lead-table-panel">
        <div className="table-header">
          <div>
            <h2>Campaign History</h2>
            <span>Past discovery jobs and qualification results</span>
          </div>
        </div>

        {campaigns.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">
              <Compass size={20} />
            </div>
            <strong>No campaigns run yet</strong>
            <span>Configure sources above and launch your first autonomous customer discovery run.</span>
          </div>
        ) : (
          <div className="priority-list">
            {campaigns.map((c) => (
              <div
                key={c.id}
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
                  <div style={{ fontWeight: 600, fontSize: 'var(--fs-base)', color: 'var(--text-main)' }}>
                    {c.name}
                  </div>
                  <div
                    style={{
                      fontSize: 'var(--fs-xs)',
                      color: 'var(--text-subtle)',
                      display: 'flex',
                      gap: 'var(--sp-3)',
                      marginTop: '2px',
                    }}
                  >
                    <span>Sources: {c.selected_platforms.join(', ')}</span>
                    <span>• Queries: {c.queries?.length || 0}</span>
                  </div>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--sp-4)' }}>
                  <div style={{ textAlign: 'right' }}>
                    <div style={{ fontSize: 'var(--fs-sm)', fontWeight: 600, color: 'var(--text-main)' }}>
                      <span className="tabular">{c.total_qualified}</span> Leads Qualified
                    </div>
                    <div style={{ fontSize: 'var(--fs-xs)', color: 'var(--success)' }}>
                      <span className="tabular">{c.high_potential_count}</span> High Potential
                    </div>
                  </div>
                  <span
                    className={`badge ${
                      c.status === 'completed'
                        ? 'badge-high'
                        : c.status === 'running'
                        ? 'badge-medium'
                        : 'badge-low'
                    }`}
                  >
                    {c.status}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
};
