import type {
  AnalyticsSummary,
  BusinessProfile,
  Campaign,
  GeneratedReply,
  LeadQualification,
  PostingSettings,
} from './types';

const BASE_URL = '/api';

export const api = {
  // Profile
  async getProfile(): Promise<BusinessProfile | null> {
    const res = await fetch(`${BASE_URL}/profile`);
    const data = await res.json();
    return data.profile;
  },

  async extractFromUrl(url: string): Promise<BusinessProfile> {
    const res = await fetch(`${BASE_URL}/profile/extract-url`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url }),
    });
    if (!res.ok) throw new Error(await res.text());
    const data = await res.json();
    return data.profile;
  },

  async extractFromManual(name: string, description: string): Promise<BusinessProfile> {
    const res = await fetch(`${BASE_URL}/profile/extract-manual`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, description }),
    });
    if (!res.ok) throw new Error(await res.text());
    const data = await res.json();
    return data.profile;
  },

  async updateProfile(profile: BusinessProfile): Promise<BusinessProfile> {
    const res = await fetch(`${BASE_URL}/profile/update`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(profile),
    });
    if (!res.ok) throw new Error(await res.text());
    const data = await res.json();
    return data.profile;
  },

  async confirmProfile(): Promise<BusinessProfile> {
    const res = await fetch(`${BASE_URL}/profile/confirm`, {
      method: 'POST',
    });
    if (!res.ok) throw new Error(await res.text());
    const data = await res.json();
    return data.profile;
  },

  // Campaigns
  async listCampaigns(): Promise<Campaign[]> {
    const res = await fetch(`${BASE_URL}/campaigns`);
    const data = await res.json();
    return data.campaigns;
  },

  async launchCampaign(name: string, platforms: string[], maxLeads: number): Promise<string> {
    const res = await fetch(`${BASE_URL}/campaigns/launch`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, platforms, max_leads: maxLeads }),
    });
    if (!res.ok) throw new Error(await res.text());
    const data = await res.json();
    return data.campaign_id;
  },

  async getCampaign(id: string): Promise<Campaign> {
    const res = await fetch(`${BASE_URL}/campaigns/${id}`);
    const data = await res.json();
    return data.campaign;
  },

  // Leads
  async listLeads(filters: {
    min_score?: number;
    platform?: string;
    classification?: string;
    pain_point_category?: string;
    buying_intent?: string;
    query?: string;
  } = {}): Promise<LeadQualification[]> {
    const params = new URLSearchParams();
    if (filters.min_score !== undefined) params.append('min_score', filters.min_score.toString());
    if (filters.platform) params.append('platform', filters.platform);
    if (filters.classification) params.append('classification', filters.classification);
    if (filters.pain_point_category) params.append('pain_point_category', filters.pain_point_category);
    if (filters.buying_intent) params.append('buying_intent', filters.buying_intent);
    if (filters.query) params.append('query', filters.query);

    const res = await fetch(`${BASE_URL}/leads?${params.toString()}`);
    const data = await res.json();
    return data.leads;
  },

  async getLeadCounts(): Promise<Record<string, number>> {
    const res = await fetch(`${BASE_URL}/leads/counts`);
    return await res.json();
  },

  async getLead(id: string): Promise<{ lead: LeadQualification; reply?: GeneratedReply }> {
    const res = await fetch(`${BASE_URL}/leads/${id}`);
    if (!res.ok) throw new Error(await res.text());
    return await res.json();
  },

  // Replies
  async getReply(leadId: string): Promise<GeneratedReply> {
    const res = await fetch(`${BASE_URL}/replies/${leadId}`);
    const data = await res.json();
    return data.reply;
  },

  async generateReply(leadId: string): Promise<GeneratedReply> {
    const res = await fetch(`${BASE_URL}/replies/${leadId}/generate`, { method: 'POST' });
    const data = await res.json();
    return data.reply;
  },

  async approveReply(leadId: string, editedReply?: string, selectedVersion?: string): Promise<GeneratedReply> {
    const res = await fetch(`${BASE_URL}/replies/${leadId}/approve`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ edited_reply: editedReply, selected_version: selectedVersion }),
    });
    const data = await res.json();
    return data.reply;
  },

  async publishReply(leadId: string): Promise<{ success: boolean; action?: string; text?: string; target_url?: string; reason?: string; message?: string }> {
    const res = await fetch(`${BASE_URL}/replies/${leadId}/publish`, { method: 'POST' });
    return await res.json();
  },

  // Analytics
  async getAnalytics(): Promise<AnalyticsSummary> {
    const res = await fetch(`${BASE_URL}/analytics`);
    return await res.json();
  },

  // Settings
  async getSettings(): Promise<{ posting_settings: PostingSettings; llm_settings: any }> {
    const res = await fetch(`${BASE_URL}/settings`);
    return await res.json();
  },

  async updateSettings(settings: { posting_settings?: PostingSettings; llm_settings?: any }): Promise<void> {
    await fetch(`${BASE_URL}/settings`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(settings),
    });
  },

  getExportUrl(format: 'json' | 'csv', minScore: number = 0): string {
    return `${BASE_URL}/export?format=${format}&min_score=${minScore}`;
  },
};
