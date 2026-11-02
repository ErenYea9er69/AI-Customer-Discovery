
import pytest

from agent_reach.discovery import thread_comments as tc
from agent_reach.discovery.accounts import (
    AccountError,
    AccountService,
    compute_health,
    filter_samples,
)
from agent_reach.discovery.models import BusinessProfile


class Resp:
    def __init__(self, code, data):
        self.status_code, self._d = code, data

    def json(self):
        return self._d


class FakeSession:
    def __init__(self, routes):
        self.routes = routes

    def get(self, url, **kw):
        for key, value in self.routes.items():
            if key in url:
                return Resp(*value)
        return Resp(404, {})


def test_health_stages():
    assert compute_health({"supported": True, "age_days": 5, "comment_karma": 3}).stage == 0
    assert compute_health({"supported": True, "age_days": 40, "comment_karma": 150}).max_pitch_level == 1
    assert compute_health({"supported": True, "age_days": 120, "comment_karma": 350}).stage == 2
    assert compute_health({"supported": True, "age_days": 400, "comment_karma": 900}).stage == 3
    over = compute_health({"supported": True, "age_days": 400, "comment_karma": 900, "recent_mention_ratio": 0.3}, "Acme")
    assert over.stage == 2
    assert compute_health({}).known is False


def test_link_refresh_voice_import(storage, now):
    about = {"data": {"created_utc": now - 200 * 86400, "comment_karma": 650, "link_karma": 10}}
    comments = {"data": {"children": [
        {"data": {"body": "I run a small agency and we spent months fixing this exact problem by writing the intake form ourselves in a spreadsheet, it worked fine until forty clients.", "subreddit": "smallbusiness"}},
        {"data": {"body": "lol", "subreddit": "x"}},
    ]}}
    svc = AccountService(storage, FakeSession({"about.json": (200, about), "comments.json": (200, comments)}))
    acc = svc.link("reddit", "https://www.reddit.com/user/rayen_test/")
    assert acc.handle == "rayen_test"
    svc.refresh("reddit", "rayen_test", "Acme")
    assert svc.health("reddit", "rayen_test").max_pitch_level == 3
    assert len(svc.import_voice_samples("reddit", "rayen_test")) == 1
    assert svc.unlink("reddit", "rayen_test") and not svc.list()


def test_bad_platform_and_handle(storage):
    svc = AccountService(storage)
    with pytest.raises(AccountError):
        svc.link("tiktok", "x")
    with pytest.raises(AccountError):
        svc.link("reddit", "bad handle!!")


def test_no_secret_fields_on_linked_account(storage):
    acc = AccountService(storage).link("reddit", "someone")
    assert not {"password", "cookie", "token"} & set(acc.model_dump())


def test_filter_samples_drops_quotes_and_short():
    out = filter_samples(["> quoted only text here", "lol", "word " * 20])
    assert len(out) == 1


def listing(now):
    return [
        {"data": {"children": [{"data": {"id": "abc", "author": "op", "title": "Need invoice tool", "selftext": "chasing late payments", "num_comments": 3}}]}},
        {"data": {"children": [
            {"kind": "t1", "data": {"id": "c1", "author": "bob", "body": "Any tool you would recommend for chasing late invoices?", "score": 3, "created_utc": now - 3600, "replies": ""}},
            {"kind": "t1", "data": {"id": "c2", "author": "AutoModerator", "body": "Please read the rules?", "score": 1, "created_utc": now - 3600, "replies": ""}},
            {"kind": "t1", "data": {"id": "c3", "author": "op", "is_submitter": True, "body": "Thanks all, what do you use for reminders?", "score": 1, "created_utc": now - 600, "replies": ""}},
        ]}},
    ]


def test_reddit_comments_and_ranking(now):
    session = FakeSession({"comments/abc.json": (200, listing(now))})
    post, flat, warns = tc.fetch_reddit_comments("https://www.reddit.com/r/freelance/comments/abc/x/", session)
    assert post["title"] == "Need invoice tool" and len(flat) == 3 and not warns
    prof = BusinessProfile(name="Acme", problems_solved=["chasing late invoices"], pain_vocabulary=["late invoices"])
    targets = tc.rank_targets(post, flat, prof)
    assert [t.target_comment_id for t in targets][:2] == ["c1", "c3"]
    assert targets[2].target_kind == "post"
    assert all(t.target_author != "AutoModerator" for t in targets)


def test_locked_thread_has_no_targets():
    assert tc.rank_targets({"locked": True}, [{"id": "1", "author": "a", "body": "Any tool for this problem you know?"}]) == []


def test_fetch_failure_returns_warning():
    post, flat, warns = tc.fetch_comments("https://www.reddit.com/r/x/comments/abc/y/", FakeSession({}))
    assert not post and not flat and warns
    assert tc.fetch_comments("https://example.com/thread")[2]
