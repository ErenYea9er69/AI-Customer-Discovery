# 🔌 Agent Reach — Model Context Protocol (MCP) Setup Guide

Agent Reach includes a universal FastMCP server that connects customer intelligence, community lead harvesting (Reddit, Hacker News, GitHub, Web), lead qualification, and reply drafting directly to your favorite AI development environments.

---

## ⚡ Zero External API Keys Needed in MCP Mode

When using Agent Reach through an MCP client (**Google Antigravity, Claude Code, Cursor, VS Code**):
- **Your host AI assistant IS the intelligence layer.**
- Community scraping across Reddit, Hacker News, GitHub, and the Web is performed directly via standard HTTP (no third-party LLM tokens or API keys required).
- The host AI analyzes the harvested discussions, determines Ideal Customer Profile (ICP) fit, qualifies buying intent, and crafts value-first responses directly in your conversation context.
- Everything is permanently stored and synchronized into your local SQLite database (`discovery.db`).

---

## 🛠️ Multi-Client Configuration

### 1. Google Antigravity
Antigravity integrates MCP servers via its Agent Panel or global configuration:

**Option A (Agent Panel UI):**
1. Open the **Agent Panel** in Antigravity.
2. Click the top-right `...` menu -> **Manage MCP Servers**.
3. Select **Add Server** or edit raw configuration:
```json
{
  "mcpServers": {
    "agent-reach": {
      "command": "python",
      "args": ["-m", "agent_reach.mcp.server"]
    }
  }
}
```

**Option B (Global Config File):**
- **Windows:** `%USERPROFILE%\.gemini\antigravity\mcp_config.json`
- **macOS / Linux:** `~/.gemini/antigravity/mcp_config.json`

---

### 2. Cursor IDE
Add to your project's `.cursor/mcp.json` or your global Cursor MCP configuration (`%USERPROFILE%\.cursor\mcp.json` on Windows / `~/.cursor/mcp.json` on macOS/Linux):

```json
{
  "mcpServers": {
    "agent-reach": {
      "command": "python",
      "args": ["-m", "agent_reach.mcp.server"]
    }
  }
}
```
*Note: A ready-to-use `.cursor/mcp.json` is already placed in this project root.*

---

### 3. Claude Code
In Claude Code, add the MCP server via CLI or project config:

```bash
# Add via CLI:
claude mcp add agent-reach python -m agent_reach.mcp.server
```

Or configure `.mcp.json` in your workspace root (already pre-configured in this repository):
```json
{
  "mcpServers": {
    "agent-reach": {
      "command": "python",
      "args": ["-m", "agent_reach.mcp.server"]
    }
  }
}
```

---

### 4. VS Code (Cline / Continue / MCP Extensions)
In VS Code, add to your extension's MCP configuration (e.g. `cline_mcp_settings.json`):

```json
{
  "mcpServers": {
    "agent-reach": {
      "command": "python",
      "args": ["-m", "agent_reach.mcp.server"],
      "disabled": false,
      "autoApprove": []
    }
  }
}
```

---

### 5. Claude Desktop
Add to your `claude_desktop_config.json` (`%APPDATA%\Claude\claude_desktop_config.json` on Windows):

```json
{
  "mcpServers": {
    "agent-reach": {
      "command": "python",
      "args": ["-m", "agent_reach.mcp.server"]
    }
  }
}
```

---

## 🧰 Available MCP Tools

| Tool Name | Description |
| :--- | :--- |
| `reach_get_or_create_profile` | Retrieve or set up the business profile (name, problems solved, ICP, competitors). |
| `reach_plan_queries` | Generate customer pain and intent search queries from profile. |
| `reach_harvest_threads` | Scrape online communities (Reddit, Hacker News, GitHub, Web) for candidate discussions without requiring any LLM API keys. |
| `reach_save_lead` | Persist qualified leads with full 100-point score breakdown directly into SQLite. |
| `reach_list_leads` | Filter and inspect qualified leads from SQLite by score, platform, or classification. |
| `reach_save_reply` | Save drafted value-first and product-aware replies into SQLite. |
| `reach_run_autonomous_batch` | Execute all-in-one discovery batch (plan -> harvest -> heuristic score -> save to SQLite). |
| `reach_get_settings` / `reach_update_settings` | Inspect and configure discovery mode (`host_driven` vs `built_in_auto`), default output formats, and score thresholds. |
| `reach_export_results` | Export leads into Markdown report (`.md`), structured dataset (`.json`), or both simultaneously. |
| `reach_control_dashboard` | Check status or launch the FastAPI & React Dashboard (`http://127.0.0.1:8000`) and optionally open your browser. |

---

## 💡 Example Prompt Workflows

### Prompt 1: Host-Driven Discovery (Zero LLM API Keys)
> *"Find 5 leads on Reddit and Hacker News for our product AlphaLead (AI customer discovery tool). Scrape candidate threads, qualify them in chat based on buying intent and urgency, save the qualified leads to the database, and export the results to both Markdown and JSON."*

### Prompt 2: Autonomous Goal Loop
> *"Run automated customer discovery until you find at least 5 leads with a score of 75+ for SaaS founders struggling with customer acquisition. When finished, open the dashboard UI so I can review them."*

### Prompt 3: Headless Export
> *"Search GitHub issues and Reddit for people complaining about expensive email outreach tools. Save the top leads to the database and generate a markdown report in `./reports/outreach_leads.md`. No need to open the UI."*

