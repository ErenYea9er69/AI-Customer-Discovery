import pytest
from conftest import PRODUCT_AWARE, VALUE_FIRST

from agent_reach.discovery.accounts import AccountService
from agent_reach.discovery.models import CommunityRule, GeneratedReply, PostingSettings
from agent_reach.discovery.publisher import CommunityPublisher

SETTINGS = PostingSettings(min_interval_seconds=0)


@pytest.fixture
def pub(storage, profile, lead):
    storage.save_lead(lead)
    return CommunityPublisher(storage, profile=profile)


def reply(kind="value_first", lead_id="x", **kw):
    return GeneratedReply(lead_id=lead_id, value_first=VALUE_FIRST, product_aware=PRODUCT_AWARE, status="approved",
                          selected_version=kind, platform="reddit", pitch_level=2, **kw)


def link_account(storage, **snap):
    svc = AccountService(storage)
    svc.link("reddit", "owner_acct")
    acc = svc.get("reddit")
    acc.snapshot = {"supported": True, "age_days": 200, "comment_karma": 650, "recent_comment_count": 100,
                    "recent_mention_ratio": 0.0, **snap}
    svc._replace(acc)


def code(pub, r, lead, settings=SETTINGS):
    return pub.gate(r, lead, settings)[0]


def test_rules_must_be_recorded_first(pub, lead):
    assert code(pub, reply(), lead) == "rules_not_read"


def test_rule_gates(pub, storage, lead):
    storage.save_community_rule(CommunityRule(community="r/freelance", self_promo="allowed"))
    link_account(storage)
    assert code(pub, reply(), lead) == "ok"
    assert code(pub, reply("product_aware"), lead) == "ok"
    storage.save_community_rule(CommunityRule(community="r/freelance", self_promo="banned"))
    assert code(pub, reply("product_aware"), lead) == "rules_no_promo"
    assert code(pub, reply(), lead) == "ok"
    storage.save_community_rule(CommunityRule(community="r/freelance", ai_content_allowed=False))
    assert code(pub, reply(), lead) == "rules_no_ai"


def test_account_gates(pub, storage, lead):
    storage.save_community_rule(CommunityRule(community="r/freelance", self_promo="allowed"))
    assert code(pub, reply("product_aware"), lead) == "account_unknown"
    link_account(storage, age_days=5, comment_karma=3)
    assert code(pub, reply("product_aware"), lead) == "account_health"
    link_account(storage, recent_mention_ratio=0.2)
    assert code(pub, reply("product_aware"), lead) == "mention_ratio"


def test_lint_and_basic_gates(pub, storage, lead):
    storage.save_community_rule(CommunityRule(community="r/freelance", self_promo="allowed"))
    bad = reply()
    bad.edited_reply = "Great question — try this."
    assert code(pub, bad, lead) == "lint"
    assert code(pub, reply(), lead, PostingSettings(emergency_stop=True)) == "emergency_stop"
    assert code(pub, reply(), lead, PostingSettings(mode="draft")) == "draft_mode"
    draft = reply()
    draft.status = "draft"
    assert code(pub, draft, lead) == "not_approved"
    assert pub.gate(reply(), lead.model_copy(update={"platform": "hackernews"}), SETTINGS)[0] == "platform_policy"


def test_manual_flow_and_one_reply_per_thread(pub, storage, lead):
    storage.save_community_rule(CommunityRule(community="r/freelance", self_promo="allowed"))
    link_account(storage)
    r = reply("product_aware", target_kind="comment", target_comment_id="c1")
    out = pub.publish_or_copy(r, lead, SETTINGS)
    assert out["success"] and out["target_url"].endswith("/abc/_/c1/") and out["kind"] == "product_aware"
    assert r.status == "pending_manual_post"
    assert pub.confirm_manual_post(r, lead, "https://reddit.com/c")["success"]
    assert storage.recent_published_kinds("reddit") == ["product_aware"]
    assert code(pub, reply(), lead) == "thread_used"


def test_confirm_requires_pending(pub, lead):
    with pytest.raises(ValueError):
        pub.confirm_manual_post(reply(), lead)


def test_automatic_needs_second_switch(pub, storage, lead, monkeypatch):
    storage.save_community_rule(CommunityRule(community="r/freelance", self_promo="allowed"))
    out = pub.publish_or_copy(reply(), lead, PostingSettings(mode="automatic", min_interval_seconds=0))
    assert out["success"] and "AGENT_REACH_ALLOW_AUTOPOST" in out["note"]


def test_daily_cap_uses_lower_of_two(pub, storage, lead):
    storage.save_community_rule(CommunityRule(community="r/freelance", self_promo="allowed"))
    link_account(storage, age_days=40, comment_karma=150)  # stage 1, cap 3
    for i in range(3):
        storage.log_post(f"l{i}", f"r{i}", "reddit", f"u{i}", "t", "manual", "published", kind="value_first")
    assert code(pub, reply(), lead, PostingSettings(daily_limit=10, min_interval_seconds=0)) == "daily_cap"


def test_interval_jitter_is_stable():
    s = PostingSettings(min_interval_seconds=600)
    a, b = CommunityPublisher._interval(s, 1000.0), CommunityPublisher._interval(s, 1000.0)
    assert a == b and 600 <= a <= 780


def test_secrets_not_persisted(storage):
    storage.save_posting_settings(PostingSettings(reddit_password="x", github_token="y"))
    saved = storage.get_posting_settings()
    assert saved.reddit_password is None and saved.github_token is None
