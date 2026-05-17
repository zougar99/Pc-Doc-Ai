"""
PC Doctor AI - Virtual Environment Setup
Creates a Python virtual environment for the project
"""

import os
import sys
import subprocess


def create_venv():
    print("=" * 50)
    print("   PC DOCTOR AI - VIRTUAL ENVIRONMENT SETUP")
    print("=" * 50)

    venv_path = ".venv"
    python_exec = sys.executable

    if os.path.exists(venv_path):
        print(f"\n[+] Virtual environment already exists at: {venv_path}")
        activate = input("\nRecreate it? (y/n): ").strip().lower()
        if activate != 'y':
            return
        print("\n[*] Removing old virtual environment...")
        import shutil
        shutil.rmtree(venv_path)

    print(f"\n[*] Creating virtual environment at: {venv_path}")
    print(f"[*] Using Python: {python_exec}")

    try:
        subprocess.run([python_exec, "-m", "venv", venv_path], check=True)
        print("[+] Virtual environment created!")

        print("\n[*] Activating virtual environment...")

        if sys.platform == "win32":
            pip_path = os.path.join(venv_path, "Scripts", "pip.exe")
            python_path = os.path.join(venv_path, "Scripts", "python.exe")
        else:
            pip_path = os.path.join(venv_path, "bin", "pip")
            python_path = os.path.join(venv_path, "bin", "python")

        print("\n[*] Installing dependencies...")

        if os.path.exists("requirements.txt"):
            subprocess.run([pip_path, "install", "-r", "requirements.txt"], check=True)
            print("[+] Dependencies installed!")
        else:
            print("[!] requirements.txt not found!")

        print("\n" + "=" * 50)
        print("   SETUP COMPLETE!")
        print("=" * 50)
        print(f"\nTo activate the virtual environment:")
        if sys.platform == "win32":
            print(f"   .venv\\Scripts\\activate")
        else:
            print(f"   source .venv/bin/activate")
        print("\nTo run PC Doctor AI:")
        print(f"   python main.py --quick")
        print("=" * 50)

    except Exception as e:
        print(f"\n[!] Error: {e}")
        print("\nAlternative: Create venv manually with:")
        print("   python -m venv .venv")
        print("   .venv\\Scripts\\activate")
        print("   pip install -r requirements.txt")


def activate_venv():
    """Check and activate virtual environment"""
    if sys.platform == "win32":
        venv_python = ".venv\\Scripts\\python.exe"
    else:
        venv_python = ".venv/bin/python"

    if os.path.exists(venv_python):
        return venv_python
    return None


if __name__ == "__main__":
    create_venv()