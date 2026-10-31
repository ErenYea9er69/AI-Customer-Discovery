"""Public access precedes installation/auth, and keeps its evidence scope."""

import json
from unittest.mock import Mock

import pytest

from agent_reach.channels.reddit import RedditChannel
from agent_reach.channels.web import WebChannel
from agent_reach.runtime import cli, manage, state, tools
from agent_reach.runtime.dispatch import run_action
from agent_reach.runtime.result import ReachError, make_item

URL = "https://www.reddit.com/r/productivity/comments/123/task_management_problems/"
TEXT = "I struggle with deadline management and staying organized. " * 10


@pytest.fixture
def public_search(monkeypatch):
    search = Mock(return_value=[make_item(title="Task Management Problems", url=URL, text="Search excerpt")])
    monkeypatch.setattr(WebChannel, "_exa_search", search)
    return search


def test_public_success_never_installs_binds_or_opens_a_browser(monkeypatch, public_search):
    from agent_reach.runtime import browser
    for module, name in ((manage, "add"), (tools, "ensure"), (browser, "ensure_running")):
        monkeypatch.setattr(module, name, Mock(side_effect=AssertionError("public query touched browser setup")))
    monkeypatch.setattr(RedditChannel, "_opencli_search", Mock(side_effect=AssertionError("used site tool")))
    out = run_action(RedditChannel(), "search", {"query": "productivity", "limit": 2})
    assert out["ok"] and out["backend"] == "public-web"
    query = public_search.call_args.kwargs["query"]
    assert "site:reddit.com/r/" in query and "productivity" in query
    assert out["meta"]["access"]["scope"] == "search_results"
    assert out["meta"]["access"]["completeness_verified"] is False


def test_public_failure_falls_back_to_added_channel_silently(monkeypatch):
    monkeypatch.setattr(WebChannel, "_exa_search", Mock(side_effect=ReachError("TIMEOUT", "search failed")))
    site = Mock(return_value=[make_item(title="Site result", url=URL)])
    monkeypatch.setattr(RedditChannel, "_opencli_search", site)
    out = run_action(RedditChannel(), "search", {"query": "productivity"}, only_backend="opencli")
    assert out["ok"] and out["backend"] == "opencli"
    assert site.called


def test_configured_channel_uses_site_tool_directly(monkeypatch):
    def add_channel(data):
        data["channels"]["reddit"] = {"added_at": state.now()}
    state.mutate(add_channel)
    site = Mock(return_value=[make_item(title="Site result", url=URL)])
    monkeypatch.setattr(RedditChannel, "_opencli_search", site)
    out = run_action(RedditChannel(), "search", {"query": "productivity"})
    assert out["ok"] and out["backend"] == "opencli"
    assert site.called


@pytest.mark.parametrize("code", ["UPSTREAM_BROKEN", "TIMEOUT", "RATE_LIMITED"])
def test_web_provider_failure_does_not_become_platform_login_or_cooldown(monkeypatch, code):
    def fail(self, **kwargs):
        raise ReachError(code, "Web provider failure")
    monkeypatch.setattr(WebChannel, "_exa_search", fail)
    monkeypatch.setattr(RedditChannel, "_opencli_search", lambda *a, **k: [make_item(title="Site result", url=URL)])
    out = run_action(RedditChannel(), "search", {"query": "productivity"})
    assert out["ok"] and out["backend"] == "opencli"
    assert not state.load().get("cooldowns", {}).get("reddit")


def test_confirmed_destination_cooldown_blocks_every_path(public_search):
    state.mutate(lambda saved: saved.setdefault("cooldowns", {}).__setitem__("reddit", {
        "code": "RATE_LIMITED", "at": state.now()}))
    out = run_action(RedditChannel(), "search", {"query": "productivity"})
    assert out["error"]["code"] == "RATE_LIMITED"
    public_search.assert_not_called()


def test_public_read_uses_jina_reader_anonymously(monkeypatch):
    monkeypatch.setattr(WebChannel, "_jina_read", Mock(return_value=[make_item(title="Post", url=URL, text=TEXT)]))
    monkeypatch.setattr(RedditChannel, "_opencli_read", Mock(side_effect=AssertionError("unnecessary browser read")))
    out = run_action(RedditChannel(), "read", {"target": URL})
    assert out["ok"] and out["backend"] == "public-web"
    assert out["items"][0]["text"] == TEXT


def test_new_policy_leaves_comments_subtitles_and_user_search_semantics_unchanged():
    from agent_reach.channels import get_all_channels
    for ch in get_all_channels():
        for action in ch.actions:
            if action.name not in {"search", "read"}:
                assert not action.public_web, (ch.name, action.name)


def test_backend_option_can_request_public_only(monkeypatch, public_search, capsys):
    monkeypatch.setattr(manage, "add", Mock(side_effect=AssertionError("unexpected setup")))
    monkeypatch.setattr(RedditChannel, "_opencli_search", Mock(side_effect=AssertionError("public-only fell back")))
    assert cli.main(["reddit", "search", "productivity", "--backend", "public-web"]) == 0
    assert json.loads(capsys.readouterr().out)["backend"] == "public-web"


def test_only_backend_unknown_fails_fast(monkeypatch):
    monkeypatch.setattr(RedditChannel, "_opencli_search", Mock(side_effect=AssertionError("unexpected site access")))
    out = run_action(RedditChannel(), "search", {"query": "productivity"}, only_backend="unknown")
    assert not out["ok"] and out["error"]["code"] == "BAD_INPUT"
