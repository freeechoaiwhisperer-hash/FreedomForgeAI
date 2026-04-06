# ============================================================
#  FreedomForge AI — core/api_bridge.py
#  Bridges API providers into the same interface as local models
#  so the rest of the app (chat.py, etc.) works identically.
# ============================================================

import json
import threading
from typing import Callable, Optional

import requests

from core.model_manager import PERSONALITIES
from core import logger


class APIBridge:
    """
    Wraps cloud API providers (OpenAI, Anthropic, Gemini, Groq, OpenRouter)
    behind the same generate_stream / is_available interface used by
    model_manager, so chat.py and other callers need zero changes.
    """

    # Generation parameters shared across all providers
    _TEMPERATURE = 0.85
    _TOP_P       = 0.95

    def __init__(self, provider: str, api_key: str, model: Optional[str] = None):
        self.provider = provider.lower()
        self.api_key = api_key
        self.model = model or self._default_model()

    # ── Model defaults ────────────────────────────────────────

    def _default_model(self) -> str:
        defaults = {
            "openai":      "gpt-3.5-turbo",
            "anthropic":   "claude-haiku-20240307",
            "gemini":      "gemini-1.5-flash",
            "groq":        "llama3-8b-8192",
            "openrouter":  "meta-llama/llama-3.1-8b-instruct:free",
        }
        return defaults.get(self.provider, "gpt-3.5-turbo")

    # ── Public interface (mirrors model_manager) ─────────────

    def is_available(self) -> bool:
        """Returns True if an API key is set."""
        return bool(self.api_key and self.api_key.strip())

    def generate_stream(
        self,
        messages:    list,
        personality: str = "normal",
        on_token:    Callable[[str], None] = None,
        on_complete: Callable[[], None]    = None,
        on_error:    Callable[[str], None] = None,
    ) -> None:
        """
        Stream a response from the configured provider.

        Runs in a background thread; same call signature as
        model_manager.generate_stream so chat.py needs no changes.
        """

        def _run():
            system_prompt = PERSONALITIES.get(personality, PERSONALITIES["normal"])
            _routes = {
                "openai":     self._stream_openai,
                "anthropic":  self._stream_anthropic,
                "gemini":     self._stream_gemini,
                "groq":       self._stream_groq,
                "openrouter": self._stream_openrouter,
            }
            fn = _routes.get(self.provider)
            if fn is None:
                supported = ", ".join(_routes)
                msg = (
                    f"Unknown provider '{self.provider}'. "
                    f"Supported providers: {supported}."
                )
                logger.error(msg)
                if on_error:
                    on_error(msg)
                return
            fn(messages, system_prompt, on_token, on_complete, on_error)

        threading.Thread(target=_run, daemon=True).start()

    # ── Shared OpenAI-compatible streaming helper ────────────

    def _stream_openai_compatible(
        self,
        url:          str,
        headers:      dict,
        messages:     list,
        system_prompt: str,
        on_token:     Callable[[str], None],
        on_complete:  Callable[[], None],
    ) -> None:
        """
        Core SSE streaming loop for any OpenAI-compatible endpoint.
        Raises RuntimeError on failure so the caller can produce a
        friendly error message.
        """
        full_messages = [{"role": "system", "content": system_prompt}] + messages[-30:]
        payload = {
            "model":       self.model,
            "messages":    full_messages,
            "stream":      True,
            "temperature": self._TEMPERATURE,
            "top_p":       self._TOP_P,
        }

        try:
            resp = requests.post(
                url, headers=headers, json=payload,
                stream=True, timeout=60,
            )
        except requests.exceptions.ConnectionError:
            raise RuntimeError(
                f"Could not connect to {url}. Check your internet connection."
            )
        except requests.exceptions.Timeout:
            raise RuntimeError("Request timed out. The server took too long to respond.")

        if not resp.ok:
            raise RuntimeError(
                f"API request failed (HTTP {resp.status_code}): {resp.text[:300]}"
            )

        for raw in resp.iter_lines():
            if not raw:
                continue
            line = raw.decode("utf-8") if isinstance(raw, bytes) else raw
            if not line.startswith("data: "):
                continue
            data = line[6:]
            if data == "[DONE]":
                break
            try:
                chunk   = json.loads(data)
                delta   = chunk["choices"][0].get("delta", {})
                content = delta.get("content", "")
                if content and on_token:
                    on_token(content)
            except (json.JSONDecodeError, KeyError, IndexError):
                continue

        if on_complete:
            on_complete()

    # ── OpenAI ───────────────────────────────────────────────

    def _stream_openai(self, messages, system_prompt, on_token, on_complete, on_error):
        try:
            self._stream_openai_compatible(
                url="https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type":  "application/json",
                },
                messages=messages,
                system_prompt=system_prompt,
                on_token=on_token,
                on_complete=on_complete,
            )
        except Exception as exc:
            msg = self._friendly_error("OpenAI", exc)
            logger.error(f"OpenAI stream error: {exc}")
            if on_error:
                on_error(msg)

    # ── Groq (OpenAI-compatible) ──────────────────────────────

    def _stream_groq(self, messages, system_prompt, on_token, on_complete, on_error):
        try:
            self._stream_openai_compatible(
                url="https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type":  "application/json",
                },
                messages=messages,
                system_prompt=system_prompt,
                on_token=on_token,
                on_complete=on_complete,
            )
        except Exception as exc:
            msg = self._friendly_error("Groq", exc)
            logger.error(f"Groq stream error: {exc}")
            if on_error:
                on_error(msg)

    # ── OpenRouter (OpenAI-compatible) ────────────────────────

    def _stream_openrouter(self, messages, system_prompt, on_token, on_complete, on_error):
        try:
            self._stream_openai_compatible(
                url="https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type":  "application/json",
                    "HTTP-Referer":  "https://github.com/FreedomForgeAI",
                    "X-Title":       "FreedomForge AI",
                },
                messages=messages,
                system_prompt=system_prompt,
                on_token=on_token,
                on_complete=on_complete,
            )
        except Exception as exc:
            msg = self._friendly_error("OpenRouter", exc)
            logger.error(f"OpenRouter stream error: {exc}")
            if on_error:
                on_error(msg)

    # ── Anthropic ─────────────────────────────────────────────

    def _stream_anthropic(self, messages, system_prompt, on_token, on_complete, on_error):
        """Stream from the Anthropic Messages API (claude-* models)."""
        try:
            url = "https://api.anthropic.com/v1/messages"
            headers = {
                "x-api-key":         self.api_key,
                "anthropic-version": "2023-06-01",
                "content-type":      "application/json",
            }
            # Anthropic keeps system separate; filter any system-role entries
            user_messages = [m for m in messages if m.get("role") != "system"]
            payload = {
                "model":      self.model,
                "system":     system_prompt,
                "messages":   user_messages[-30:],
                "max_tokens": 4096,
                "stream":     True,
            }

            try:
                resp = requests.post(
                    url, headers=headers, json=payload,
                    stream=True, timeout=60,
                )
            except requests.exceptions.ConnectionError:
                raise RuntimeError(
                    "Could not connect to Anthropic. Check your internet connection."
                )
            except requests.exceptions.Timeout:
                raise RuntimeError("Anthropic request timed out.")

            if not resp.ok:
                raise RuntimeError(
                    f"Anthropic API error (HTTP {resp.status_code}): {resp.text[:300]}"
                )

            for raw in resp.iter_lines():
                if not raw:
                    continue
                line = raw.decode("utf-8") if isinstance(raw, bytes) else raw
                if not line.startswith("data: "):
                    continue
                try:
                    event = json.loads(line[6:])
                    etype = event.get("type", "")
                    if etype == "content_block_delta":
                        delta = event.get("delta", {})
                        if delta.get("type") == "text_delta":
                            text = delta.get("text", "")
                            if text and on_token:
                                on_token(text)
                    elif etype == "message_stop":
                        break
                except (json.JSONDecodeError, KeyError):
                    continue

            if on_complete:
                on_complete()

        except Exception as exc:
            msg = self._friendly_error("Anthropic", exc)
            logger.error(f"Anthropic stream error: {exc}")
            if on_error:
                on_error(msg)

    # ── Gemini ────────────────────────────────────────────────

    def _stream_gemini(self, messages, system_prompt, on_token, on_complete, on_error):
        """Stream from the Google Gemini API."""
        try:
            url = (
                f"https://generativelanguage.googleapis.com/v1beta/models/"
                f"{self.model}:streamGenerateContent"
                f"?key={self.api_key}&alt=sse"
            )

            # Convert OpenAI-style messages to Gemini contents format
            contents = []
            for msg in messages[-30:]:
                role = "user" if msg.get("role") == "user" else "model"
                contents.append({
                    "role":  role,
                    "parts": [{"text": msg.get("content", "")}],
                })

            payload = {
                "system_instruction": {
                    "parts": [{"text": system_prompt}],
                },
                "contents": contents,
                "generationConfig": {
                    "temperature": self._TEMPERATURE,
                    "topP":        self._TOP_P,
                },
            }

            try:
                resp = requests.post(
                    url, json=payload,
                    stream=True, timeout=60,
                )
            except requests.exceptions.ConnectionError:
                raise RuntimeError(
                    "Could not connect to Google Gemini. Check your internet connection."
                )
            except requests.exceptions.Timeout:
                raise RuntimeError("Gemini request timed out.")

            if not resp.ok:
                raise RuntimeError(
                    f"Gemini API error (HTTP {resp.status_code}): {resp.text[:300]}"
                )

            for raw in resp.iter_lines():
                if not raw:
                    continue
                line = raw.decode("utf-8") if isinstance(raw, bytes) else raw
                if not line.startswith("data: "):
                    continue
                try:
                    chunk = json.loads(line[6:])
                    for candidate in chunk.get("candidates", []):
                        for part in candidate.get("content", {}).get("parts", []):
                            text = part.get("text", "")
                            if text and on_token:
                                on_token(text)
                except (json.JSONDecodeError, KeyError):
                    continue

            if on_complete:
                on_complete()

        except Exception as exc:
            msg = self._friendly_error("Gemini", exc)
            logger.error(f"Gemini stream error: {exc}")
            if on_error:
                on_error(msg)

    # ── Error formatting ──────────────────────────────────────

    @staticmethod
    def _friendly_error(provider: str, exc: Exception) -> str:
        """Convert an exception into a plain English error message."""
        msg = str(exc)
        low = msg.lower()
        if "401" in msg or "unauthorized" in low or "invalid api" in low or "authentication" in low:
            return (
                f"{provider}: Invalid API key. "
                "Please check your key in Settings."
            )
        if "403" in msg or "forbidden" in low:
            return (
                f"{provider}: Access denied. "
                "Your API key may not have permission for this model."
            )
        if "429" in msg or "rate limit" in low or "quota" in low:
            return (
                f"{provider}: Rate limit reached. "
                "Please wait a moment and try again."
            )
        if any(code in msg for code in ("500", "502", "503")):
            return (
                f"{provider}: Server error. "
                "The service may be temporarily unavailable — try again shortly."
            )
        if "connectionerror" in type(exc).__name__.lower() or "internet" in low:
            return (
                f"{provider}: Could not connect. "
                "Check your internet connection."
            )
        if "timed out" in low or "timeout" in type(exc).__name__.lower():
            return (
                f"{provider}: Request timed out. "
                "Try again in a moment."
            )
        return f"{provider} error: {msg}"
