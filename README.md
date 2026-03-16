# AI Desktop Agent (JARVIS-style)

A local AI agent inspired by [*I Built an AI agent That Works For Me 24/7*](https://youtu.be/D-t3W3pDI4k) — it takes natural-language commands and automates your PC: organize desktop, run apps, clean recycle bin, separate files by category, and more.

## What it can do

- **System & apps**: Run commands, open VS Code / Notepad / Explorer, empty Recycle Bin, schedule or cancel shutdown
- **Files**: List folders (Desktop, Documents, any path), read files, create folders
- **Organize**: Organize desktop into an "Organized Desktop" folder by type (Documents, Images, Videos, etc.)
- **Separate by category**: In a folder, split files into subfolders by keywords (e.g. Pakistan vs International clients)

## Setup

1. **Python 3.10+**  
   Make sure Python is installed.

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **API key**  
   Create a `.env` file in the project folder (copy from `.env.example`).

   **Using Groq (e.g. Qwen 3 32B):**
   ```env
   GROQ_API_KEY=gsk_your-groq-key-here
   ```
   Get a key at [console.groq.com](https://console.groq.com/). The agent uses `qwen/qwen3-32b` by default.

   **Or using OpenAI:**
   ```env
   OPENAI_API_KEY=sk-your-openai-key
   MODEL=gpt-4o-mini
   ```

4. **Optional**: set a different model in `.env` (e.g. `MODEL=qwen/qwen3-32b` for Groq).

## Run

From the project folder:

```bash
python main.py
```

Then type commands in plain English, for example:

- *Organize my desktop*
- *List files on my Desktop*
- *Empty the recycle bin and shut down the PC in 60 seconds*
- *In the folder Business Docs, separate files into Pakistan and International using keywords pak and intl*
- *Open VS Code*

Type `quit` or `exit` to stop.

## Voice (optional)

This project supports **offline** voice:

- **Voice output (TTS)**: via `pyttsx3` (no API needed)
- **Voice input (STT)**: via `vosk` + `sounddevice` (requires downloading a small speech model)

### Install voice deps

```bash
pip install -r requirements.txt
```

### Download the speech model (one-time)

```bash
python download_vosk_model.py
```

### Use voice

In the app:

- Turn voice input on/off: `/voice on` or `/voice off`
- Turn voice output on/off: `/mute off` (turns voice output ON) or `/mute on` (turns it OFF)
- When voice input is ON: at the prompt, **press Enter** to talk instead of typing.

## Project layout

- `main.py` — CLI entry; chat loop
- `config.py` — API key, model, paths
- `agent/brain.py` — LLM + tool-calling loop
- `agent/tools/` — system and file tools (run_command, organize_desktop, etc.)

You can extend the agent by adding new tools in `agent/tools/` and registering them in `agent/tools/__init__.py` and `agent/brain.py`.

## Note

- Commands and file operations run on your machine; use with care.
- For browser automation (e.g. YouTube Studio, WhatsApp Web), you’d add a separate tool using Playwright or similar; the structure is ready for that.
