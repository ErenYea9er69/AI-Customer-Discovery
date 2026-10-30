import React, { useState, useEffect } from 'react';
import {
  Save,
  Download,
  ShieldAlert,
  Sliders,
  Cpu,
  Share2,
  CheckCircle2,
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
  const [saving, setSaving] = useState(false);

  const loadSettings = async () => {
    try {
      const data = await api.getSettings();
      if (data.posting_settings) setPostingSettings(data.posting_settings);
      if (data.llm_settings) setLlmSettings(data.llm_settings);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    void loadSettings();
  }, []);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
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
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="page-shell">
      <div className="page-heading">
        <div>
          <div className="eyebrow">
            <Sliders size={13} /> Guardrails & Engine Configuration
          </div>
          <h1>Settings & Safety Controls</h1>
          <p>
            Configure LLM providers, community whitelists, rate limits, and publishing safety mechanisms.
          </p>
        </div>
      </div>

      {savedMessage && (
        <div className="notice notice-info" role="status">
          <CheckCircle2 size={16} />
          <span>{savedMessage}</span>
        </div>
      )}
      {errorMessage && (
        <div className="notice notice-error" role="alert">
          <span>{errorMessage}</span>
          <button className="btn btn-secondary btn-sm" onClick={() => setErrorMessage(null)}>
            Dismiss
          </button>
        </div>
      )}

      <form onSubmit={handleSave} style={{ display: 'flex', flexDirection: 'column', gap: 'var(--sp-6)' }}>
        {/* Emergency Stop Switch */}
        <section
          className="card"
          style={{
            padding: 'var(--sp-5)',
            background: postingSettings.emergency_stop ? 'var(--danger-bg)' : 'var(--surface)',
            borderColor: postingSettings.emergency_stop ? 'var(--danger-border)' : 'var(--border)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: 'var(--sp-4)',
            flexWrap: 'wrap',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--sp-3)' }}>
            <ShieldAlert size={28} color={postingSettings.emergency_stop ? 'var(--danger)' : 'var(--text-subtle)'} />
            <div>
              <div
                style={{
                  fontWeight: 700,
                  fontSize: 'var(--fs-base)',
                  color: postingSettings.emergency_stop ? 'var(--danger-text)' : 'var(--text-main)',
                }}
              >
                Master Emergency Stop
              </div>
              <div style={{ fontSize: 'var(--fs-xs)', color: 'var(--text-muted)', marginTop: '2px' }}>
                Instantly halts and locks all community discovery, reply drafting, and posting automation.
              </div>
            </div>
          </div>

          <label
            htmlFor="emergency-stop-toggle"
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 'var(--sp-2)',
              cursor: 'pointer',
              fontWeight: 600,
              fontSize: 'var(--fs-sm)',
            }}
          >
            <input
              id="emergency-stop-toggle"
              type="checkbox"
              checked={postingSettings.emergency_stop}
              onChange={(e) => setPostingSettings({ ...postingSettings, emergency_stop: e.target.checked })}
              style={{ width: '20px', height: '20px', cursor: 'pointer' }}
            />
            <span style={{ color: postingSettings.emergency_stop ? 'var(--danger-text)' : 'var(--text-main)' }}>
              {postingSettings.emergency_stop ? 'STOP ACTIVE (BLOCKED)' : 'Normal Active Operation'}
            </span>
          </label>
        </section>

        {/* AI Provider Configuration */}
        <section className="panel">
          <div className="panel-header">
            <div>
              <div className="eyebrow eyebrow-muted">
                <Cpu size={13} /> Intelligence Backend
              </div>
              <h2>AI Model Provider</h2>
              <p>Select which LLM powers business understanding extraction and personalized reply drafts.</p>
            </div>
          </div>

          <div className="form-grid-2" style={{ marginBottom: 'var(--sp-4)' }}>
            <div className="form-group">
              <label htmlFor="settings-llm-provider" className="label">
                LLM Provider
              </label>
              <select
                id="settings-llm-provider"
                className="select"
                value={llmSettings.provider}
                onChange={(e) => setLlmSettings({ ...llmSettings, provider: e.target.value })}
              >
                <option value="mock">Local Heuristic Engine (Mock / Zero-Cost)</option>
                <option value="openai">OpenAI (GPT-4o)</option>
                <option value="gemini">Google Gemini (Gemini 2.0 Flash)</option>
                <option value="groq">Groq (Llama 3.3 70B)</option>
                <option value="anthropic">Anthropic (Claude 3.5 Sonnet)</option>
              </select>
            </div>

            <div className="form-group">
              <label htmlFor="settings-llm-model" className="label">
                Model Identifier
              </label>
              <input
                id="settings-llm-model"
                type="text"
                className="input"
                placeholder="e.g. gpt-4o or gemini-2.0-flash"
                value={llmSettings.model || ''}
                onChange={(e) => setLlmSettings({ ...llmSettings, model: e.target.value })}
              />
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="settings-llm-key" className="label">
              API Key (Stored locally in SQLite/env, never shared)
            </label>
            <input
              id="settings-llm-key"
              type="password"
              className="input"
              placeholder={
                llmSettings.provider === 'mock'
                  ? 'Not required for local heuristic mock'
                  : 'Enter API key…'
              }
              value={llmSettings.api_key || ''}
              onChange={(e) => setLlmSettings({ ...llmSettings, api_key: e.target.value })}
              disabled={llmSettings.provider === 'mock'}
            />
          </div>
        </section>

        {/* Publishing Safety & Whitelisting */}
        <section className="panel">
          <div className="panel-header">
            <div>
              <div className="eyebrow eyebrow-muted">
                <Sliders size={13} /> Rate Limits & Guardrails
              </div>
              <h2>Publishing Controls & Safety Rules</h2>
              <p>Enforce strict community boundaries and rate limiting to maintain account standing.</p>
            </div>
          </div>

          <div className="form-grid-3" style={{ marginBottom: 'var(--sp-4)' }}>
            <div className="form-group">
              <label htmlFor="settings-post-mode" className="label">
                Publishing Mode
              </label>
              <select
                id="settings-post-mode"
                className="select"
                value={postingSettings.mode}
                onChange={(e) =>
                  setPostingSettings({ ...postingSettings, mode: e.target.value as any })
                }
              >
                <option value="draft">Draft Mode Only (Read-Only Review)</option>
                <option value="manual">Manual Approval (Recommended Default)</option>
                <option value="automatic">Controlled Automatic Posting</option>
              </select>
            </div>

            <div className="form-group">
              <label htmlFor="settings-daily-limit" className="label">
                Daily Posting Limit
              </label>
              <input
                id="settings-daily-limit"
                type="number"
                className="input"
                min={1}
                max={50}
                value={postingSettings.daily_limit}
                onChange={(e) =>
                  setPostingSettings({
                    ...postingSettings,
                    daily_limit: parseInt(e.target.value) || 5,
                  })
                }
              />
            </div>

            <div className="form-group">
              <label htmlFor="settings-min-interval" className="label">
                Minimum Interval (Seconds)
              </label>
              <input
                id="settings-min-interval"
                type="number"
                className="input"
                min={60}
                step={60}
                value={postingSettings.min_interval_seconds}
                onChange={(e) =>
                  setPostingSettings({
                    ...postingSettings,
                    min_interval_seconds: parseInt(e.target.value) || 600,
                  })
                }
              />
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="settings-allowed-communities" className="label">
              Allowed Communities Whitelist (Comma-separated)
            </label>
            <input
              id="settings-allowed-communities"
              type="text"
              className="input"
              placeholder="r/startups, r/SaaS, r/Entrepreneur, r/programming"
              value={postingSettings.allowed_communities.join(', ')}
              onChange={(e) =>
                setPostingSettings({
                  ...postingSettings,
                  allowed_communities: e.target.value
                    .split(',')
                    .map((x) => x.trim())
                    .filter(Boolean),
                })
              }
            />
            <div className="helper-text" style={{ marginTop: '4px' }}>
              The agent strictly refuses to discover or post in any community not explicitly listed here.
            </div>
          </div>
        </section>

        {/* Lead Export & Backup */}
        <section className="panel">
          <div className="panel-header">
            <div>
              <div className="eyebrow eyebrow-muted">
                <Share2 size={13} /> Data Portability
              </div>
              <h2>Data Export & CRM Sync</h2>
              <p>Download discovered leads, qualification scores, and discussion URLs for CRM import.</p>
            </div>
          </div>

          <div style={{ display: 'flex', gap: 'var(--sp-3)', flexWrap: 'wrap' }}>
            <a href={api.getExportUrl('csv', 0)} className="btn btn-secondary" download>
              <Download size={14} />
              <span>Export Leads (CSV)</span>
            </a>
            <a href={api.getExportUrl('json', 0)} className="btn btn-secondary" download>
              <Download size={14} />
              <span>Export Full Intelligence (JSON)</span>
            </a>
          </div>
        </section>

        {/* Form Submission */}
        <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: 'var(--sp-2)' }}>
          <button type="submit" className="btn btn-primary" disabled={saving}>
            <Save size={16} />
            <span>{saving ? 'Saving Changes…' : 'Save Platform Settings'}</span>
          </button>
        </div>
      </form>
    </div>
  );
};
