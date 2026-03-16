"""
Download a small Vosk English model into ./models/.

Run:
  python download_vosk_model.py
"""

from __future__ import annotations

import io
import zipfile
from pathlib import Path

import httpx


MODEL_URL = "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip"
DEST_DIR = Path(__file__).resolve().parent / "models"


def main() -> int:
    DEST_DIR.mkdir(exist_ok=True)
    print("Downloading Vosk model...")
    with httpx.Client(timeout=httpx.Timeout(120.0, connect=10.0), follow_redirects=True) as client:
        r = client.get(MODEL_URL)
        r.raise_for_status()
        data = r.content

    print("Extracting...")
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        z.extractall(DEST_DIR)

    print("Done. Model folder is in ./models/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

