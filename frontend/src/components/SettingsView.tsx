import React, { useState, useEffect } from 'react';
import {
  Save,
  Download,
  ShieldAlert,
  Sliders,
  Cpu,
  Share2,
} from 'lucide-react';
import type { PostingSettings } from '../types';
import { api } from '../api';

export const SettingsView: React.FC = () => {
  const [postingSettings, setPostingSettings] = useState<PostingSettings>({
    mode: 'manual',
    daily_limit: 5,
    min_interval_seconds: 600,
    allowed_communities: ['r/startups', 'r/SaaS', 'r/Entrepreneur', 'r/programming', 'r/devops'],
    emergency_stop: false,
  });

  const [llmSettings, setLlmSettings] = useState({
    provider: 'mock',
    model: 'gpt-4o',
    api_key: '',
  });

  const [savedMessage, setSavedMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      const data = await api.getSettings();
      if (data.posting_settings) setPostingSettings(data.posting_settings);
      if (data.llm_settings) setLlmSettings(data.llm_settings);
    } catch (e) {
      console.error(e);
    }
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.updateSettings({
        posting_settings: postingSettings,
        llm_settings: llmSettings,
      });
      setSavedMessage('Settings saved successfully.');
      setErrorMessage(null);
      setTimeout(() => setSavedMessage(null), 3000);
    } catch (err: any) {
      setErrorMessage(`Save error: ${err.message}`);
    }
  };

  return (
    <div style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1.5rem', maxWidth: '1000px' }}>
      <div>
        <h2 style={{ fontSize: '1.25rem', fontWeight: 700, color: '#0f172a' }}>Platform Settings & Safety Guardrails</h2>
        <div style={{ fontSize: '0.8125rem', color: '#64748b' }}>
          Configure AI model providers, safety rate limits, community whitelists, and publishing automation.
        </div>
      </div>

      {savedMessage && (
        <div style={{ padding: '0.75rem 1rem', background: '#ecfdf5', color: '#047857', border: '1px solid #a7f3d0', borderRadius: 'var(--radius)', fontSize: '0.8125rem', fontWeight: 500 }}>
          {savedMessage}
        </div>
      )}
      {errorMessage && <div className="notice notice-error" role="alert"><span>{errorMessage}</span><button className="btn btn-secondary btn-sm" onClick={() => setErrorMessage(null)}>Dismiss</button></div>}

      <form onSubmit={handleSave} style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
        {/* Emergency Stop Switch */}
        <div
          className="card"
          style={{
            background: postingSettings.emergency_stop ? '#fef2f2' : '#ffffff',
            borderColor: postingSettings.emergency_stop ? '#fecaca' : 'var(--card-border)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <ShieldAlert size={24} color={postingSettings.emergency_stop ? '#dc2626' : '#64748b'} />
            <div>
              <div style={{ fontWeight: 700, color: postingSettings.emergency_stop ? '#991b1b' : '#0f172a' }}>
                Master Emergency Stop
              </div>
              <div style={{ fontSize: '0.75rem', color: '#64748b' }}>
                Instantly blocks and halts all community interactions, publishing, and automated actions.
              </div>
            </div>
          </div>

          <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer', fontWeight: 600 }}>
            <input
              type="checkbox"
              checked={postingSettings.emergency_stop}
              onChange={(e) => setPostingSettings({ ...postingSettings, emergency_stop: e.target.checked })}
              style={{ width: '18px', height: '18px', cursor: 'pointer' }}
            />
            <span style={{ color: postingSettings.emergency_stop ? '#dc2626' : '#475569' }}>
              {postingSettings.emergency_stop ? 'EMERGENCY STOP ON' : 'Normal Operation'}
            </span>
          </label>
        </div>

        {/* AI Provider Configuration */}
        <div className="card">
          <div style={{ fontWeight: 700, fontSize: '0.9375rem', color: '#0f172a', marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Cpu size={16} /> AI Model Configuration
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '1rem', marginBottom: '1rem' }}>
            <div>
              <label className="label">LLM Provider</label>
              <select
                className="select"
                value={llmSettings.provider}
                onChange={(e) => setLlmSettings({ ...llmSettings, provider: e.target.value })}
              >
                <option value="mock">Local Heuristic Engine (Mock / Zero-Cost)</option>
                <option value="openai">OpenAI (GPT-4o)</option>
                <option value="gemini">Google Gemini (Gemini 1.5/2.0 Flash)</option>
                <option value="groq">Groq (Llama 3.3 70B)</option>
                <option value="anthropic">Anthropic (Claude 3.5 Sonnet)</option>
              </select>
            </div>

            <div>
              <label className="label">Model Identifier</label>
              <input
                type="text"
                className="input"
                placeholder="e.g. gpt-4o or gemini-1.5-flash"
                value={llmSettings.model || ''}
                onChange={(e) => setLlmSettings({ ...llmSettings, model: e.target.value })}
              />
            </div>
          </div>

          <div>
            <label className="label">API Key (Stored locally in SQLite/env, never exposed)</label>
            <input
              type="password"
              className="input"
              placeholder={llmSettings.provider === 'mock' ? 'Not required for local heuristic mock' : 'Enter API key...'}
              value={llmSettings.api_key || ''}
              onChange={(e) => setLlmSettings({ ...llmSettings, api_key: e.target.value })}
              disabled={llmSettings.provider === 'mock'}
            />
          </div>
        </div>

        {/* Publishing Safety & Whitelisting */}
        <div className="card">
          <div style={{ fontWeight: 700, fontSize: '0.9375rem', color: '#0f172a', marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Sliders size={16} /> Publishing Controls & Rate Limiting
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem', marginBottom: '1rem' }}>
            <div>
              <label className="label">Publishing Mode</label>
              <select
                className="select"
                value={postingSettings.mode}
                onChange={(e) => setPostingSettings({ ...postingSettings, mode: e.target.value as any })}
              >
                <option value="draft">Draft Mode Only (Safe Storage)</option>
                <option value="manual">Manual Approval (Recommended Default)</option>
                <option value="automatic">Controlled Automatic Posting</option>
              </select>
            </div>

            <div>
              <label className="label">Max Posts Per Day</label>
              <input
                type="number"
                className="input"
                min={1}
                max={50}
                value={postingSettings.daily_limit}
                onChange={(e) => setPostingSettings({ ...postingSettings, daily_limit: parseInt(e.target.value) || 5 })}
              />
            </div>

            <div>
              <label className="label">Minimum Interval (Seconds)</label>
              <input
                type="number"
                className="input"
                min={60}
                step={60}
                value={postingSettings.min_interval_seconds}
                onChange={(e) => setPostingSettings({ ...postingSettings, min_interval_seconds: parseInt(e.target.value) || 600 })}
              />
            </div>
          </div>

          <div>
            <label className="label">Allowed Communities Whitelist (Comma-separated)</label>
            <input
              type="text"
              className="input"
              placeholder="r/startups, r/SaaS, r/Entrepreneur, r/programming"
              value={postingSettings.allowed_communities.join(', ')}
              onChange={(e) =>
                setPostingSettings({
                  ...postingSettings,
                  allowed_communities: e.target.value.split(',').map((x) => x.trim()).filter(Boolean),
                })
              }
            />
            <div style={{ fontSize: '0.6875rem', color: '#64748b', marginTop: '0.25rem' }}>
              The agent will refuse to post or interact in any community not explicitly listed here.
            </div>
          </div>
        </div>

        {/* Lead Export & Backup */}
        <div className="card">
          <div style={{ fontWeight: 700, fontSize: '0.9375rem', color: '#0f172a', marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Share2 size={16} /> Data Export & CRM Sync
          </div>
          <div style={{ fontSize: '0.8125rem', color: '#64748b', marginBottom: '1rem' }}>
            Download discovered leads, conversation URLs, and qualification scores for CRM or spreadsheet import.
          </div>

          <div style={{ display: 'flex', gap: '0.75rem' }}>
            <a href={api.getExportUrl('csv', 0)} className="btn btn-secondary" download>
              <Download size={14} /> Export Leads (CSV)
            </a>
            <a href={api.getExportUrl('json', 0)} className="btn btn-secondary" download>
              <Download size={14} /> Export Full Leads (JSON)
            </a>
          </div>
        </div>

        {/* Save button */}
        <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
          <button type="submit" className="btn btn-primary">
            <Save size={16} /> Save Settings
          </button>
        </div>
      </form>
    </div>
  );
};
