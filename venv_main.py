"""
VENV AI Main Entry Point
Run this to start the VENV AI GUI interface.
"""

import sys
from pathlib import Path

# Ensure project root is on path
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from venv_gui import main

if __name__ == "__main__":
    print("Starting VENV AI...")
    main()
