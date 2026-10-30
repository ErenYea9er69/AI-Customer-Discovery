---
name: agent-reach
description: >
  Internet access, customer discovery, and lead generation for AI agents: search, read posts, evaluate customer problems, qualify leads, and extract structured business intelligence.
  Use when the user mentions or pastes a link from Reddit, Web, GitHub, Twitter/X, LinkedIn, V2EX,
  or asks to "discover customers", "find leads", "search for problems", or "read this link" and your built-in
  web search or fetch is unavailable, fails, or misses the body;
  or wants to launch customer discovery, manage platforms, configure keys, or run the lead intelligence dashboard.
  Does not: spam, bypass platform terms, or ask for passwords.
metadata:
  homepage: https://github.com/Panniantong/Agent-Reach
  version: "{{VERSION}}"
---

# Agent Reach

One command for community search, customer intelligence, and lead generation: `agent-reach`. All output is structured JSON.

Before acting, say "using the agent-reach skill (channel X)". Once invoked, these rules apply for the whole session.

## Customer Discovery & Lead Intelligence

To discover potential customers experiencing problems your product solves:

```bash
# Analyze a website or product description to extract ICP and problems solved
agent-reach discovery profile --url <url>
agent-reach discovery profile --name <name> --desc <description>

# Generate customer pain queries and search communities (Reddit, Web, GitHub, V2EX)
agent-reach discovery plan
agent-reach discovery search --max 15

# View qualified leads (0-100 score) and generate personalized responses
agent-reach discovery leads --min-score 70
agent-reach discovery reply <lead-id>

# Launch the visual Precision CRM dashboard
agent-reach dashboard --port 8000
```

## Reading and Searching Platforms

- For public content, use your own search/read tools first. Check body text, comments, and subtitles separately; when they are sufficient, answer directly without adding channels or logging in.
- Use Reach when your tools are unavailable, the result lacks what the user needs, or the user wants a site action a channel declares. Unsure of actions and params? Run `agent-reach channels`.
- An added channel sends search/read straight to its site tool. For channels not added yet, search/read first tries anonymous public web access; results mark it with `backend: public-web`. `--backend public-web` limits to public web; `--backend <backend>` picks a site tool.
- A platform name or link only identifies the source; it never triggers install or login by itself.

```bash
agent-reach channels                      # actions and params per channel
agent-reach <channel> <action> [args]     # e.g. agent-reach reddit search "backlog triage" --limit 5
agent-reach read <url>                    # picks the channel from the URL
```

## Results and Errors

- `ok: true` → content in `items`; each has `title / url / author / published_at / text`, upstream data in `raw`.
- `ok: false` → branch on `error.code` and follow `error.hint`:

| error.code | What to do |
|---|---|
| `NEED_SETUP` | Missing dependency or key. Run `agent-reach add <channel>` as hinted; for a key, the user provides it, then `agent-reach configure <key>` |
| `NEED_LOGIN` | Keep existing results and tell the user login is needed; `agent-reach login <channel>` opens the browser and the user logs in themselves. Never log in for them or ask for a password |
| `UPSTREAM_BROKEN` | This platform is temporarily not working; `message` is what was reported. Tell the user which platform is unavailable and roughly why, by platform name, without naming tools; run `agent-reach update` once, after they agree, only if the message points to an outdated tool; never retry in a loop |
| `TIMEOUT` | Check the failed stage and channel status (`agent-reach doctor --text`); do not retry or reopen windows in a loop |
| `RATE_LIMITED` | The platform rate-limited; Reach paused the channel. Wait `retry_after_seconds`; do not switch backends |
| `PLATFORM_BLOCKED` | The platform wants verification (captcha/risk check). Stop; the user resolves it on the official page. Do not switch accounts or backends |
| `BUSY` | The browser stayed full for the 2-minute wait in line, or the user has a login window open. Retry later, or after the user says they are logged in; do not close the window or switch profiles |
| `NOT_FOUND` | Content does not exist; check the link or ID |
| `BAD_INPUT` | Wrong arguments; run `agent-reach channels` for usage |

On `PLATFORM_BLOCKED`, `RATE_LIMITED`, `NEED_LOGIN` or `BUSY`, stop this attempt; do not retry with other accounts, backends, or browsers.

## Login and Dedicated Browser

All browser channels share one dedicated browser (CloakBrowser preferred, falling back to installed Chrome). It runs headless by default, closes after 10 idle minutes, and reopens on the next call. Calls may run in parallel: up to 2 per platform and 4 in total run at once, the rest wait in line, and two searches on the same platform start at least 10 seconds apart.

See [Sessions](references/sessions.md) for session reuse, multi-profile management, and logout details.

## Capability Boundaries

What each platform offers publicly and what Reach adds is documented in [Capability Scope](references/capabilities.md).

## Channel Overview

{{CHANNEL_TABLE}}

`default` channels are installed by default and can be removed; updates never add a removed one back. The `login` column is the authentication entry point, not a prerequisite for public content.

## Managing Agent Reach

| User says | You run |
|---|---|
| Add a platform | `agent-reach add <channel>`; dependencies install automatically. Tell the user only what they must do (log in or provide a key) |
| Remove a platform | `agent-reach remove <channel>` |
| Log in / login expired | `agent-reach login <channel>`; the user logs in themselves in the window that opens |
| Log out | `agent-reach logout <channel>` |
| Status / what works | `agent-reach doctor --text`; for a live test `agent-reach check <channel> --text` |
| Launch Lead Dashboard | `agent-reach dashboard` |
| Upgrade / update | `agent-reach update` |
| Uninstall | show `agent-reach uninstall --dry-run` first, then `agent-reach uninstall` once they confirm |
| Another AI should use it | `agent-reach skill link <that AI's skills folder>`; `agent-reach skill` shows where it is placed now |

Troubleshooting, browser maintenance, and uninstall details are in [Maintenance](references/maintenance.md).

## Red Lines

- Read-only for web fetching; automated customer reply posting is strictly guarded with manual approval, rate limits, and community whitelists.
- Never log in for the user; never ask for or print passwords, cookies, or credentials.
- Ordinary queries never change dependencies or update automatically.
