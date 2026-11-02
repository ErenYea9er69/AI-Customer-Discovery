# Agent Reach

Agent Reach finds people who have a problem your product solves, in public communities, and drafts honest replies in your own voice. You post every reply yourself from your own account.

It works in two ways that share the same rules:

- A command line pipeline that calls a language model of your choice.
- An MCP server for Claude Code, Cursor, VS Code, Claude Desktop and Antigravity. Your host AI does the reasoning and the server supplies the tools.

Both use one skill pack in `skills/`. Both use the same linter, the same lead scoring rule and the same posting gates. A lead gets the same class on either path.

## What it does

1. Reads your website or your description and builds a profile: the problems you solve, your ideal customer, the words customers use, and the people who should not become leads.
2. Plans searches by buyer stage (switching, solution, problem) in your customers' own words. It never puts your product name in a query.
3. Searches Reddit, Hacker News, GitHub, Quora, X and the web. It keeps open threads that can still take a comment.
4. Scores each thread with a five-part rubric and checks the evidence quote against the stored post. Keyword-only scoring can never reach high potential.
5. Reads the comments and picks where a reply fits: the post, or one comment that asks for a tool.
6. Drafts two replies. The value-first reply never names your product. The product-aware reply names it once and states your connection in a natural first-person sentence.
7. Lints every draft: banned words, dashes, markdown, links, emoji, length, affiliation, repeats, and how closely it matches your voice.
8. Gates posting by your account's real age and karma, the community's rules you recorded, the share of your comments that name the product, a daily cap and one reply per thread.

## Your own accounts

You link accounts you already use. The app stores the handle only. It never stores a password or a cookie and it never creates accounts. It reads public data (age, karma, recent comments) to decide how much promotion the account can carry, and to learn your writing style from your own comments.

| Stage | Account | Highest pitch level |
| --- | --- | --- |
| build | under 30 days or under 100 karma, or unreadable | 0, help only |
| trusted | 30 days and 100 karma | 1, describe the kind of tool |
| established | 90 days and 300 karma | 2, name the product once, no link |
| veteran | 180 days and 500 karma | 3, name it with a link when the thread asks |

An account whose recent comments name the product more than 10 percent of the time drops one stage.

## Install

```
pip install .
```

Python 3.10 or newer. For the MCP server only, you need no model key. For the pipeline, set one provider key (see `.env.example`).

## Quick start with the MCP server

Add this to your client's MCP configuration:

```json
{
  "mcpServers": {
    "agent-reach": { "command": "agent-reach", "args": ["mcp"] }
  }
}
```

Then tell your assistant: "Use Agent Reach to find customers for https://your-site.com". It calls `reach_status` and follows the `customer-discovery` skill. See `docs/mcp_setup.md` for each client.

## Quick start with the command line

```
export ANTHROPIC_API_KEY=...            # or OPENAI_API_KEY, GEMINI_API_KEY, GROQ_API_KEY, DEEPSEEK_API_KEY
agent-reach discovery profile --url https://your-site.com --confirm
agent-reach discovery accounts link reddit:your_handle
agent-reach discovery voice --from-account reddit:your_handle
agent-reach discovery rules set r/freelance --self-promo thread_only --ai-content no
agent-reach discovery search --max 10 --communities r/freelance,r/smallbusiness
agent-reach discovery leads --min-score 60
agent-reach discovery reply LEAD_ID
agent-reach discovery approve REPLY_ID --version value_first
agent-reach discovery post REPLY_ID          # prints the text and a direct link
agent-reach discovery confirm REPLY_ID --url https://www.reddit.com/...
```

`agent-reach discovery` with no command lists every command. Every command prints JSON.

## Platform rules the app follows

| Platform | Drafts | Posting |
| --- | --- | --- |
| Reddit | yes | manual by default. API posting needs approved credentials, two switches and a passing gate |
| Hacker News | no. Generated and AI-edited comments are banned there, so threads are research only | manual |
| GitHub | yes | manual by default, API with a token |
| X | yes, short | manual only. X forbids unsolicited automated replies |
| Quora, web forums | yes | manual only |

Many subreddits ban AI-written content or self promotion. Read each community's rules and record them with `discovery rules set` (or `reach_set_community_rules`). The publisher refuses Reddit posts to communities whose rules you did not record. See `docs/safety.md`.

## The skill pack

Seven skills in `skills/`, one per stage, each with references:

| Skill | Stage | Purpose |
| --- | --- | --- |
| customer-discovery | router | Order of work, stop rules, report format |
| business-intelligence | profile | Facts versus inferences, pain vocabulary, not-for list |
| community-search | search | How members write, query shapes, community choice |
| lead-qualification | qualify | Rubric, anti-inflation rules, calibration examples |
| thread-engagement | engage | Choosing the post or a comment, handling replies |
| community-copywriting | write | Reddit voice, banned words, pitch ladder, disclosure phrases, voice cloning |
| platform-safety | safety | Rules per platform, FTC disclosure, warm-up plan |

Edit them freely. `python scripts/validate_skills.py` checks the result: frontmatter, references, dashes, tool names and that every good example passes the linter while every bad example fails it. `docs/skills.md` explains how to add your own voice samples and banned words.

## Limits you should know

- Reddit's public JSON endpoints are rate limited and sometimes blocked. When comments cannot be read, the reply goes to the post.
- Keyed search providers (Serper, Brave, Tavily), Reddit and GitHub posting through APIs, and the Docker image were written against vendor documentation and were not exercised against live accounts. Run `agent-reach discovery check search` and `check llm` with your keys.
- The linter cannot guarantee that a human moderator or a platform classifier will not notice generated text. Edit every reply so it sounds like you, and post only where the rules allow it.
- The word lists are tuned to English.
- The `dashboard` command needs the dashboard module, which is not part of this build.

## Development

```
pip install -e ".[dev]"
ruff check agent_reach/discovery agent_reach/mcp scripts tests
mypy agent_reach/discovery agent_reach/mcp
pytest
python scripts/validate_skills.py
python scripts/gen_tool_reference.py --check
```

`docs/ci-cd.md` describes the workflows. `AUDIT.md` lists what the original code did and what changed.
