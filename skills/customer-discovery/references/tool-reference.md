# MCP tool reference

Generated from the server by `scripts/gen_tool_reference.py`. Do not edit by hand.

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
