import json

import pytest
from conftest import PRODUCT_AWARE, VALUE_FIRST, FakeLLM

from agent_reach.discovery import cli, thread_comments
from agent_reach.discovery.orchestrator import DiscoveryOrchestrator


@pytest.fixture
def orch(storage, profile, lead, now, monkeypatch):
    storage.save_business_profile(profile)
    storage.save_lead(lead)
    o = DiscoveryOrchestrator(storage)
    o.reply_generator.llm = FakeLLM({"value_first": VALUE_FIRST, "product_aware": PRODUCT_AWARE})
    monkeypatch.setattr(thread_comments, "fetch_comments", lambda url, *a, **k: (
        {"id": "abc", "author": "op", "title": "t", "selftext": "s", "num_comments": 2},
        [{"id": "c1", "author": "bob", "body": "Any tool you would recommend for chasing late invoices?", "score": 2,
          "depth": 0, "created_utc": now - 3600, "reply_count": 0}], []))
    return o


def test_draft_picks_comment_target_and_approves(orch, lead):
    reply = orch.draft_for_lead(lead)
    assert reply.target_comment_id == "c1" and not reply.needs_human_edit
    assert orch.approve_reply(reply.id, selected_version="product_aware").status == "approved"


def test_voice_import_and_prefs(orch):
    prefs = orch.set_voice_samples(["honestly i just use a spreadsheet and a calendar reminder, works fine till you hit around twenty clients and then it falls apart"])
    assert prefs.voice_card["n_samples"] == 1
    again = orch.set_voice_samples(["second comment that is long enough to count as a sample for this test of appending behavior"], append=True)
    assert len(again.voice_samples) == 2


def test_hn_lead_cannot_draft(orch):
    from conftest import make_lead

    from agent_reach.discovery.reply_generator import ReplyGenerationError

    with pytest.raises(ReplyGenerationError):
        orch.draft_for_lead(make_lead(platform="hackernews"))


def run(args, capsys):
    code = cli.cmd_discovery(args)
    out = capsys.readouterr().out
    return code, json.loads(out) if out.strip().startswith(("{", "[")) else out


def test_cli_prefs_rules_lint_skills(storage, capsys):
    code, data = run(["prefs", "--pitch-level", "1", "--ban", "synergy"], capsys)
    assert code == 0 and data["pitch_level"] == 1 and data["banned_words"] == ["synergy"]
    code, data = run(["rules", "set", "r/freelance", "--self-promo", "allowed"], capsys)
    assert code == 0 and data["self_promo"] == "allowed"
    code, data = run(["lint", "--text", "Great question — try this."], capsys)
    assert code == 0 and data["passed"] is False
    code, data = run(["skills", "list"], capsys)
    assert code == 0 and len(data) >= 7
    code, data = run(["accounts", "link", "tiktok:x"], capsys)
    assert code == 1 and "Unsupported" in data["error"]
    code, data = run(["bogus"], capsys)
    assert code == 1 and "commands" in data


def test_cli_posting_never_prints_secrets(storage, capsys):
    code, data = run(["posting", "set", "--daily-limit", "3"], capsys)
    assert code == 0 and data["daily_limit"] == 3 and "reddit_password" not in data
    code, data = run(["posting", "stop"], capsys)
    assert data["emergency_stop"] is True
