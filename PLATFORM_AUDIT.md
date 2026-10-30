# Platform Integration Audit: Customer Discovery & Lead Generation

## Executive Summary

This audit evaluates all existing channel integrations in Agent-Reach for the transformation into an **AI Customer Discovery and Lead Generation Agent**.

Rather than functioning as a generic scraper or media downloader, the agent's new mission is:
1. Discovering people experiencing problems that a specific product or service solves.
2. Extracting exact pain points, buying intent, and customer context.
3. Generating personalized, helpful, value-first replies.
4. Managing lead approvals, tracking analytics, and supporting compliant publishing workflows.

---

## Evaluation Framework

Each integration is evaluated against 9 criteria:
1. **Customer Complaints & Discussions:** Does the platform contain users describing real-world problems and frustrations?
2. **Conversation Search:** Can we search for problem expressions, complaints, and alternative requests?
3. **Comments & Replies Access:** Can we inspect full conversation context (root post + replies)?
4. **Solution-Seeking Signals:** Do users ask for tool/service recommendations or better ways of doing things?
5. **Search Filters:** Does the platform support targeted filtering (by community/subreddit, date, keyword)?
6. **Data Reliability:** Is the data structured, reliable, and high-fidelity for lead qualification?
7. **Authentication & Cost:** Does it require complex logins, proxy pools, or expensive paid subscriptions?
8. **Permitted Publishing:** Does it support documented, compliant publishing (or clean manual copy workflows)?
9. **Strategic Value:** Is it worth maintaining for customer discovery and lead generation?

---

## Detailed Platform Evaluation

### 1. Reddit (`agent_reach/channels/reddit.py`)
- **Customer Complaints & Discussions:** **Exceptional.** Reddit is the premier public forum where users express frustration ("I hate having to...", "Does anyone know a better way..."), review products, and complain about existing SaaS/tools.
- **Search Capabilities:** Search by keywords across subreddits or within specific targeted communities.
- **Comments & Replies:** `read` retrieves the original post plus threaded comments and replies with author metadata.
- **Solution Seeking:** **Very High.** People frequently ask for software alternatives and recommendations.
- **Search Filters:** Filtering by subreddit (`r/<name>`), keyword, and limit.
- **Data Reliability:** High text fidelity and clear timestamps.
- **Authentication & Cost:** Public posts and comments can be fetched without authentication or using the managed browser session. Official Reddit API is accessible for registered developer credentials.
- **Publishing:** Draft mode & manual copy-paste workflow by default; official OAuth2 PRAW-compatible script posting supported when configured.
- **Classification:** **CORE** (Primary discovery source).

### 2. Web Channel (`agent_reach/channels/web.py`)
- **Customer Complaints & Discussions:** **Very High.** Covers discussions across independent forums, Discourse instances, Quora, Medium, StackExchange, and review aggregators.
- **Search Capabilities:** Multi-query search via Exa MCP hosted gateway and HTTP fallback.
- **Comments & Replies:** Jina Reader clean Markdown extraction of full articles, discussions, and forums.
- **Solution Seeking:** **High.** Uncovers niche community threads and buyer guides.
- **Search Filters:** Domain filtering, search scoping.
- **Data Reliability:** High readability and structured Markdown extraction.
- **Authentication & Cost:** Exa free hosted endpoint + Jina reader; no API keys required for basic discovery.
- **Publishing:** N/A (read-only search and website analysis engine).
- **Classification:** **CORE** (Supplementary search & business website analyzer).

### 3. GitHub (`agent_reach/channels/github.py`)
- **Customer Complaints & Discussions:** **High** for developer tools, libraries, infrastructure, and technical SaaS. Users log feature requests, tool pain points, and shortcomings of open-source alternatives.
- **Search Capabilities:** Issue and PR search across GitHub repositories.
- **Comments & Replies:** Full issue bodies and threaded discussion comments.
- **Solution Seeking:** High for technical and B2B software solutions.
- **Search Filters:** Repository, issue status (open/closed), labels.
- **Data Reliability:** Structured REST API and `gh` CLI JSON.
- **Authentication & Cost:** Free GitHub personal access token or unauthenticated public rate limit.
- **Publishing:** Documented and permitted via official GitHub REST API (`POST /repos/{owner}/{repo}/issues/{number}/comments`).
- **Classification:** **OPTIONAL** (Enabled automatically for developer & tech ICPs).

### 4. Twitter / X (`agent_reach/channels/twitter.py`)
- **Customer Complaints & Discussions:** **High.** Users vent about broken software, tag competitors, and request recommendations.
- **Search Capabilities:** Keyword search via OpenCLI browser session.
- **Comments & Replies:** Thread extraction supported.
- **Solution Seeking:** Moderate to high.
- **Search Filters:** Keyword and limit.
- **Data Reliability:** Moderate; character constraints and noise/bots require strict filtering.
- **Authentication & Cost:** OpenCLI browser session required. Official API v2 is paywalled ($100+/month).
- **Publishing:** Manual approval with one-click copy and original post redirect. (Automated posting restricted due to API costs).
- **Classification:** **OPTIONAL** (Enabled for social/consumer/indie niches).

### 5. LinkedIn (`agent_reach/channels/linkedin.py`)
- **Customer Complaints & Discussions:** High on LinkedIn feeds/groups for enterprise and B2B; existing channel is focused on job search and job specs.
- **Search Capabilities:** Job listings and company roles.
- **Comments & Replies:** Limited in current implementation.
- **Solution Seeking:** High for HR, recruiting, and B2B services.
- **Search Filters:** Query and location.
- **Data Reliability:** High for job postings and company requirements.
- **Authentication & Cost:** Requires session cookie (`li_at`).
- **Publishing:** Manual copy-only; strict anti-bot and Terms of Service enforcement.
- **Classification:** **OPTIONAL** (Focused on B2B hiring & workforce solutions).

### 6. Facebook (`agent_reach/channels/facebook.py`)
- **Customer Complaints & Discussions:** High within private groups and niche community pages.
- **Search Capabilities:** Basic OpenCLI search.
- **Comments & Replies:** Unstable without active logged-in browser session.
- **Solution Seeking:** Moderate.
- **Search Filters:** Keyword.
- **Data Reliability:** Fragile due to aggressive anti-scraping challenges.
- **Authentication & Cost:** Mandatory browser session.
- **Publishing:** Strictly prohibited without Meta Business Graph API verification. Manual copy workflow only.
- **Classification:** **OPTIONAL** (Disabled by default).

### 7. V2EX (`agent_reach/channels/v2ex.py`)
- **Customer Complaints & Discussions:** **High** for developer tools, indie products, remote work, and tech hardware.
- **Search Capabilities:** Node topics, hot topics, topic detail with replies.
- **Comments & Replies:** Full comments thread with author usernames.
- **Solution Seeking:** High among tech-savvy and indie builder audiences.
- **Search Filters:** By node name (`create`, `programmer`, `ideas`, `share`).
- **Data Reliability:** Exceptionally high (native HTTPS JSON API).
- **Authentication & Cost:** Public API requires no token; personal token supported.
- **Publishing:** Manual copy workflow.
- **Classification:** **OPTIONAL** (Enabled for tech & indie hacker products).

---

## Discontinued / Irrelevant Integrations (Disabled from Workflow)

| Platform | Reason for Disabling from Lead Generation Workflow |
| :--- | :--- |
| **YouTube** (`youtube.py`) | Video downloading and Whisper audio transcription are high latency, resource-heavy, and yield passive video content rather than direct customer complaints. Disabled from default discovery. |
| **Bilibili** (`bilibili.py`) | Video sharing platform with low signal-to-noise ratio for customer problem discovery. Disabled from default discovery. |
| **Xiaoyuzhou** (`xiaoyuzhou.py`) | Podcast transcription channel. Irrelevant for real-time customer conversation discovery. Disabled from default discovery. |
| **Boss Zhipin** (`boss.py`) | Chinese job recruiting portal. Irrelevant for general software and service customer discovery. Disabled from default discovery. |
| **Xueqiu** (`xueqiu.py`) | Stock market and financial ticker quotes. Irrelevant to customer discovery and lead generation. Disabled. |
| **XiaoHongShu** (`xiaohongshu.py`) | Lifestyle image notes requiring mobile device signatures. High friction; disabled from default workflow. |
| **Instagram** (`instagram.py`) | Visual media platform with poor conversation indexing. Disabled from default workflow. |

---

## Action Plan & Architectural Strategy

1. **Keep Channel Infrastructure Intact:** Retain the clean `agent_reach/channels/` adapter architecture and existing CLI commands so existing capabilities remain functional.
2. **Prioritize Discovery Sources:**
   - Default: **Reddit** + **Web Search / Jina Reader**.
   - Profile-driven: **GitHub** (for dev tools), **V2EX** (for tech/indie), **Twitter/LinkedIn** (when relevant).
3. **Build the Lead Engine Layers:**
   - `agent_reach/discovery/`: Business understanding, search planning, qualification, reply generation, and safe publishing.
   - `agent_reach/server/`: FastAPI backend with REST endpoints and WebSocket/SSE progress updates.
   - `frontend/`: Modern React + TypeScript + Vite UI built with the **Precision** design system tokens.

