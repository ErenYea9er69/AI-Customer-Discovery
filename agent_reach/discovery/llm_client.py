# -*- coding: utf-8 -*-
"""LLM client for OpenAI, Gemini, Groq, Anthropic and DeepSeek. Plain HTTP, no vendor SDK.

Rules:
- The mock provider runs only when LLM_PROVIDER=mock is set on purpose.
- With no provider and no key the client raises LLMNotConfiguredError. It never invents data.
- Each provider has an ordered list of model names per tier. "fast" serves scoring,
  "smart" serves profiles and replies. When a model name is retired or unknown the
  client tries the next name and remembers the one that works.
- Set LLM_MODEL (or LLM_MODEL_FAST, LLM_MODEL_SMART) to pin a model and skip the list.
"""

from __future__ import annotations

import json
import logging
import os
import re
import time
from collections import Counter
from typing import Any, Dict, List, Optional

import requests

log = logging.getLogger("agent_reach.discovery")

# Ordered candidates per tier. Vendors retire models often (Groq retired
# llama-3.3-70b-versatile on 2026-08-16, DeepSeek retired deepseek-chat on 2026-07-24).
# Names were taken from vendor deprecation pages and docs in 2026. Run
# `agent-reach discovery llm-check` to confirm the names work for your key.
MODEL_CANDIDATES: Dict[str, Dict[str, List[str]]] = {
    "anthropic": {
        "fast": ["claude-haiku-5-5", "claude-sonnet-5-5"],
        "smart": ["claude-sonnet-5-5", "claude-opus-5-5"],
    },
    "openai": {
        "fast": ["gpt-6-luna", "gpt-5.6-luna", "gpt-4.1-mini"],
        "smart": ["gpt-6-sol", "gpt-5.6-sol", "gpt-4.1"],
    },
    "gemini": {
        "fast": ["gemini-3.5-flash-lite", "gemini-2.5-flash-lite", "gemini-2.5-flash"],
        "smart": ["gemini-3.6-flash", "gemini-3.5-flash", "gemini-2.5-flash"],
    },
    "groq": {
        "fast": ["openai/gpt-oss-20b", "openai/gpt-oss-120b"],
        "smart": ["openai/gpt-oss-120b"],
    },
    "deepseek": {
        "fast": ["deepseek-v4-flash"],
        "smart": ["deepseek-v4-pro", "deepseek-v4-flash"],
    },
}
# Kept for older callers: the first "smart" name per provider.
DEFAULT_MODELS = {p: tiers["smart"][0] for p, tiers in MODEL_CANDIDATES.items()}

_KEY_ENV = {
    "groq": "GROQ_API_KEY",
    "openai": "OPENAI_API_KEY",
    "gemini": "GEMINI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "deepseek": "DEEPSEEK_API_KEY",
}
_OPENAI_COMPAT_URL = {
    "openai": "https://api.openai.com/v1/chat/completions",
    "groq": "https://api.groq.com/openai/v1/chat/completions",
    "deepseek": "https://api.deepseek.com/chat/completions",
}
_TIMEOUT_SECONDS = 90
_RETRY_STATUS = {408, 429, 500, 502, 503, 504, 529}
_MODEL_GONE = re.compile(
    r"model[^\"]{0,80}(?:not found|does not exist|decommission|deprecated|retired|unknown|invalid|not supported|no longer)",
    re.I,
)


class LLMProviderError(RuntimeError):
    """Raised when a configured provider fails."""


class LLMNotConfiguredError(LLMProviderError):
    """Raised when no provider or API key is available."""


class ModelUnavailableError(LLMProviderError):
    """The model name is retired or unknown. The client tries the next name."""


class LLMClient:
    """Small provider switch with explicit failure."""

    def __init__(
        self,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        tier: str = "smart",
        session: Optional[requests.Session] = None,
    ):
        chosen = (provider or os.getenv("LLM_PROVIDER") or "").strip().lower()
        if not chosen:
            for name in ("anthropic", "openai", "gemini", "groq", "deepseek"):
                if self._resolve_api_key(name):
                    chosen = name
                    break
        self.provider = chosen
        self.tier = tier if tier in ("fast", "smart") else "smart"
        self.api_key = api_key or None
        if not self.api_key and self.provider and self.provider != "mock":
            self.api_key = self._resolve_api_key(self.provider) or os.getenv("LLM_API_KEY")
        self._pinned = model or os.getenv(f"LLM_MODEL_{self.tier.upper()}") or os.getenv("LLM_MODEL")
        self._working: Dict[str, str] = {}
        self.session = session or requests.Session()
        self.usage: Counter = Counter()
        self.calls = 0

    # ── Setup ──

    @staticmethod
    def _resolve_api_key(provider: str) -> Optional[str]:
        if provider == "gemini":
            val = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
            if val:
                return val
        elif provider in _KEY_ENV:
            val = os.getenv(_KEY_ENV[provider])
            if val:
                return val
        try:
            from agent_reach.config import Config

            cfg = Config(read_only=True)
            return cfg.get(f"{provider}_api_key") or cfg.get(f"{provider}-key")
        except Exception:
            return None

    def for_tier(self, tier: str) -> "LLMClient":
        """Return a client for another tier. It shares the key, session and usage counter."""
        if tier == self.tier:
            return self
        clone = LLMClient(self.provider, None, self.api_key, tier=tier, session=self.session)
        clone.usage = self.usage
        if not clone._pinned and self._pinned and not os.getenv(f"LLM_MODEL_{tier.upper()}"):
            clone._pinned = self._pinned
        return clone

    @property
    def candidates(self) -> List[str]:
        if self._pinned:
            return [self._pinned]
        tiers = MODEL_CANDIDATES.get(self.provider)
        if not tiers:
            return []
        first = self._working.get(self.tier)
        ordered = list(tiers[self.tier])
        if first and first in ordered:
            ordered.remove(first)
            ordered.insert(0, first)
        return ordered

    @property
    def model(self) -> Optional[str]:
        cands = self.candidates
        return cands[0] if cands else None

    @property
    def is_configured(self) -> bool:
        if self.provider == "mock":
            return True
        return bool(self.provider in MODEL_CANDIDATES and self.api_key)

    @property
    def is_mock(self) -> bool:
        return self.provider == "mock"

    # ── Public API ──

    def complete(self, prompt: str, system_prompt: Optional[str] = None, json_mode: bool = False) -> str:
        if self.provider == "mock":
            from agent_reach.discovery.llm_mock import mock_completion

            log.warning("LLM provider is 'mock'. Output is canned test data, not real analysis.")
            return mock_completion(prompt, system_prompt)
        if not self.provider:
            raise LLMNotConfiguredError(
                "No LLM is configured. Set LLM_PROVIDER (anthropic, openai, gemini, groq, deepseek) "
                "and an API key, or choose a provider in Settings."
            )
        if self.provider not in MODEL_CANDIDATES:
            raise LLMProviderError(f"Unsupported LLM provider: {self.provider}")
        if not self.api_key:
            raise LLMNotConfiguredError(f"Provider '{self.provider}' has no API key.")

        last: Optional[Exception] = None
        for model in self.candidates:
            try:
                text = self._call(model, prompt, system_prompt, json_mode)
            except ModelUnavailableError as exc:
                log.warning("Model %s is unavailable (%s). Trying the next name.", model, str(exc)[:120])
                last = exc
                continue
            self._working[self.tier] = model
            self.calls += 1
            return text
        raise LLMProviderError(
            f"No working model for {self.provider}/{self.tier}. Set LLM_MODEL to a current model name. Last error: {last}"
        )

    def complete_json(self, prompt: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        """Request a JSON object. Retries once when the reply is not valid JSON."""
        json_system = ((system_prompt or "") + "\n\nRespond ONLY with one valid JSON object. No commentary.").strip()
        raw = self.complete(prompt, json_system, json_mode=True)
        try:
            return self._extract_json(raw)
        except LLMProviderError:
            retry = self.complete(
                prompt + "\n\nYour last reply was not valid JSON. Reply with one JSON object only.",
                json_system,
                json_mode=True,
            )
            return self._extract_json(retry)

    def check(self) -> Dict[str, Any]:
        """Send a tiny request. Returns ok, model and timing. Used by `llm-check`."""
        started = time.time()
        try:
            text = self.complete("Reply with the single word: ok", None, json_mode=False)
            return {
                "ok": True,
                "provider": self.provider,
                "tier": self.tier,
                "model": self._working.get(self.tier, self.model),
                "seconds": round(time.time() - started, 2),
                "reply": text.strip()[:40],
            }
        except LLMProviderError as exc:
            return {"ok": False, "provider": self.provider, "tier": self.tier, "error": str(exc)[:300]}

    @staticmethod
    def _extract_json(raw: str) -> Dict[str, Any]:
        cleaned = (raw or "").strip()
        if "```" in cleaned:
            match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", cleaned)
            if match:
                cleaned = match.group(1).strip()
        candidates = [cleaned]
        block = re.search(r"(\{[\s\S]*\})", cleaned)
        if block:
            candidates.append(block.group(1))
        for text in candidates:
            try:
                parsed = json.loads(text)
            except json.JSONDecodeError:
                continue
            if isinstance(parsed, dict):
                return parsed
        raise LLMProviderError("The LLM returned invalid JSON.")

    # ── Providers ──

    def _call(self, model: str, prompt: str, system_prompt: Optional[str], json_mode: bool) -> str:
        if self.provider in _OPENAI_COMPAT_URL:
            return self._call_openai_compatible(model, prompt, system_prompt, json_mode)
        if self.provider == "gemini":
            return self._call_gemini(model, prompt, system_prompt, json_mode)
        return self._call_anthropic(model, prompt, system_prompt)

    def _post_json(self, url: str, headers: Dict[str, str], payload: Dict[str, Any]) -> Dict[str, Any]:
        last = ""
        for attempt in range(4):
            try:
                resp = self.session.post(url, json=payload, headers=headers, timeout=_TIMEOUT_SECONDS)
            except requests.RequestException as exc:
                last = type(exc).__name__
            else:
                if resp.status_code == 200:
                    try:
                        return resp.json()
                    except ValueError as exc:
                        raise LLMProviderError(f"{self.provider} returned a non-JSON body.") from exc
                body = resp.text[:400]
                last = f"http {resp.status_code}: {body}"
                if resp.status_code == 404 or (resp.status_code in (400, 403) and _MODEL_GONE.search(body)):
                    raise ModelUnavailableError(last)
                if resp.status_code not in _RETRY_STATUS:
                    break
                retry_after = resp.headers.get("retry-after") if hasattr(resp, "headers") else None
                if retry_after and retry_after.isdigit():
                    time.sleep(min(30, int(retry_after)))
                    continue
            time.sleep(min(20, 1.5 * (2 ** attempt)))
        raise LLMProviderError(f"{self.provider} request failed ({last})")

    def _call_openai_compatible(self, model: str, prompt: str, system_prompt: Optional[str], json_mode: bool) -> str:
        url = _OPENAI_COMPAT_URL[self.provider]
        if self.provider == "openai" and os.getenv("OPENAI_BASE_URL"):
            url = os.getenv("OPENAI_BASE_URL", "").rstrip("/") + "/chat/completions"
        messages: List[Dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        payload: Dict[str, Any] = {"model": model, "messages": messages}
        if json_mode:
            payload["response_format"] = {"type": "json_object"}
        temperature = os.getenv("LLM_TEMPERATURE")
        if temperature:
            payload["temperature"] = float(temperature)
        data = self._post_json(url, {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}, payload)
        usage = data.get("usage") or {}
        self.usage["input_tokens"] += int(usage.get("prompt_tokens") or 0)
        self.usage["output_tokens"] += int(usage.get("completion_tokens") or 0)
        try:
            return data["choices"][0]["message"].get("content") or ""
        except (KeyError, IndexError, TypeError) as exc:
            raise LLMProviderError(f"{self.provider} returned no text.") from exc

    def _call_gemini(self, model: str, prompt: str, system_prompt: Optional[str], json_mode: bool) -> str:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        payload: Dict[str, Any] = {"contents": [{"parts": [{"text": prompt}]}]}
        if system_prompt:
            payload["systemInstruction"] = {"parts": [{"text": system_prompt}]}
        if json_mode:
            payload["generationConfig"] = {"responseMimeType": "application/json"}
        data = self._post_json(url, {"Content-Type": "application/json", "x-goog-api-key": str(self.api_key)}, payload)
        meta = data.get("usageMetadata") or {}
        self.usage["input_tokens"] += int(meta.get("promptTokenCount") or 0)
        self.usage["output_tokens"] += int(meta.get("candidatesTokenCount") or 0)
        try:
            parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
            text_parts = [p.get("text", "") for p in parts if not p.get("thought") and p.get("text")]
            if not text_parts:
                text_parts = [p.get("text", "") for p in parts if p.get("text")]
            result = "".join(text_parts).strip()
        except (KeyError, IndexError, TypeError, AttributeError) as exc:
            raise LLMProviderError("Gemini returned no text (blocked or empty).") from exc
        if not result:
            raise LLMProviderError("Gemini returned no text (blocked or empty).")
        return result

    def _call_anthropic(self, model: str, prompt: str, system_prompt: Optional[str]) -> str:
        payload: Dict[str, Any] = {
            "model": model,
            "max_tokens": int(os.getenv("LLM_MAX_TOKENS", "4096")),
            "messages": [{"role": "user", "content": prompt}],
        }
        if system_prompt:
            if len(system_prompt) > 1500:
                # The skill text repeats across calls. Cache it to cut cost and latency.
                payload["system"] = [{"type": "text", "text": system_prompt, "cache_control": {"type": "ephemeral"}}]
            else:
                payload["system"] = system_prompt
        temperature = os.getenv("LLM_TEMPERATURE")
        if temperature:
            payload["temperature"] = float(temperature)
        data = self._post_json(
            "https://api.anthropic.com/v1/messages",
            {"x-api-key": str(self.api_key), "anthropic-version": "2023-06-01", "content-type": "application/json"},
            payload,
        )
        usage = data.get("usage") or {}
        self.usage["input_tokens"] += int(usage.get("input_tokens") or 0)
        self.usage["output_tokens"] += int(usage.get("output_tokens") or 0)
        self.usage["cached_tokens"] += int(usage.get("cache_read_input_tokens") or 0)
        try:
            text = "".join(b.get("text", "") for b in data.get("content", []) if b.get("type") == "text")
        except (AttributeError, TypeError) as exc:
            raise LLMProviderError("Anthropic returned no text.") from exc
        if not text:
            raise LLMProviderError("Anthropic returned no text.")
        return text
