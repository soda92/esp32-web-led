import machine
import framebuf
import il3820
import time
import network

# --- Hardware Setup ---
spi = machine.SPI(1, baudrate=2000000, polarity=0, phase=0)
cs = machine.Pin(15, machine.Pin.OUT)
dc = machine.Pin(4, machine.Pin.OUT)
busy = machine.Pin(5, machine.Pin.IN)

epd = il3820.EPD(spi, cs, dc, busy, rst=None)

def scan_wifi():
    """Scans for WiFi networks and returns a sorted list."""
    print("Scanning for WiFi...")
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    
    # scan() returns a list of tuples: (ssid, bssid, channel, RSSI, authmode, hidden)
    networks = wlan.scan()
    
    # Sort by RSSI (Signal Strength) - stronger signal (closer to 0) first
    # RSSI is index 3 in the tuple
    networks.sort(key=lambda x: x[3], reverse=True)
    
    return networks

def main():
    print("Init Display...")
    epd.init()
    
    # 1. Clear Screen (White) to remove ghosting
    print("Clearing...")
    buf = bytearray([0xFF] * (128 * 296 // 8))
    
    # Reset pointers
    epd._command(0x4E, bytearray([0x00]))
    epd._command(0x4F, bytearray([0x00, 0x00]))
    epd.set_frame_memory(buf)
    epd.display_frame()
    
    # 2. Get Data
    nets = scan_wifi()
    print(f"Found {len(nets)} networks.")
    
    # 3. Draw UI
    fb = framebuf.FrameBuffer(buf, 128, 296, framebuf.MONO_HLSB)
    fb.fill(0xFF) # Clear buffer
    
    # Header
    fb.fill_rect(0, 0, 128, 20, 0x00) # Black bar
    fb.text("WIFI SCANNER", 15, 6, 0xFF) # White text
    
    y_pos = 25
    for n in nets:
        ssid = n[0].decode('utf-8')
        rssi = n[3]
        
        # Format: "SSID (-Signal)"
        # Truncate SSID if too long to fit
        display_text = f"{ssid[:12]} ({rssi})"
        
        fb.text(display_text, 5, y_pos, 0x00)
        y_pos += 12 # Move down for next line
        
        # Stop if we run out of screen space
        if y_pos > 280:
            break
            
    if not nets:
        fb.text("No WiFi Found", 10, 40, 0x00)

    # 4. Display
    print("Updating Display...")
    epd._command(0x4E, bytearray([0x00]))
    epd._command(0x4F, bytearray([0x00, 0x00]))
    epd.set_frame_memory(buf)
    epd.display_frame()
    
    print("Done. Sleeping...")
    epd.sleep()

if __name__ == "__main__":
    main()