# Pipeline workflow: stage contracts

The pipeline runs without a host AI. It calls an external language model through plain HTTP and uses the same skills as the MCP server. Each stage below states what goes in, what comes out, which skill supplies the prompt and which code enforces the rules.

## Model setup

Set one provider key in the environment: `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `GEMINI_API_KEY`, `GROQ_API_KEY` or `DEEPSEEK_API_KEY`. Set `LLM_PROVIDER` to choose when several keys exist. Two tiers exist. The fast tier runs qualification. The smart tier runs profiling, query planning and reply writing. Pin a model with `LLM_MODEL_FAST`, `LLM_MODEL_SMART` or `LLM_MODEL`. Without a pin, the client tries a list of current models and remembers the one that works. Run `agent-reach discovery check llm` to test the key.

## Stages

| Stage | Code | Skill in the system prompt | Output |
| --- | --- | --- | --- |
| Profile | `business_engine.py` | business-intelligence | `BusinessProfile` with facts, inferences, `pain_vocabulary`, `not_for` |
| Plan | `search_planner.py` | community-search | `SearchQuery` list ranked by buyer stage |
| Harvest | `harvester.py`, `search_backends.py` | none (code only) | `DiscoveredItem` with `thread_health` |
| Qualify | `qualifier.py` | lead-qualification | `LeadQualification` with sub-scores and a class |
| Target | `thread_comments.py` | thread-engagement rules in code | `ReplyTarget` (post or comment) |
| Draft | `reply_generator.py` | community-copywriting, thread-engagement | `GeneratedReply` with lint reports |
| Gate | `publisher.py` | platform-safety rules in code | a copy-ready text, or a refusal with a code |

## Contracts

Profile. The input is a website or a description. The crawler reads the home page and up to four key pages, refuses private addresses, and stops at 1.5 MB per page. If it cannot read 200 characters of text, it raises an error and asks for a description, because a model asked to describe an unreadable site invents one. The output must list at least one problem the product solves.

Plan. The planner builds queries from `pain_vocabulary`, `problems_solved`, competitors and outcomes. It keeps at most 2 queries per buyer stage and platform, then fills up to 8 per platform and 24 in total. Switching queries come first. A query never contains the product name. A model adds up to six queries and five subreddits. Owner-chosen communities go first.

Harvest. The backend chain is Serper, Brave, Tavily (when keyed), then Exa, then DuckDuckGo. The first backend with results wins. `agent-reach discovery check search` shows which backends are active. The harvester drops locked, archived, removed, promotional, link-only and duplicate threads and records why in `diagnostics`.

Qualify. A rule pass drops spam, sellers and posts with injection patterns. A model then scores the survivors with the five-part rubric. The code verifies the evidence quote against the stored post, caps every score, adds the total and calls `classify`. Without a model, a keyword pass scores the thread, sets `judged_by` to `heuristic` and cannot reach `high_potential`. Qualification stops after `LLM_QUALIFY_MAX` model calls (default 80) per run.

Target. For `high_potential` leads the pipeline reads the thread's comments. It scores each comment: the author's follow-up question 7, an unanswered tool question 6, an answered question 3.5, plus up to 2 for overlap with the profile's problems. Age over 3 days subtracts 3, depth 3 or more subtracts 2, a link-only comment subtracts 4. The post itself scores 5, and 2 when the thread has an answer already or 80 or more comments. The best target wins. Other leads reply to the post.

Draft. The generator builds the system prompt from two skills and the user prompt from product facts, the owner's voice card and samples, the allowed pitch level, approved affiliation phrases, two good examples and recent replies. It lints each version. A failed version goes back to the model with the exact issues. After three attempts a draft that still fails is saved with `needs_human_edit` set. The account's health caps the pitch level before drafting starts.

Gate. `CommunityPublisher.gate` checks, in order: emergency stop, draft mode, approval, platform policy, lint, recorded community rules, optional allow-list, one reply per thread, account health, mention ratio, daily cap, gap between posts with jitter, and a live check that the thread is open. A refusal returns a code. Manual mode returns the text and a direct link and counts the reply as published only after `confirm`. Automatic mode needs `mode=automatic`, `AGENT_REACH_ALLOW_AUTOPOST=1` and approved API credentials in the environment. Credentials are never written to the database.

## Commands

```
agent-reach discovery profile --url https://example.com
agent-reach discovery accounts link reddit:your_handle
agent-reach discovery voice --from-account reddit:your_handle
agent-reach discovery rules set r/freelance --self-promo thread_only
agent-reach discovery search --max 10 --communities r/freelance,r/smallbusiness
agent-reach discovery reply LEAD_ID --target auto
agent-reach discovery approve REPLY_ID
agent-reach discovery post REPLY_ID
agent-reach discovery confirm REPLY_ID --url https://reddit.com/...
```

## Failure behavior

A failed model call during qualification falls back to rules for that thread. A failed model call during drafting leaves the lead saved without a draft and counts `reply_draft_failed` in the campaign diagnostics. A failed search backend moves to the next one and counts `search_error:NAME`. A campaign that raises an error is marked failed with the error text. Nothing in the pipeline posts without an approved reply and a passing gate.
