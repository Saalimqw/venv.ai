"""File and folder tools: list, organize desktop, read files, separate by category."""
import shutil
from pathlib import Path

from config import DESKTOP, USER_HOME


def _resolve_path(path: str) -> Path:
    """Resolve Desktop/Documents or full path."""
    path = path.strip()
    if path.lower() == "desktop":
        return DESKTOP
    if path.lower() == "documents":
        return USER_HOME / "Documents"
    return Path(path).expanduser().resolve()


def list_directory(path: str) -> str:
    """List contents of a directory."""
    p = _resolve_path(path)
    if not p.exists():
        return f"Path does not exist: {p}"
    if not p.is_dir():
        return f"Not a directory: {p}"
    items = []
    for c in sorted(p.iterdir()):
        kind = "DIR " if c.is_dir() else "FILE"
        items.append(f"  [{kind}] {c.name}")
    return "\n".join(items) if items else "(empty)"


def organize_desktop() -> str:
    """Organize desktop files into 'Organized Desktop' by type."""
    desktop = DESKTOP
    if not desktop.exists():
        return f"Desktop not found: {desktop}"
    organized = desktop / "Organized Desktop"
    organized.mkdir(exist_ok=True)
    subdirs = {
        "Documents": [".txt", ".doc", ".docx", ".pdf", ".xlsx", ".xls", ".csv", ".json"],
        "Images": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".svg"],
        "Videos": [".mp4", ".mkv", ".avi", ".mov", ".wmv"],
        "Audio": [".mp3", ".wav", ".flac", ".m4a"],
        "Code": [".py", ".js", ".ts", ".html", ".css", ".json", ".md"],
        "Other": [],
    }
    moved = []
    for f in desktop.iterdir():
        if f.is_file() and f.name != "desktop.ini":
            ext = f.suffix.lower()
            dest_dir = "Other"
            for name, exts in subdirs.items():
                if ext in exts:
                    dest_dir = name
                    break
            dest = organized / dest_dir
            dest.mkdir(exist_ok=True)
            dest_file = dest / f.name
            if dest_file.exists():
                base, suf = f.stem, f.suffix
                n = 1
                while dest_file.exists():
                    dest_file = dest / f"{base}_{n}{suf}"
                    n += 1
            shutil.move(str(f), str(dest_file))
            moved.append(f.name)
    return f"Organized {len(moved)} file(s) into '{organized.name}' (Documents, Images, Videos, etc.)."


def read_file(path: str, max_lines: int = 500) -> str:
    """Read text file contents."""
    p = Path(path).expanduser().resolve()
    if not p.exists():
        return f"File not found: {p}"
    if not p.is_file():
        return f"Not a file: {p}"
    try:
        with open(p, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
        if len(lines) > max_lines:
            lines = lines[:max_lines]
            return "".join(lines) + f"\n... (truncated, total lines > {max_lines})"
        return "".join(lines)
    except Exception as e:
        return f"Error reading file: {e}"


def separate_files_by_keywords(folder_path: str, categories: dict[str, list[str]]) -> str:
    """Separate files into subfolders by keyword (in filename or content)."""
    folder = _resolve_path(folder_path)
    if not folder.exists() or not folder.is_dir():
        return f"Folder not found or not a directory: {folder}"
    results = []
    for cat_name, keywords in categories.items():
        cat_dir = folder / cat_name
        cat_dir.mkdir(exist_ok=True)
        count = 0
        keywords_lower = [k.lower() for k in keywords]
        for f in list(folder.iterdir()):
            if f.is_file():
                name_lower = f.name.lower()
                content_lower = ""
                try:
                    with open(f, "r", encoding="utf-8", errors="replace") as fp:
                        content_lower = fp.read(2000).lower()
                except Exception:
                    pass
                for kw in keywords_lower:
                    if kw in name_lower or kw in content_lower:
                        dest = cat_dir / f.name
                        if dest.exists():
                            dest = cat_dir / f"{f.stem}_dup{f.suffix}"
                        shutil.move(str(f), str(dest))
                        count += 1
                        break
        results.append(f"{cat_name}: {count} file(s)")
    return "Separated files: " + "; ".join(results)


def create_folder(path: str) -> str:
    """Create a folder."""
    p = Path(path).expanduser().resolve()
    try:
        p.mkdir(parents=True, exist_ok=True)
        return f"Created folder: {p}"
    except Exception as e:
        return f"Error: {e}"
