# MCP setup

The MCP server runs over stdio. Your host AI does the reasoning. The server fetches public pages, stores results, checks scores and writing, and gates posting. You need no model key for it.

## Install

```
pip install agent-reach          # or: pip install .  from a checkout
agent-reach mcp --help
```

The server needs the MCP Python SDK in the range `>=1.27,<3`. Both the 1.x and 2.x lines are tested in CI. The package declares the range, so pip picks a working version.

To run it without installing, use the container:

```
docker build -t agent-reach .
docker run -i --rm -v reach-data:/data agent-reach mcp
```

## Client configuration

Every client takes the same entry. Use `agent-reach` when it is on your PATH, or the full path to the executable.

```json
{
  "mcpServers": {
    "agent-reach": {
      "command": "agent-reach",
      "args": ["mcp"],
      "env": { "AGENT_REACH_DISCOVERY_DB": "/home/you/.agent-reach/discovery.db" }
    }
  }
}
```

Where to put it:

| Client | Location |
| --- | --- |
| Claude Code | `claude mcp add agent-reach -- agent-reach mcp`, or `.mcp.json` in the project |
| Cursor | `.cursor/mcp.json` in the project, or `~/.cursor/mcp.json` |
| VS Code | `.vscode/mcp.json` (use the key `servers` instead of `mcpServers`) |
| Claude Desktop | `claude_desktop_config.json` (Settings, Developer, Edit Config) |
| Antigravity | `~/.gemini/antigravity/mcp_config.json`, or Agent Panel, Manage MCP Servers |

The repository ships `.mcp.json` and `.cursor/mcp.json` with this entry.

Optional environment values go in the `env` block: `SERPER_API_KEY`, `BRAVE_API_KEY` or `TAVILY_API_KEY` for better search, and a model key only if you want the server's own `reach_analyze_business` or batch qualification to use a model. See `.env.example`.

## First conversation

Tell the assistant: "Use Agent Reach to find customers for https://your-site.com." It should:

1. call `reach_status`, then read the `customer-discovery` skill with `reach_get_skill`;
2. read your site with `reach_fetch_site_text`, write the profile and show it to you;
3. ask which of your accounts to link, and which communities you plan to use;
4. search, read threads, score leads and draft replies, one skill per stage.

The server also publishes the skills as resources (`skill://NAME`) and three prompts: `find_customers`, `draft_reply` and `weekly_review`.

## Tools

`skills/customer-discovery/references/tool-reference.md` lists all 31 tools with their arguments. It is generated from the server, and CI fails when it is stale. The groups are:

- State and skills: `reach_status`, `reach_list_skills`, `reach_get_skill`
- Profile: `reach_fetch_site_text`, `reach_analyze_business`, `reach_get_or_create_profile`
- Search: `reach_plan_queries`, `reach_harvest_threads`, `reach_read_thread`
- Leads: `reach_save_lead`, `reach_list_leads`, `reach_set_lead_status`, `reach_run_autonomous_batch`
- Replies: `reach_get_reply_context`, `reach_lint_reply`, `reach_save_reply`, `reach_approve_reply`
- Posting: `reach_publish_reply`, `reach_confirm_posted`
- Owner setup: `reach_link_account`, `reach_account_health`, `reach_unlink_account`, `reach_import_voice_from_account`, `reach_set_voice_samples`, `reach_set_reply_preferences`, `reach_set_community_rules`
- Settings and output: `reach_get_settings`, `reach_update_settings`, `reach_export_results`, `reach_get_insights`, `reach_control_dashboard`

Each tool carries annotations: read only, writes locally, or reads public pages and writes locally. Clients that honor them can ask before the second and third kind.

## What protects you

- Thread text, comments and pages come back wrapped as untrusted, with `injection_flags`. Skip flagged items.
- `reach_save_lead` takes sub-scores, not a class. The server caps each score, looks for your evidence quote in the stored thread and sets the class. An unverified quote cannot reach high potential.
- `reach_save_reply` runs the linter and refuses a draft with errors. The issues come back as a list to fix.
- `reach_publish_reply` runs every gate. In manual mode it returns text and a link. A reply counts as posted only after `reach_confirm_posted`.
- `reach_export_results` writes only under the current folder, your home folder or the temp folder.
- `reach_update_settings` with `emergency_stop` stops all posting at once.

## Troubleshooting

| Symptom | Cause and fix |
| --- | --- |
| `ModuleNotFoundError: mcp.server.fastmcp` in an older install | The SDK is 2.x. Upgrade this package. The new server picks the right import. |
| Client shows no tools | Run `agent-reach mcp` in a terminal. It should wait silently for input. Check the path to `agent-reach`. |
| `reach_harvest_threads` returns few items | Run `agent-reach discovery check search`. Without a keyed backend the app uses Exa and DuckDuckGo, which rate limit. |
| `rules_not_read` when publishing | Record the community's rules with `reach_set_community_rules`. |
| `account_unknown` | Link the account with `reach_link_account`, or turn off `require_account_health` knowingly. |
