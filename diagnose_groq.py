"""
Groq connectivity diagnostics.

Run:
  python diagnose_groq.py
"""

import os
import sys

import httpx
from dotenv import load_dotenv


def main() -> int:
    load_dotenv()
    key = os.getenv("GROQ_API_KEY")
    if not key:
        print("Missing GROQ_API_KEY in .env")
        return 2

    base = os.getenv("OPENAI_BASE_URL") or "https://api.groq.com/openai/v1"
    url = base.rstrip("/") + "/models"
    headers = {"Authorization": f"Bearer {key}"}

    timeout = httpx.Timeout(15.0, connect=5.0)
    try:
        with httpx.Client(timeout=timeout) as client:
            r = client.get(url, headers=headers)
        print("HTTP:", r.status_code)
        if r.status_code != 200:
            print(r.text[:500])
            return 1
        data = r.json()
        models = [m.get("id") for m in data.get("data", []) if isinstance(m, dict)]
        print("Models returned:", len(models))
        # Print a few, including Qwen if present
        show = [m for m in models if m and ("qwen" in m or "llama" in m)]
        for m in (show[:15] if show else models[:15]):
            print("-", m)
        return 0
    except httpx.TimeoutException as e:
        print("TIMEOUT talking to Groq:", e)
        return 3
    except Exception as e:
        print("ERROR talking to Groq:", repr(e))
        return 4


if __name__ == "__main__":
    raise SystemExit(main())

