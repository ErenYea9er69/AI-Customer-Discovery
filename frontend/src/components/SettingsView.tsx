import React, { useState, useEffect, useCallback } from 'react';
import {
  Save,
  Download,
  ShieldAlert,
  CheckCircle2,
  AlertTriangle,
  Cpu,
  ShieldCheck,
  KeyRound,
} from 'lucide-react';
import type { PostingSettings, LLMSettings, MCPSettings } from '../types';
import { api } from '../api';

export const SettingsView: React.FC = () => {
  const [postingSettings, setPostingSettings] = useState<PostingSettings>({
    mode: 'manual',
    daily_limit: 5,
    min_interval_seconds: 600,
    interval_jitter: 0.3,
    max_mention_ratio: 0.1,
    require_account_health: true,
    require_rules_ack: true,
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

  const [mcpSettings, setMcpSettings] = useState<MCPSettings>({
    discovery_mode: 'host_driven',
    default_output_format: 'both',
    default_min_score: 70,
    default_export_path: './discovery_exports',
    emergency_stop: false,
    auto_launch_dashboard: false,
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
          interval_jitter: data.posting_settings.interval_jitter ?? 0.3,
          max_mention_ratio: data.posting_settings.max_mention_ratio ?? 0.1,
          require_account_health: data.posting_settings.require_account_health ?? true,
          require_rules_ack: data.posting_settings.require_rules_ack ?? true,
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
      if (data.mcp_settings) {
        setMcpSettings(data.mcp_settings);
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
        mcp_settings: mcpSettings,
      });

      setSavedMessage('Platform settings saved successfully. Changes applied to active engine.');
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
            Configure AI providers, community safety boundaries, rate limiting, platform credentials, and publishing guardrails.
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
        {/* Master Emergency Stop Switch */}
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
                Instantly halts and locks all community discovery, reply drafting, and posting operations across the system.
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
              <p>Configure which LLM powers profile extraction, search query planning, and personalized reply generation.</p>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--sp-2)' }}>
              {llmSettings.configured ? (
                <span className="badge badge-high" style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                  <CheckCircle2 size={13} />
                  AI Ready & Configured
                </span>
              ) : llmSettings.provider === 'mock' ? (
                <span className="badge badge-low">Local Heuristic Mock (Test Mode)</span>
              ) : (
                <span className="badge badge-amber" style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                  <AlertTriangle size={13} />
                  API Key Required
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
                    gemini: 'gemini-2.5-flash',
                    openai: 'gpt-4o',
                    anthropic: 'claude-sonnet-5-5',
                    groq: 'llama-3.3-70b-versatile',
                    deepseek: 'deepseek-chat',
                    mock: 'mock',
                  };
                  setLlmSettings({
                    ...llmSettings,
                    provider: p,
                    model: defaultModels[p] || '',
                  });
                }}
              >
                <option value="gemini">Google Gemini (gemini-2.5-flash, gemini-2.0-flash)</option>
                <option value="openai">OpenAI (gpt-4o, gpt-4o-mini, o3-mini)</option>
                <option value="anthropic">Anthropic (claude-sonnet-5-5, claude-3-7-sonnet)</option>
                <option value="groq">Groq (llama-3.3-70b-versatile, llama-3.1-8b)</option>
                <option value="deepseek">DeepSeek (deepseek-chat, deepseek-reasoner)</option>
                <option value="mock">Local Heuristic Mock (Offline Testing)</option>
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
              {(() => {
                const modelPresets: Record<string, string[]> = {
                  gemini: ['gemini-2.5-flash', 'gemini-2.0-flash', 'gemini-1.5-flash'],
                  openai: ['gpt-4o', 'gpt-4o-mini', 'o3-mini'],
                  anthropic: ['claude-sonnet-5-5', 'claude-3-7-sonnet-latest', 'claude-3-5-sonnet-latest'],
                  groq: ['llama-3.3-70b-versatile', 'llama-3.1-8b-instant'],
                  deepseek: ['deepseek-chat', 'deepseek-reasoner'],
                };
                const presets = modelPresets[llmSettings.provider];
                if (!presets) return null;
                return (
                  <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap', marginTop: '6px' }}>
                    {presets.map((preset) => (
                      <button
                        key={preset}
                        type="button"
                        className={`btn btn-xs ${llmSettings.model === preset ? 'btn-primary' : 'btn-secondary'}`}
                        style={{ fontSize: '11px', padding: '2px 8px', borderRadius: '12px' }}
                        onClick={() => setLlmSettings({ ...llmSettings, model: preset })}
                      >
                        {preset}
                      </button>
                    ))}
                  </div>
                );
              })()}
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
              Stored securely in local SQLite. Re-applies immediately without needing a server restart.
            </div>
          </div>
        </section>

        {/* Publishing Safety Gates & Anti-Spam Controls */}
        <section className="panel">
          <div className="panel-header">
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--sp-2)' }}>
                <ShieldCheck size={18} style={{ color: 'var(--primary)' }} />
                <h2>Publishing Controls & Safety Gates</h2>
              </div>
              <p>Enforce strict community boundaries, randomized intervals, and promotional ratios to prevent automated spam penalties.</p>
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
                <option value="draft">Draft Mode Only (Read & Copy Only)</option>
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
                    daily_limit: parseInt(e.target.value, 10) || 5,
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
                    min_interval_seconds: parseInt(e.target.value, 10) || 600,
                  })
                }
              />
            </div>
          </div>

          {/* Granular Anti-Spam Safety Settings */}
          <div className="form-grid-2" style={{ marginBottom: 'var(--sp-4)' }}>
            <div className="form-group">
              <label htmlFor="settings-interval-jitter" className="label">
                Interval Jitter Fraction ({Math.round((postingSettings.interval_jitter ?? 0.3) * 100)}%)
              </label>
              <input
                id="settings-interval-jitter"
                type="range"
                min="0"
                max="0.5"
                step="0.05"
                value={postingSettings.interval_jitter ?? 0.3}
                onChange={(e) =>
                  setPostingSettings({
                    ...postingSettings,
                    interval_jitter: parseFloat(e.target.value),
                  })
                }
                style={{ width: '100%', cursor: 'pointer' }}
              />
              <span className="helper-text">
                Adds random extra delay on top of minimum interval to avoid predictable bot timing.
              </span>
            </div>

            <div className="form-group">
              <label htmlFor="settings-max-mention" className="label">
                Max Product Mention Ratio ({Math.round((postingSettings.max_mention_ratio ?? 0.1) * 100)}%)
              </label>
              <input
                id="settings-max-mention"
                type="range"
                min="0.05"
                max="0.3"
                step="0.05"
                value={postingSettings.max_mention_ratio ?? 0.1}
                onChange={(e) =>
                  setPostingSettings({
                    ...postingSettings,
                    max_mention_ratio: parseFloat(e.target.value),
                  })
                }
                style={{ width: '100%', cursor: 'pointer' }}
              />
              <span className="helper-text">
                Safety ceiling: at most this fraction of recent comments may mention the product (default: 10%).
              </span>
            </div>
          </div>

          <div className="form-grid-2" style={{ marginBottom: 'var(--sp-4)' }}>
            <label
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 'var(--sp-2)',
                cursor: 'pointer',
                fontSize: 'var(--fs-sm)',
                fontWeight: 500,
              }}
            >
              <input
                type="checkbox"
                checked={postingSettings.require_account_health ?? true}
                onChange={(e) =>
                  setPostingSettings({ ...postingSettings, require_account_health: e.target.checked })
                }
                style={{ width: '16px', height: '16px' }}
              />
              <span>Enforce account health requirements before allowing product-aware replies</span>
            </label>

            <label
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 'var(--sp-2)',
                cursor: 'pointer',
                fontSize: 'var(--fs-sm)',
                fontWeight: 500,
              }}
            >
              <input
                type="checkbox"
                checked={postingSettings.require_rules_ack ?? true}
                onChange={(e) =>
                  setPostingSettings({ ...postingSettings, require_rules_ack: e.target.checked })
                }
                style={{ width: '16px', height: '16px' }}
              />
              <span>Require recorded community rules acknowledgement before publishing</span>
            </label>
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
              The publisher strictly refuses to post to any Reddit community not explicitly listed here.
            </div>
          </div>
        </section>

        {/* Platform API Credentials (Reddit & GitHub) */}
        <section className="panel">
          <div className="panel-header">
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--sp-2)' }}>
                <KeyRound size={18} style={{ color: 'var(--primary)' }} />
                <h2>Platform API Credentials (Optional)</h2>
              </div>
              <p>Configure credentials for direct API posting on Reddit and GitHub. If omitted, responses default to safe clipboard copy mode.</p>
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

        {/* Model Context Protocol (MCP) & Host AI Settings */}
        <section className="panel">
          <div className="panel-header">
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--sp-2)' }}>
                <Cpu size={18} style={{ color: 'var(--primary)' }} />
                <h2>Model Context Protocol (MCP) & Host AI Controls</h2>
              </div>
              <p>
                Configure how AgentReach connects to IDEs (Cursor, Claude Code, Antigravity, VS Code).
                Choose whether your AI assistant reasons directly in chat without external keys or triggers background batching.
              </p>
            </div>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--sp-5)' }}>
            <fieldset style={{ border: 'none', padding: 0, margin: 0 }}>
              <legend className="label" style={{ marginBottom: 'var(--sp-2)' }}>
                Discovery Workflow Mode
              </legend>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 'var(--sp-3)' }}>
                <label
                  style={{
                    display: 'flex',
                    flexDirection: 'column',
                    gap: 'var(--sp-1)',
                    padding: 'var(--sp-4)',
                    borderRadius: 'var(--r-md)',
                    border: `1.5px solid ${mcpSettings.discovery_mode === 'host_driven' ? 'var(--primary)' : 'var(--border)'}`,
                    backgroundColor: mcpSettings.discovery_mode === 'host_driven' ? 'var(--surface-subtle)' : 'var(--surface)',
                    cursor: 'pointer',
                    transition: 'all 0.15s ease',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--sp-2)', fontWeight: 600 }}>
                    <input
                      type="radio"
                      name="discovery_mode"
                      value="host_driven"
                      checked={mcpSettings.discovery_mode === 'host_driven'}
                      onChange={() => setMcpSettings({ ...mcpSettings, discovery_mode: 'host_driven' })}
                    />
                    <span>Host-Driven Stepping (Recommended)</span>
                  </div>
                  <span style={{ fontSize: 'var(--fs-xs)', color: 'var(--text-muted)', paddingLeft: 'var(--sp-5)' }}>
                    Your host AI (Cursor, Claude Code, Antigravity) reads scraped community threads, reasons, qualifies leads, and drafts replies inside your chat. <strong>Zero external API keys required.</strong>
                  </span>
                </label>

                <label
                  style={{
                    display: 'flex',
                    flexDirection: 'column',
                    gap: 'var(--sp-1)',
                    padding: 'var(--sp-4)',
                    borderRadius: 'var(--r-md)',
                    border: `1.5px solid ${mcpSettings.discovery_mode === 'built_in_auto' ? 'var(--primary)' : 'var(--border)'}`,
                    backgroundColor: mcpSettings.discovery_mode === 'built_in_auto' ? 'var(--surface-subtle)' : 'var(--surface)',
                    cursor: 'pointer',
                    transition: 'all 0.15s ease',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--sp-2)', fontWeight: 600 }}>
                    <input
                      type="radio"
                      name="discovery_mode"
                      value="built_in_auto"
                      checked={mcpSettings.discovery_mode === 'built_in_auto'}
                      onChange={() => setMcpSettings({ ...mcpSettings, discovery_mode: 'built_in_auto' })}
                    />
                    <span>Built-in Autonomous Engine</span>
                  </div>
                  <span style={{ fontSize: 'var(--fs-xs)', color: 'var(--text-muted)', paddingLeft: 'var(--sp-5)' }}>
                    AgentReach executes query planning, scraping, heuristic scoring, and SQLite persistence automatically in a single background tool call.
                  </span>
                </label>
              </div>
            </fieldset>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: 'var(--sp-4)' }}>
              <div className="form-group">
                <label htmlFor="settings-mcp-output-format" className="label">
                  Default Export Format
                </label>
                <select
                  id="settings-mcp-output-format"
                  className="input"
                  value={mcpSettings.default_output_format}
                  onChange={(e) =>
                    setMcpSettings({
                      ...mcpSettings,
                      default_output_format: e.target.value as 'markdown' | 'json' | 'both',
                    })
                  }
                >
                  <option value="both">Both Markdown & JSON (.md + .json)</option>
                  <option value="markdown">Markdown Report (.md)</option>
                  <option value="json">Structured JSON (.json)</option>
                </select>
                <span className="helper-text">Used when AI exports customer discovery findings.</span>
              </div>

              <div className="form-group">
                <label htmlFor="settings-mcp-min-score" className="label">
                  Default Lead Score Threshold (0–100)
                </label>
                <input
                  id="settings-mcp-min-score"
                  type="number"
                  min={0}
                  max={100}
                  className="input"
                  value={mcpSettings.default_min_score}
                  onChange={(e) =>
                    setMcpSettings({
                      ...mcpSettings,
                      default_min_score: Math.max(0, Math.min(100, parseInt(e.target.value, 10) || 0)),
                    })
                  }
                />
                <span className="helper-text">Filter threshold for high-intent qualified leads.</span>
              </div>

              <div className="form-group">
                <label htmlFor="settings-mcp-export-path" className="label">
                  Default Export Directory
                </label>
                <input
                  id="settings-mcp-export-path"
                  type="text"
                  className="input"
                  value={mcpSettings.default_export_path}
                  onChange={(e) => setMcpSettings({ ...mcpSettings, default_export_path: e.target.value })}
                />
                <span className="helper-text">Where .md and .json files are saved on disk.</span>
              </div>
            </div>

            <div className="form-group" style={{ marginBottom: 0 }}>
              <label
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 'var(--sp-3)',
                  cursor: 'pointer',
                  userSelect: 'none',
                }}
              >
                <input
                  type="checkbox"
                  checked={mcpSettings.auto_launch_dashboard}
                  onChange={(e) => setMcpSettings({ ...mcpSettings, auto_launch_dashboard: e.target.checked })}
                  style={{ width: '16px', height: '16px' }}
                />
                <span style={{ fontSize: 'var(--fs-sm)', fontWeight: 500 }}>
                  Automatically open browser UI when AI launches the dashboard tool
                </span>
              </label>
            </div>
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

export default SettingsView;
