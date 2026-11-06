import pytest
from conftest import PRODUCT_AWARE, VALUE_FIRST, FakeLLM, make_lead

from agent_reach.discovery.models import ReplyTarget
from agent_reach.discovery.reply_generator import (
    ReplyGenerationError,
    ReplyGenerator,
    ReplyLintError,
)

BAD = {"value_first": "Great question! Acme can help — you should leverage a spreadsheet.", "product_aware": "Use Acme."}
GOOD = {"value_first": VALUE_FIRST, "product_aware": PRODUCT_AWARE}


def test_failed_lint_triggers_retry_with_issues(lead, profile):
    llm = FakeLLM(BAD, GOOD)
    reply = ReplyGenerator(llm).generate_replies(
        lead, profile, target=ReplyTarget(target_kind="comment", target_comment_id="c1", target_author="bob", target_text="any tool?")
    )
    assert len(llm.calls) == 2 and not reply.needs_human_edit
    assert "lint_issues" in llm.calls[1][0] and "dash" in llm.calls[1][0]
    assert "Skill: community-copywriting" in llm.calls[0][1] and "Skill: thread-engagement" in llm.calls[0][1]
    assert reply.target_kind == "comment" and reply.target_comment_id == "c1"
    assert profile.name in reply.affiliation_disclosure


def test_persistent_failure_is_flagged_not_hidden(lead, profile):
    reply = ReplyGenerator(FakeLLM(BAD)).generate_replies(lead, profile)
    assert reply.needs_human_edit and reply.lint["value_first"]["passed"] is False


def test_account_health_caps_pitch_level(lead, profile):
    reply = ReplyGenerator(FakeLLM(GOOD)).generate_replies(lead, profile, max_pitch_level=1)
    assert reply.product_aware == "" and reply.pitch_level == 1


def test_hacker_news_never_drafts(profile):
    with pytest.raises(ReplyGenerationError):
        ReplyGenerator(FakeLLM(GOOD)).generate_replies(make_lead(platform="hackernews"), profile)


def test_prompt_contains_untrusted_wrapper_and_voice(lead, profile):
    from agent_reach.discovery import voice
    from agent_reach.discovery.models import ReplyPreferences

    samples = ["honestly i just use a spreadsheet and a calendar reminder, works fine till you hit around twenty clients and then it falls apart"] * 3
    prefs = ReplyPreferences(voice_samples=samples, voice_card=voice.analyze_samples(samples), banned_words=["synergy"])
    ctx = ReplyGenerator(FakeLLM(GOOD)).build_prompts(lead, profile, prefs=prefs)
    assert "<untrusted_thread" in ctx["prompt"] and "synergy" in ctx["prompt"] and "spreadsheet and a calendar" in ctx["prompt"]
    assert ctx["want_product"] is True and len(ctx["phrases"]) == 4


def test_approve_gate_keeps_reply_unchanged_on_failure(lead, profile):
    gen = ReplyGenerator(FakeLLM(GOOD))
    reply = gen.generate_replies(lead, profile)
    with pytest.raises(ReplyLintError):
        gen.approve_reply(reply, edited_text="Great question! use acme", selected_version="custom", profile=profile)
    assert reply.edited_reply is None and reply.status == "draft"
    ok = gen.approve_reply(reply, selected_version="product_aware", profile=profile)
    assert ok.status == "approved" and ok.lint["final"]["passed"]
    forced = gen.approve_reply(reply, edited_text="Great question! use acme", selected_version="custom", profile=profile, force=True)
    assert forced.needs_human_edit


def test_custom_needs_text(lead, profile):
    gen = ReplyGenerator(FakeLLM(GOOD))
    reply = gen.generate_replies(lead, profile)
    with pytest.raises(ValueError):
        gen.approve_reply(reply, selected_version="custom")
