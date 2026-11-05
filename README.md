# Agent Reach

Agent Reach is a small AI company that finds people who have a problem your product solves, in public communities, and drafts honest replies in your own voice. You post every reply yourself from your own account.

You talk to one person: the CEO. The CEO plans the work, hands tasks to specialists, makes them check each other, and tells you only what passed verification.

```
                 you
                  |
                 CEO  (your AI assistant, or the server's own model)
                  |  plans tasks, writes briefs, launches tools, decides
   +----------+---+---------+-----------+-----------+-----------+------------+
 analyst    scout     qualifier     writer     editor     strategist   researcher   follow_up
 profile    search      leads       drafts    2nd read     reviews     competitors   threads
                  \          |          /
                   +-- verifier (evidence, quotes, numbers, links) and the automatic posting inspector --+
```

## How the company works

1. You ask the CEO for something: "find customers for https://my-site.com".
2. The CEO opens a directive and plans tasks (`ceo_open_directive`). Each task has a role, an instruction, acceptance checks and dependencies.
3. Each specialist gets a brief built from its charter, the skill pack and the verified output of earlier tasks. It works only through the tools its role allows.
4. Every tool call lands in an evidence ledger. A specialist's output must cite those evidence ids.
5. The verifier checks each output before it counts: unknown evidence ids, quotes that are not in the evidence, numbers or links no tool returned, leads without a verified quote, drafts that fail the linter. A second model (the auditor model) may object to unsupported claims. After three failed tries the task goes back to the CEO, who retries, reassigns or skips it.
6. The CEO stops at owner checkpoints: you confirm the profile, and you approve each reply. The CEO records your own words.
7. The report lists verified work, what did not pass, numbers from the database and your next actions.

The CEO can also create tasks (`ceo_create_task`), hire a new specialist with its own prompt and tool list (`ceo_hire_specialist`) and save a reusable plan (`ceo_create_playbook`). A specialist can never hold a posting, approval, settings or account tool.

Since 3.1 the company also:
- has nine specialists (analyst, scout, qualifier, writer, editor, strategist, researcher, follow_up) plus an automatic posting inspector that runs without a model, and seven built-in plans, and plans a request that fits none of them;
- asks you for a site or a description when your request has neither;
- treats "nothing found" as a valid result: the scout widens the search once, later steps are skipped, and the report lists what was tried;
- has an editor who reads every draft and sends weak ones back to the writer once;
- remembers your standing preferences (`ceo_memory`) and what it learned, and shows them to every specialist;
- tells the assistant the single next action (`ceo_next_step`), recovers tasks that stalled, stops on `ceo_cancel_directive` and stops runaway tool use with a budget;
- reports lead cards (thread, verified quote, draft, gate result), a trust level and what was tried. See `docs/company.md`.

## Two ways to run it

| | Server model | Host assistant |
| --- | --- | --- |
| Who is the CEO | The server's model | Your assistant (Claude Code, Cursor, VS Code, Claude Desktop, Antigravity) |
| Who works | Specialists on the server's model | Your assistant plays each specialist through work orders |
| Needs | One provider key | No key |
| Checks | Same ledger, same permissions, same verifier | Same |

Everything is an MCP tool. The server registers no MCP prompts.

## What the specialists do

1. The analyst reads your website or description and builds a profile: the problems you solve, your ideal customer, the words customers use, and the people who should not become leads.
2. The scout plans searches by buyer stage (switching, solution, problem) in your customers' own words. It never puts your product name in a query. It searches Reddit, Hacker News, GitHub, Quora, X and the web, and keeps open threads that can still take a comment.
3. The qualifier scores each thread with a five-part rubric and checks the evidence quote against the stored post. Keyword-only scoring can never reach high potential. A second model reads high potential threads again.
4. The writer drafts two replies in your voice. The value-first reply never names your product. The product-aware reply names it once and states your connection in a natural first-person sentence. Every draft passes the linter: banned words, dashes, markdown, links, emoji, length, affiliation, repeats and voice match. Numbers in a draft must appear in the profile or the thread.
5. The editor reads every draft against its thread and the profile and sends weak ones back once.
6. The posting inspector runs by itself. For each draft it asks the posting gates what they would say if you approved it today: your account's real age and karma, the community rules you recorded, the share of your comments that name the product, a daily cap and one reply per thread. It also flags a draft edited after the editor read it.
7. The strategist reviews results when you ask for a weekly review.

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
pip install .                      # MCP server and CLI
pip install ".[dashboard]"         # adds the API for your dashboard
```

Python 3.10 or newer. With only the MCP server you need no model key. For server-side specialists, the CLI and the dashboard chat, set one provider key (see `.env.example`).

## Quick start with the MCP server

Add this to your client's MCP configuration:

```json
{
  "mcpServers": {
    "agent-reach": { "command": "agent-reach", "args": ["mcp"] }
  }
}
```

Then tell your assistant: "Use Agent Reach to find customers for https://your-site.com". It acts as the CEO: it calls `ceo_open_directive` and follows the `company-operations` skill. By default the host sees the CEO tools plus the owner tools (approve, publish, confirm, accounts, settings). Use `agent-reach mcp --mode full` to show every low level tool as well. See `docs/mcp_setup.md` for each client.

## Quick start with the command line

Talk to the CEO from the terminal (needs a provider key):

```
agent-reach team ask "Find customers for https://your-site.com"
agent-reach team status
agent-reach team checkpoint TASK_ID approve --message "The profile is right."
agent-reach team report DIRECTIVE_ID
```

Or run the pipeline step by step:

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

Eight skills in `skills/`, each with references. `company-operations` is the CEO's playbook. The other seven are the stages the specialists follow:

| Skill | Stage | Purpose |
| --- | --- | --- |
| company-operations | router | How the CEO plans, delegates, verifies and reports |
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
- The host-assistant mode cannot prove that you, and not the assistant, answered an owner checkpoint. The server records your words and refuses an empty answer.
- The auditor model and the second opinion need a provider key on the server. Without one, only the deterministic checks run.

## Development

```
pip install -e ".[dev]"
ruff check agent_reach scripts tests
mypy agent_reach/discovery agent_reach/mcp agent_reach/team
pytest
python scripts/validate_skills.py
python scripts/gen_tool_reference.py --check
```

`docs/ci-cd.md` describes the workflow. `AUDIT.md` lists what the first audit found. `COMPANY_AUDIT.md` lists the weaknesses of the company layer and the 3.1 fixes. `CHANGELOG.md` lists the release notes.
