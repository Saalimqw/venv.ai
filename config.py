"""Configuration for the AI agent."""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# LLM — Groq (Qwen 3 32B) or OpenAI
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")  # optional override

# Use Groq if GROQ_API_KEY is set, else OpenAI
if GROQ_API_KEY:
    API_KEY = GROQ_API_KEY
    BASE_URL = OPENAI_BASE_URL or "https://api.groq.com/openai/v1"
    # Qwen 3 32B supports tool use reliably. For faster (but less reliable) use llama-3.1-8b-instant
    MODEL = os.getenv("MODEL", "qwen/qwen3-32b")
else:
    API_KEY = OPENAI_API_KEY
    BASE_URL = OPENAI_BASE_URL
    MODEL = os.getenv("MODEL", "gpt-4o-mini")

# Paths (Windows-friendly)
USER_HOME = Path(os.path.expanduser("~"))
DESKTOP = USER_HOME / "Desktop"
DOCUMENTS = USER_HOME / "Documents"

# Safe list of allowed system commands (extend as needed)
ALLOWED_COMMANDS = {
    "shutdown": ["shutdown", "/s", "/t", "60"],
    "shutdown_cancel": ["shutdown", "/a"],
    "recycle_bin": "explorer",  # open recycle bin; cleanup via PowerShell
}
