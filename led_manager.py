import machine
import neopixel
import time
import ujson
import os

# --- LED Configuration ---
PIN_LEDS = 9
NUM_LEDS = 4

# Modes
MODE_AUTO = 0   # System controls LEDs (Weather, Heartbeat)
MODE_MANUAL = 1 # User controls LEDs via Web

# State
GLOBAL_BRIGHTNESS = 0.1
ENABLED = True
CURRENT_MODE = MODE_AUTO
MANUAL_COLORS = [(0,0,0)] * NUM_LEDS

CONFIG_FILE = "led_config.json"

led_pin = machine.Pin(PIN_LEDS, machine.Pin.OUT)
pixels = neopixel.NeoPixel(led_pin, NUM_LEDS)

def save_state():
    try:
        data = {
            "brightness": GLOBAL_BRIGHTNESS,
            "enabled": ENABLED,
            "mode": CURRENT_MODE,
            "colors": MANUAL_COLORS
        }
        with open(CONFIG_FILE, "w") as f:
            ujson.dump(data, f)
    except Exception as e:
        print(f"Save LED Config Error: {e}")

def load_state():
    global GLOBAL_BRIGHTNESS, ENABLED, CURRENT_MODE, MANUAL_COLORS
    try:
        with open(CONFIG_FILE, "r") as f:
            data = ujson.load(f)
            GLOBAL_BRIGHTNESS = data.get("brightness", 0.1)
            ENABLED = data.get("enabled", True)
            CURRENT_MODE = data.get("mode", MODE_AUTO)
            MANUAL_COLORS = data.get("colors", [(0,0,0)] * NUM_LEDS)
    except:
        pass # Use defaults

def toggle(state):
    global ENABLED
    ENABLED = state
    save_state()
    if not ENABLED:
        pixels.fill((0,0,0))
        pixels.write()
    else:
        refresh()

def set_mode(mode):
    global CURRENT_MODE
    CURRENT_MODE = mode
    save_state()
    refresh()

def set_brightness(val):
    global GLOBAL_BRIGHTNESS
    GLOBAL_BRIGHTNESS = max(0.0, min(1.0, float(val)))
    save_state()
    refresh()

def apply_color(r, g, b):
    r = int(r * GLOBAL_BRIGHTNESS)
    g = int(g * GLOBAL_BRIGHTNESS)
    b = int(b * GLOBAL_BRIGHTNESS)
    return (r, g, b)

def refresh():
    if not ENABLED:
        pixels.fill((0,0,0))
        pixels.write()
        return

    if CURRENT_MODE == MODE_MANUAL:
        for i in range(NUM_LEDS):
            r, g, b = MANUAL_COLORS[i]
            pixels[i] = apply_color(r, g, b)
        pixels.write()

def set_manual_pixel(i, r, g, b):
    if 0 <= i < NUM_LEDS:
        MANUAL_COLORS[i] = (r, g, b)
        save_state()
    if CURRENT_MODE == MODE_MANUAL:
        refresh()

def set_led(r, g, b):
    if not ENABLED: return
    
    c = apply_color(r, g, b)
    for i in range(NUM_LEDS):
        pixels[i] = c
    pixels.write()

def led_off():
    if CURRENT_MODE == MODE_AUTO:
        set_led(0, 0, 0)

def breathe(r, g, b, cycles=1, speed=0.05):
    if CURRENT_MODE != MODE_AUTO: return
    
    for _ in range(cycles):
        for i in range(0, 101, 5):
            factor = i / 100
            set_led(int(r * factor), int(g * factor), int(b * factor))
            time.sleep(speed)
        for i in range(100, -1, -5):
            factor = i / 100
            set_led(int(r * factor), int(g * factor), int(b * factor))
            time.sleep(speed)
    led_off()

# --- System Functions ---

def led_wifi_wait():
    breathe(255, 200, 0, cycles=1, speed=0.02)

def led_wifi_success():
    for _ in range(3):
        set_led(0, 255, 0)
        time.sleep(0.1)
        set_led(0, 0, 0)
        time.sleep(0.1)

def led_wifi_fail():
    set_led(255, 0, 0)

def led_syncing():
    if CURRENT_MODE == MODE_AUTO: set_led(0, 0, 255)

def led_heartbeat():
    if CURRENT_MODE == MODE_AUTO:
        set_led(64, 64, 64) 
        time.sleep(0.1)
        led_off()

def led_minute_update():
    if CURRENT_MODE == MODE_AUTO: set_led(0, 255, 255)

def led_web_request():
    if CURRENT_MODE == MODE_AUTO: set_led(0, 0, 255)

# Init
load_state()
refresh()
