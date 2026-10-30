# AI Customer Discovery & Lead Generation Agent Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Transform Agent-Reach into a complete, full-stack AI Customer Discovery & Lead Generation Agent with website analysis, community discovery (Reddit, Web, GitHub, V2EX), explainable lead qualification, value-first & product-aware reply generation, safe publishing controls, and a high-density Precision-style dashboard.

**Architecture:** A modular Python engine (`agent_reach/discovery/`) handling website extraction, query planning, harvesting, scoring, reply generation, safe publishing, and SQLite persistence, coupled with a FastAPI server (`agent_reach/server/`) and a React + Vite + TypeScript dashboard (`frontend/`) adopting the Better Design Precision system.

**Tech Stack:** Python 3.10+, FastAPI, SQLite, Pydantic, Requests/BeautifulSoup, React, TypeScript, Vite, Tailwind CSS.

**Spec:** `transfermation.md`

## Global Constraints
- Core discovery source: Reddit; supplementary: Web Search and Jina Reader.
- Secondary profile-driven sources: GitHub (dev tools), V2EX (tech), Twitter/LinkedIn (when relevant).
- Disabled from default workflow: YouTube, Bilibili, Xiaoyuzhou podcasts, Boss Zhipin, Xueqiu stock research, Xiaohongshu, Instagram.
- Explainable scoring: ICP match (25), Problem fit (30), Buying intent (20), Urgency (15), Recency (10) -> Total 100.
- Reply modes: Value-first (no pitch) and Product-aware (transparent affiliation disclosure).
- Publishing safety: Draft, Manual approval (default), Automatic with rate limits and emergency stop; copy-reply fallback.
- Design system: Precision (data-dense, light CRM, indigo accent, clean 6px radii).
- Clean up: Remove unused old assets/pngs/sponsors at the end.

---

### Task 1: Core Data Models & SQLite Persistence Layer
- [ ] Create `agent_reach/discovery/models.py` with Pydantic models for BusinessProfile, SearchQuery, DiscoveredItem, LeadQualification, GeneratedReply, PostingSettings, and Campaign.
- [ ] Create `agent_reach/discovery/storage.py` with SQLite schema, CRUD operations, filtering, and CSV/JSON export.
- [ ] Write unit tests in `tests/test_discovery_storage.py` verifying persistence and queries.

### Task 2: Configurable LLM Client & Fact/Inference Engine
- [ ] Create `agent_reach/discovery/llm_client.py` supporting mock fallback heuristic engine, OpenAI, Gemini, Groq, and structured JSON parsing.
- [ ] Write unit tests in `tests/test_llm_client.py` verifying parsing, prompt formats, and fallback modes.

### Task 3: Business Understanding Engine (Website & Manual)
- [ ] Create `agent_reach/discovery/business_engine.py` to scrape websites (homepage, /pricing, /features, /about, /faq) via Jina Reader/requests and extract structured BusinessProfile.
- [ ] Distinguish verified facts (with source links) from AI inferences with confidence scores.
- [ ] Support manual product/service description input.
- [ ] Write unit tests in `tests/test_business_engine.py`.

### Task 4: Intelligent Search Planner & Multi-Platform Harvester
- [ ] Create `agent_reach/discovery/search_planner.py` generating frustration, alternative, and intent queries based on ICP and niche.
- [ ] Create `agent_reach/discovery/harvester.py` connecting to Reddit (public API/JSON + OpenCLI), Web (Exa/Jina), GitHub issues, and V2EX.
- [ ] Implement deduplication, stale filtering (>12 months), and noise filtering.
- [ ] Write unit tests in `tests/test_harvester.py`.

### Task 5: Explainable Lead Qualification & Scoring System
- [ ] Create `agent_reach/discovery/qualifier.py` implementing the 100-point explainable scoring: ICP (25), Fit (30), Intent (20), Urgency (15), Recency (10).
- [ ] Classify into High-Potential, Relevant, Customer Insight, Competitor Intel, and Irrelevant.
- [ ] Write unit tests in `tests/test_qualifier.py`.

### Task 6: AI Reply Generator (Value-First & Product-Aware)
- [ ] Create `agent_reach/discovery/reply_generator.py` generating both Value-First and Product-Aware responses with community guideline compliance and affiliation disclosures.
- [ ] Write unit tests in `tests/test_reply_generator.py`.

### Task 7: Publishing Layer, Rate Limiter & Automation Controls
- [ ] Create `agent_reach/discovery/publisher.py` supporting Draft, Manual Approval (default), and Automatic mode with emergency stop, rate limits, and fallback copy-reply workflow.
- [ ] Write unit tests in `tests/test_publisher.py`.

### Task 8: Analytics Engine
- [ ] Create `agent_reach/discovery/analytics.py` aggregating common pain points, urgent problems, competitor feedback, and recommendations.
- [ ] Write unit tests in `tests/test_discovery_analytics.py`.

### Task 9: FastAPI Backend API & CLI Integration
- [ ] Create `agent_reach/server/app.py` with endpoints for profile, campaigns, leads, replies, analytics, export, and settings.
- [ ] Add `agent-reach discovery` CLI subcommands in `agent_reach/runtime/cli.py` and `agent_reach/cli.py`.
- [ ] Write API integration tests in `tests/test_server_api.py`.

### Task 10: Frontend Dashboard (Vite + React + TypeScript + Precision Design System)
- [ ] Scaffold `frontend/` with Vite, React, TypeScript, and Tailwind CSS.
- [ ] Apply Better Design Precision design system tokens (colors, font, radii, layout density).
- [ ] Implement all 7 views: Overview, Business Profile, Discovery, Leads Inbox, Reply Studio, Analytics, Settings.
- [ ] Build static assets into backend static folder or runnable dev server.

### Task 11: End-to-End Verification & 16 Required Test Scenarios
- [ ] Run full automated verification covering all 16 test scenarios listed in `transfermation.md`.
- [ ] Verify error handling (failed URL, empty results, auth limits).
- [ ] Clean up unused legacy assets/pngs/sponsors as requested in line 1 of `transfermation.md`.

