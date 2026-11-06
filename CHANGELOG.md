# Changelog

## 3.3.1

Resource audit. Behavior, tools, skills, workflows and outputs are unchanged. Numbers and method are in RESOURCE_AUDIT.md.

### Changed
- SQLite: the storage layer keeps one idle connection per database file (at most 8, released with `DiscoveryStorage.close()`). Each storage call opens its own connection, and SQLite checkpointed and deleted the WAL file every time the last one closed. Write plus read per call went from 1.26 ms to 0.37 ms in a micro benchmark, and the full test suite runs about 17 percent faster.
- New indexes on `discovered_items` (created_at, platform and created_at), `replies` (created_at), `business_profiles` (updated_at), `team_directives` (created_at) and `team_tasks` (status). Newest-first lists no longer scan and sort the whole table. On 20,000 stored threads, 100 list calls went from 3.7 s to 17 ms.
- `LLMClient` reads the config file at most once per client. It read it once per provider probe, which was 904 reads in the test suite and is now 248.
- Team engine: the per-directive lock tables hold weak references. A lock disappears when no thread holds it. Before, every directive left two lock objects behind for the life of the process (220 after 200 directives, now 0).
- `AGENT_REACH_DB_SYNC` (NORMAL, EXTRA or OFF) is an opt-in switch for the SQLite sync mode. The default is unchanged.

### Fixed
- `get_setting` failed with a TypeError for a stored number or boolean, because the `settings.value` column has numeric affinity and returns a number instead of text. It now returns the value. No stored setting used a bare number before, so no existing data is affected.

### Added
- `tests/test_resources.py`: idle connection lifecycle and bound, recreated database file, lock release, one config read per client, query plans use the new indexes, numeric settings.
- `RESOURCE_AUDIT.md`.

## 3.3.0

Prompt and reply audit. Scope: the text the owner posts (Reddit replies and other platforms), the prompts that produce it, the linter that checks it and the examples that teach it. Details are in PROMPT_AUDIT.md.

### Fixed
- The linter missed inflected forms of banned words (unlocked, discovering, illuminating, harnesses, unveiled, utilizes, delved, imagining, remarkably). Single words of 5 or more letters now match their regular forms. Patterns are cached.
- A spaced hyphen or double hyphen used in place of an em dash passed the dash check. It is now an error, and `normalize_text` replaces it with a comma.
- Four approved disclosure phrases ("I'm on the {product} team", "My day job is {product}") did not count as an affiliation. The detector now accepts them.
- The fix prompt let the model swap a banned word for a synonym. It now says to rewrite the sentence.

### Added
- New errors in the reply linter: `contrast_frame` (not just X but Y, it's not X it's Y), `lead_in` (Here's why, The catch:, Pro tip, Let's break this down), `empathy_script` (I understand how frustrating, totally valid), `closing_question` (What do you think?), `greeting_opener` (allowed when the owner's samples open that way).
- New warnings: `repeated_openers`, `stacked_triples`, `mirror_contrast`, `hedge_stack`, `semicolons`, `stiff_register` (no contractions in a long reply), `no_specific_detail`, `product_first_sentence`.
- Wider flattery opener check (solid point, certainly, of course, love this, I'd be happy to).
- About 80 new lexicon entries: sales jargon, scripted sign-offs, filler openers, intensifiers.
- `tests/test_voice_lint.py`.

### Changed
- `community-copywriting` 1.1.0. The prompt now starts with three steps (find the one detail, say what you would say across a table, check what you know), lists the sentence patterns to avoid, drops the fixed 4/20/9 sentence rhythm, makes the limit statement conditional, and asks for a different opening and ending from recent replies.
- `ai-tells.md` gains a section on slop thinking (generic advice, both sides, survey of options, invented specifics, template arc, tidy ending).
- The 12 examples use contractions, differ in opening and ending, and no longer close on the same limit sentence. Two examples were added (rate increase, early payment discount). Every example passes lint with no warnings.
- Disclosure phrases: 26 natural variants. The bias apology is optional.
- `reddit-voice.md`: removed "Short version:" as an opener, added a rule to rotate openers.
- Reply generator prompt: examples are marked as a quality bar, the model must pick one concrete detail, and the pattern list is stated before the output instruction.
- Reasons in `lead-qualification` and `thread-engagement` are one plain sentence with one fact.
- Platform style hints for GitHub, Quora and X are more specific.

## 3.2.0

### Changed
- Roster review. Two positions were removed because they added nothing, and one automatic step replaces them.
  - `compliance` only copied a gate code that the verifier then recomputed. Because drafts are not approved yet, every draft stopped at the approval gate, so the report said "not_approved" for all of them and hid the real blockers. Confirmed by test.
  - `auditor` (the closing task) only had to make one read call, nothing used its findings, and it had no tool to re-read fetched pages in market research. The auditor model inside the verifier (with the planted false claim), the qualifier's second opinion and the editor remain.
  - `inspector` replaces both. It runs by itself with no model and no assistant turn. It runs the posting gates as if the draft were approved and posting were on, flags drafts edited after the editor read them and leads whose quote is not verified. The report shows the result per lead card and in `owner_actions`.
- Plans are shorter: `find_customers` has seven steps instead of eight, `market_research`, `follow_up` and `weekly_review` have one task each. A plan chosen by the model or by rules no longer gets an automatic audit task.
- The roster is now analyst, scout, qualifier, writer, editor, strategist, researcher and follow_up, plus the automatic inspector.

### Removed
- Roles `compliance` and `auditor`, their output contracts and their verifier checks, and the `team_check_gates` toolbox tool (nothing held it).

### Fixed
- `WORKFLOW_AND_ARCHITECTURE_EXPLAINED.md` listed the 3.0 roster. It lists the current one.
- 3.0 listed `team_check_gates` returning `not_approved` as expected for drafts. It no longer exists.

## 3.1.0

### Added
- Three specialists: `researcher` (competitors and market from fetched pages), `editor` (second read of every draft, one revision round) and `follow_up` (re-reads threads where the owner replied). Seven built-in plans, up from four.
- Honest empty results. `data.nothing_found` is valid with a reason and proof of work. The CEO widens an empty search once, skips the steps that have nothing to work on and reports what was tried.
- Planning for requests that fit no plan (server model or keyword rules), readiness notes on every new directive, and an owner question when the request names no site and no product.
- `ceo_next_step` (one next action for the host assistant), `ceo_cancel_directive` and `ceo_memory`. Dashboard routes for the same, and CLI commands `team next|cancel|memory`.
- Company memory: owner preferences and lessons, shown in work orders, never usable as evidence.
- Report v2: headline, trust level, lead cards, what was tried, quality numbers, progress, and which channel confirmed each checkpoint.
- Recovery: stalled tasks return to the queue after 20 minutes, rate limits retry without using an attempt, a tool budget per directive, duplicate requests are not planned twice, evidence ids stay unique under parallel calls.
- Optional independent auditor provider (`AGENT_REACH_AUDITOR_PROVIDER`, `AGENT_REACH_AUDITOR_MODEL`).
- 35 tests (85 in total) and `docs/company.md`.

### Changed
- The verifier rejects a claim whose words the cited evidence does not hold, a summary that says more than the evidence, a result with no claims and no tool call, claims that cite only failed calls, and spelled numbers that no source states. Two of these gaps were confirmed by test before the fix: an unrelated claim next to a real quote passed, and a summary with no tool call passed.
- The auditor model receives a planted false claim in every batch. An auditor that passes it is marked unreliable and the trust level drops.
- Workers run the deterministic checks before handing in a result and fix issues without using an attempt.
- Checkpoint answers from the dashboard or the CLI are recorded as given by the owner directly.

## 3.0.0

### Added
- The company layer (`agent_reach/team/`). The owner talks to a CEO. The CEO plans directives as tasks, hands them to seven built-in specialists (analyst, scout, qualifier, writer, compliance, strategist, auditor), launches tools for them, and reports only verified work.
- 13 MCP tools for the CEO: `ceo_open_directive`, `ceo_status`, `ceo_run`, `ceo_next_work_order`, `ceo_call_tool`, `ceo_submit_result`, `ceo_resolve_checkpoint`, `ceo_create_task`, `ceo_update_task`, `ceo_hire_specialist`, `ceo_create_playbook`, `ceo_list_team`, `ceo_report`.
- An evidence ledger and a verifier. Every output is checked for evidence ids, verbatim quotes, numbers, links, lead quotes, linter results and gate codes. A second model audits claims and can only object to a real claim. Leads rated high potential get a second opinion.
- Role based tool permissions. Restricted tools (publish, approve, confirm, settings, accounts, community rules) never reach a specialist.
- Two run modes with the same checks: server model (specialists run on the server's key) and host assistant (the host plays the CEO and the specialists through work orders).
- Company mode for the MCP server (default). The host sees the CEO tools and the owner tools. `--mode full` shows every tool.
- `agent-reach team ...` commands and `/api/team/*` endpoints for a chat front end.
- The `company-operations` skill and its verification rules.
- 50 tests, a Dockerfile, `.cursor/mcp.json`, `AUDIT.md`.

### Changed
- The MCP server no longer registers prompts (`find_customers`, `draft_reply`, `weekly_review`). Everything is a tool.
- One version number (3.0.0) in the package, the API and the user agent. They were 2.2.0, 1.6.0, 2.1.0, 2.1.0 and 2.2.
- `agent-reach` now routes only `mcp`, `team`, `discovery`, `dashboard`, `doctor` and `version`.
- Exa search lives in `discovery/search_backends.py` and uses `requests`.
- `config.py` and `utils/paths.py` are in English and no longer depend on the removed runtime state module.
- Docs and CI describe what exists.

### Fixed
- `reach_harvest_threads` returned a new item id for a thread that was already stored. `reach_save_lead` then found no stored thread, could not verify the evidence quote and the lead stayed unverified. The harvest now returns the stored row, and `reach_save_lead` falls back to the URL when the id is unknown.
- `ensure_dashboard_running` checked for a module that always exists. It now checks for `fastapi` and `uvicorn` and says how to install them.
- Messages that named commands that do not exist (`llm-check`, `search-check`).
- The dashboard `POST /api/settings` stored Reddit and GitHub credentials and the model key in SQLite. Credentials are now dropped, the model key goes to the owner-only config file, and old rows are scrubbed at start.

### Removed
- About 6,900 lines of the old general web access tool: browser and CDP control, session handling, the OpenCLI and Cloak backends, platform channels (Twitter, Reddit, YouTube, GitHub, web readers), transcription, onboarding and the installer. None of it served customer discovery.
- The `yt-dlp` pin and the `loguru` dependency.
- Keywords and metadata that described the old tool.
