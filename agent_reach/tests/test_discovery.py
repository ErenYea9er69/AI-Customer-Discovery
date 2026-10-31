# -*- coding: utf-8 -*-
import datetime
import time

import pytest

from agent_reach.discovery import thread_check as tc
from agent_reach.discovery.harvester import CommunityHarvester
from agent_reach.discovery.llm_client import LLMClient, LLMNotConfiguredError, LLMProviderError
from agent_reach.discovery.models import (
    BusinessProfile, DiscoveredItem, GeneratedReply, LeadQualification, PostingSettings,
    ScoreBreakdown, SearchQuery,
)
from agent_reach.discovery.publisher import CommunityPublisher
from agent_reach.discovery.qualifier import LeadQualifier
from agent_reach.discovery.reply_generator import ReplyGenerationError, ReplyGenerator
from agent_reach.discovery.search_planner import SearchPlanner
from agent_reach.discovery.storage import DiscoveryStorage

TODAY = datetime.date(2026, 10, 31)


@pytest.fixture
def storage(tmp_path):
    return DiscoveryStorage(tmp_path / "t.db")


@pytest.fixture
def profile():
    return BusinessProfile(
        name="PlumbBooks", url="https://www.plumbbooks.com", industry="Accounting software",
        niche="Invoicing for plumbers",
        main_product_or_service="Invoicing tool that chases unpaid invoices for plumbing firms",
        problems_solved=["Chasing unpaid customer invoices takes hours", "Late payments hurt cash flow"],
        customer_outcomes=["Get paid faster"],
        customer_frustrations=["Customers ignore invoice reminders"],
        icp="Small plumbing business owners", target_roles=["Owner", "Office manager"],
        competitors_and_alternatives=["QuickBooks", "Jobber"],
    )


class StubLLM:
    provider, model, is_mock, is_configured = "stub", "x", False, True

    def __init__(self, reply):
        self.reply = reply

    def complete_json(self, prompt, system_prompt=None):
        if isinstance(self.reply, Exception):
            raise self.reply
        return self.reply


def item(title="Customers ignore my invoice reminders, how do you chase unpaid invoices?", body="",
         platform="reddit", health=None, published="2026-10-20"):
    return DiscoveredItem(url="https://reddit.com/r/smallbusiness/comments/abc", platform=platform,
                          community="r/smallbusiness", author="u1", published_at=published, title=title,
                          content=f"{title}\n\n{body}", thread_health=health or {"age_days": 11, "num_comments": 4})


# ── URL and thread rules ──

def test_canonical_url_merges_mirrors():
    a = tc.canonical_url("https://old.reddit.com/r/Foo/comments/abc123/slug/?utm_source=x")
    b = tc.canonical_url("https://www.reddit.com/r/foo/comments/abc123/other/def456/")
    assert a == b == "https://reddit.com/r/foo/comments/abc123"
    assert tc.canonical_url("https://twitter.com/bob/status/12345?s=20") == "https://x.com/i/status/12345"


def reddit_data(**kw):
    base = {"id": "abc", "created_utc": time.mktime((2026, 10, 25, 12, 0, 0, 0, 0, 0)), "num_comments": 5,
            "score": 3, "is_self": True, "title": "Help?", "selftext": "body"}
    base.update(kw)
    return base


@pytest.mark.parametrize("extra,code", [
    ({"archived": True}, "archived"), ({"locked": True}, "locked"), ({"over_18": True}, "nsfw"),
    ({"stickied": True}, "mod_post"), ({"link_flair_text": "Self Promotion"}, "promo_flair"),
    ({"is_self": False, "title": "Cool article"}, "link_post"),
    ({"num_comments": 0, "created_utc": time.mktime((2026, 10, 1, 12, 0, 0, 0, 0, 0))}, "dead_thread"),
    ({"created_utc": time.mktime((2026, 3, 1, 12, 0, 0, 0, 0, 0))}, "too_old"),
])
def test_reddit_rejections(extra, code):
    assert tc.judge_reddit(reddit_data(**extra), now=TODAY).reject == code


def test_reddit_fresh_empty_thread_is_kept():
    h = tc.judge_reddit(reddit_data(num_comments=0), now=TODAY)
    assert h.reject is None and h.verified and h.commentable


def test_reddit_without_api_data_uses_archive_age():
    assert tc.judge_reddit(None, "2025-01-01", now=TODAY).reject == "archived"
    assert tc.judge_reddit(None, None, now=TODAY).reject == "no_date"
    ok = tc.judge_reddit(None, "2026-10-20", now=TODAY)
    assert ok.reject is None and "unverified_comment_state" in ok.warnings


def test_github_rules():
    base = {"state": "open", "locked": False, "comments": 2, "created_at": "2026-09-01T00:00:00Z", "user": {"type": "User"}}
    assert tc.judge_github(base, now=TODAY).reject is None
    assert tc.judge_github({**base, "locked": True}, now=TODAY).reject == "locked"
    assert tc.judge_github({**base, "author_association": "OWNER"}, now=TODAY).reject == "maintainer_post"


@pytest.mark.parametrize("url,title,code", [
    ("https://www.plumbbooks.com/", "x", "own_or_competitor_site"),
    ("https://example.com/pricing", "Pricing", "marketing_page"),
    ("https://blog.example.com/post", "10 best invoicing tools in 2026", "listicle"),
    ("https://example.com/blog/how-we-grew", "How we grew", "not_discussion"),
    ("https://www.reddit.com/r/x/comments/abc/t", "t", "covered_elsewhere"),
])
def test_web_rejections(url, title, code):
    assert tc.classify_web_result(url, title, ["plumbbooks.com"]).reject == code


def test_web_accepts_forums():
    for url in ("https://community.example.com/t/invoice-help/123", "https://stackoverflow.com/questions/1/x"):
        assert tc.classify_web_result(url, "How do I chase invoices?").reject is None


def test_promo_detection():
    assert tc.is_promotional("Show HN: my invoicing tool", "")
    assert tc.is_promotional("We just launched a new app", "")
    assert not tc.is_promotional("How do you chase unpaid invoices?", "Customers keep ignoring me")


# ── Harvester: the original fabrication bug ──

class FakeMeta:
    def __init__(self, data=None):
        self.data, self.last_error = data or {}, None

    def fetch(self, ids):
        return {i: self.data[i] for i in ids if i in self.data}


def test_harvester_returns_nothing_when_all_sources_fail(storage, monkeypatch):
    h = CommunityHarvester(storage, reddit_meta=FakeMeta())
    monkeypatch.setattr(h, "_search", lambda q, n: [])
    monkeypatch.setattr(h, "_reddit_direct", lambda *a, **k: [])
    out = h.execute_query(SearchQuery(query="invoice chasing", platform="reddit"), limit=3)
    assert out == []   # the old code returned made-up threads here


def test_harvester_reddit_filters_and_keeps(storage, monkeypatch):
    now = time.time()
    meta = FakeMeta({
        "good1": {"id": "good1", "created_utc": now - 5 * 86400, "num_comments": 3, "score": 9, "is_self": True,
                  "title": "How do you chase unpaid invoices?", "selftext": "Customers ignore me", "subreddit": "smallbusiness", "author": "bob"},
        "old1": {"id": "old1", "created_utc": now - 9 * 86400, "num_comments": 1, "archived": True, "is_self": True, "title": "x"},
        "lock1": {"id": "lock1", "created_utc": now - 2 * 86400, "num_comments": 1, "locked": True, "is_self": True, "title": "y"},
    })
    h = CommunityHarvester(storage, reddit_meta=meta)
    results = [{"url": f"https://www.reddit.com/r/smallbusiness/comments/{i}/slug/", "title": "t", "text": "Customers ignore me"}
               for i in ("good1", "old1", "lock1")]
    monkeypatch.setattr(h, "_search", lambda q, n: results)
    items = h.search_reddit("invoice chasing", limit=5)
    assert [i.url for i in items] == ["https://reddit.com/r/smallbusiness/comments/good1"]
    assert items[0].thread_health["num_comments"] == 3
    assert h.diagnostics["rejected:archived"] == 1 and h.diagnostics["rejected:locked"] == 1
    # same thread again is a duplicate
    assert h.search_reddit("invoice chasing", limit=5) == []


def test_harvester_hackernews(storage):
    class Resp:
        status_code = 200

        def __init__(self, hits):
            self._h = hits

        def json(self):
            return {"hits": self._h}

    class Sess:
        def get(self, url, params=None, **kw):
            now = datetime.datetime.now(datetime.timezone.utc).isoformat()
            return Resp([
                {"objectID": "1", "title": "Ask HN: How do you chase unpaid invoices?", "story_text": "<p>Clients pay late</p>",
                 "author": "a", "created_at": now, "num_comments": 4, "points": 5},
                {"objectID": "2", "title": "Show HN: InvoiceBot", "story_text": "x", "author": "b", "created_at": now, "num_comments": 1},
            ]) if params["tags"] == "ask_hn" else Resp([])
    h = CommunityHarvester(storage, session=Sess())
    items = h.search_hackernews("invoices", limit=5)
    assert len(items) == 1 and items[0].url.endswith("id=1") and "Clients pay late" in items[0].content
    assert h.diagnostics["rejected:promo_post"] == 1


# ── Qualifier ──

def test_qualifier_heuristic_matches_and_never_claims_high(profile):
    q = LeadQualifier(LLMClient(provider="none"))
    lead = q.qualify(item(body="I am tired of chasing unpaid invoices. Any recommendations for a tool? Late payments hurt cash flow."), profile)
    assert lead and lead.judged_by == "heuristic" and lead.classification != "high_potential"
    assert "triage" not in lead.product_fit_explanation.lower()
    assert lead.confidence == 0.5


def test_qualifier_rejects_off_topic_and_sellers(profile):
    q = LeadQualifier(LLMClient(provider="none"))
    assert q.qualify(item(title="Best pizza in Austin?", body="Looking for recommendations"), profile) is None
    assert q.last_rejection == "off_topic"
    assert q.qualify(item(title="I built an invoice chasing tool", body="unpaid invoices"), profile) is None
    assert q.last_rejection == "promotional"


def test_qualifier_llm_verifies_quote(profile):
    body = "Clients ignore my reminders and I chase unpaid invoices every week."
    good = {"author_is_potential_customer": True, "post_type": "asking_for_help", "problem_fit": 28, "icp_match": 20,
            "buying_intent": 16, "urgency": 10, "customer_problem": "Chasing unpaid invoices",
            "evidence_quote": "I chase unpaid invoices every week", "reason": "Owner with the exact problem"}
    q = LeadQualifier(StubLLM(good))
    lead = q.qualify(item(body=body), profile)
    assert lead.judged_by == "llm" and lead.classification == "high_potential" and lead.confidence == 0.9
    assert lead.evidence == "Author wrote: 'I chase unpaid invoices every week'"

    fake = dict(good, evidence_quote="We would pay $500 for this today")
    lead = LeadQualifier(StubLLM(fake)).qualify(item(body=body), profile)
    assert lead.confidence == 0.7 and "would pay" not in lead.evidence

    nope = dict(good, author_is_potential_customer=False, post_type="seller_promo")
    q = LeadQualifier(StubLLM(nope))
    assert q.qualify(item(body=body), profile) is None and q.last_rejection == "llm_not_a_lead"


def test_qualifier_falls_back_when_llm_fails(profile):
    q = LeadQualifier(StubLLM(LLMProviderError("down")))
    lead = q.qualify(item(body="I chase unpaid invoices and late payments hurt cash flow. Any tool?"), profile)
    assert lead and lead.judged_by == "heuristic"


def test_crowded_thread_lowers_score(profile):
    q = LeadQualifier(LLMClient(provider="none"))
    quiet = q._opportunity_points(item(health={"age_days": 3, "num_comments": 2}))
    crowded = q._opportunity_points(item(health={"age_days": 3, "num_comments": 200}))
    assert quiet == 10 and crowded == 7


# ── Planner ──

def test_planner_has_no_hardcoded_niche_terms(profile):
    queries = SearchPlanner(LLMClient(provider="none")).plan_queries(profile, ["reddit", "hackernews", "web", "twitter"])
    blob = " ".join(q.query for q in queries).lower()
    assert "focus" not in blob and "deadline" not in blob
    assert {q.platform for q in queries} == {"reddit", "hackernews", "web", "twitter"}
    assert len(queries) <= 24


def test_planner_word_boundaries_and_blocklist(profile):
    profile.niche = "He said she paid late"   # "said" contains "ai" but is not the word
    planner = SearchPlanner(LLMClient(provider="none"))
    subs = planner._select_subreddits(planner._profile_text(profile), False, ["r/programming", "r/SaaS"])
    assert "r/ArtificialInteligence" not in subs and "r/programming" not in subs and "r/SaaS" in subs


def test_planner_respects_selected_platforms(profile):
    queries = SearchPlanner(LLMClient(provider="none")).plan_queries(profile, ["web"])
    assert {q.platform for q in queries} == {"web"}


# ── LLM client ──

def test_llm_client_never_falls_back_to_mock():
    c = LLMClient()
    assert not c.is_configured
    with pytest.raises(LLMNotConfiguredError):
        c.complete("hello")
    assert LLMClient(provider="mock").is_mock


# ── Replies ──

def test_reply_generator_enforces_rules(profile):
    lead = LeadQualification(
        discovered_item_id="d", title="t", url="https://reddit.com/r/x/comments/abc", platform="reddit", community="r/x",
        author="a", published_at="2026-10-01", excerpt="e", customer_problem="p", pain_point_category="c", profile_match="m",
        product_fit_explanation="f", evidence="ev", score=80,
        score_breakdown=ScoreBreakdown(icp_match=1, problem_fit=1, buying_intent=1, urgency=1, recency=1, total=5))
    llm = StubLLM({"value_first": "Send reminders on day 3. PlumbBooks is great. Offer card payment.",
                   "product_aware": "Try reminders. We built PlumbBooks for this."})
    reply = ReplyGenerator(llm).generate_replies(lead, profile)
    assert "PlumbBooks" not in reply.value_first
    assert reply.product_aware.endswith("Disclosure: I am affiliated with PlumbBooks.")
    with pytest.raises(ReplyGenerationError):
        ReplyGenerator(StubLLM({"value_first": "only one"})).generate_replies(lead, profile)


# ── Publisher ──

class NoNetwork:
    def __getattr__(self, name):
        raise AssertionError("manual mode must not touch the network")


def make_lead_reply(storage, status="approved", version="value_first"):
    lead = LeadQualification(
        discovered_item_id="d", title="t", url="https://reddit.com/r/smallbusiness/comments/abc123", platform="reddit",
        community="r/smallbusiness", author="a", published_at="2026-10-01", excerpt="e", customer_problem="p",
        pain_point_category="c", profile_match="m", product_fit_explanation="f", evidence="ev", score=80,
        score_breakdown=ScoreBreakdown(icp_match=1, problem_fit=1, buying_intent=1, urgency=1, recency=1, total=5))
    reply = GeneratedReply(lead_id=lead.id, value_first="Helpful text", product_aware="Pitch", status=status,
                           selected_version=version, platform="reddit", target_url=lead.url,
                           affiliation_disclosure="Disclosure: I am affiliated with X.")
    storage.save_lead(lead)
    storage.save_reply(reply)
    return lead, reply


def test_manual_mode_copies_and_only_confirm_publishes(storage):
    pub = CommunityPublisher(storage, session=NoNetwork())
    lead, reply = make_lead_reply(storage)
    settings = PostingSettings(mode="manual", reddit_client_id="id", reddit_client_secret="s",
                               reddit_username="u", reddit_password="p", min_interval_seconds=0)
    res = pub.publish_or_copy(reply, lead, settings)
    assert res["action"] == "copy_and_open" and reply.status == "pending_manual_post"
    assert storage.count_posts_today("reddit") == 0          # not published yet
    assert pub.confirm_manual_post(reply, lead)["success"]
    assert storage.count_posts_today("reddit") == 1
    with pytest.raises(ValueError):
        pub.confirm_manual_post(reply, lead)


def test_publisher_blocks(storage):
    pub = CommunityPublisher(storage, session=NoNetwork())
    lead, reply = make_lead_reply(storage, status="draft")
    s = PostingSettings(mode="manual", min_interval_seconds=0)
    assert "Approve" in pub.can_publish(reply, lead, s)[1]
    reply.status = "approved"
    assert not pub.can_publish(reply, lead, PostingSettings(mode="draft"))[0]
    assert not pub.can_publish(reply, lead, PostingSettings(emergency_stop=True))[0]
    assert "not in the allowed" in pub.can_publish(reply, lead, PostingSettings(allowed_communities=["r/other"]))[1]
    storage.log_post(lead.id, reply.id, "reddit", lead.url, "x", "manual", "published")
    assert "Wait" in pub.can_publish(reply, lead, PostingSettings(min_interval_seconds=600))[1]


def test_product_aware_always_gets_disclosure(storage):
    pub = CommunityPublisher(storage, session=NoNetwork())
    _, reply = make_lead_reply(storage, version="product_aware")
    assert pub._final_content(reply).endswith("Disclosure: I am affiliated with X.")


def test_reddit_api_uses_t3_id_and_reads_error_list(storage):
    calls = []

    class R:
        def __init__(self, code, body):
            self.status_code, self._b = code, body

        def json(self):
            return self._b

    class Sess:
        def post(self, url, **kw):
            calls.append((url, kw.get("data")))
            if "access_token" in url:
                return R(200, {"access_token": "tok", "expires_in": 3600})
            return R(200, {"json": {"errors": [["THREAD_LOCKED", "nope", "thing_id"]]}})

        def get(self, url, **kw):
            return R(200, {"data": {"children": [{"data": reddit_data(id="abc123", created_utc=time.time() - 86400)}]}})
    pub = CommunityPublisher(storage, session=Sess())
    lead, reply = make_lead_reply(storage)
    s = PostingSettings(mode="automatic", reddit_client_id="id", reddit_client_secret="s", reddit_username="u",
                        reddit_password="p", min_interval_seconds=0)
    res = pub.publish_or_copy(reply, lead, s)
    assert res["success"] is False and "THREAD_LOCKED" in res["reason"]
    assert calls[-1][1]["thing_id"] == "t3_abc123"
    assert reply.status == "approved"      # a failed post does not claim success


# ── Storage ──

def test_csv_export_blocks_formula_injection(storage):
    lead, _ = make_lead_reply(storage)
    lead.title = '=HYPERLINK("http://evil","x")'
    storage.save_lead(lead)
    assert "'=HYPERLINK" in storage.export_leads_csv()


def test_stale_campaigns_are_closed(storage):
    from agent_reach.discovery.models import Campaign
    storage.save_campaign(Campaign(status="running"))
    assert storage.mark_stale_campaigns_failed() == 1
    assert storage.list_campaigns()[0].status == "failed"
