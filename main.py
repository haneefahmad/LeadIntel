"""
Launcher for the Lead Intelligence System Web Dashboard & API.
Usage: python main.py
URL:   http://localhost:8000
"""

from pathlib import Path
import os
import sys

ROOT = Path(__file__).resolve().parent

# Auto-switch to project .venv if available
VENV_PYTHON = ROOT / ".venv" / "bin" / "python"
if VENV_PYTHON.exists() and Path(sys.executable).resolve() != VENV_PYTHON.resolve():
    os.execv(str(VENV_PYTHON), [str(VENV_PYTHON)] + sys.argv)

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

if __name__ == "__main__":
    from run_web import main
    main()
