import os
import glob
import sys
import time
import shutil
import subprocess
from ampy.pyboard import Pyboard
from ampy.files import Files

# Configuration
PORT = "/dev/esp32"
BAUD = 115200
BUILD_DIR = "build"

def flash_file(board, local_path, remote_path):
    print(f"Uploading {remote_path}...")
    files = Files(board)
    with open(local_path, "rb") as f:
        # Create directory if needed (simplistic check)
        if "/" in remote_path:
            parent = remote_path.rsplit("/", 1)[0]
            try: files.mkdir(parent)
            except: pass
        files.put(remote_path, f.read())

def prepare_build():
    if os.path.exists(BUILD_DIR):
        shutil.rmtree(BUILD_DIR)
    os.makedirs(BUILD_DIR)
    
    # 1. Build Frontend
    print("Building Frontend...")
    subprocess.run(["npm", "run", "build"], cwd="frontend", check=True)
    
    # 2. Copy Source Files
    sources = glob.glob("*.py") + glob.glob("*.json")
    for src in sources:
        if src == os.path.basename(__file__): continue
        shutil.copy(src, os.path.join(BUILD_DIR, src))
        
    # 3. Copy Microdot Lib
    # Find it dynamically or hardcode path found earlier
    microdot_path = ".venv/lib/python3.13/site-packages/microdot/microdot.py"
    if os.path.exists(microdot_path):
        shutil.copy(microdot_path, os.path.join(BUILD_DIR, "microdot.py"))
    else:
        print("Warning: microdot.py not found!")

    # 4. Copy WWW (Static Assets)
    if os.path.exists("www"):
        shutil.copytree("www", os.path.join(BUILD_DIR, "www"))

def clean_board(board):
    print("Cleaning board (removing obsolete)...")
    files = Files(board)
    try:
        # Recursive delete is hard with ampy, just delete top level .py/.mpy
        board_files = files.ls()
        for f in board_files:
            f = f.strip().lstrip("/")
            if f.endswith(".mpy") or f.endswith(".py"):
                # Don't delete boot.py if we are not uploading it (we aren't)
                if f == "boot.py": continue
                try: files.rm(f)
                except: pass
    except:
        pass

def upload_recursive(board, local_dir, remote_prefix=""):
    files_to_upload = glob.glob(os.path.join(local_dir, "*"))
    for local_path in files_to_upload:
        filename = os.path.basename(local_path)
        if filename == "compile_font.py": continue
        
        remote_path = os.path.join(remote_prefix, filename)
        
        if os.path.isdir(local_path):
            upload_recursive(board, local_path, remote_path)
        else:
            flash_file(board, local_path, remote_path)

def main():
    if not os.path.exists(PORT):
        print(f"Error: Device {PORT} not found.")
        return

    print("Preparing Build Directory...")
    prepare_build()
    
    print("Compiling Fonts...")
    subprocess.run([sys.executable, "compile_font.py"], cwd=BUILD_DIR, check=True)
    
    # Prepare board connection
    try:
        pyb = Pyboard(PORT, baudrate=BAUD)
        pyb.enter_raw_repl()
    except Exception as e:
        print(f"Error connecting to board: {e}")
        return

    try:
        # Clean Source Files (Code)
        clean_board(pyb)
        
        # Upload Everything
        print("Uploading Files...")
        upload_recursive(pyb, BUILD_DIR)

        print("Upload complete.")
        print("Resetting board...")
        pyb.exit_raw_repl()
        pyb.serial.write(b"\x04")

        print("--- Serial Output (Monitoring for 10s) ---")
        start_time = time.time()
        while time.time() - start_time < 10:
            if pyb.serial.inWaiting() > 0:
                data = pyb.serial.read(pyb.serial.inWaiting())
                sys.stdout.write(data.decode("utf-8", errors="replace"))
                sys.stdout.flush()
            time.sleep(0.1)
        print("\nDone.")

    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        print(f"\nError: {e}")
    finally:
        pyb.close()

if __name__ == "__main__":
    main()