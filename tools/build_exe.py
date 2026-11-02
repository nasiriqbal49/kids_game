import os
import subprocess
import sys
from pathlib import Path

REPO_DIR = Path(__file__).resolve().parent.parent


def build():
    print("==================================================")
    print(" BUILDING STANDALONE KidsMotionGame.exe")
    print("==================================================")

    # 1. Ensure PyInstaller is installed
    try:
        import PyInstaller
    except ImportError:
        print("Installing PyInstaller into .venv...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)

    # 2. PyInstaller packaging command
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name=KidsMotionGame",
        "--onedir",
        "--noconsole",
        "--add-data=config.json;.",
        "--add-data=user_data;user_data",
        "main.py"
    ]

    print("Running PyInstaller...")
    subprocess.run(cmd, cwd=REPO_DIR, check=True)

    dist_path = REPO_DIR / "dist" / "KidsMotionGame"
    print("\n==================================================")
    print(" BUILD SUCCESSFUL!")
    print(f" Output folder: {dist_path}")
    print(f" Executable: {dist_path / 'KidsMotionGame.exe'}")
    print(" You can copy this folder to any Windows PC without Python!")
    print("==================================================")


if __name__ == "__main__":
    build()