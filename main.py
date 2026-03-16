"""
AI Desktop Agent — JARVIS-style assistant.

Inspired by STONIC / "I Built an AI agent That Works For Me 24/7".
Talk in natural language; the agent runs commands, organizes files, and more.
"""
import sys
import threading
import queue
import time
from pathlib import Path

# Ensure project root is on path
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:  # pyright: ignore[reportUndefinedVariable]
    sys.path.insert(0, str(ROOT))

from agent.brain import run_agent
from agent.tools import (
    clean_recycle_bin,
    list_directory,
    organize_desktop,
    open_url,
    run_command,
    shutdown_pc,
)
from voice import listen_once, speak


def _try_fastpath(user: str) -> str | None:
    u = user.strip().lower()
    if u in {"open cmd", "cmd"}:
        return run_command("cmd")
    if u in {"open powershell", "powershell"}:
        return run_command("powershell")
    if u in {"open pwsh", "pwsh"}:
        return run_command("pwsh")
    if u in {"open notepad", "notepad"}:
        return run_command("notepad")
    if u in {"open explorer", "explorer", "open file explorer"}:
        return run_command("explorer")
    if u in {"open chrome", "chrome"}:
        return run_command("chrome")
    if u in {"open edge", "edge", "open microsoft edge"}:
        return run_command("msedge")
    if u in {"open instagram", "instagram"}:
        return open_url("https://www.instagram.com")
    if u in {"open comet", "comet"}:
        # If the Comet browser isn't installed/registered, this will still open the website.
        return open_url("https://www.comet.com")
    if u in {"organize desktop", "clean desktop", "sort desktop"}:
        return organize_desktop()
    if u in {"empty recycle bin", "clear recycle bin", "clean recycle bin"}:
        return clean_recycle_bin()
    if u in {"shutdown", "shut down", "shutdown pc"}:
        return shutdown_pc(cancel=False, delay_seconds=60)
    if u in {"cancel shutdown", "abort shutdown"}:
        return shutdown_pc(cancel=True, delay_seconds=0)
    if u.startswith("list "):
        target = user.strip()[5:].strip()
        if target:
            return list_directory(target)
    return None


def main():
    print("AI Desktop Agent — type OR speak (or 'quit' to exit).")
    print("Commands: /voice on|off, /mute on|off, /talk (one-shot voice)\n")
    history = []
    voice_in = False
    voice_out = False
    vosk_model_dir = ROOT / "models" / "vosk-model-small-en-us-0.15"
    while True:
        try:
            raw = input("You (type, or press Enter to talk): ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye.")
            break
        if not raw:
            if not voice_in:
                print("Voice input is OFF. Turn it on with: /voice on", flush=True)
                continue
            try:
                print("Listening...", flush=True)
                raw = listen_once(vosk_model_dir)
                if not raw:
                    print("Heard nothing.", flush=True)
                    continue
                print(f'You (voice): {raw}', flush=True)
            except Exception as e:
                print(f"Voice error: {e}", flush=True)
                print("Tip: run `python download_vosk_model.py` once to install the speech model.", flush=True)
                continue
        user = raw
        if user.lower() in ("quit", "exit", "q"):
            print("Bye.")
            break

        if user.lower().startswith("/voice"):
            voice_in = "on" in user.lower()
            print(f"Voice input is now {'ON' if voice_in else 'OFF'}.", flush=True)
            continue
        if user.lower().startswith("/mute"):
            voice_out = not ("on" in user.lower())
            # /mute on => voice_out False; /mute off => voice_out True
            voice_out = ("off" in user.lower())
            print(f"Voice output is now {'ON' if voice_out else 'OFF'}.", flush=True)
            continue
        if user.lower().strip() == "/talk":
            voice_in = True
            print("Voice input is now ON. Press Enter at the prompt to talk.", flush=True)
            continue

        fast = _try_fastpath(user)
        if fast is not None:
            print(fast, flush=True)
            if voice_out:
                speak(fast)
            print(flush=True)
            history.append({"role": "user", "content": user})
            history.append({"role": "assistant", "content": fast})
            if len(history) > 10:
                history = history[-10:]
            continue

        print("Thinking... (max 45s) ", end="", flush=True)
        q: queue.Queue = queue.Queue()

        def _worker():
            try:
                res = run_agent(
                    user,
                    history,
                    stream_callback=lambda d: print(d, end="", flush=True),
                )
                q.put(("ok", res))
            except Exception as e:
                q.put(("err", str(e) or repr(e)))

        t = threading.Thread(target=_worker, daemon=True)
        t.start()

        hard_timeout_s = 55.0
        start = time.time()
        while True:
            try:
                status, payload = q.get(timeout=0.25)
                break
            except KeyboardInterrupt:
                print("\nCancelled.\n", flush=True)
                status, payload = ("err", "Cancelled by user (Ctrl+C).")
                break
            except queue.Empty:
                if time.time() - start > hard_timeout_s:
                    print("\nStill waiting on Groq/network. Press Ctrl+C to cancel.\n", flush=True)
                    start = time.time()  # rate-limit this message

        if status == "err":
            reply, streamed = (f"Error: {payload}", False)
        else:
            reply, streamed = payload

        if not streamed:
            print(reply, flush=True)
        if voice_out:
            speak(reply)

        print(flush=True)
        history.append({"role": "user", "content": user})
        history.append({"role": "assistant", "content": reply})
        # Keep last N exchanges to avoid huge context
        if len(history) > 10:
            history = history[-10:]


if __name__ == "__main__":
    main()
