import os
import glob
import sys
import time
import shutil
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
        files.put(remote_path, f.read())

def prepare_build():
    if os.path.exists(BUILD_DIR):
        shutil.rmtree(BUILD_DIR)
    os.makedirs(BUILD_DIR)
    
    # Copy files
    sources = glob.glob("*.py") + glob.glob("*.html") + glob.glob("*.json")
    myself = os.path.basename(__file__)
    if myself in sources:
        sources.remove(myself)
        
    for src in sources:
        shutil.copy(src, os.path.join(BUILD_DIR, src))
        
    return sources

def clean_board(board):
    print("Cleaning board (removing .mpy garbage)...")
    files = Files(board)
    try:
        board_files = files.ls()
        for f in board_files:
            f = f.strip().lstrip("/")
            # Delete any .mpy file found
            if f.endswith(".mpy"):
                print(f"Deleting obsolete: {f}")
                try: files.rm(f)
                except: pass
    except Exception as e:
        print(f"Error listing files: {e}")

def main():
    if not os.path.exists(PORT):
        print(f"Error: Device {PORT} not found.")
        return

    print("Preparing Build Directory...")
    prepare_build()
    
    # 1. Compile Fonts (Source Gen)
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
        # 2. Clean old .mpy files
        clean_board(pyb)
        
        # 3. Upload Source Files
        files_to_upload = glob.glob(os.path.join(BUILD_DIR, "*"))
        
        # Add font binary
        if os.path.exists(os.path.join(BUILD_DIR, "font_data.bin")):
            if os.path.join(BUILD_DIR, "font_data.bin") not in files_to_upload:
                files_to_upload.append(os.path.join(BUILD_DIR, "font_data.bin"))
        
        for local_path in files_to_upload:
            filename = os.path.basename(local_path)
            if filename == "compile_font.py":
                continue
            
            flash_file(pyb, local_path, filename)

        print("Upload complete.")

        # 4. Soft Reset
        print("Resetting board...")
        pyb.exit_raw_repl()
        pyb.serial.write(b"\x04")

        # 5. Monitor Output
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
    import subprocess # Import missing module
    main()
