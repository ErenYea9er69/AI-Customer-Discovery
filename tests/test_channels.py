# -*- coding: utf-8 -*-
"""Tests for channel registry basics and URL routing."""

from agent_reach.channels import get_all_channels, get_channel
from agent_reach.channels.github import GitHubChannel
from agent_reach.channels.reddit import RedditChannel
from agent_reach.channels.twitter import TwitterChannel
from agent_reach.channels.web import WebChannel
from agent_reach.channels.youtube import YouTubeChannel


class TestChannelRegistry:
    def test_get_channel_by_name(self):
        ch = get_channel("github")
        assert ch is not None
        assert ch.name == "github"

    def test_get_unknown_channel_returns_none(self):
        assert get_channel("not-exists") is None

    def test_all_channels_registered(self):
        channels = get_all_channels()
        names = [ch.name for ch in channels]
        assert "web" in names
        assert "github" in names
        assert "twitter" in names
        assert "reddit" in names
        assert "youtube" in names


class TestRedditChannel:
    def test_can_handle_reddit_urls(self):
        ch = RedditChannel()
        assert ch.can_handle("https://www.reddit.com/r/python/comments/abc123/")
        assert ch.can_handle("https://redd.it/abc123")
        assert not ch.can_handle("https://github.com/user/repo")


class TestTwitterChannel:
    def test_can_handle_twitter_urls(self):
        ch = TwitterChannel()
        assert ch.can_handle("https://twitter.com/user/status/123")
        assert ch.can_handle("https://x.com/user/status/123")
        assert not ch.can_handle("https://github.com/user/repo")


class TestGitHubChannel:
    def test_can_handle_github_urls(self):
        ch = GitHubChannel()
        assert ch.can_handle("https://github.com/user/repo")
        assert ch.can_handle("https://github.com/user/repo/issues/1")
        assert not ch.can_handle("https://reddit.com/r/python")


class TestYouTubeChannel:
    def test_can_handle_youtube_urls(self):
        ch = YouTubeChannel()
        assert ch.can_handle("https://www.youtube.com/watch?v=123")
        assert ch.can_handle("https://youtu.be/123")
        assert not ch.can_handle("https://reddit.com/r/python")
