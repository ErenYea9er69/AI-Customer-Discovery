# Model Context Protocol (MCP) Server Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Provide a standard Model Context Protocol (MCP) server for Agent-Reach over stdio, enabling Antigravity, Claude Code, Cursor, and VS Code to run autonomous or host-driven customer discovery, save to SQLite, trigger UI launch on demand, and export results to Markdown, JSON, or both, with zero required external LLM API keys.

**Architecture:** A standalone FastMCP server module (`agent_reach/mcp/server.py`) uses existing `DiscoveryStorage` and `CommunityHarvester` directly. It exposes both fine-grained stepping tools (host AI evaluates and scores) and automated batching tools (engine runs heuristic loop), stores settings in SQLite, controls UI startup/browser launch, and exports results into Markdown and JSON files.

**Tech Stack:** Python 3.10+, FastMCP (`mcp.server.fastmcp`), SQLite3, Pydantic, Uvicorn, Pytest.

**Spec:** User request dated 2026-10-31 for universal MCP client support (Antigravity, Cursor, Claude Code, VS Code), dual execution modes (host-driven stepping and built-in auto batching) toggled via settings, SQLite persistence, optional UI launching, and Markdown/JSON exports.

---

## Global Constraints

- Never break or alter existing CLI commands (`agent-reach discovery`, `agent-reach dashboard`, `agent-reach read`, etc.).
- Never require an external LLM API key (OpenAI/Groq/Gemini) for MCP functionality; all scraping runs via direct HTTP and AI qualification is powered by the host client.
- All persistent data (profiles, items, leads, replies, settings) MUST write to and read from the central SQLite database (`discovery.db`).
- Transport MUST be standard I/O (stdio) via FastMCP to guarantee cross-client compatibility.
- Windows file paths and UTF-8 encodings MUST be handled safely without blocking or console crashes.

---

## Review Focus

1. **Dashboard Process Conflict:** Launching the dashboard when port 8000 is already in use must detect the running instance gracefully without crashing or creating orphan processes.
2. **Formula Injection in Markdown/CSV Exports:** User-provided or scraped community texts starting with `=, +, -, @` must be escaped safely.
3. **Empty or Missing Search Results:** When queries yield zero candidates on certain platforms, tools must return clean empty lists and diagnostics instead of throwing unhandled exceptions.
4. **Settings Default Fallbacks:** Accessing uninitialized settings (e.g. `discovery_mode`) must return validated defaults without raising database errors.
5. **Stdio Stream Cleanliness:** Background logging or prints must not write unformatted text to stdout, preserving the clean JSON-RPC protocol channel for MCP clients.

---

## Task Decomposition

### Task 1: Exporters, Settings, and Dashboard Process Helpers

**Files:**
- Create: `agent_reach/mcp/helpers.py`
- Create: `agent_reach/mcp/__init__.py`
- Test: `tests/test_mcp_helpers.py`

**Interfaces:**
- Consumes: `DiscoveryStorage` (`agent_reach/discovery/storage.py`), `LeadQualification` (`agent_reach/discovery/models.py`)
- Produces:
  - `generate_markdown_report(leads: List[LeadQualification], profile: Optional[BusinessProfile]) -> str`
  - `export_results_files(storage: DiscoveryStorage, output_dir: Path, formats: str, min_score: int) -> Dict[str, str]`
  - `get_or_init_mcp_settings(storage: DiscoveryStorage) -> Dict[str, Any]`
  - `update_mcp_settings(storage: DiscoveryStorage, updates: Dict[str, Any]) -> Dict[str, Any]`
  - `is_port_in_use(port: int, host: str) -> bool`
  - `ensure_dashboard_running(port: int, host: str, open_browser: bool) -> Dict[str, Any]`

- [ ] **Step 1: Write the failing tests for helpers**
  - Create `tests/test_mcp_helpers.py` testing:
    - `generate_markdown_report` generates valid markdown containing lead titles, scores, and URLs.
    - `export_results_files` handles "markdown", "json", and "both" and writes output files correctly.
    - `get_or_init_mcp_settings` initializes default settings (`discovery_mode="host_driven"`, `default_output_format="both"`).
    - `update_mcp_settings` safely mutates settings in SQLite.

- [ ] **Step 2: Run test to verify it fails**
  Run: `python -m pytest tests/test_mcp_helpers.py -v`
  Expected: FAIL (ModuleNotFoundError: No module named 'agent_reach.mcp')

- [ ] **Step 3: Implement `agent_reach/mcp/helpers.py` and `__init__.py`**
  - Implement report generation, file export, settings management, and dashboard socket check/browser launch.

- [ ] **Step 4: Run test to verify it passes**
  Run: `python -m pytest tests/test_mcp_helpers.py -v`
  Expected: PASS

- [ ] **Step 5: Commit**
  Run: `git add agent_reach/mcp/ tests/test_mcp_helpers.py && git commit -m "feat(mcp): add export, settings and dashboard helper functions"`

---

### Task 2: FastMCP Server Core & Tool Implementations

**Files:**
- Create: `agent_reach/mcp/server.py`
- Test: `tests/test_mcp_server.py`

**Interfaces:**
- Consumes: `agent_reach.mcp.helpers`, `agent_reach.discovery.storage.DiscoveryStorage`, `agent_reach.discovery.harvester.CommunityHarvester`, `agent_reach.discovery.search_planner.SearchPlanner`, `agent_reach.discovery.qualifier.LeadQualifier`
- Produces FastMCP tools:
  - `reach_get_or_create_profile`: manage active business profile in SQLite.
  - `reach_plan_queries`: generate search queries from profile or manual pains.
  - `reach_harvest_threads`: search Reddit, HN, GitHub, Web directly (no LLM keys).
  - `reach_save_lead`: save lead qualified by host AI into SQLite.
  - `reach_list_leads`: list and filter qualified leads from SQLite.
  - `reach_save_reply`: save value-first and product-aware replies into SQLite.
  - `reach_run_autonomous_batch`: automated discovery batch running plan, scrape, heuristic scoring, and SQLite persistence in one step.
  - `reach_get_settings` / `reach_update_settings`: get or update settings (mode: host_driven vs built_in_auto, default output format, min score).
  - `reach_export_results`: export leads to markdown, json, or both.
  - `reach_control_dashboard`: launch FastAPI server or open browser UI on demand.

- [ ] **Step 1: Write the failing tests for MCP server tools**
  - Create `tests/test_mcp_server.py` verifying tool calls directly:
    - Profile creation and retrieval.
    - Query planning.
    - Lead saving with score breakdown into SQLite.
    - Settings read and update.
    - Result export in both formats.
    - Autonomous batch discovery execution.

- [ ] **Step 2: Run test to verify it fails**
  Run: `python -m pytest tests/test_mcp_server.py -v`
  Expected: FAIL (Cannot import server or tools)

- [ ] **Step 3: Implement `agent_reach/mcp/server.py`**
  - Initialize `FastMCP("AgentReach")`.
  - Decorate and register all tools with complete docstrings, type annotations, and structured return envelopes.
  - Add `main()` entrypoint running `mcp.run(transport="stdio")`.

- [ ] **Step 4: Run test to verify it passes**
  Run: `python -m pytest tests/test_mcp_server.py -v`
  Expected: PASS

- [ ] **Step 5: Commit**
  Run: `git add agent_reach/mcp/server.py tests/test_mcp_server.py && git commit -m "feat(mcp): implement FastMCP server with host-driven and autonomous discovery tools"`

---

### Task 3: CLI Entrypoint Integration (`agent-reach mcp`)

**Files:**
- Modify: `agent_reach/runtime/cli.py`
- Modify: `pyproject.toml`
- Test: `tests/test_mcp_cli.py`

**Interfaces:**
- Consumes: `agent_reach.mcp.server.main`
- Produces: `agent-reach mcp` command supporting `--transport stdio`

- [ ] **Step 1: Write the failing test for `agent-reach mcp` CLI routing**
  - Create `tests/test_mcp_cli.py` testing that executing `agent_reach.runtime.cli.main(["mcp", "--help"])` recognizes the MCP command.

- [ ] **Step 2: Run test to verify it fails**
  Run: `python -m pytest tests/test_mcp_cli.py -v`
  Expected: FAIL

- [ ] **Step 3: Add `mcp` handler to `agent_reach/runtime/cli.py`**
  - Add `mcp` to CLI routing and help description.
  - Call `agent_reach.mcp.server.main()`.

- [ ] **Step 4: Run test to verify it passes**
  Run: `python -m pytest tests/test_mcp_cli.py -v`
  Expected: PASS

- [ ] **Step 5: Commit**
  Run: `git add agent_reach/runtime/cli.py tests/test_mcp_cli.py && git commit -m "feat(cli): add agent-reach mcp command for stdio server launch"`

---

### Task 4: Client Configuration Presets & Setup Documentation

**Files:**
- Create: `.mcp.json` (Claude Code configuration)
- Create: `.cursor/mcp.json` (Cursor IDE configuration)
- Create: `docs/mcp_setup.md` (Setup instructions for Antigravity, Claude Code, Cursor, VS Code)
- Modify: `README.md` (Add MCP Server Quickstart section)

- [ ] **Step 1: Create client config JSON files**
  - Generate `.mcp.json` for Claude Code.
  - Generate `.cursor/mcp.json` for Cursor.
- [ ] **Step 2: Document configuration steps in `docs/mcp_setup.md`**
  - Antigravity: instructions for `~/.gemini/antigravity/mcp_config.json` and Agent Panel.
  - Claude Code: `claude mcp add` and `.mcp.json`.
  - Cursor: Cursor Settings > Features > MCP.
  - VS Code: Cline / Continue / GitHub Copilot config.
  - Explain dual modes (Host-Driven vs Built-in Auto) and settings customization.
- [ ] **Step 3: Update `README.md`**
  - Add MCP usage section alongside Dashboard and CLI sections.
- [ ] **Step 4: Commit**
  Run: `git add .mcp.json .cursor/mcp.json docs/mcp_setup.md README.md && git commit -m "docs: add MCP configuration files and multi-client guide"`

---

### Task 5: Full Verification and End-to-End Regression Test

**Files:**
- Run: Entire test suite (`pytest tests/`)

- [ ] **Step 1: Verify all 16 existing discovery tests pass**
  Run: `python -m pytest tests/test_end_to_end_scenarios.py -v`
  Expected: 16 passed.

- [ ] **Step 2: Verify full test suite passes**
  Run: `python -m pytest tests/ -v`
  Expected: All tests pass with 0 failures.

- [ ] **Step 3: Test MCP stdio handshake**
  Run a Python test simulating MCP `initialize` and `tools/list` JSON-RPC handshake over STDIO.
  Expected: Returns list of `reach_*` tools.

- [ ] **Step 4: Commit any final test fixtures**
  Run: `git commit -m "test: verify end-to-end MCP server and full test suite"`

