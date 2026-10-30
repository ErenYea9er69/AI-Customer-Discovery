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
    loadCampaigns();
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
          loadCampaigns();
          onCampaignFinished();
        }
      } catch (err) {
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
    <div style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1.5rem', maxWidth: '1200px' }}>
      {feedback && <div className={`notice ${feedback.includes('error') || feedback.includes('Error') ? 'notice-error' : 'notice-info'}`} role="status"><span>{feedback}</span><button className="btn btn-secondary btn-sm" onClick={() => setFeedback(null)}>Dismiss</button></div>}
      {/* Launch Configuration Card */}
      <div className="card">
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem' }}>
          <div>
            <div style={{ fontWeight: 700, fontSize: '1.125rem', color: '#0f172a', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Compass size={20} color="var(--primary)" /> Customer Discovery Engine
            </div>
            <div style={{ fontSize: '0.8125rem', color: '#64748b' }}>
              Configure platforms and discovery depth to uncover active conversations and buying signals.
            </div>
          </div>
          <button
            className="btn btn-primary"
            onClick={handleLaunch}
            disabled={running || !profile}
          >
            {running ? <RotateCcw size={16} className="spin" /> : <Play size={16} />}
            {running ? 'Research in Progress...' : 'Launch Customer Discovery'}
          </button>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem', paddingTop: '0.5rem', borderTop: '1px solid var(--border)' }}>
          <div>
            <label className="label">Campaign Name</label>
            <input
              type="text"
              className="input"
              value={campaignName}
              onChange={(e) => setCampaignName(e.target.value)}
              disabled={running}
            />
          </div>

          <div>
            <label className="label">Discovery Sources</label>
            <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
              {[
                { id: 'reddit', label: 'Reddit (Core)', default: true },
                { id: 'web', label: 'Public Web', default: true },
                { id: 'github', label: 'GitHub Issues', default: false },
                { id: 'v2ex', label: 'V2EX Tech', default: false },
              ].map((p) => {
                const isSelected = selectedPlatforms.includes(p.id);
                return (
                  <button
                    key={p.id}
                    type="button"
                    className="btn btn-sm"
                    style={{
                      background: isSelected ? 'var(--primary-light)' : '#ffffff',
                      borderColor: isSelected ? 'var(--primary)' : '#cbd5e1',
                      color: isSelected ? 'var(--primary)' : '#475569',
                    }}
                    onClick={() => togglePlatform(p.id)}
                    disabled={running}
                  >
                    {isSelected && <CheckCircle size={12} />} {p.label}
                  </button>
                );
              })}
            </div>
          </div>

          <div>
            <label className="label">Max Leads to Qualify</label>
            <select
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
          <div style={{ marginTop: '1.25rem', padding: '1rem', background: '#f8fafc', border: '1px solid var(--border)', borderRadius: 'var(--radius)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8125rem', fontWeight: 600, marginBottom: '0.5rem' }}>
              <span style={{ color: 'var(--primary)' }}>{activeCampaign.current_step}</span>
              <span>{activeCampaign.progress_percentage}%</span>
            </div>
            <div style={{ width: '100%', height: '6px', background: '#e2e8f0', borderRadius: '3px', overflow: 'hidden' }}>
              <div
                style={{
                  width: `${activeCampaign.progress_percentage}%`,
                  height: '100%',
                  background: 'var(--primary)',
                  transition: 'width 0.3s ease',
                }}
              ></div>
            </div>
            <div style={{ display: 'flex', gap: '1rem', marginTop: '0.5rem', fontSize: '0.75rem', color: '#64748b' }}>
              <span>Discovered: <strong>{activeCampaign.total_found}</strong> conversations</span>
              <span>Qualified: <strong>{activeCampaign.total_qualified}</strong> leads</span>
              <span>High Potential: <strong>{activeCampaign.high_potential_count}</strong></span>
            </div>
          </div>
        )}
      </div>

      {/* Discovery Strategy Explainer */}
      <div className="card" style={{ padding: '1rem', background: '#f8fafc' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontWeight: 600, fontSize: '0.8125rem', color: '#334155', marginBottom: '0.5rem' }}>
          <HelpCircle size={16} /> Autonomous Query Generation Logic
        </div>
        <div style={{ fontSize: '0.75rem', color: '#64748b', display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem' }}>
          <div>
            <strong>1. Problem & Vent Expressions</strong>
            <p>Searches for phrases like "I hate having to...", "struggling with...", "is there a better way to solve..."</p>
          </div>
          <div>
            <strong>2. Competitor Alternatives</strong>
            <p>Finds people unhappy with competitors ("alternative to...", "...is too expensive", "...clunky and slow")</p>
          </div>
          <div>
            <strong>3. Active Tool Seeking</strong>
            <p>Identifies people directly asking communities: "what tool do you recommend for...", "willing to pay for..."</p>
          </div>
        </div>
      </div>

      {/* Campaign History Table */}
      <div className="card" style={{ padding: 0 }}>
        <div style={{ padding: '0.75rem 1rem', borderBottom: '1px solid var(--border)', fontSize: '0.75rem', fontWeight: 600, color: '#64748b' }}>
          RESEARCH CAMPAIGN HISTORY
        </div>
        {campaigns.length === 0 ? (
          <div style={{ padding: '2rem', textAlign: 'center', color: '#94a3b8' }}>No campaigns run yet.</div>
        ) : (
          campaigns.map((c) => (
            <div
              key={c.id}
              style={{
                padding: '0.875rem 1rem',
                borderBottom: '1px solid var(--border)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
              }}
            >
              <div>
                <div style={{ fontWeight: 600, fontSize: '0.875rem', color: '#0f172a' }}>{c.name}</div>
                <div style={{ fontSize: '0.75rem', color: '#64748b', display: 'flex', gap: '0.5rem' }}>
                  <span>Platforms: {c.selected_platforms.join(', ')}</span>
                  <span>• Queries Planned: {c.queries?.length || 0}</span>
                </div>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                <div style={{ textAlign: 'right' }}>
                  <div style={{ fontSize: '0.8125rem', fontWeight: 600, color: '#0f172a' }}>
                    {c.total_qualified} Leads Qualified
                  </div>
                  <div style={{ fontSize: '0.6875rem', color: '#10b981' }}>
                    {c.high_potential_count} High Potential
                  </div>
                </div>
                <span className={`badge ${c.status === 'completed' ? 'badge-high' : c.status === 'running' ? 'badge-medium' : 'badge-low'}`}>
                  {c.status}
                </span>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};
