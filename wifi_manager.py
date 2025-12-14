import network
import config
import led_manager
import time

# Global State
ip_address = "0.0.0.0"

def connect():
    global ip_address
    print("Connecting to WiFi...")
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    if not wlan.isconnected():
        wlan.connect(config.WIFI_SSID, config.WIFI_PASS)

        # Wait up to 20 seconds
        for _ in range(20):
            if wlan.isconnected():
                break
            # Visual feedback
            led_manager.led_wifi_wait()
            print(".")

    if wlan.isconnected():
        ip_address = wlan.ifconfig()[0]
        print(f"Connected! IP: {ip_address}")
        led_manager.led_wifi_success()
        return True
    else:
        print("WiFi Connection Failed")
        led_manager.led_wifi_fail()
        return False
