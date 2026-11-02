import subprocess
import sys
from pathlib import Path

REPO_DIR = Path(__file__).resolve().parent.parent


def build():
    print("==================================================")
    print(" PACKAGING STANDALONE MotionController.exe")
    print("==================================================")

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name=MotionController",
        "--onedir",
        "--noconsole",
        "--add-data=config.json;.",
        "tools/motion_controller_app.py"
    ]

    subprocess.run(cmd, cwd=REPO_DIR, check=True)
    dist_path = REPO_DIR / "dist" / "MotionController"
    print("\nSUCCESS! Built standalone controller to:", dist_path / "MotionController.exe")


if __name__ == "__main__":
    build()