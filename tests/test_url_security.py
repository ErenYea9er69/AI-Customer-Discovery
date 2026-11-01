"""Credential-bearing channels must reject lookalike or disguised hosts."""

import pytest

from agent_reach.channels.github import GitHubChannel
from agent_reach.channels.reddit import RedditChannel
from agent_reach.channels.twitter import TwitterChannel
from agent_reach.channels.youtube import YouTubeChannel
from agent_reach.utils.url import host_matches


@pytest.mark.parametrize(
    ("channel", "valid_url"),
    [
        (TwitterChannel(), "https://mobile.twitter.com/user/status/1"),
        (TwitterChannel(), "https://X.COM./user/status/1"),
        (RedditChannel(), "https://www.reddit.com/r/python/comments/1"),
    ],
)
def test_credential_channels_accept_exact_hosts_and_subdomains(channel, valid_url):
    assert channel.can_handle(valid_url)


@pytest.mark.parametrize(
    ("channel", "malicious_url"),
    [
        (TwitterChannel(), "https://x.com.evil.test/user/status/1"),
        (TwitterChannel(), "https://notx.com/user/status/1"),
        (TwitterChannel(), "https://x.com@evil.test/user/status/1"),
        (TwitterChannel(), "https://user:pass@x.com/user/status/1"),
        (TwitterChannel(), "ftp://x.com/user/status/1"),
        (RedditChannel(), "https://reddit.com.evil.test/r/python"),
        (RedditChannel(), "https://reddit.com@evil.test/r/python"),
    ],
)
def test_credential_channels_reject_lookalikes_and_userinfo(channel, malicious_url):
    assert not channel.can_handle(malicious_url)


@pytest.mark.parametrize(
    ("channel", "subdomain_url", "port_url"),
    [
        (
            GitHubChannel(),
            "https://api.github.com/repos/openai/openai-python",
            "https://github.com:443/openai/openai-python",
        ),
        (
            YouTubeChannel(),
            "https://m.youtube.com/watch?v=abc",
            "https://youtu.be:443/abc",
        ),
        (
            RedditChannel(),
            "https://old.reddit.com/r/python",
            "https://reddit.com:443/r/python",
        ),
    ],
)
def test_fixed_domain_channels_accept_subdomains_and_explicit_ports(
    channel, subdomain_url, port_url
):
    assert channel.can_handle(subdomain_url)
    assert channel.can_handle(port_url)


@pytest.mark.parametrize(
    ("channel", "official_domain"),
    [
        (GitHubChannel(), "github.com"),
        (YouTubeChannel(), "youtube.com"),
        (RedditChannel(), "reddit.com"),
    ],
)
def test_fixed_domain_channels_reject_suffix_lookalikes_and_userinfo(
    channel, official_domain
):
    assert not channel.can_handle(f"https://{official_domain}.evil.test/path")
    assert not channel.can_handle(f"https://{official_domain}@evil.test/path")
    assert not channel.can_handle(f"https://user:pass@{official_domain}/path")


@pytest.mark.parametrize(
    "malicious_url",
    [
        "https://x.com:not-a-port/path",
        "https://x.com:65536/path",
        "https://x.com:-1/path",
        "https://x.com:999999999999/path",
    ],
)
def test_host_matches_rejects_invalid_ports(malicious_url):
    assert not host_matches(malicious_url, "x.com")


def test_dns_rebinding_defense():
    from agent_reach.utils.url import create_safe_session

    session = create_safe_session()
    for target in ("http://127.0.0.1:80", "http://localhost:80", "http://169.254.169.254", "http://10.0.0.1"):
        with pytest.raises(Exception) as exc_info:
            session.get(target, timeout=1)
        assert any(term in str(exc_info.value).lower() for term in ("blocked", "connection", "private", "internal"))
