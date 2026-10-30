import React from 'react';
import { AlertCircle, ArrowRight, CheckCircle2, Compass, ExternalLink, Flame, MessageSquare, ShieldCheck, Sparkles, Target } from 'lucide-react';
import type { BusinessProfile, LeadQualification } from '../types';

interface OverviewViewProps { profile: BusinessProfile | null; leads: LeadQualification[]; leadCounts: Record<string, number>; onNavigate: (tab: string, leadId?: string) => void; onLaunchCampaign: () => void; }
const classificationLabel = (value: string) => value.replaceAll('_', ' ').replace(/\b\w/g, (letter) => letter.toUpperCase());

export const OverviewView: React.FC<OverviewViewProps> = ({ profile, leads, leadCounts, onNavigate, onLaunchCampaign }) => {
  const priorityLeads = leads.filter((lead) => lead.classification === 'high_potential' || lead.score >= 75).sort((a, b) => b.score - a.score).slice(0, 4);
  const sourceCount = new Set(leads.map((lead) => lead.platform)).size;
  const qualified = (leadCounts.high_potential || 0) + (leadCounts.relevant || 0);
  const needsReview = leads.filter((lead) => lead.score >= 50 && lead.purchase_intent !== 'None').length;

  return <div className="page-shell overview-page">
    <section className="page-heading overview-heading">
      <div><div className="eyebrow"><Sparkles size={13} /> Opportunity desk</div><h1>Turn public pain into your next conversation.</h1><p>AgentReach finds problem-aware conversations, explains why they matter, and keeps every reply under your control.</p></div>
      <div className="heading-actions"><button className="btn btn-secondary" onClick={() => onNavigate('leads')}>Review queue <ArrowRight size={15} /></button><button className="btn btn-primary" onClick={onLaunchCampaign} disabled={!profile?.confirmed}><Compass size={15} /> Run discovery</button></div>
    </section>

    {!profile ? <section className="notice notice-warning" role="status"><AlertCircle size={19} /><div><strong>Set up your business profile first</strong><span>AgentReach needs a confirmed product and audience model before it can judge relevance.</span></div><button className="btn btn-secondary btn-sm" onClick={() => onNavigate('profile')}>Create profile</button></section> : !profile.confirmed ? <section className="notice notice-info" role="status"><Target size={19} /><div><strong>{profile.name || 'Business profile'} is ready for review</strong><span>Confirm the extracted facts before launching a campaign. Unconfirmed profiles can produce weak searches.</span></div><button className="btn btn-secondary btn-sm" onClick={() => onNavigate('profile')}>Review profile</button></section> : null}

    <section className="metric-grid" aria-label="Discovery summary">
      <article className="metric-card metric-card-primary"><div className="metric-label">Conversations found</div><div className="metric-value">{leadCounts.total || 0}</div><div className="metric-meta"><span className="status-dot status-dot-blue" /> {sourceCount || 0} sources in this queue</div></article>
      <article className="metric-card"><div className="metric-label">Qualified opportunities</div><div className="metric-value">{qualified}</div><div className="metric-meta"><span className="status-dot status-dot-green" /> Score 50+ with a relevant signal</div></article>
      <article className="metric-card"><div className="metric-label">Priority conversations</div><div className="metric-value">{leadCounts.high_potential || 0}</div><div className="metric-meta"><span className="status-dot status-dot-amber" /> High intent or urgent pain</div></article>
      <article className="metric-card"><div className="metric-label">Needs a human review</div><div className="metric-value">{needsReview}</div><div className="metric-meta"><ShieldCheck size={14} /> Drafts stay unposted until approved</div></article>
    </section>

    <section className="overview-grid">
      <article className="panel priority-panel"><div className="panel-header"><div><div className="eyebrow eyebrow-muted"><Flame size={13} /> Next best conversations</div><h2>Priority conversations</h2><p>Start with the clearest evidence and the strongest reason to respond.</p></div></div>
        {priorityLeads.length === 0 ? <div className="empty-state"><div className="empty-icon"><Compass size={20} /></div><strong>No priority conversations yet</strong><span>Confirm your profile, then run discovery to populate the review queue.</span><button className="btn btn-secondary btn-sm" onClick={onLaunchCampaign} disabled={!profile?.confirmed}>Run first discovery</button></div> : <div className="priority-list">{priorityLeads.map((lead) => <div className="priority-row" key={lead.id}><div className="score-ring" aria-label={`Score ${lead.score} out of 100`}><strong>{lead.score}</strong><span>/100</span></div><div className="priority-copy"><div className="priority-meta"><span className="badge badge-high">{classificationLabel(lead.classification)}</span><span>{lead.platform} · {lead.community}</span></div><h3>{lead.title}</h3><p>{lead.customer_problem}</p><div className="evidence-line">“{lead.excerpt}”</div></div><div className="priority-actions"><span className={`intent-pill ${lead.urgency === 'High' ? 'intent-pill-urgent' : ''}`}>{lead.purchase_intent} intent</span><button className="btn btn-primary btn-sm" onClick={() => onNavigate('reply_studio', lead.id)}><MessageSquare size={14} /> Draft reply</button><a className="icon-link" href={lead.url} target="_blank" rel="noreferrer" aria-label={`Open ${lead.title}`}><ExternalLink size={15} /></a></div></div>)}</div>}
      </article>
      <aside className="panel control-panel"><div className="eyebrow eyebrow-muted"><ShieldCheck size={13} /> Control room</div><h2>Safe by default</h2><p className="control-intro">AgentReach separates discovery, drafting, approval, and publication so automation never skips your decision.</p><div className="status-stack"><div className="status-row"><span className="status-icon status-icon-green"><CheckCircle2 size={15} /></span><div><strong>Discovery is explainable</strong><span>Every lead includes score evidence and a source link.</span></div></div><div className="status-row"><span className="status-icon status-icon-blue"><MessageSquare size={15} /></span><div><strong>Replies are drafts first</strong><span>Value-first and disclosed versions stay editable.</span></div></div><div className="status-row"><span className="status-icon status-icon-amber"><ShieldCheck size={15} /></span><div><strong>Publishing is gated</strong><span>Manual copy is pending until you confirm it was posted.</span></div></div></div></aside>
    </section>

    <section className="panel coverage-panel"><div className="panel-header compact-header"><div><h2>Coverage snapshot</h2><p>Where the current queue came from. Counts reflect stored leads, not invented trends.</p></div></div><div className="coverage-grid">{['reddit', 'web', 'github', 'v2ex'].map((platform) => { const count = leads.filter((lead) => lead.platform === platform).length; return <div className="coverage-item" key={platform}><span className="coverage-name">{platform}</span><strong>{count}</strong><span className="coverage-bar"><span style={{ width: `${Math.min(100, count ? Math.max(8, count / Math.max(1, leads.length) * 100) : 0)}%` }} /></span></div>; })}</div></section>
  </div>;
};
