"""Agent brain: LLM + tool-calling loop."""
import json
import sys
from pathlib import Path

# Allow running from project root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import httpx
from openai import OpenAI

from config import API_KEY, BASE_URL, MODEL
from agent.tools import (
    TOOLS_SCHEMA,
    run_command,
    clean_recycle_bin,
    shutdown_pc,
    open_url,
    list_directory,
    organize_desktop,
    read_file,
    separate_files_by_keywords,
    create_folder,
)

# Short prompt = faster first response ("thinking" phase)
SYSTEM_PROMPT = """You are an assistant that can BOTH answer questions and control the user's PC using tools.

Rules:
- If the user asks a normal question (facts, explanations, advice), answer normally.
- If the user asks to DO something on the PC (open apps, organize files, list folders, shutdown, etc.), use the appropriate tool(s).
- If you cannot do something (e.g. browse the live web), say so and provide the best offline answer you can.

Keep replies concise (1-6 sentences)."""
SYSTEM_PROMPT += "\nAvoid emoji and non-ASCII characters in replies."

TOOL_HANDLERS = {
    "run_command": lambda **kw: run_command(kw.get("command", ""), kw.get("args")),
    "clean_recycle_bin": lambda **kw: clean_recycle_bin(),
    "shutdown_pc": lambda **kw: shutdown_pc(
        cancel=kw.get("cancel", False),
        delay_seconds=kw.get("delay_seconds", 60),
    ),
    "open_url": lambda **kw: open_url(kw.get("url", "")),
    "list_directory": lambda **kw: list_directory(kw.get("path", "")),
    "organize_desktop": lambda **kw: organize_desktop(),
    "read_file": lambda **kw: read_file(kw.get("path", ""), kw.get("max_lines", 500)),
    "separate_files_by_keywords": lambda **kw: separate_files_by_keywords(
        kw.get("folder_path", ""), kw.get("categories", {})
    ),
    "create_folder": lambda **kw: create_folder(kw.get("path", "")),
}


def run_tool(name: str, arguments: dict) -> str:
    """Execute a tool by name with given arguments."""
    if name not in TOOL_HANDLERS:
        return f"Unknown tool: {name}"
    try:
        return TOOL_HANDLERS[name](**arguments)
    except Exception as e:
        return f"Tool error: {e}"


def run_agent(
    user_message: str,
    history: list[dict] | None = None,
    stream_callback: callable | None = None,
) -> tuple[str, bool]:
    """
    Run one agent turn: send user message (and optional history) to the LLM,
    execute any tool calls, and return (final_reply, did_stream).
    If stream_callback(delta: str) is given, stream the final reply to it.
    """
    if not API_KEY:
        return "Error: No API key. Set GROQ_API_KEY=your-groq-key (or OPENAI_API_KEY) in a .env file.", False

    # 45s timeout (connect + read) so we don't hang forever
    timeout = httpx.Timeout(45.0, connect=10.0)
    client = OpenAI(api_key=API_KEY, base_url=BASE_URL or None, timeout=timeout)
    client_t = client.with_options(timeout=timeout)
    history = history or []
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        *history,
        {"role": "user", "content": user_message},
    ]
    max_tool_rounds = 5
    final_reply = ""

    try:
        for _ in range(max_tool_rounds):
            # First (or only) LLM call — no streaming so we can handle tool_calls
            response = client_t.chat.completions.create(
                model=MODEL,
                messages=messages,
                tools=TOOLS_SCHEMA,
                tool_choice="auto",
                max_tokens=1024,
            )
            choice = response.choices[0]
            msg = choice.message
            tool_calls = getattr(msg, "tool_calls", None) or []
            if not msg.content and not tool_calls:
                break
            if msg.content:
                final_reply = msg.content
            messages.append(msg)

            if not tool_calls:
                break

            for tc in tool_calls:
                fn = getattr(tc, "function", tc) if not isinstance(tc, dict) else tc.get("function", {})
                name = fn.get("name", getattr(fn, "name", "")) if isinstance(fn, dict) else getattr(fn, "name", "")
                raw_args = fn.get("arguments", getattr(fn, "arguments", None)) if isinstance(fn, dict) else getattr(fn, "arguments", None)
                try:
                    args = json.loads(raw_args or "{}")
                except (json.JSONDecodeError, TypeError):
                    args = {}
                result = run_tool(name, args)
                tc_id = tc.get("id", "") if isinstance(tc, dict) else getattr(tc, "id", "")
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tc_id,
                        "content": result,
                    }
                )

            # Second call: get final reply — stream if callback provided
            if stream_callback:
                full_content = []
                stream = client_t.chat.completions.create(
                    model=MODEL,
                    messages=messages,
                    tools=TOOLS_SCHEMA,
                    tool_choice="auto",
                    stream=True,
                )
                for chunk in stream:
                    if chunk.choices and chunk.choices[0].delta.content:
                        delta = chunk.choices[0].delta.content
                        full_content.append(delta)
                        stream_callback(delta)
                final_reply = "".join(full_content)
                messages.append({"role": "assistant", "content": final_reply})
                return final_reply or "Done.", True
            else:
                response = client_t.chat.completions.create(
                    model=MODEL,
                    messages=messages,
                    tools=TOOLS_SCHEMA,
                    tool_choice="auto",
                )
                choice = response.choices[0]
                messages.append(choice.message)
                if choice.message.content:
                    final_reply = choice.message.content
                if not choice.message.tool_calls:
                    break

        return final_reply or "Done.", False
    except Exception as e:
        err = str(e).strip() or repr(e)
        return f"API error: {err}", False
