# -*- coding: utf-8 -*-
"""
Channel registry — active platforms for customer discovery, search, and reading.
"""

from typing import List, Optional

from .base import Channel
from .github import GitHubChannel
from .reddit import RedditChannel
from .twitter import TwitterChannel
from .web import WebChannel
from .youtube import YouTubeChannel

ALL_CHANNELS: List[Channel] = [
    RedditChannel(),
    TwitterChannel(),
    WebChannel(),
    GitHubChannel(),
    YouTubeChannel(),
]


def get_channel(name: str) -> Optional[Channel]:
    """Get a channel by name."""
    for ch in ALL_CHANNELS:
        if ch.name == name:
            return ch
    return None


def get_all_channels() -> List[Channel]:
    """Get all registered channels."""
    return ALL_CHANNELS


__all__ = [
    "Channel",
    "ALL_CHANNELS",
    "get_channel",
    "get_all_channels",
]
