# -*- coding: utf-8 -*-
"""Configurable LLM client for OpenAI, Gemini, Groq and Anthropic.

The mock provider runs only when LLM_PROVIDER=mock is set on purpose. With no
provider and no key the client raises LLMNotConfiguredError. It never invents
business data.
"""

from __future__ import annotations

import json
import logging
import os
import re
import time
from typing import Any, Dict, Optional

import requests

log = logging.getLogger("agent_reach.discovery")

# Override any default with LLM_MODEL or the dashboard setting. These names
# were not checked against each vendor's live model list.
DEFAULT_MODELS = {
    "openai": "gpt-4o",
    "gemini": "gemini-2.5-flash",
    "groq": "llama-3.3-70b-versatile",
    "anthropic": "claude-sonnet-5-5",
    "deepseek": "deepseek-chat",
}
_KEY_ENV = {
    "groq": "GROQ_API_KEY",
    "openai": "OPENAI_API_KEY",
    "gemini": "GEMINI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "deepseek": "DEEPSEEK_API_KEY",
}
_TIMEOUT_SECONDS = 60
_RETRY_STATUS = {429, 500, 502, 503, 504}


class LLMProviderError(RuntimeError):
    """Raised when a configured provider fails."""


class LLMNotConfiguredError(LLMProviderError):
    """Raised when no provider or API key is available."""


class LLMClient:
    """Small provider switch with explicit failure."""

    def __init__(
        self,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
    ):
        chosen = (provider or os.getenv("LLM_PROVIDER") or "").strip().lower()
        if not chosen:
            # Pick the first provider that has a key. Leave empty when none does.
            for name in ("groq", "openai", "gemini", "anthropic", "deepseek"):
                if self._resolve_api_key(name):
                    chosen = name
                    break
        self.provider = chosen

        self.api_key = api_key or None
        if not self.api_key and self.provider:
            self.api_key = self._resolve_api_key(self.provider) or os.getenv("LLM_API_KEY")

        self.model = model or os.getenv("LLM_MODEL") or DEFAULT_MODELS.get(self.provider)

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
        # Check ~/.agent-reach/config.yaml
        try:
            from agent_reach.config import Config
            cfg = Config(read_only=True)
            return cfg.get(f"{provider}_api_key") or cfg.get(f"{provider}-key")
        except Exception:
            return None

    @property
    def is_configured(self) -> bool:
        if self.provider == "mock":
            return True
        return bool(self.provider in DEFAULT_MODELS and self.api_key)

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
                "No LLM is configured. Set LLM_PROVIDER (openai, gemini, groq, anthropic, deepseek) "
                "and an API key, or choose a provider in Settings."
            )
        if self.provider not in DEFAULT_MODELS:
            raise LLMProviderError(f"Unsupported LLM provider: {self.provider}")
        if not self.api_key:
            raise LLMNotConfiguredError(f"Provider '{self.provider}' has no API key.")

        if self.provider == "openai":
            return self._call_openai_compatible(prompt, system_prompt, json_mode, base_url=None)
        if self.provider == "groq":
            return self._call_openai_compatible(prompt, system_prompt, json_mode, base_url="groq")
        if self.provider == "deepseek":
            return self._call_openai_compatible(prompt, system_prompt, json_mode, base_url="https://api.deepseek.com")
        if self.provider == "gemini":
            return self._call_gemini(prompt, system_prompt, json_mode)
        return self._call_anthropic(prompt, system_prompt, json_mode)

    def complete_json(self, prompt: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        """Request a JSON object. Retries once when the reply is not valid JSON."""
        json_system = ((system_prompt or "") + "\nRespond ONLY with a valid JSON object. No commentary.").strip()
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

    def _call_openai_compatible(
        self, prompt: str, system_prompt: Optional[str], json_mode: bool, base_url: Optional[str]
    ) -> str:
        try:
            if base_url == "groq":
                try:
                    from groq import Groq

                    client = Groq(api_key=self.api_key, timeout=_TIMEOUT_SECONDS, max_retries=2)
                except ImportError:
                    from openai import OpenAI

                    client = OpenAI(
                        api_key=self.api_key,
                        base_url="https://api.groq.com/openai/v1",
                        timeout=_TIMEOUT_SECONDS,
                        max_retries=2,
                    )
            else:
                from openai import OpenAI

                target_base_url = base_url or os.getenv("OPENAI_BASE_URL")
                client_kwargs: Dict[str, Any] = {
                    "api_key": self.api_key,
                    "timeout": _TIMEOUT_SECONDS,
                    "max_retries": 2,
                }
                if target_base_url:
                    client_kwargs["base_url"] = target_base_url
                client = OpenAI(**client_kwargs)

            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            kwargs: Dict[str, Any] = {"model": self.model, "messages": messages}
            if json_mode:
                kwargs["response_format"] = {"type": "json_object"}
            resp = client.chat.completions.create(**kwargs)
            return resp.choices[0].message.content or ""
        except ImportError as exc:
            raise LLMProviderError(f"Install the '{self.provider}' package: {exc}") from exc
        except Exception as exc:  # SDK errors vary by vendor
            raise LLMProviderError(f"{self.provider} request failed: {type(exc).__name__}: {str(exc)[:300]}") from exc

    def _post_json(self, url: str, headers: Dict[str, str], payload: Dict[str, Any]) -> Dict[str, Any]:
        last = ""
        for attempt in range(3):
            try:
                resp = requests.post(url, json=payload, headers=headers, timeout=_TIMEOUT_SECONDS)
            except requests.RequestException as exc:
                last = type(exc).__name__
            else:
                if resp.status_code == 200:
                    return resp.json()
                last = f"http {resp.status_code}: {resp.text[:300]}"
                if resp.status_code not in _RETRY_STATUS:
                    break
            time.sleep(1.5 * (attempt + 1))
        raise LLMProviderError(f"{self.provider} request failed ({last})")

    def _call_gemini(self, prompt: str, system_prompt: Optional[str], json_mode: bool) -> str:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"
        payload: Dict[str, Any] = {"contents": [{"parts": [{"text": prompt}]}]}
        if system_prompt:
            payload["systemInstruction"] = {"parts": [{"text": system_prompt}]}
        if json_mode:
            payload["generationConfig"] = {"responseMimeType": "application/json"}
        data = self._post_json(
            url, {"Content-Type": "application/json", "x-goog-api-key": str(self.api_key)}, payload
        )
        try:
            candidate = data.get("candidates", [{}])[0]
            parts = candidate.get("content", {}).get("parts", [])
            # Filter out thinking parts if present, extract actual text
            text_parts = [p.get("text", "") for p in parts if not p.get("thought") and p.get("text")]
            if not text_parts:
                text_parts = [p.get("text", "") for p in parts if p.get("text")]
            result_text = "".join(text_parts).strip()
            if not result_text:
                raise LLMProviderError("Gemini returned no text (blocked or empty).")
            return result_text
        except (KeyError, IndexError, TypeError) as exc:
            raise LLMProviderError("Gemini returned no text (blocked or empty).") from exc

    def _call_anthropic(self, prompt: str, system_prompt: Optional[str], json_mode: bool = False) -> str:
        payload: Dict[str, Any] = {
            "model": self.model,
            "max_tokens": 8192,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system_prompt:
            payload["system"] = system_prompt
        data = self._post_json(
            "https://api.anthropic.com/v1/messages",
            {
                "x-api-key": str(self.api_key),
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            payload,
        )
        try:
            return "".join(b.get("text", "") for b in data.get("content", []) if b.get("type") == "text")
        except (KeyError, TypeError) as exc:
            raise LLMProviderError("Anthropic returned no text.") from exc
