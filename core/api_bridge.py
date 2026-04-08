# ============================================================
#  FreedomForge AI — core/api_bridge.py
#  Streaming inference via external AI API providers
#  (OpenAI-compatible SSE protocol)
# ============================================================

import json
import threading
from typing import Callable, Optional

from core import config, logger

try:
    import requests as _requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

# ── Provider base URLs ───────────────────────────────────────

_PROVIDER_URLS: dict = {
    "openai":     "https://api.openai.com/v1/chat/completions",
    "openrouter": "https://openrouter.ai/api/v1/chat/completions",
    "groq":       "https://api.groq.com/openai/v1/chat/completions",
}

_PROVIDER_DEFAULT_MODELS: dict = {
    "openai":     "gpt-4o-mini",
    "openrouter": "openai/gpt-4o-mini",
    "groq":       "llama3-8b-8192",
}

MAX_MESSAGE_HISTORY = 30  # matching model_manager.generate_stream


# ── APIBridge ────────────────────────────────────────────────

class APIBridge:
    """Thin wrapper around an OpenAI-compatible chat-completions endpoint.

    Mirrors the ``generate_stream`` interface of ``core.model_manager``
    so callers can swap between local and remote inference transparently.
    """

    def __init__(self, provider: str, api_key: str) -> None:
        self.provider = provider.lower()
        self.api_key  = api_key
        self.url      = _PROVIDER_URLS.get(
            self.provider, _PROVIDER_URLS["openai"]
        )
        self.model    = (
            config.get(f"api_model_{self.provider}")
            or _PROVIDER_DEFAULT_MODELS.get(self.provider, "gpt-4o-mini")
        )

    # ── Public streaming entry-point ─────────────────────────

    def generate_stream(
        self,
        messages:    list,
        personality: str = "normal",
        on_token:    Optional[Callable[[str], None]] = None,
        on_complete: Optional[Callable[[], None]]    = None,
        on_error:    Optional[Callable[[str], None]] = None,
    ) -> None:
        """Start streaming generation in a background thread.

        Matches the signature of ``model_manager.generate_stream`` so that
        ChatPanel can call either backend without branching on the callbacks.
        """
        threading.Thread(
            target=self._stream,
            args=(messages, personality, on_token, on_complete, on_error),
            daemon=True,
        ).start()

    # ── Internal streaming worker ────────────────────────────

    def _stream(
        self,
        messages:    list,
        personality: str,
        on_token:    Optional[Callable[[str], None]],
        on_complete: Optional[Callable[[], None]],
        on_error:    Optional[Callable[[str], None]],
    ) -> None:
        if not REQUESTS_AVAILABLE:
            if on_error:
                on_error("requests library is not installed")
            return

        from core.model_manager import PERSONALITIES

        system        = PERSONALITIES.get(personality, PERSONALITIES["normal"])
        full_messages = [{"role": "system", "content": system}] + messages[-MAX_MESSAGE_HISTORY:]

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type":  "application/json",
        }
        payload = {
            "model":       self.model,
            "messages":    full_messages,
            "stream":      True,
            "temperature": 0.85,
            "top_p":       0.95,
        }

        try:
            with _requests.post(
                self.url,
                headers=headers,
                json=payload,
                stream=True,
                timeout=60,
            ) as resp:
                if resp.status_code != 200:
                    msg = f"API error {resp.status_code}: {resp.text[:200]}"
                    logger.error(msg)
                    if on_error:
                        on_error(msg)
                    return

                for raw_line in resp.iter_lines():
                    if not raw_line:
                        continue
                    line = (
                        raw_line.decode("utf-8")
                        if isinstance(raw_line, bytes)
                        else raw_line
                    )
                    if not line.startswith("data: "):
                        continue
                    data = line[6:]
                    if data == "[DONE]":
                        break
                    try:
                        chunk   = json.loads(data)
                        content = (
                            chunk["choices"][0]
                            .get("delta", {})
                            .get("content", "")
                        )
                        if content and on_token:
                            on_token(content)
                    except (json.JSONDecodeError, KeyError, IndexError):
                        continue

            if on_complete:
                on_complete()

        except Exception as exc:
            logger.error(f"APIBridge stream error: {exc}")
            if on_error:
                on_error(str(exc))
