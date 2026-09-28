"""
Launcher for the Lead Intelligence System Web Dashboard & API.
Usage: python run_web.py
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

def stop_running_server():
    """Finds and terminates any running server on port 8000."""
    import subprocess
    import signal
    print("\n🔍 Checking for running LeadIntel servers on port 8000...")
    try:
        out = subprocess.check_output(["lsof", "-t", "-i", ":8000"]).decode("utf-8").strip()
        pids = [int(p) for p in out.splitlines() if p.strip()]
        if pids:
            for pid in pids:
                try:
                    os.kill(pid, signal.SIGTERM)
                    print(f"  ✓ Stopped process PID {pid}")
                except Exception as e:
                    print(f"  Notice for PID {pid}: {e}")
            print("✅ Server stopped successfully. Port 8000 is now released.\n")
        else:
            print("ℹ️ No server is currently running on port 8000.\n")
    except subprocess.CalledProcessError:
        print("ℹ️ No server is currently running on port 8000.\n")
    except Exception as exc:
        print(f"⚠️ Error checking port 8000: {exc}\n")


def main():
    if len(sys.argv) > 1 and sys.argv[1].lower() in ("--stop", "stop", "-s", "--kill", "kill"):
        stop_running_server()
        sys.exit(0)

    import uvicorn
    print("\n" + "═" * 60)
    print("  🚀 Lead Intelligence Mission Control Starting...")
    print("  🌐 Dashboard: http://localhost:8000")
    print("  📚 API Docs:  http://localhost:8000/docs")
    print("  ⏹  To stop:   Click 'Stop Server' in the UI or run 'python run_web.py --stop'")
    print("═" * 60 + "\n")
    uvicorn.run("backend.app.main:app", host="127.0.0.1", port=8000, reload=True)


if __name__ == "__main__":
    main()
