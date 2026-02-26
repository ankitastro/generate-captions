"""
Cross-platform installer for Video Caption Dashboard.
Usage: python install.py
Requires Python 3.9+ and ffmpeg installed on your system.
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent


def run(cmd):
    print(f"  $ {' '.join(str(c) for c in cmd)}")
    subprocess.run(cmd, check=True)


def main():
    print("=" * 50)
    print("  Video Caption Dashboard — Installer")
    print("=" * 50)

    # Check Python version
    if sys.version_info < (3, 9):
        print("\nERROR: Python 3.9 or higher is required.")
        sys.exit(1)
    print(f"\n✓ Python {sys.version_info.major}.{sys.version_info.minor}")

    # Check ffmpeg
    if shutil.which("ffmpeg"):
        print("✓ ffmpeg found")
    else:
        print("\n⚠  ffmpeg not found — it is required for audio extraction.")
        print("   Install it before running the app:")
        print("     macOS   : brew install ffmpeg")
        print("     Ubuntu  : sudo apt install ffmpeg")
        print("     Windows : https://ffmpeg.org/download.html")

    # Create virtual environment
    venv_dir = ROOT / ".venv"
    if venv_dir.exists():
        print("\n✓ Virtual environment already exists")
    else:
        print("\nCreating virtual environment...")
        run([sys.executable, "-m", "venv", str(venv_dir)])
        print("✓ Virtual environment created")

    # Resolve pip / python inside venv
    if sys.platform == "win32":
        pip = venv_dir / "Scripts" / "pip"
        python = venv_dir / "Scripts" / "python"
    else:
        pip = venv_dir / "bin" / "pip"
        python = venv_dir / "bin" / "python"

    # Install dependencies
    print("\nInstalling dependencies...")
    run([str(pip), "install", "--upgrade", "pip"])
    run([str(pip), "install", "-r", str(ROOT / "requirements.txt")])
    print("✓ Dependencies installed")

    # Create .env from .env.example if needed
    env_file = ROOT / ".env"
    env_example = ROOT / ".env.example"
    if env_file.exists():
        print("\n✓ .env already exists")
    elif env_example.exists():
        shutil.copy(env_example, env_file)
        print("\n✓ .env created from .env.example")
        print("  → Open .env and fill in your Azure API keys before running.")
    else:
        print("\n⚠  No .env found — create one with your Azure API keys.")

    print("\n" + "=" * 50)
    print("  Installation complete!")
    print("=" * 50)
    print("\nTo start the dashboard, run:")
    if sys.platform == "win32":
        print("  python run.py")
    else:
        print("  python run.py")


if __name__ == "__main__":
    main()
