# Audit: what the original code did, and what changed

This audit follows the code, not the README files. Each finding names the evidence and the change. "Verified" means I ran the original code or read the exact lines. "Not verified" means I could not run it here.

## Findings in the original

| # | Finding | Evidence | Change |
| --- | --- | --- | --- |
| 1 | The MCP server fails on a fresh install. `mcp>=1.0.0` installs SDK 2.3.0, which removed `mcp.server.fastmcp`. | Verified: import error on a clean virtualenv | `mcp/compat.py` picks `MCPServer` (2.x) or `FastMCP` (1.x). The pin is `mcp>=1.27,<3`. CI tests both lines. |
| 2 | `bs4` and `pydantic` are imported but not declared. A clean wheel install breaks. | Verified in pyproject | Declared. A clean-wheel install test runs in CI. |
| 3 | Default model names are retired or about to be: Groq `llama-3.3-70b-versatile` (2026-08-16) and DeepSeek `deepseek-chat` (2026-07-24). One fixed name per provider, no fallback. | `llm_client.py` `DEFAULT_MODELS` | Candidate lists per provider and tier, with fallback and a remembered working model. `discovery check llm` tests the key. A weekly canary job calls it. |
| 4 | A second reply for the same lead crashes the MCP `reach_save_reply`. `replies.lead_id` is UNIQUE and the upsert keyed on `id` only. | Verified | Upsert by lead. |
| 5 | The MCP `reach_save_lead` trusted the host's `score` and `classification`. A host could save any class with no evidence check. | `mcp/server.py` signature | The host sends sub-scores. The server caps them, finds the evidence quote in the stored post, sums the total and calls the same `classify` function the pipeline uses. |
| 6 | Thread and comment text reached the host AI with no marking. | `mcp/server.py` | Untrusted envelope with injection flags on every tool that returns community text. Flagged threads are skipped. |
| 7 | Replies could only target the post (`t3_` on Reddit). Comments were never read. The product said "respond on the comments". | `publisher.py` | `thread_comments.py` reads Reddit, Hacker News and GitHub comments, scores targets, and the publisher replies to a comment (`t1_`). |
| 8 | The product-aware reply carried a stock footer, "Disclosure: I am affiliated with X." Communities and readers recognize that form. | `reply_generator.py` | A natural first-person sentence inside the reply, chosen from 22 approved phrases or a close variant. The linter rejects footers and tags. |
| 9 | Reddit password and token fields sat in `PostingSettings`, which the app saved to SQLite. | `models.py`, `storage.py` | Secrets never persist. They come from the environment. Settings output hides them. |
| 10 | Automatic posting needed only `mode=automatic`. No community rules check, no account health, no one-reply-per-thread rule. The default allow-list named six startup subreddits. | `publisher.py`, `models.py` | Thirteen ordered gates (see `docs/safety.md`). Automatic mode needs a second switch and approved credentials. The allow-list default is empty. |
| 11 | No link to a real account. The app could not tell a 10-day-old account from a 5-year-old one. | whole code base | `accounts.py`: link a handle, read public age, karma and recent comments, derive a stage and the allowed pitch level. |
| 12 | No voice handling and no writing checks. Output went to a person after a plain prompt. | `reply_generator.py` | `voice.py`: voice card from your own comments, banned lists (169 hard terms, 29 avoid terms), dash, markdown, link, emoji, length and repeat checks, a voice score and a three-attempt repair loop. |
| 13 | Search used one DuckDuckGo HTML scrape. | `harvester.py` | Backend chain: Serper, Brave, Tavily (keyed), then Exa, then DuckDuckGo, with per-backend diagnostics. |
| 14 | The planner built queries from stripped keywords and did not rank by buyer stage. | `search_planner.py` | Queries use the profile's pain vocabulary, rank switching over solution over problem, cap 2 per stage and platform, never include the product name, and drop nonsense queries for non-product alternatives. |
| 15 | MCP export wrote to any path. The MCP batch tool crossed every query with every platform. Emergency stop existed in two places that did not talk to each other. | `mcp/server.py`, `mcp/helpers.py` | Export limited to the working folder, home or temp. The batch plans per platform. One switch sets both stops. |
| 16 | The `dashboard` command starts `agent_reach.server.app`, which is not in the archive. | Verified: no `server/` folder | The command prints a clear message when the module is missing. Not rebuilt. |
| 17 | Hacker News was treated like any platform. | `publisher.py` | No drafts for Hacker News (generated and AI-edited comments are banned since March 2026). Leads from it carry `reply_policy=human_only`. |

## What was already good and kept

SSRF checks on every redirect hop in the site crawler. Refusal to describe a site it could not read. Thread health checks before qualification. The 100-point rubric shape. Evidence-quote verification in the pipeline qualifier. Heuristic scoring marked as such and capped below high potential.

## Research behind the rules

- Hacker News guidelines forbid generated and AI-edited comments (March 2026).
- X's automation rules forbid unsolicited automated replies.
- Reddit ended self-service API keys in November 2025 (Responsible Builder Policy). API posting needs approval.
- The Reddit 90/10 rule is community practice, not an official rule. The app enforces its own, softer limit of 10 percent.
- FTC endorsement guidance calls for a clear statement of a material connection.
- Bot-detection heuristics (account age, karma, posting rhythm, repeated phrasing) come from vendor and community reports. They are not official, so the app treats them as guidance.

## Not verified

- Keyed search backends (Serper, Brave, Tavily): written from vendor docs, tested with recorded response shapes only.
- Reddit and GitHub posting through APIs: written from docs, tested with fake sessions.
- Reddit's public JSON endpoints and Exa's free endpoint: blocked from the build sandbox, so account reads and comment reads were tested with fake sessions.
- Docker image build and the GitHub Actions run itself: no Docker daemon and no GitHub runner here. Workflow files pass actionlint. The wheel build and clean install ran locally.
- GitHub Actions versions: `checkout` v6, `setup-python` v6 and `upload-artifact` v7 were confirmed. Dependabot keeps the rest current.
- Language models: the pipeline was tested with scripted models. No live model call ran.

## Trade-offs

- The hard banned list is long. It keeps drafts clean and costs a retry or two. Loosen it with `prefs --user-list off` or edit the files.
- Product replies need a linked, readable account by default. That blocks pitching from an unlinked account. `posting set --require-account-health no` turns it off, at your own risk.
- Pitch level 2 states your connection in the reply. It trades some reach for honesty and for fewer removals. Level 0 and 1 remain available.
