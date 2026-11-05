# -*- coding: utf-8 -*-
"""The company roster and the built-in playbooks.

The CEO is the owner's assistant. It plans, assigns and decides. Specialists do the work,
each with a short list of tools. Nobody posts anything: posting stays with the owner.
"""

from __future__ import annotations

from typing import Dict, List

from agent_reach.team.models import Playbook, PlaybookStep, RoleSpec

# Tools no specialist may hold, however a role is defined. The owner acts through the CEO
# surface (approve, publish, confirm, settings, accounts, community rules).
RESTRICTED_TOOLS = frozenset({
    "reach_approve_reply",
    "reach_publish_reply",
    "reach_confirm_posted",
    "reach_update_settings",
    "reach_link_account",
    "reach_unlink_account",
    "reach_set_community_rules",
    "reach_control_dashboard",
    "reach_export_results",
    "reach_run_autonomous_batch",
})

# Tools the host AI does not need to see when it plays the CEO. Specialists call them through the team.
WORKER_ONLY_TOOLS = frozenset({
    "reach_fetch_site_text",
    "reach_analyze_business",
    "reach_get_or_create_profile",
    "reach_plan_queries",
    "reach_harvest_threads",
    "reach_read_thread",
    "reach_save_lead",
    "reach_set_lead_status",
    "reach_get_reply_context",
    "reach_lint_reply",
    "reach_save_reply",
    "reach_import_voice_from_account",
    "reach_get_insights",
    "reach_run_autonomous_batch",
    "reach_control_dashboard",
})

BUILTIN_ROLES: Dict[str, RoleSpec] = {
    "analyst": RoleSpec(
        name="analyst",
        title="Business Analyst",
        charter=(
            "You build the business profile. You work only from the owner's request text and from pages "
            "read with your tools. State facts the sources say. Label every guess as a guess. "
            "Never invent features, prices, customers or numbers."
        ),
        skills=["business-intelligence"],
        tools=["reach_fetch_site_text", "reach_get_or_create_profile", "reach_get_skill"],
        check="profile",
    ),
    "scout": RoleSpec(
        name="scout",
        title="Community Scout",
        charter=(
            "You plan searches and harvest open threads where people describe the problem the product solves. "
            "You search in the customer's words and never put the product name in a query. "
            "You report only threads your harvest returned."
        ),
        skills=["community-search"],
        tools=["team_read_profile", "reach_plan_queries", "reach_harvest_threads", "reach_get_skill"],
        tier="fast",
        check="scout",
    ),
    "qualifier": RoleSpec(
        name="qualifier",
        title="Lead Qualifier",
        charter=(
            "You score harvested threads with the five-part rubric and save only real leads. "
            "Every lead needs an evidence quote copied word for word from the thread. "
            "Most threads are not leads. Reject the rest."
        ),
        skills=["lead-qualification"],
        tools=[
            "team_read_profile", "team_read_items", "reach_read_thread", "reach_save_lead",
            "reach_list_leads", "reach_set_lead_status", "reach_get_skill",
        ],
        check="qualifier",
    ),
    "writer": RoleSpec(
        name="writer",
        title="Reply Writer",
        charter=(
            "You draft replies in the owner's voice for saved leads. You write only from product facts in the "
            "profile and from the thread. You never invent customers, results, numbers or personal stories. "
            "Every draft must pass the linter before you save it."
        ),
        skills=["community-copywriting", "thread-engagement"],
        tools=[
            "team_read_profile", "reach_list_leads", "reach_get_reply_context", "reach_lint_reply",
            "reach_save_reply", "reach_import_voice_from_account", "reach_set_voice_samples", "reach_get_skill",
        ],
        check="writer",
    ),
    "strategist": RoleSpec(
        name="strategist",
        title="Growth Strategist",
        charter=(
            "You review results: which communities gave good leads, the reply mix, account health and what the "
            "owner should do next. Every number you state comes from a tool result."
        ),
        skills=["customer-discovery"],
        tools=["team_read_profile", "reach_list_leads", "reach_get_insights", "reach_account_health", "reach_get_skill"],
        tier="fast",
    ),
    "researcher": RoleSpec(
        name="researcher",
        title="Market Researcher",
        charter=(
            "You study competitors and the market from pages you fetch with your tools. Every fact you report "
            "carries a quote copied from a fetched page and the page's URL. You never fill a gap from memory. "
            "When a page says nothing about a point, you write that the source does not say."
        ),
        skills=["business-intelligence"],
        tools=["team_read_profile", "reach_fetch_site_text", "reach_get_skill"],
        check="researcher",
    ),
    "editor": RoleSpec(
        name="editor",
        title="Reply Editor",
        charter=(
            "You are the second reader of every draft. You read each draft against the thread and the product facts, "
            "run the linter yourself, and give one verdict per draft: approve, revise or reject. "
            "Revise and reject need concrete reasons: a claim the thread or profile does not support, a pitch that "
            "ignores the question, a tone that does not match the owner's voice. You never rewrite the draft yourself."
        ),
        skills=["community-copywriting", "platform-safety"],
        tools=["team_read_profile", "team_read_replies", "team_read_items", "reach_list_leads", "reach_lint_reply", "reach_get_skill"],
        tier="smart",
        check="editor",
    ),
    "follow_up": RoleSpec(
        name="follow_up",
        title="Follow-up Tracker",
        charter=(
            "You watch threads where the owner already replied. You re-read each thread, report whether it is "
            "still open and whether new comments arrived, and move a lead to replied or closed when the thread shows it. "
            "You report only what the thread read in this task shows."
        ),
        skills=["thread-engagement"],
        tools=["team_read_replies", "reach_list_leads", "reach_read_thread", "reach_set_lead_status", "reach_get_skill"],
        tier="fast",
        check="follow_up",
    ),
    "inspector": RoleSpec(
        name="inspector",
        title="Posting Inspector",
        charter=(
            "Runs by itself, without a model. For every draft of the request it asks the posting gates what they "
            "would say if you approved the draft today, and it checks that the draft was not edited after the editor "
            "read it and that its lead still has a verified quote."
        ),
        tools=[],
        tier="fast",
        auto=True,
    ),
}


def _step(key, role, title, instruction, deps=None, acceptance=None, kind="work", checkpoint="", skip_when_empty=False) -> PlaybookStep:
    return PlaybookStep(
        key=key, role=role, title=title, instruction=instruction, depends_on=list(deps or []),
        acceptance=list(acceptance or []), kind=kind, checkpoint=checkpoint, skip_when_empty=skip_when_empty,
    )


NOTHING_FOUND_RULE = (
    " If your honest result is that nothing qualifies, set data.nothing_found to true and data.reason to one sentence. "
    "An honest empty result passes. An invented one does not."
)


BUILTIN_PLAYBOOKS: Dict[str, Playbook] = {
    "find_customers": Playbook(
        name="find_customers",
        description="Profile the business, search communities, qualify leads, draft replies, have the editor read them, inspect the posting gates.",
        steps=[
            _step(
                "profile", "analyst", "Build the business profile",
                "Read the owner's site (or use the description in the request) and save the profile. "
                "Fill problems_solved, pain_vocabulary (8 to 15 phrases customers type, no product names), icp and not_for.",
                acceptance=[
                    "A profile is saved with at least one problem solved.",
                    "Features and pricing appear in the source text.",
                ],
            ),
            _step(
                "confirm_profile", "owner", "Owner confirms the profile",
                "Show the saved profile to the owner and wait for approval.",
                deps=["profile"], kind="checkpoint", checkpoint="confirm_profile",
            ),
            _step(
                "search", "scout", "Plan queries and harvest threads",
                "Plan queries by buyer stage, then harvest open threads. Report only harvested threads." + NOTHING_FOUND_RULE,
                deps=["confirm_profile"],
                acceptance=["At least one harvest call ran.", "Every reported URL came from a harvest result."],
            ),
            _step(
                "qualify", "qualifier", "Qualify threads into leads",
                "Read the harvested threads, score the promising ones and save real leads. Reject weak threads." + NOTHING_FOUND_RULE,
                deps=["search"], skip_when_empty=True,
                acceptance=["Each lead has a verbatim evidence quote.", "No lead is high potential without a verified quote."],
            ),
            _step(
                "write", "writer", "Draft replies for the best leads",
                "Draft value-first and product-aware replies for the top leads. Lint each draft before saving.",
                deps=["qualify"], skip_when_empty=True,
                acceptance=["Every saved draft passed the linter.", "No invented numbers, customers or results."],
            ),
            _step(
                "edit", "editor", "Second read of every draft",
                "Read each new draft against its thread and the profile, lint it, and give a verdict: approve, revise or reject.",
                deps=["write"], skip_when_empty=True,
                acceptance=["Every new draft has a verdict.", "Revise and reject name concrete reasons."],
            ),
            _step(
                "inspect", "inspector", "Inspect the posting gates",
                "Automatic. Ask the posting gates what each draft would get if approved today.",
                deps=["edit"], skip_when_empty=True,
            ),
        ],
    ),
    "draft_replies": Playbook(
        name="draft_replies",
        description="Draft replies for leads that already exist, have the editor read them, then inspect the posting gates.",
        steps=[
            _step(
                "write", "writer", "Draft replies for the best leads",
                "Draft value-first and product-aware replies for the leads named in the request, or for the top saved leads.",
                acceptance=["Every saved draft passed the linter.", "No invented numbers, customers or results."],
            ),
            _step(
                "edit", "editor", "Second read of every draft",
                "Read each new draft against its thread and the profile, lint it, and give a verdict.", deps=["write"],
            ),
            _step(
                "inspect", "inspector", "Inspect the posting gates",
                "Automatic. Ask the posting gates what each draft would get if approved today.", deps=["edit"],
            ),
        ],
    ),
    "review_drafts": Playbook(
        name="review_drafts",
        description="Second read of existing drafts, then an automatic check of the posting gates.",
        steps=[
            _step(
                "edit", "editor", "Second read of every draft",
                "Read every draft that is still a draft against its thread and the profile, lint it, and give a verdict.",
            ),
            _step(
                "inspect", "inspector", "Inspect the posting gates",
                "Automatic. Ask the posting gates what each draft would get if approved today.", deps=["edit"], skip_when_empty=True,
            ),
        ],
    ),
    "market_research": Playbook(
        name="market_research",
        description="Study competitors or the market from fetched pages. Every fact carries a quote.",
        steps=[
            _step(
                "research", "researcher", "Study the market",
                "Fetch the pages the request names, or the competitor pages you can reach from them, and report facts "
                "with a quote and the page URL for each. Say what the pages do not state.",
                acceptance=["Every fact has a quote from a fetched page.", "Every URL was fetched in this task."],
            ),
        ],
    ),
    "follow_up": Playbook(
        name="follow_up",
        description="Re-read threads where the owner replied and report what changed.",
        steps=[
            _step(
                "track", "follow_up", "Check the threads",
                "List the replies that were posted, re-read each thread and report whether it is open and whether new comments came.",
                acceptance=["Every reported thread was read in this task."],
            ),
        ],
    ),
    "weekly_review": Playbook(
        name="weekly_review",
        description="Review leads, reply mix and account health. Every number comes from a tool result.",
        steps=[
            _step(
                "review", "strategist", "Review the week",
                "Read the insights, the leads and the account health. Report which communities worked and what to do next.",
            ),
        ],
    ),
    "setup_voice": Playbook(
        name="setup_voice",
        description="Learn the owner's writing style from their own public comments.",
        steps=[
            _step(
                "voice", "writer", "Learn the owner's voice",
                "Import the owner's own public comments from the linked account, or store the samples the owner gave.",
                acceptance=["The voice card has samples."],
            ),
        ],
    ),
}

INTENTS = (
    "find_customers", "draft_replies", "review_drafts", "weekly_review", "setup_voice",
    "market_research", "follow_up", "status", "custom",
)


def role_names() -> List[str]:
    return sorted(BUILTIN_ROLES)
