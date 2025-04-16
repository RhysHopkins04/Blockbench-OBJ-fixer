import sys
import subprocess
import os

# NOTE: Removed strict blender check

BUNDLED_BLENDER_PATH = os.path.join("tools", "blender-3.6.22-windows-x64", "blender.exe")

def check_python_version():
    if sys.version_info < (3, 8):
        print("[ERROR] Python 3.8+ is required.")
        sys.exit(1)
    print("[OK] Python version is compatible.")

def install_requirements():
    try:
        print("[INFO] Installing required Python packages...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("[OK] Python packages installed successfully.")
    except subprocess.CalledProcessError:
        print("[ERROR] Failed to install dependencies from requirements.txt.")
        sys.exit(1)

def main():
    print("[INFO] Running environment checks...")
    check_python_version()
    install_requirements()
    print("[SUCCESS] All checks passed. You can now run the GUI using: python gui_app.py")

if __name__ == "__main__":
    main()