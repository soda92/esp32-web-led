import ujson
import hashlib
import os
import ubinascii

AUTH_FILE = "auth.json"
SERIAL_FILE = "serial.txt"

def hash_password(password):
    return ubinascii.hexlify(hashlib.sha256(password.encode()).digest()).decode()

def is_setup():
    return os.path.exists(AUTH_FILE)

def set_password(password):
    p_hash = hash_password(password)
    with open(AUTH_FILE, "w") as f:
        ujson.dump({"hash": p_hash}, f)
    print("Password set.")

def verify_password(password):
    if not is_setup(): return False
    try:
        with open(AUTH_FILE, "r") as f:
            data = ujson.load(f)
        return hash_password(password) == data.get("hash")
    except:
        return False

def get_serial():
    try:
        with open(SERIAL_FILE, "r") as f:
            return f.read().strip()
    except:
        return "UNKNOWN"

def factory_reset(serial_input):
    # If serial matches, delete auth.json
    real_serial = get_serial()
    if serial_input == real_serial:
        try: os.remove(AUTH_FILE)
        except: pass
        return True
    return False
