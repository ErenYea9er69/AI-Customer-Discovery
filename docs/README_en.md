# 🎯 Agent Reach: AI Customer Discovery & Lead Generation Agent

> Transform raw community conversations into high-intent customer leads and personalized, value-first replies.

Agent Reach is an AI customer intelligence and lead discovery agent. It analyzes a business website or product description, identifies the exact problems it solves and its Ideal Customer Profile (ICP), searches relevant online communities (Reddit, Web, GitHub Issues, V2EX) for people actively experiencing those problems, evaluates lead intent with an explainable 100-point score, and generates personalized, community-compliant responses.

---

## ⚡ Key Capabilities

- **🧠 Business Understanding Engine:** Crawls company websites (`/pricing`, `/features`, `/about`, `/faq`) or analyzes manual product descriptions. Extracts verified facts (with direct source links) and AI inferences with confidence ratings.
- **🔍 Intelligent Customer Discovery:** Generates targeted queries based on customer pain expressions (`"struggling with..."`, `"looking for an alternative to..."`, `"hate having to..."`, `"is there a tool that..."`). Prioritizes Reddit as the primary source, supplemented by Web, GitHub, and V2EX.
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

### 1. Start the Customer Discovery Dashboard

```bash
# Starts the FastAPI server and serves the built dashboard UI at http://127.0.0.1:8000
agent-reach dashboard --port 8000
```
Open [http://127.0.0.1:8000](http://127.0.0.1:8000) in your browser.

---

### 2. CLI Customer Discovery Workflows

```bash
# Extract from a website URL:
agent-reach discovery profile --url "https://myproduct.example.com"

# Or extract from a manual description:
agent-reach discovery profile --name "SuperTask" --desc "AI tool that automates GitHub issue triage and backlog deduplication."

# Plan search queries:
agent-reach discovery plan

# Run discovery search:
agent-reach discovery search --max 10 --name "Q4 Inbound Hunt"

# List qualified leads:
agent-reach discovery leads --min-score 70

# Generate response:
agent-reach discovery reply <lead-id>

# Export leads to CSV/JSON:
agent-reach discovery export --format csv > leads.csv

# View customer pain analytics:
agent-reach discovery analytics
```

---

## 🧪 Testing & Verification

Run the full automated test suite verifying all 16 required transformation scenarios:

```bash
python -m pytest tests/test_end_to_end_scenarios.py -v
```

---

## 📄 License

MIT
