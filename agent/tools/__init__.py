"""Tools the AI agent can use."""
from .system import run_command, clean_recycle_bin, shutdown_pc, open_url
from .files import (
    list_directory,
    organize_desktop,
    read_file,
    separate_files_by_keywords,
    create_folder,
)

__all__ = [
    "run_command",
    "clean_recycle_bin",
    "shutdown_pc",
    "open_url",
    "list_directory",
    "organize_desktop",
    "read_file",
    "separate_files_by_keywords",
    "create_folder",
]

# Tool definitions for the LLM (name, description, parameters)
TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "run_command",
            "description": "Run a safe system command or open an app. Use for: opening apps (e.g. 'code' for VS Code, 'notepad', 'explorer'), or running PowerShell/CMD commands. Avoid destructive commands.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "The command to run (e.g. 'code', 'notepad', 'explorer')"},
                    "args": {"type": "array", "items": {"type": "string"}, "description": "Optional list of arguments"},
                },
                "required": ["command"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "clean_recycle_bin",
            "description": "Empty the Windows Recycle Bin.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "open_url",
            "description": "Open a website URL in the default browser (e.g. https://instagram.com).",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "The URL to open (with or without https://)."},
                },
                "required": ["url"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "shutdown_pc",
            "description": "Shut down the PC. Optionally cancel a pending shutdown.",
            "parameters": {
                "type": "object",
                "properties": {
                    "cancel": {"type": "boolean", "description": "If true, cancel a pending shutdown. Default false."},
                    "delay_seconds": {"type": "integer", "description": "Seconds before shutdown (default 60)."},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_directory",
            "description": "List files and folders in a directory. Use to inspect Desktop, Documents, or any path.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Folder path (e.g. Desktop, Documents, or full path)."},
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "organize_desktop",
            "description": "Organize desktop files into an 'Organized Desktop' folder by file type (Documents, Images, etc.).",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read contents of a text file (e.g. .txt, .csv, .json). Use to analyze data before separating or processing.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Full path to the file."},
                    "max_lines": {"type": "integer", "description": "Max lines to read (default 500)."},
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "separate_files_by_keywords",
            "description": "In a folder, separate files into subfolders by keyword/category. E.g. separate 'Pakistan' vs 'International' clients by filename or content. Creates category folders and moves matching files.",
            "parameters": {
                "type": "object",
                "properties": {
                    "folder_path": {"type": "string", "description": "Path to the folder containing files to separate."},
                    "categories": {"type": "object", "description": "Map of category name to list of keywords (e.g. {\"Pakistan\": [\"pak\", \"pk\"], \"International\": [\"intl\", \"usa\"]}). Files whose name or content match a keyword go to that category folder."},
                },
                "required": ["folder_path", "categories"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_folder",
            "description": "Create a folder at the given path.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Full path for the new folder."},
                },
                "required": ["path"],
            },
        },
    },
]
