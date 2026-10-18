import os
import sys
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

def build():
    print("=" * 60)
    print("Building Personal JARVIS Standalone Windows Executable...")
    print("=" * 60)
    
    icon_path = PROJECT_ROOT / "assets" / "jarvis_icon.ico"
    main_script = PROJECT_ROOT / "main.py"
    
    cmd = [
        sys.executable,
        "-m", "PyInstaller",
        "--name=PersonalJARVIS",
        "--onedir",
        "--windowed",
        "--noconfirm",
        f"--icon={icon_path}",
        f"--add-data={PROJECT_ROOT / 'assets'}{os.pathsep}assets",
        "--collect-all=pyttsx3",
        "--collect-all=langdetect",
        "--collect-all=sounddevice",
        f"--workpath={PROJECT_ROOT / 'build'}",
        f"--distpath={PROJECT_ROOT / 'dist'}",
        str(main_script)
    ]
    
    print("Executing PyInstaller command:\n", " ".join(cmd))
    res = subprocess.run(cmd, cwd=PROJECT_ROOT)
    if res.returncode == 0:
        print("\nBuild completed successfully!")
        print(f"Distributable binary located at: {PROJECT_ROOT / 'dist' / 'PersonalJARVIS' / 'PersonalJARVIS.exe'}")
    else:
        print(f"\nBuild failed with exit code {res.returncode}")

if __name__ == "__main__":
    build()
