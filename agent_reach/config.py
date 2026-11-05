# -*- coding: utf-8 -*-
"""Optional key file: ~/.agent-reach/config.yaml.

Environment variables are the main way to set keys (see .env.example). This file is a fallback
for owners who prefer a file. Reads never create files or folders. The first write creates a
private folder and writes the file atomically with owner-only permissions. Symbolic links in the
path are refused so a planted link cannot redirect a credential read or write.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Optional

import yaml

from agent_reach.utils.paths import (
    PrivatePathError,
    atomic_write_private_text,
    ensure_no_symlink_path,
    home_dir,
    read_small_text_no_follow,
)

_MAX_CONFIG_BYTES = 1024 * 1024


class ConfigError(RuntimeError):
    """Base class for configuration errors that are safe to show to the user."""


class ConfigReadOnlyError(ConfigError):
    """Raised when code tries to change a config opened read only."""


class ConfigSecurityError(ConfigError):
    """Raised when a config path could redirect a credential read or write."""


class Config:
    """Key and value settings. `get` checks the file first, then the upper-case environment variable."""

    CONFIG_DIR = home_dir() / ".agent-reach"
    CONFIG_FILE = CONFIG_DIR / "config.yaml"

    def __init__(self, config_path: Optional[Path] = None, *, read_only: bool = False):
        self.config_path = Path(config_path) if config_path else self.CONFIG_FILE
        self.read_only = read_only
        self.data: dict = {}
        self.load()

    def _check_path(self) -> None:
        try:
            ensure_no_symlink_path(self.config_path.parent, "config folder")
            ensure_no_symlink_path(self.config_path, "config file")
        except PrivatePathError as exc:
            raise ConfigSecurityError(str(exc)) from exc

    def load(self) -> None:
        self._check_path()
        try:
            payload = read_small_text_no_follow(self.config_path, max_bytes=_MAX_CONFIG_BYTES)
        except PrivatePathError as exc:
            raise ConfigSecurityError(str(exc)) from exc
        if payload is None:
            self.data = {}
            return
        loaded = yaml.safe_load(payload) or {}
        if not isinstance(loaded, dict):
            raise ConfigError("The top level of the config file must be a mapping.")
        self.data = loaded

    def save(self) -> None:
        if self.read_only:
            raise ConfigReadOnlyError("This config is read only.")
        self._check_path()
        text = yaml.safe_dump(self.data, default_flow_style=False, allow_unicode=True)
        try:
            atomic_write_private_text(self.config_path, text)
        except PrivatePathError as exc:
            raise ConfigSecurityError(str(exc)) from exc

    def get(self, key: str, default: Any = None) -> Any:
        if key in self.data:
            return self.data[key]
        env_val = os.environ.get(key.upper())
        return env_val if env_val else default

    def set(self, key: str, value: Any) -> None:
        if self.read_only:
            raise ConfigReadOnlyError("This config is read only.")
        missing = object()
        previous = self.data.get(key, missing)
        self.data[key] = value
        try:
            self.save()
        except BaseException:
            if previous is missing:
                self.data.pop(key, None)
            else:
                self.data[key] = previous
            raise

    def delete(self, key: str) -> None:
        if self.read_only:
            raise ConfigReadOnlyError("This config is read only.")
        missing = object()
        previous = self.data.pop(key, missing)
        try:
            self.save()
        except BaseException:
            if previous is not missing:
                self.data[key] = previous
            raise
