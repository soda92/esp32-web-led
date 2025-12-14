import os
import time

LOG_FILE = "system.log"
BACKUP_FILE = "system.old.log"
MAX_SIZE = 10 * 1024 # 10KB

def rotate():
    try:
        if os.stat(LOG_FILE)[6] > MAX_SIZE:
            try: os.remove(BACKUP_FILE)
            except: pass
            os.rename(LOG_FILE, BACKUP_FILE)
    except:
        pass

def write(level, message):
    try:
        rotate()
        t = time.localtime()
        ts = "{:02d}:{:02d}:{:02d}".format(t[3], t[4], t[5])
        log_line = f"[{ts}] {level}: {message}\n"
        print(log_line.strip()) # Print to serial console too
        
        with open(LOG_FILE, "a") as f:
            f.write(log_line)
    except Exception as e:
        print(f"Logging Failed: {e}")

def info(msg):
    write("INFO", msg)

def error(msg):
    write("ERROR", msg)

def debug(msg):
    # Only if needed, maybe filter
    write("DEBUG", msg)

def get_logs():
    try:
        logs = ""
        if os.path.exists(BACKUP_FILE):
            with open(BACKUP_FILE, "r") as f:
                logs += f.read()
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, "r") as f:
                logs += f.read()
        return logs
    except:
        return "Error reading logs"

def clear():
    try:
        os.remove(LOG_FILE)
        os.remove(BACKUP_FILE)
    except:
        pass
