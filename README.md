# 🎯 Agent Reach: AI Customer Discovery & Lead Generation Agent

> Transform raw community conversations into high-intent customer leads and personalized, value-first replies.

Agent Reach is an AI customer intelligence and lead discovery agent. It analyzes a business website or product description, identifies the exact problems it solves and its Ideal Customer Profile (ICP), searches relevant online communities (Reddit, Web, GitHub Issues) for people actively experiencing those problems, evaluates lead intent with an explainable 100-point score, and generates personalized, community-compliant responses.

---

## ⚡ Key Capabilities

- **🧠 Business Understanding Engine:** Crawls company websites (`/pricing`, `/features`, `/about`, `/faq`) or analyzes manual product descriptions. Extracts verified facts (with direct source links) and AI inferences with confidence ratings.
- **🔍 Intelligent Customer Discovery:** Generates targeted queries based on customer pain expressions (`"struggling with..."`, `"looking for an alternative to..."`, `"hate having to..."`, `"is there a tool that..."`). Prioritizes Reddit as the primary source, supplemented by Web, GitHub, and .
- **📊 Explainable Lead Qualification (100 Points):**
  - **ICP Match:** 25 points
  - **Problem & Product Fit:** 30 points
  - **Buying Intent:** 20 points
  - **Urgency:** 15 points
  - **Recency:** 10 points
  - Classifies into *High-Potential Lead*, *Relevant Lead*, *Customer Research Insight*, and *Competitor Intelligence*.
- **💬 AI Reply Studio:** Generates two distinct response strategies:
  - **Value-First Response:** Genuine actionable advice and solutions with zero promotional pitch.
  - **Product-Aware Response:** Helpful answer naturally introducing the product with transparent affiliation disclosure.
- **🛡️ Safe Publishing & Automation:** Draft mode, Manual Approval mode (default), and Automatic mode with emergency stops, allowed community whitelists, and daily rate limits. Fallback copy-and-open workflow for platforms without direct API posting.
- **🖥️ Precision CRM Dashboard:** Full-stack dashboard built with FastAPI, SQLite, React, TypeScript, Vite, and the Better Design Precision system tokens.

---

## 🚀 Quick Start

### 1. Model Context Protocol (MCP) Mode (Antigravity, Claude Code, Cursor, VS Code)

Connect Agent Reach directly to your AI assistant:
```bash
# Run FastMCP server over stdio:
agent-reach mcp
# or:
python -m agent_reach.mcp.server
```

> **Zero External LLM APIs Needed:** In MCP mode, your host AI (Claude, Cursor, Antigravity) handles all reasoning, lead scoring, and reply generation. The server harvests community conversations directly and persists findings into SQLite.

See [docs/mcp_setup.md](docs/mcp_setup.md) for pre-built configurations for Antigravity, Cursor (`.cursor/mcp.json`), Claude Code (`.mcp.json`), and VS Code.

---

### 2. Start the Customer Discovery Dashboard

```bash
# Starts the FastAPI server and serves the built dashboard UI at http://127.0.0.1:8000
agent-reach dashboard --port 8000
```
Open [http://127.0.0.1:8000](http://127.0.0.1:8000) in your browser.

---

### 2. CLI Customer Discovery Workflows

You can also run all customer discovery stages directly from the command line:

#### Step 1: Analyze Website or Product Description
```bash
# Extract from a website URL:
agent-reach discovery profile --url "https://myproduct.example.com"

# Or extract from a manual description:
agent-reach discovery profile --name "SuperTask" --desc "AI tool that automates GitHub issue triage and backlog deduplication."
```

#### Step 2: Plan Customer Discovery Queries
```bash
agent-reach discovery plan
```

#### Step 3: Run Research Campaign
```bash
agent-reach discovery search --max 10 --name "Q4 Inbound Hunt"
```

#### Step 4: List & Inspect Qualified Leads
```bash
agent-reach discovery leads --min-score 70
```

#### Step 5: Generate & Inspect Replies
```bash
agent-reach discovery reply <lead-id>
```

#### Step 6: Export Leads for CRM Sync
```bash
# Export to CSV:
agent-reach discovery export --format csv > leads.csv

# Export to JSON:
agent-reach discovery export --format json > leads.json
```

#### Step 7: View Pain Point Analytics
```bash
agent-reach discovery analytics
```

---

## 🏛️ Architecture & Modules

```
agent_reach/
├── discovery/
│   ├── models.py          # Pydantic data models (Profile, Lead, Reply, Settings)
│   ├── storage.py         # SQLite persistence & CSV/JSON export
│   ├── business_engine.py # Website scraping & fact/inference extraction
│   ├── search_planner.py  # Problem & competitor alternative query generation
│   ├── harvester.py       # Multi-platform community search (Reddit, Web, GitHub)
│   ├── qualifier.py       # 100-point explainable lead qualification
│   ├── reply_generator.py # Value-first and product-aware response generation
│   ├── publisher.py       # Safe publishing layer, rate limits & emergency stop
│   ├── analytics.py       # Customer pain points, competitor gaps & strategy suggestions
│   ├── orchestrator.py    # Background campaign execution coordinator
│   └── cli.py             # CLI commands (dashboard, discovery)
├── server/
│   └── app.py             # FastAPI REST endpoints & static asset serving
├── channels/              # Platform integration adapters
frontend/                  # React + TypeScript + Vite Dashboard (Precision DS)
tests/                     # Test suite covering all 16 spec scenarios
```

---

## 🧪 Testing & Verification

Run the full automated test suite verifying all 16 required transformation scenarios:

```bash
# Run discovery engine & 16 scenario tests:
python -m pytest tests/test_end_to_end_scenarios.py -v

# Run entire test suite:
python -m pytest tests/
```

---

## 📄 License

MIT
