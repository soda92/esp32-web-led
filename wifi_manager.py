import network
import led_manager
import time
import ujson
import os

# Global State
ip_address = "0.0.0.0"
is_ap_mode = False

CONFIG_FILE = "wifi.json"

def load_config():
    try:
        with open(CONFIG_FILE, "r") as f:
            return ujson.load(f)
    except:
        return None

def save_config(ssid, password):
    data = {"ssid": ssid, "password": password}
    with open(CONFIG_FILE, "w") as f:
        ujson.dump(data, f)
    print("WiFi Config Saved")

def scan_networks():
    print("Scanning networks...")
    sta = network.WLAN(network.STA_IF)
    sta.active(True)
    
    try:
        networks = sta.scan() # Returns list of tuples
    except Exception as e:
        print(f"Scan failed: {e}")
        return []
        
    # Format: (ssid, bssid, channel, RSSI, authmode, hidden)
    result = []
    for n in networks:
        ssid = n[0].decode('utf-8')
        if not ssid: continue # Skip hidden
        
        result.append({
            "ssid": ssid,
            "rssi": n[3],
            "auth": n[4] # 0=Open, other=Secure
        })
        
    # Sort by Signal Strength
    result.sort(key=lambda x: x["rssi"], reverse=True)
    return result

def start_ap():
    global ip_address, is_ap_mode
    print("Starting AP Mode...")
    is_ap_mode = True
    
    # ESP32 can do AP+STA. We ensure STA is active for scanning later.
    sta = network.WLAN(network.STA_IF)
    sta.active(True)
    
    ap = network.WLAN(network.AP_IF)
    ap.active(True)
    ap.config(essid="InkFrame-Setup", authmode=network.AUTH_OPEN)
    
    while ap.active() == False:
        pass
        
    ip_address = ap.ifconfig()[0]
    print(f"AP Started. Connect to 'InkFrame-Setup'. IP: {ip_address}")
    
    led_manager.breathe(255, 0, 255, cycles=3, speed=0.02)
    led_manager.set_led(50, 0, 50)

def connect():
    global ip_address, is_ap_mode
    
    # 1. Try to load config
    conf = load_config()
    if not conf:
        print("No WiFi Config Found.")
        start_ap()
        return False

    # 2. Try to connect
    ssid = conf.get("ssid")
    password = conf.get("password")
    
    print(f"Connecting to {ssid}...")
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    
    # Set Hostname (mDNS usually follows this)
    try:
        wlan.config(hostname="inkframe")
    except:
        pass
    
    if not wlan.isconnected():
        wlan.connect(ssid, password)

        # Wait up to 20 seconds
        for _ in range(20):
            if wlan.isconnected():
                break
            led_manager.led_wifi_wait()
            print(".")

    if wlan.isconnected():
        ip_address = wlan.ifconfig()[0]
        is_ap_mode = False
        print(f"Connected! IP: {ip_address}")
        print("Try http://inkframe.local")
        led_manager.led_wifi_success()
        return True
    else:
        print("Connection Failed.")
        led_manager.led_wifi_fail()
        start_ap() # Fallback to AP
        return False
