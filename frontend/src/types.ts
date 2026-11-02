export interface FactItem {
  claim: string;
  source_url: string;
  category: string;
}

export interface InferenceItem {
  insight: string;
  confidence: number;
  basis: string;
}

export interface BusinessProfile {
  id: string;
  name: string;
  url?: string;
  description: string;
  industry: string;
  niche: string;
  main_product_or_service: string;
  features: string[];
  problems_solved: string[];
  customer_outcomes: string[];
  icp: string;
  target_industries: string[];
  target_roles: string[];
  customer_demographics: string[];
  customer_frustrations: string[];
  competitors_and_alternatives: string[];
  unique_selling_points: string[];
  pricing_info?: string;
  geographic_market: string;
  trigger_events: string[];
  pain_vocabulary: string[];
  not_for: string[];
  facts: FactItem[];
  inferences: InferenceItem[];
  confirmed: boolean;
  created_at: number;
  updated_at: number;
}

export interface SearchQuery {
  id: string;
  query: string;
  intent_type: string;
  platform: string;
  target_community?: string;
  rationale: string;
  stage?: string;
}

export interface Campaign {
  id: string;
  name: string;
  business_profile_id: string;
  status: 'idle' | 'running' | 'completed' | 'failed' | 'cancelled';
  selected_platforms: string[];
  queries: SearchQuery[];
  diagnostics?: Record<string, number>;
  total_found: number;
  total_qualified: number;
  high_potential_count: number;
  progress_percentage: number;
  current_step: string;
  created_at: number;
  completed_at?: number;
}

export interface ScoreBreakdown {
  icp_match: number;
  problem_fit: number;
  buying_intent: number;
  urgency: number;
  recency: number;
  total: number;
  explanation: string;
}

export type LeadClassification =
  | 'high_potential'
  | 'relevant_potential'
  | 'customer_insight'
  | 'competitor_intel'
  | 'irrelevant';

export interface ThreadHealth {
  verified?: boolean;
  commentable?: boolean | null;
  num_comments?: number | null;
  score?: number | null;
  age_days?: number | null;
  kind?: string;
  warnings?: string[];
  crowded?: boolean;
}

export interface LeadQualification {
  id: string;
  discovered_item_id: string;
  title: string;
  url: string;
  platform: string;
  community: string;
  author: string;
  published_at: string;
  excerpt: string;
  customer_problem: string;
  pain_point_category: string;
  profile_match: string;
  competitor_mentioned?: string;
  purchase_intent: 'High' | 'Medium' | 'Low' | 'None';
  urgency: 'High' | 'Medium' | 'Low';
  product_fit_explanation: string;
  evidence: string;
  score: number;
  score_breakdown: ScoreBreakdown;
  classification: LeadClassification;
  confidence: number;
  judged_by?: 'llm' | 'heuristic';
  thread_health?: ThreadHealth;
  post_type?: string;
  evidence_verified?: boolean;
  reply_policy?: 'draft' | 'human_only' | string;
  status?: 'new' | 'rejected' | 'replied' | 'closed';
  reject_reason?: string;
  created_at: number;
}

export interface GeneratedReply {
  id: string;
  lead_id: string;
  value_first: string;
  product_aware: string;
  edited_reply?: string;
  selected_version: 'value_first' | 'product_aware' | 'custom';
  status: 'draft' | 'approved' | 'pending_manual_post' | 'published' | 'rejected';
  published_at?: number;
  platform: string;
  target_url: string;
  affiliation_disclosure: string;
  error_message?: string;
  target_kind?: 'post' | 'comment';
  target_comment_id?: string;
  target_author?: string;
  target_text?: string;
  target_reason?: string;
  pitch_level?: number;
  lint?: Record<string, any>;
  needs_human_edit?: boolean;
  generated_by?: string;
  published_comment_id?: string;
  published_url?: string;
  outcome?: Record<string, any>;
  created_at?: number;
  updated_at?: number;
}

export interface PostingSettings {
  mode: 'draft' | 'manual' | 'automatic';
  daily_limit: number;
  min_interval_seconds: number;
  allowed_communities: string[];
  require_account_health?: boolean;
  emergency_stop: boolean;
  interval_jitter?: number;
  max_mention_ratio?: number;
  require_rules_ack?: boolean;
  reddit_client_id?: string;
  reddit_client_secret?: string;
  reddit_username?: string;
  reddit_password?: string;
  github_token?: string;
  has_reddit_password?: boolean;
  has_reddit_client_secret?: boolean;
  has_github_token?: boolean;
}

export interface LLMSettings {
  provider: string;
  model: string;
  api_key?: string;
  has_api_key?: boolean;
  configured?: boolean;
}

export interface MCPSettings {
  discovery_mode: 'host_driven' | 'built_in_auto';
  default_output_format: 'markdown' | 'json' | 'both';
  default_min_score: number;
  default_export_path: string;
  emergency_stop: boolean;
  auto_launch_dashboard: boolean;
}

export interface SettingsPayload {
  posting_settings: PostingSettings;
  llm_settings: LLMSettings;
  mcp_settings?: MCPSettings;
}

export interface PlatformInfo {
  platforms: string[];
  default: string[];
  weak: string[];
}

export interface AnalyticsSummary {
  total_leads: number;
  top_communities?: { community: string; leads: number; high_potential: number }[];
  reply_mix?: {
    published_last_90_days: number;
    product_aware: number;
    value_first: number;
    product_share?: number;
  };
  common_complaints: { problem: string; count: number; category: string }[];
  pain_point_categories: { category: string; count: number }[];
  high_urgency_problems: { problem: string; count: number; community: string; excerpt: string }[];
  competitor_intelligence: { competitor: string; mentions: number }[];
  intent_distribution: Record<string, number>;
  urgency_distribution: Record<string, number>;
  platform_distribution: Record<string, number>;
  recommendations: { type: string; title: string; description: string }[];
}
