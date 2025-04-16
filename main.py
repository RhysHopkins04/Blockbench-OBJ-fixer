import subprocess
import sys
import os

def run_setup():
    print("[INFO] Running setup checks...")
    result = subprocess.call([sys.executable, "setup.py"])
    if result != 0:
        print("[ERROR] Setup failed. Please fix the issues above.")
        sys.exit(1)

def launch_gui():
    print("[INFO] Launching Blockbench-OBJ-Fixer GUI...")
    subprocess.call([sys.executable, "gui_app.py"])

if __name__ == "__main__":
    run_setup()
    launch_gui()
