# ============================================================
#  FreedomForge AI — core/tts.py
#  Voice input (speech recognition) and output (TTS)
# ============================================================

import threading
from typing import Callable, Optional

try:
    import pyttsx3
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False

try:
    import speech_recognition as sr
    SR_AVAILABLE = True
except ImportError:
    SR_AVAILABLE = False

_tts_engine = None
_tts_lock   = threading.Lock()


# ── TTS (voice output) ───────────────────────────────────────

def init_tts() -> bool:
    global _tts_engine
    if not TTS_AVAILABLE:
        return False
    try:
        with _tts_lock:
            _tts_engine = pyttsx3.init()
            _tts_engine.setProperty("rate", 165)
            _tts_engine.setProperty("volume", 0.9)
        return True
    except Exception:
        _tts_engine = None
        return False


def speak(text: str) -> None:
    """Speak text in a background thread."""
    if _tts_engine is None:
        return

    def _speak():
        with _tts_lock:
            try:
                _tts_engine.say(text[:500])  # Limit length
                _tts_engine.runAndWait()
            except Exception:
                pass

    threading.Thread(target=_speak, daemon=True).start()


def tts_available() -> bool:
    return TTS_AVAILABLE and _tts_engine is not None


# ── Voice input (speech recognition) ────────────────────────

def listen(
    on_result: Callable[[str], None],
    on_error:  Callable[[str], None],
    timeout:   int = 8,
) -> None:
    """Listen for speech in a background thread."""
    if not SR_AVAILABLE:
        on_error("SpeechRecognition not installed. Run: pip install SpeechRecognition pyaudio")
        return

    def _listen():
        try:
            recognizer = sr.Recognizer()
            recognizer.energy_threshold        = 300
            recognizer.dynamic_energy_threshold = True

            with sr.Microphone() as source:
                recognizer.adjust_for_ambient_noise(source, duration=0.4)
                audio = recognizer.listen(
                    source,
                    timeout=timeout,
                    phrase_time_limit=30,
                )

            text = recognizer.recognize_google(audio)
            on_result(text)

        except sr.WaitTimeoutError:
            on_error("No speech detected")
        except sr.UnknownValueError:
            on_error("Could not understand audio")
        except sr.RequestError as e:
            on_error(f"Speech service error: {e}")
        except Exception as e:
            on_error(str(e))

    threading.Thread(target=_listen, daemon=True).start()


def sr_available() -> bool:
    return SR_AVAILABLE
