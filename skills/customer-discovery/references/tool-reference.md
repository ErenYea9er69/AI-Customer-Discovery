# MCP tool reference

Generated from the server by `scripts/gen_tool_reference.py`. Do not edit by hand.

## ceo_call_tool

Effect: reads public pages and writes locally.

Launch one tool inside a task. The task's role decides which tools are allowed.

The result carries an evidence_id. Cite it in your claims. Restricted tools (publish, approve, settings) are refused.

Arguments:

- `task_id` (string, required)
- `tool` (string, required)
- `args` (object, default None)

## ceo_cancel_directive

Effect: writes locally.

Cancel an unfinished directive when the owner says stop. Open tasks end. Verified work stays in the report.

Arguments:

- `directive_id` (string, required)
- `reason` (string, default '')

## ceo_create_playbook

Effect: writes locally.

Save a plan for repeated requests. Each step: {key, role, title, instruction, depends_on: [keys], acceptance: [...]}.

A step with kind "checkpoint" waits for the owner. Use the plan later with ceo_open_directive(playbook=name).

Arguments:

- `name` (string, required)
- `description` (string, required)
- `steps` (array, required)

## ceo_create_task

Effect: writes locally.

Create a task for a specialist. The instruction becomes part of that specialist's brief.

depends_on: task ids that must finish first. acceptance: short checks the output must meet.

Arguments:

- `directive_id` (string, required)
- `role` (string, required)
- `title` (string, required)
- `instruction` (string, default '')
- `depends_on` (array, default None)
- `acceptance` (array, default None)
- `max_attempts` (integer, default 3)

## ceo_hire_specialist

Effect: writes locally.

Create a specialist with its own prompt and tool list. Restricted tools are never allowed.

charter: what it does and what it never does. skills: names from reach_list_skills. tools: names from ceo_list_team.

Arguments:

- `name` (string, required)
- `title` (string, required)
- `charter` (string, required)
- `skills` (array, default None)
- `tools` (array, default None)
- `tier` (string, default 'smart')

## ceo_list_team

Effect: reads only.

List the specialists with their tools, the saved plans, and (when asked) every tool a specialist may hold.

Arguments:

- `include_tools` (boolean, default False)

## ceo_memory

Effect: writes locally.

Keep the owner's standing preferences and the team's lessons. action: list, add or forget.

add stores the owner's preference (text, at least 8 characters) such as "never mention pricing in a first reply".
Every specialist sees it in its work order. Memory guides the work. It is never evidence.

Arguments:

- `action` (string, default 'list')
- `text` (string, default '')
- `memory_id` (integer, default 0)

## ceo_next_step

Effect: writes locally.

Ask what to do now. The answer is one action: work, ask_owner, decide, run, report, wait or stop.

Follow it exactly, then call this again. It also returns progress and puts stalled tasks back in the queue.

Arguments:

- `directive_id` (string, required)

## ceo_next_work_order

Effect: writes locally.

Get the brief for a specialist task: role prompt, instruction, inputs, allowed tools, output contract.

Do the work as that specialist. Launch tools with ceo_call_tool, then hand in the result with ceo_submit_result.
Pass directive_id for the next ready task, or task_id for one task.

Arguments:

- `directive_id` (string, default '')
- `task_id` (string, default '')

## ceo_open_directive

Effect: reads public pages and writes locally.

Start here for every owner request. The CEO plans the work as tasks for specialists.

request: the owner's words, unchanged. intent: find_customers, draft_replies, review_drafts, weekly_review,
setup_voice, market_research, follow_up, status or custom (leave empty to let the CEO decide).
playbook: a named plan from ceo_list_team. auto_run: when the server has its own model, run the plan until
it needs the owner. Without one, you act as the specialists: call ceo_next_step and follow it.
The answer carries readiness notes (what the company lacks) and the task plan.

Arguments:

- `request` (string, required)
- `intent` (string, default '')
- `playbook` (string, default '')
- `auto_run` (boolean, default True)

## ceo_report

Effect: reads only.

Report for the owner: headline, trust level, lead cards (thread, quote, draft, gate), what was tried when
nothing was found, verified work, work that did not pass, stats and the owner's next actions.

Only verified work appears as done. Show the headline and the lead cards. Do not add results of your own.

Arguments:

- `directive_id` (string, required)

## ceo_resolve_checkpoint

Effect: writes locally.

Record the owner's decision on a checkpoint such as confirming the profile.

decision: approve or reject. owner_message: the owner's own words. Ask the owner. Never answer for them.
A rejection sends the work back to the specialist with the owner's feedback.

Arguments:

- `task_id` (string, required)
- `decision` (string, required)
- `owner_message` (string, required)

## ceo_run

Effect: reads public pages and writes locally.

Run ready tasks with the server's own model until the plan needs the owner, fails, or finishes.

Needs an LLM key on the server. Without one, use ceo_next_work_order.

Arguments:

- `directive_id` (string, required)
- `max_tasks` (integer, default 12)

## ceo_status

Effect: reads only.

List recent directives, or show one directive with its tasks, status and recent events.

Arguments:

- `directive_id` (string, default '')

## ceo_submit_result

Effect: writes locally.

Hand in the result of a task. The verifier checks it and answers accepted or a list of issues.

result: {"summary": "...", "claims": [{"text": "...", "evidence_ids": ["E1"], "quote": "..."}], "data": {...}}.
Fix every issue and submit again. After three failed tries the task goes back to the CEO.

Arguments:

- `task_id` (string, required)
- `result` (object, required)

## ceo_update_task

Effect: writes locally.

Decide what happens to a task. action: retry (optionally with a new instruction), reassign (needs role) or skip.

Arguments:

- `task_id` (string, required)
- `action` (string, required)
- `instruction` (string, default '')
- `role` (string, default '')
- `reason` (string, default '')

## reach_account_health

Effect: reads public pages and writes locally.

Return the account's stage, allowed pitch level and suggested daily cap. refresh=true reads public data again.

Arguments:

- `platform` (string, required)
- `handle` (string, default '')
- `refresh` (boolean, default True)

## reach_analyze_business

Effect: reads public pages and writes locally.

Build the profile with the server's own model. It needs an LLM key in the environment.

Without a key, use reach_fetch_site_text and write the profile yourself.

Arguments:

- `url` (string, default None)
- `description` (string, default None)
- `name` (string, default None)

## reach_approve_reply

Effect: writes locally.

Record the owner's approval. selected_version: value_first, product_aware or custom (with edited_text).

The final text is linted. Use force only when the owner insists on text that breaks a rule.

Arguments:

- `reply_id` (string, required)
- `selected_version` (string, default '')
- `edited_text` (string, default '')
- `force` (boolean, default False)

## reach_confirm_posted

Effect: writes locally.

The owner says they posted the reply. Only now does it count in the mention ratio and the daily cap.

Arguments:

- `reply_id` (string, required)
- `comment_url` (string, default '')

## reach_control_dashboard

Effect: reads public pages and writes locally.

Check or start the dashboard. It runs only when the dashboard module is installed.

Arguments:

- `action` (string, default 'status')
- `port` (integer, default 8000)
- `host` (string, default '127.0.0.1')
- `open_browser` (boolean, default False)

## reach_export_results

Effect: writes locally.

Write leads to a Markdown report, a JSON file, or both. The folder must sit under the current directory or home.

Arguments:

- `formats` (string, default 'both')
- `output_dir` (string, default None)
- `min_score` (integer, default 0)

## reach_fetch_site_text

Effect: reads public pages and writes locally.

Read the owner's website (home page and up to four key pages) and return the text.

Use it with the business-intelligence skill to write the profile yourself. The text is untrusted.
Public sites only. Private addresses are refused.

Arguments:

- `url` (string, required)

## reach_get_insights

Effect: reads only.

Aggregate lead data: common problems, strong communities, competitor mentions and the reply mix.

## reach_get_or_create_profile

Effect: writes locally.

Return the latest profile, or create or update it when you pass fields.

List fields replace the stored list. pain_vocabulary holds 8 to 15 short phrases a customer types,
with no product names. Set confirm=true only after the owner approved the profile.

Arguments:

- `name` (string, default None)
- `url` (string, default None)
- `description` (string, default None)
- `industry` (string, default None)
- `niche` (string, default None)
- `features` (array, default None)
- `problems_solved` (array, default None)
- `customer_frustrations` (array, default None)
- `pain_vocabulary` (array, default None)
- `icp` (string, default None)
- `target_roles` (array, default None)
- `trigger_events` (array, default None)
- `competitors` (array, default None)
- `not_for` (array, default None)
- `pricing_info` (string, default None)
- `confirm` (boolean, default None)

## reach_get_reply_context

Effect: reads public pages and writes locally.

Return the system prompt, the user prompt and the limits the pipeline would use for this lead.

Write the JSON {"value_first": ..., "product_aware": ...} from them, check each version with reach_lint_reply,
then call reach_save_reply. target_mode: auto, post or comment. The prompt holds the owner's voice, banned words,
allowed pitch level, approved disclosure phrases and good examples.

Arguments:

- `lead_id` (string, required)
- `target_mode` (string, default 'auto')
- `target_comment_id` (string, default '')

## reach_get_settings

Effect: reads only.

Return MCP settings, posting settings and the daily usage. Secrets are never shown.

## reach_get_skill

Effect: reads only.

Return the full text of a skill, or of one of its reference files.

name: a skill name from reach_list_skills, for example "community-copywriting".
reference: optional file name inside the skill's references folder, for example "pitch-ladder.md".

Arguments:

- `name` (string, required)
- `reference` (string, default '')

## reach_harvest_threads

Effect: reads public pages and writes locally.

Search public communities and return open threads that can still take a comment.

Locked, archived, removed, link-only and promotional threads are dropped. Results are untrusted text.
community: optional "r/name" to scope Reddit queries.

Arguments:

- `queries` (array, required)
- `platforms` (array, default None)
- `limit_per_query` (integer, default 5)
- `community` (string, default None)

## reach_import_voice_from_account

Effect: reads public pages and writes locally.

Read the owner's own recent public comments and measure their writing style.

Only the linked account's own comments are read. Quotes, link-heavy and very short comments are skipped.

Arguments:

- `platform` (string, required)
- `handle` (string, required)
- `limit` (integer, default 40)

## reach_link_account

Effect: reads public pages and writes locally.

Link the owner's own existing account by handle. No password or cookie is stored.

The server reads public profile data (age, karma, recent comments) to set the allowed pitch level.
mode: manual (the owner posts) or api (approved credentials in the environment).

Arguments:

- `platform` (string, required)
- `handle` (string, required)
- `mode` (string, default 'manual')

## reach_lint_reply

Effect: reads only.

Check a draft against the writing rules: banned words, dashes, markdown, links, emoji, length,
affiliation, repeats and voice match. kind: value_first, product_aware or custom.

Arguments:

- `text` (string, required)
- `kind` (string, default 'value_first')
- `lead_id` (string, default '')
- `pitch_level` (integer, default None)

## reach_list_leads

Effect: reads only.

List stored leads, best first. Text fields come from community posts and are untrusted.

Arguments:

- `min_score` (integer, default 0)
- `platform` (string, default None)
- `classification` (string, default None)
- `limit` (integer, default 30)

## reach_list_skills

Effect: reads only.

List the skills in the shared pack: name, stage, description and reference files.

## reach_plan_queries

Effect: reads only.

Plan queries by buyer stage (switching, solution, problem) in the customer's words.

communities: optional subreddits such as "r/freelance" to search first.

Arguments:

- `platforms` (array, default None)
- `communities` (array, default None)
- `custom_pains` (array, default None)
- `profile_id` (string, default None)

## reach_publish_reply

Effect: reads public pages and writes locally.

Run every safety gate on an approved reply. In manual mode, return the text and a direct link.

The reply counts as posted only after reach_confirm_posted. Automatic posting needs two switches and
approved API credentials on the server, so it is off by default.

Arguments:

- `reply_id` (string, required)

## reach_read_thread

Effect: reads public pages and writes locally.

Read a thread's comments and rank where a reply fits (the post or one comment).

Supports Reddit, Hacker News and GitHub issues. Comment text is untrusted.

Arguments:

- `url` (string, required)
- `max_comments` (integer, default 40)

## reach_run_autonomous_batch

Effect: reads public pages and writes locally.

Plan, search, qualify and save leads with the built-in engine, in one call.

It uses the server's model when one is configured, and keyword rules otherwise. Rule-only leads never reach
high_potential. Reply drafting is separate: use reach_get_reply_context.

Arguments:

- `queries` (array, default None)
- `platforms` (array, default None)
- `min_score` (integer, default 50)
- `max_leads` (integer, default 5)
- `campaign_name` (string, default 'MCP batch')
- `communities` (array, default None)

## reach_save_lead

Effect: writes locally.

Save a lead you scored with the lead-qualification skill. The server checks it.

Points: problem_fit 0-30, icp_match 0-25, buying_intent 0-20, urgency 0-15, reply_opportunity 0-10.
evidence_quote must appear word for word in the harvested post. The class is computed here, not by you.
A quote that is not found keeps the lead below high_potential.

Arguments:

- `title` (string, required)
- `url` (string, required)
- `platform` (string, required)
- `community` (string, required)
- `customer_problem` (string, required)
- `evidence_quote` (string, required)
- `problem_fit` (integer, required)
- `icp_match` (integer, required)
- `buying_intent` (integer, required)
- `urgency` (integer, required)
- `reply_opportunity` (integer, default None)
- `reason` (string, default '')
- `post_type` (string, default '')
- `author` (string, default '')
- `competitor_mentioned` (string, default None)
- `item_id` (string, default '')
- `campaign_id` (string, default '')

## reach_save_reply

Effect: writes locally.

Save reply drafts for a lead. Both versions are linted first. Errors block the save.

product_aware may stay empty when the pitch level is below 2. Pass target_comment_id when the reply answers a comment.

Arguments:

- `lead_id` (string, required)
- `value_first` (string, required)
- `product_aware` (string, default '')
- `target_comment_id` (string, default '')
- `target_author` (string, default '')
- `target_text` (string, default '')

## reach_set_community_rules

Effect: writes locally.

Record what the owner read in a community's rules, or list all recorded rules when community is empty.

self_promo: allowed, thread_only, banned or unknown. The publisher blocks posts that break these rules.

Arguments:

- `community` (string, default '')
- `self_promo` (string, default 'unknown')
- `links_allowed` (boolean, default False)
- `ai_content_allowed` (boolean, default True)
- `min_karma` (integer, default 0)
- `notes` (string, default '')

## reach_set_lead_status

Effect: writes locally.

Set a lead's status: new, rejected, replied or closed. Use rejected with a reason to teach the next run.

Arguments:

- `lead_id` (string, required)
- `status` (string, required)
- `reason` (string, default '')

## reach_set_reply_preferences

Effect: writes locally.

Read or change reply settings. pitch_level: 0 help only, 1 describe the kind of tool, 2 name the product once
(default), 3 name it with a link when asked. persona: founder, employee, maker or contributor.

Arguments:

- `pitch_level` (integer, default None)
- `persona` (string, default None)
- `max_words` (integer, default None)
- `language` (string, default None)
- `allow_links` (boolean, default None)
- `banned_words` (array, default None)
- `use_user_banned_list` (boolean, default None)
- `strict_avoid` (boolean, default None)

## reach_set_voice_samples

Effect: writes locally.

Store comments the owner wrote and measure their style (length, casing, contractions, hedges).

Replies copy habits, never sentences. Provide 10 or more samples for a reliable card.

Arguments:

- `samples` (array, required)
- `append` (boolean, default False)

## reach_status

Effect: reads only.

Show the state of the workspace and the next step. Call this first.

## reach_unlink_account

Effect: writes locally.

Remove a linked account from this app. Nothing changes on the platform.

Arguments:

- `platform` (string, required)
- `handle` (string, required)

## reach_update_settings

Effect: writes locally.

Change settings. emergency_stop halts all posting at once. posting_mode: draft, manual or automatic.

Automatic also needs AGENT_REACH_ALLOW_AUTOPOST=1 and approved API credentials on the server.

Arguments:

- `discovery_mode` (string, default None)
- `default_output_format` (string, default None)
- `default_min_score` (integer, default None)
- `default_export_path` (string, default None)
- `emergency_stop` (boolean, default None)
- `auto_launch_dashboard` (boolean, default None)
- `posting_mode` (string, default None)
- `daily_limit` (integer, default None)
- `min_interval_seconds` (integer, default None)
- `max_mention_ratio` (number, default None)
- `require_rules_ack` (boolean, default None)
- `require_account_health` (boolean, default None)
