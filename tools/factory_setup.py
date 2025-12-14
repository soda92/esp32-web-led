import random
import string

SERIAL_FILE = "serial.txt"

def generate():
    if not os.path.exists(SERIAL_FILE):
        # Generate SN-XXXX-XXXX
        chars = string.ascii_uppercase + string.digits
        suffix = ''.join(random.choice(chars) for _ in range(8))
        serial = f"SN-{suffix}"
        
        with open(SERIAL_FILE, "w") as f:
            f.write(serial)
        print(f"Generated Serial: {serial}")
    else:
        print("Serial already exists.")

if __name__ == "__main__":
    import os
    generate()
