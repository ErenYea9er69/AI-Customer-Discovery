# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [2.0.0] - 2026-10-31

### 🚀 Major Transformation: AI Customer Discovery & Lead Intelligence Agent

Agent Reach has evolved into a focused, full-lifecycle **Autonomous AI Customer Discovery & Lead Generation Platform**. Given a website URL or product description, the agent automatically models your ICP, discovers prospects actively complaining about problems you solve across online communities, qualifies leads with a 100-point explainable scoring engine, and drafts authentic, non-spam replies.

#### Summary for Users:
- **Instant Product & ICP Modeling**: Analyzes product landing pages or raw text descriptions to identify target audiences, core problems solved, and value propositions.
- **Dynamic 2-Year Recency Filtering**: Automatically adapts search queries to the current calendar year (e.g., 2026 and 2025) and enforces post/comment recency, ensuring prospects are active.
- **Direct Community Harvesting**: Scrapes authentic complaints and discussions from Reddit, Twitter/X (`x.com/<user>/status/<id>`), Quora, and general web communities.
- **Purged Legacy Platforms**: Completely removed legacy Chinese social and media download channels (Bilibili, Xiaohongshu, Boss Zhipin, Xueqiu, Xiaoyuzhou, Instagram, Facebook) to deliver a lightweight, high-performance customer discovery core.
- **Resilient Multi-Engine Fallback**: Seamless fallback across DuckDuckGo HTML, Jina Reader, SearXNG, and Exa AI prevents rate-limit blockades.
- **100-Point Explainable Qualification**: Evaluates every discovered post on Pain Severity (30), Purchase Intent (25), Solution Fit (25), and Urgency/Recency (20).
- **Dual-Mode Response Generation**: Generates value-first educational replies (no sales pitch) and tailored product recommendations based on prospect context.
- **Precision CRM Dashboard**: Modern web interface (FastAPI + React/Vite) for reviewing leads, editing replies, managing campaigns, and tracking customer pain analytics.

### ✨ Active Channels

- **Reddit (`RedditChannel`)**: Community search, problem discussion threads, comments, and sentiment analysis.
- **Twitter / X (`TwitterChannel`)**: Real-time tweets, customer complaints, and direct `x.com` status threads.
- **Web (`WebChannel`)**: Multi-engine search and content reading fallback (DuckDuckGo, Jina Reader, Quora, blogs).
- **GitHub (`GitHubChannel`)**: Developer complaints, open-source discussions, and technical bug reports.
- **YouTube (`YouTubeChannel`)**: Tutorial workflow discussions, tool comparison comments, and transcripts.
- ** (`Channel`)**: Tech community discussions, node topics, and developer replies.

---

## [1.6.0] - 2026-10-23

### 🔄 Architecture & CLI Refactoring

- **Unified CLI Architecture**: Unified all channel commands under `agent-reach <channel> <action>` with structured JSON envelopes.
- **Isolated Storage**: Moved private tools and channel state under `~/.agent-reach/`.
- **Capability Diagnostics**: Added `agent-reach doctor` for real-time health checks of scraping backends.
