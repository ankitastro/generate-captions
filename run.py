"""Launch the Video Caption Dashboard."""
import subprocess
import sys
from pathlib import Path

venv = Path(__file__).parent / ".venv"

if not venv.exists():
    print("Virtual environment not found. Run 'python install.py' first.")
    sys.exit(1)

streamlit = venv / ("Scripts" if sys.platform == "win32" else "bin") / "streamlit"
subprocess.run([str(streamlit), "run", "app.py"])
