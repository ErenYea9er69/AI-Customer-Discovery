# Changelog

## 2.2.0

Added
- Shared skill pack in `skills/` (7 skills, 28 reference files) used by both the pipeline and the MCP server. Validator, manifest and generated tool reference.
- Linked accounts: handle only, public age and karma, stage and pitch level, voice import from your own comments.
- Voice cloning and the reply linter: two banned lists, dash, markdown, link, emoji, length, affiliation and repeat checks, voice score, three-attempt repair loop.
- Thread comment reading and reply targets for Reddit, Hacker News and GitHub.
- Community rules record and thirteen ordered posting gates, including account health, mention ratio, one reply per thread and jittered gaps.
- Search backend chain: Serper, Brave, Tavily, Exa, DuckDuckGo.
- Untrusted text envelope and injection flags.
- MCP: compat layer for SDK 1.x and 2.x, 31 annotated tools, skill resources and templates, three prompts, reply context tool that returns the pipeline's own prompt.
- CLI: `discovery` now covers profile, plan, search, leads, reply, lint, approve, post, confirm, voice, prefs, accounts, rules, posting, skills, check, export and analytics.
- CI (lint, types, skills, 6-way test matrix, wheel install, Docker handshake, actionlint), release and weekly canary workflows, Dependabot, Dockerfile.
- 59 tests.

Changed
- `mcp>=1.27,<3`, and `pydantic` and `beautifulsoup4` declared.
- Model selection uses candidate lists with fallback and two tiers.
- Qualifier, planner, business engine and reply generator use the skill pack prompts.
- Product replies carry a natural first-person affiliation sentence instead of a footer.
- `reach_save_lead` takes sub-scores and computes the class on the server. The `score`, `classification`, `buying_intent` (string) and `urgency` (string) arguments were replaced by numeric sub-scores.
- Reddit password and tokens are no longer stored. The allow-list default is empty.
- Hacker News produces no drafts.

Fixed
- MCP server import failure on SDK 2.x.
- Second reply save for the same lead.
- Export paths outside the working folder, home or temp are refused.

Removed
- The fixed `Disclosure: I am affiliated with X.` footer.
