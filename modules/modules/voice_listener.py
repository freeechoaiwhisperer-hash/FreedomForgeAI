# modules/voice_listener.py
import pyaudio
import json
import threading
import queue
import os
import sys
from vosk import Model, KaldiRecognizer

_listener_thread = None
_stop_event = None
_audio_queue = None
_recognizer = None
_stream = None
_pyaudio_instance = None
_wake_word = "hey freedom"
_command_callback = None
_is_listening = False
_is_initialized = False

def init(model_path: str = "ghost/voice/vosk-model-small-en-us-0.15", wake_word: str = "hey freedom"):
    global _recognizer, _pyaudio_instance, _stream, _wake_word, _is_initialized
    _wake_word = wake_word.lower()
    
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Vosk model not found at {model_path}")
    
    try:
        model = Model(model_path)
        _recognizer = KaldiRecognizer(model, 16000)
        _recognizer.SetWords(False)

        _pyaudio_instance = pyaudio.PyAudio()
        _stream = _pyaudio_instance.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=16000,
            input=True,
            frames_per_buffer=8000,
        )
        _is_initialized = True
        print("[Voice] Initialization successful")
    except Exception as e:
        print(f"[Voice] Init failed: {e}")
        raise

def start_listening(callback):
    global _listener_thread, _stop_event, _audio_queue, _command_callback, _is_listening
    if not _is_initialized:
        raise RuntimeError("Voice listener not initialized. Call init() first.")
    
    if _is_listening:
        print("[Voice] Already listening")
        return
    
    _stop_event = threading.Event()
    _audio_queue = queue.Queue()
    _command_callback = callback
    _is_listening = True
    _listener_thread = threading.Thread(target=_listen_loop, daemon=True)
    _listener_thread.start()
    print("[Voice] Listening started")

def stop_listening():
    global _stop_event, _listener_thread, _is_listening
    if not _is_listening:
        print("[Voice] Not listening")
        return
    
    if _stop_event:
        _stop_event.set()
    if _listener_thread:
        _listener_thread.join(timeout=2.0)
    
    _is_listening = False
    print("[Voice] Listening stopped")

def cleanup():
    global _stream, _pyaudio_instance, _is_initialized
    stop_listening()
    if _stream:
        try:
            _stream.stop_stream()
            _stream.close()
        except:
            pass
    if _pyaudio_instance:
        try:
            _pyaudio_instance.terminate()
        except:
            pass
    _is_initialized = False
    print("[Voice] Cleanup complete")

def is_listening():
    return _is_listening

def _listen_loop():
    global _recognizer, _stream, _stop_event, _command_callback, _wake_word
    wake_detected = False
    
    while not _stop_event.is_set():
        try:
            data = _stream.read(4000, exception_on_overflow=False)
        except Exception as e:
            print(f"[Voice] Audio read error: {e}")
            continue
        
        if _recognizer.AcceptWaveform(data):
            try:
                res = json.loads(_recognizer.Result())
                text = res.get("text", "").lower().strip()
                
                if not wake_detected:
                    if _wake_word in text:
                        wake_detected = True
                        print(f"[Voice] Wake word detected: '{text}'")
                else:
                    if text:
                        print(f"[Voice] Command captured: '{text}'")
                        if _command_callback:
                            _command_callback(text)
                        wake_detected = False
            except json.JSONDecodeError:
                pass
