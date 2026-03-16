"""
Voice I/O helpers.

TTS: offline via pyttsx3.
STT: offline via Vosk (requires a model folder).
"""

from __future__ import annotations

import json
import queue
import threading
from pathlib import Path


def speak(text: str) -> None:
    """Speak text out loud (offline)."""
    try:
        import pyttsx3

        engine = pyttsx3.init()
        engine.setProperty("rate", 185)
        engine.say(text)
        engine.runAndWait()
    except Exception:
        # If TTS isn't available, fail silently (CLI still works)
        return


def listen_once(model_path: str | Path, timeout_s: float = 8.0, phrase_time_s: float = 6.0) -> str:
    """
    Listen from microphone once and return recognized text.

    - model_path: Vosk model directory (download separately)
    - timeout_s: how long to wait for speech to start
    - phrase_time_s: max recording window once speech starts
    """
    from vosk import Model, KaldiRecognizer  # type: ignore
    import numpy as np  # type: ignore
    import sounddevice as sd  # type: ignore

    model_dir = Path(model_path).expanduser().resolve()
    if not model_dir.exists():
        raise FileNotFoundError(f"Vosk model not found: {model_dir}")

    model = Model(str(model_dir))
    rec = KaldiRecognizer(model, 16000)

    audio_q: "queue.Queue[bytes]" = queue.Queue()
    stop_flag = threading.Event()

    def callback(indata, frames, time, status):  # noqa: ANN001
        if status:
            return
        if stop_flag.is_set():
            return
        # Convert float32 -> int16 bytes
        pcm16 = (indata[:, 0] * 32767.0).astype(np.int16).tobytes()
        audio_q.put(pcm16)

    text_parts: list[str] = []

    with sd.InputStream(
        samplerate=16000,
        channels=1,
        dtype="float32",
        callback=callback,
    ):
        # Wait for some audio
        try:
            first = audio_q.get(timeout=timeout_s)
        except queue.Empty as e:
            raise TimeoutError("No speech detected (timeout).") from e

        # Process initial chunk
        if rec.AcceptWaveform(first):
            res = json.loads(rec.Result() or "{}")
            if res.get("text"):
                text_parts.append(res["text"])

        # Continue for phrase_time_s
        import time as _time

        end_at = _time.time() + phrase_time_s
        while _time.time() < end_at:
            try:
                chunk = audio_q.get(timeout=0.25)
            except queue.Empty:
                continue
            if rec.AcceptWaveform(chunk):
                res = json.loads(rec.Result() or "{}")
                if res.get("text"):
                    text_parts.append(res["text"])

        stop_flag.set()
        final = json.loads(rec.FinalResult() or "{}")
        if final.get("text"):
            text_parts.append(final["text"])

    return " ".join([t for t in text_parts if t]).strip()

