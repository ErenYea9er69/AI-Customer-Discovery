import React, { useState, useEffect, useCallback } from 'react';
import {
  Save,
  Download,
  ShieldAlert,
  CheckCircle2,
  AlertTriangle,
} from 'lucide-react';
import type { PostingSettings, LLMSettings } from '../types';
import { api } from '../api';

export const SettingsView: React.FC = () => {
  const [postingSettings, setPostingSettings] = useState<PostingSettings>({
    mode: 'manual',
    daily_limit: 5,
    min_interval_seconds: 600,
    allowed_communities: [
      'r/startups',
      'r/SaaS',
      'r/Entrepreneur',
      'r/smallbusiness',
      'r/devops',
      'r/webdev',
    ],
    emergency_stop: false,
    reddit_client_id: '',
    reddit_client_secret: '',
    reddit_username: '',
    reddit_password: '',
    github_token: '',
    has_reddit_password: false,
    has_reddit_client_secret: false,
    has_github_token: false,
  });

  const [llmSettings, setLlmSettings] = useState<LLMSettings>({
    provider: 'gemini',
    model: 'gemini-2.5-flash',
    api_key: '',
    has_api_key: false,
    configured: false,
  });

  const [savedMessage, setSavedMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const loadSettings = useCallback(async () => {
    try {
      const data = await api.getSettings();
      if (data.posting_settings) {
        setPostingSettings((prev) => ({
          ...prev,
          ...data.posting_settings,
          reddit_password: '',
          reddit_client_secret: '',
          github_token: '',
        }));
      }
      if (data.llm_settings) {
        setLlmSettings((prev) => ({
          ...prev,
          ...data.llm_settings,
          api_key: '',
        }));
      }
    } catch (e) {
      setErrorMessage(e instanceof Error ? e.message : 'Could not load current settings.');
    }
  }, []);

  useEffect(() => {
    void loadSettings();
  }, [loadSettings]);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setErrorMessage(null);
    try {
      const postPayload: Partial<PostingSettings> = { ...postingSettings };
      if (!postPayload.reddit_password) delete postPayload.reddit_password;
      if (!postPayload.reddit_client_secret) delete postPayload.reddit_client_secret;
      if (!postPayload.github_token) delete postPayload.github_token;

      const llmPayload: Partial<LLMSettings> = {
        provider: llmSettings.provider,
        model: llmSettings.model,
      };
      if (llmSettings.api_key && llmSettings.api_key.trim()) {
        llmPayload.api_key = llmSettings.api_key.trim();
      }

      await api.updateSettings({
        posting_settings: postPayload,
        llm_settings: llmPayload,
      });

      setSavedMessage('Settings saved successfully. Changes applied to active engine.');
      await loadSettings();
      setTimeout(() => setSavedMessage(null), 3500);
    } catch (err: any) {
      setErrorMessage(err instanceof Error ? err.message : 'Failed to save settings.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="page-shell">
      <div className="page-heading">
        <div>
          <h1>Settings & Safety Controls</h1>
          <p>
            Configure LLM providers, community whitelists, rate limits, platform credentials, and publishing safety gates.
          </p>
        </div>
      </div>

      {savedMessage && (
        <div className="notice notice-success" role="status">
          <CheckCircle2 size={16} />
          <span>{savedMessage}</span>
        </div>
      )}
      {errorMessage && (
        <div className="notice notice-error" role="alert">
          <AlertTriangle size={16} />
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
              {postingSettings.emergency_stop ? 'STOP ACTIVE (HALTED)' : 'Normal Active Operation'}
            </span>
          </label>
        </section>

        {/* AI Provider Configuration */}
        <section className="panel">
          <div className="panel-header" style={{ flexWrap: 'wrap', gap: 'var(--sp-2)' }}>
            <div>
              <h2>AI Model Provider</h2>
              <p>Configure which LLM powers profile extraction, search planning, and personalized reply generation.</p>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--sp-2)' }}>
              {llmSettings.configured ? (
                <span className="badge badge-high" style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                  <CheckCircle2 size={13} />
                  AI Ready & Configured
                </span>
              ) : llmSettings.provider === 'mock' ? (
                <span className="badge badge-low">Mock Engine (Test Mode)</span>
              ) : (
                <span className="badge badge-amber" style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                  <AlertTriangle size={13} />
                  Key Required for Live AI
                </span>
              )}
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
                onChange={(e) => {
                  const p = e.target.value;
                  const defaultModels: Record<string, string> = {
                    openai: 'gpt-4o',
                    gemini: 'gemini-2.5-flash',
                    groq: 'llama-3.3-70b-versatile',
                    anthropic: 'claude-sonnet-5-5',
                    mock: 'mock',
                  };
                  setLlmSettings({
                    ...llmSettings,
                    provider: p,
                    model: defaultModels[p] || '',
                  });
                }}
              >
                <option value="gemini">Google Gemini (gemini-2.5-flash)</option>
                <option value="openai">OpenAI (gpt-4o)</option>
                <option value="groq">Groq (llama-3.3-70b-versatile)</option>
                <option value="anthropic">Anthropic (claude-sonnet-5-5)</option>
                <option value="mock">Local Heuristic Mock (Testing Only)</option>
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
                placeholder="e.g. gemini-2.5-flash or gpt-4o"
                value={llmSettings.model || ''}
                onChange={(e) => setLlmSettings({ ...llmSettings, model: e.target.value })}
              />
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="settings-llm-key" className="label">
              Provider API Key
              {llmSettings.has_api_key && (
                <span style={{ color: 'var(--success)', fontWeight: 600, marginLeft: '8px' }}>
                  ✓ Stored on server
                </span>
              )}
            </label>
            <input
              id="settings-llm-key"
              type="password"
              className="input"
              placeholder={
                llmSettings.has_api_key
                  ? '•••••••••••••••• (Leave blank to keep current key)'
                  : llmSettings.provider === 'mock'
                  ? 'Not needed for mock mode'
                  : 'Enter API key…'
              }
              value={llmSettings.api_key || ''}
              onChange={(e) => setLlmSettings({ ...llmSettings, api_key: e.target.value })}
              disabled={llmSettings.provider === 'mock'}
            />
            <div className="helper-text" style={{ marginTop: '4px' }}>
              Stored securely in the local SQLite database. Never exposed in API responses or shared externally.
            </div>
          </div>
        </section>

        {/* Publishing Safety & Whitelisting */}
        <section className="panel">
          <div className="panel-header">
            <div>
              <h2>Publishing Controls & Safety Rules</h2>
              <p>Enforce strict community boundaries and rate limiting to maintain account standing and community trust.</p>
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
                <option value="draft">Draft Mode Only (Copy & View Only)</option>
                <option value="manual">Manual Approval (Recommended Default)</option>
                <option value="automatic">Controlled Automatic Posting (API)</option>
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
              Allowed Reddit Communities Whitelist (Comma-separated)
            </label>
            <input
              id="settings-allowed-communities"
              type="text"
              className="input"
              placeholder="r/startups, r/SaaS, r/Entrepreneur, r/smallbusiness"
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
              The agent strictly refuses to post to any Reddit community not explicitly listed here.
            </div>
          </div>
        </section>

        {/* Platform API Credentials (Reddit & GitHub) */}
        <section className="panel">
          <div className="panel-header">
            <div>
              <h2>Platform API Credentials (Optional)</h2>
              <p>Configure official credentials to enable direct API posting for Reddit and GitHub. If omitted, replies use clipboard copy mode.</p>
            </div>
          </div>

          <div className="form-grid-2" style={{ marginBottom: 'var(--sp-4)' }}>
            <div className="form-group">
              <label htmlFor="settings-reddit-client-id" className="label">
                Reddit App Client ID
              </label>
              <input
                id="settings-reddit-client-id"
                type="text"
                className="input"
                placeholder="e.g. d1F_x..."
                value={postingSettings.reddit_client_id || ''}
                onChange={(e) => setPostingSettings({ ...postingSettings, reddit_client_id: e.target.value })}
              />
            </div>

            <div className="form-group">
              <label htmlFor="settings-reddit-client-secret" className="label">
                Reddit App Secret
                {postingSettings.has_reddit_client_secret && (
                  <span style={{ color: 'var(--success)', fontWeight: 600, marginLeft: '8px' }}>
                    ✓ Stored
                  </span>
                )}
              </label>
              <input
                id="settings-reddit-client-secret"
                type="password"
                className="input"
                placeholder={
                  postingSettings.has_reddit_client_secret
                    ? '•••••••••••••••• (Leave blank to keep)'
                    : 'Reddit client secret'
                }
                value={postingSettings.reddit_client_secret || ''}
                onChange={(e) => setPostingSettings({ ...postingSettings, reddit_client_secret: e.target.value })}
              />
            </div>

            <div className="form-group">
              <label htmlFor="settings-reddit-username" className="label">
                Reddit Username
              </label>
              <input
                id="settings-reddit-username"
                type="text"
                className="input"
                placeholder="Reddit account username"
                value={postingSettings.reddit_username || ''}
                onChange={(e) => setPostingSettings({ ...postingSettings, reddit_username: e.target.value })}
              />
            </div>

            <div className="form-group">
              <label htmlFor="settings-reddit-password" className="label">
                Reddit Password
                {postingSettings.has_reddit_password && (
                  <span style={{ color: 'var(--success)', fontWeight: 600, marginLeft: '8px' }}>
                    ✓ Stored
                  </span>
                )}
              </label>
              <input
                id="settings-reddit-password"
                type="password"
                className="input"
                placeholder={
                  postingSettings.has_reddit_password
                    ? '•••••••••••••••• (Leave blank to keep)'
                    : 'Reddit account password'
                }
                value={postingSettings.reddit_password || ''}
                onChange={(e) => setPostingSettings({ ...postingSettings, reddit_password: e.target.value })}
              />
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="settings-github-token" className="label">
              GitHub Personal Access Token (for Issue Comments)
              {postingSettings.has_github_token && (
                <span style={{ color: 'var(--success)', fontWeight: 600, marginLeft: '8px' }}>
                  ✓ Stored
                </span>
              )}
            </label>
            <input
              id="settings-github-token"
              type="password"
              className="input"
              placeholder={
                postingSettings.has_github_token
                  ? '•••••••••••••••• (Leave blank to keep)'
                  : 'ghp_...'
              }
              value={postingSettings.github_token || ''}
              onChange={(e) => setPostingSettings({ ...postingSettings, github_token: e.target.value })}
            />
          </div>
        </section>

        {/* Lead Export & Backup */}
        <section className="panel">
          <div className="panel-header">
            <div>
              <h2>Data Export & CRM Sync</h2>
              <p>Download discovered leads, qualification scores, and discussion URLs for CRM import or spreadsheet analysis.</p>
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
