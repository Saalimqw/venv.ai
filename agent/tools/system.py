"""System control tools: run commands, recycle bin, shutdown."""
import subprocess
import sys


def open_url(url: str) -> str:
    """Open a URL in the default browser (Windows)."""
    if sys.platform != "win32":
        return "open_url is supported on Windows only."
    u = (url or "").strip()
    if not u:
        return "Error: URL is empty."
    if not (u.startswith("http://") or u.startswith("https://")):
        u = "https://" + u
    try:
        subprocess.Popen(["cmd", "/c", "start", "", u], shell=False)
        return f"Opened {u}"
    except Exception as e:
        return f"Error: {e}"


def run_command(command: str, args: list[str] | None = None) -> str:
    """Run a safe system command. Opens apps or runs shell commands."""
    args = args or []
    try:
        if sys.platform == "win32":
            # Allow common apps; avoid arbitrary cmd injection
            safe_apps = {"code", "notepad", "explorer", "calc", "msedge", "chrome", "spotify", "cmd", "powershell", "pwsh"}
            cmd_lower = command.strip().lower()
            if cmd_lower in safe_apps:
                # For shells, open a NEW console window (not inside current terminal)
                if cmd_lower in {"cmd", "powershell", "pwsh"}:
                    # Most reliable on Windows: use `start` via cmd.exe
                    # This opens a new window even when parent is a terminal.
                    subprocess.Popen(
                        ["cmd", "/c", "start", "", command, *args],
                        shell=False,
                    )
                    return f"Opened a new {command} window."

                # Browsers are often not in PATH; use Windows `start` so it finds the installed app
                if cmd_lower in {"chrome", "msedge"}:
                    subprocess.Popen(["cmd", "/c", "start", "", command, *args], shell=False)
                    return f"Started {command}."

                # For GUI apps, normal spawn is fine
                subprocess.Popen([command] + args)
                return f"Started {command}."
            # Generic run (e.g. "python", "pwsh")
            result = subprocess.run(
                [command] + args,
                capture_output=True,
                text=True,
                timeout=30,
                shell=True,
            )
            out = (result.stdout or "").strip() or (result.stderr or "").strip()
            return out or f"Command finished with code {result.returncode}."
        else:
            result = subprocess.run(
                [command] + args,
                capture_output=True,
                text=True,
                timeout=30,
                shell=True,
            )
            out = (result.stdout or "").strip() or (result.stderr or "").strip()
            return out or f"Command finished with code {result.returncode}."
    except subprocess.TimeoutExpired:
        return "Command timed out."
    except Exception as e:
        return f"Error: {e}"


def clean_recycle_bin() -> str:
    """Empty the Windows Recycle Bin."""
    if sys.platform != "win32":
        return "Recycle bin cleanup is supported on Windows only."
    try:
        subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                "Clear-RecycleBin -Force -ErrorAction SilentlyContinue",
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )
        return "Recycle bin has been emptied."
    except Exception as e:
        return f"Error: {e}"


def shutdown_pc(cancel: bool = False, delay_seconds: int = 60) -> str:
    """Shut down the PC or cancel a pending shutdown."""
    if sys.platform != "win32":
        return "Shutdown is supported on Windows only."
    try:
        if cancel:
            subprocess.run(["shutdown", "/a"], capture_output=True, timeout=10)
            return "Shutdown cancelled."
        subprocess.run(
            ["shutdown", "/s", "/t", str(max(0, min(delay_seconds, 600)))],
            capture_output=True,
            timeout=10,
        )
        return f"Shutdown scheduled in {delay_seconds} seconds. Say 'cancel shutdown' to cancel."
    except Exception as e:
        return f"Error: {e}"
