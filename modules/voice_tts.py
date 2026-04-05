# modules/voice_tts.py
import subprocess
import threading
import platform

try:
    import pyttsx3
    _engine = pyttsx3.init()
    _engine.setProperty('rate', 150)
    _engine.setProperty('volume', 0.9)
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False
    _engine = None

def speak(text: str, blocking: bool = True):
    """Speak text aloud using local TTS engine."""
    if not TTS_AVAILABLE:
        system = platform.system()
        try:
            if system == "Darwin":
                subprocess.run(["say", text], check=False, timeout=10)
            elif system == "Linux":
                subprocess.run(["espeak", text], check=False, timeout=10)
            elif system == "Windows":
                ps_cmd = f'Add-Type –AssemblyName System.Speech; (New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak("{text}")'
                subprocess.run(["powershell", "-Command", ps_cmd], check=False, timeout=10)
        except Exception as e:
            print(f"[TTS] Speak failed: {e}")
        return
    
    try:
        if blocking:
            _engine.say(text)
            _engine.runAndWait()
        else:
            def _speak_thread():
                _engine.say(text)
                _engine.runAndWait()
            t = threading.Thread(target=_speak_thread, daemon=True)
            t.start()
    except Exception as e:
        print(f"[TTS] Error: {e}")

def set_voice(voice_id: str = None):
    if not TTS_AVAILABLE:
        return
    try:
        voices = _engine.getProperty('voices')
        if voice_id:
            for v in voices:
                if voice_id in v.id:
                    _engine.setProperty('voice', v.id)
                    return
    except Exception as e:
        print(f"[TTS] Voice change failed: {e}")
