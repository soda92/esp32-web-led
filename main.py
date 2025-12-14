import machine
import uasyncio
import il3820
import wifi_manager
import time_manager
import weather_api
import display_ui
import led_manager
import web_server

# --- Hardware Setup ---
spi = machine.SPI(1, baudrate=2000000, polarity=0, phase=0)
cs = machine.Pin(15, machine.Pin.OUT)
dc = machine.Pin(4, machine.Pin.OUT)
busy = machine.Pin(5, machine.Pin.IN)

epd = il3820.EPD(spi, cs, dc, busy, rst=None)

async def heartbeat_task():
    """Flashes LED every 5 seconds"""
    while True:
        led_manager.led_heartbeat()
        await uasyncio.sleep(5)

async def weather_task():
    """Updates weather every 15 minutes"""
    while True:
        # Check cache inside weather_api to respect 15m limit, 
        # but here we just sleep to be safe.
        # Initial update happens in main setup.
        await uasyncio.sleep(900) # 15 mins
        
        print("Updating Weather (Async)...")
        led_manager.led_web_request()
        # weather_api.update() is blocking (socket). 
        # In a perfect world we'd make it async, but for now 1s blocking every 15m is fine.
        weather_api.update()
        led_manager.led_off()

async def ui_task():
    """Updates the screen when Time changes OR Message changes"""
    last_time_str = ""
    last_msg_str = ""
    
    while True:
        t_str, d_str, _ = time_manager.get_local_time()
        msg_str = web_server.custom_message
        
        # Check for changes
        time_changed = (t_str != last_time_str)
        msg_changed = (msg_str != last_msg_str)
        
        if time_changed or msg_changed:
            if time_changed:
                led_manager.led_minute_update()
            if msg_changed:
                led_manager.led_web_request()
            
            display_ui.draw_screen(epd, t_str, d_str, msg_str)
            led_manager.led_off()
            
            last_time_str = t_str
            last_msg_str = msg_str
        
        # Check every 100ms for fast UI response
        await uasyncio.sleep(0.1)

async def main_loop():
    print("Init System...")
    epd.init()

    # Initial Connection (Blocking is fine here)
    if wifi_manager.connect():
        led_manager.led_syncing()
        time_manager.sync()
        weather_api.update()
        led_manager.led_off()
    
    # Start Web Server
    # start_server() creates a task automatically
    await web_server.start_server()
    
    # Create other tasks
    uasyncio.create_task(heartbeat_task())
    uasyncio.create_task(weather_task())
    uasyncio.create_task(ui_task())
    
    print("System Running...")
    # Keep main alive
    while True:
        await uasyncio.sleep(3600)

def main():
    try:
        uasyncio.run(main_loop())
    except KeyboardInterrupt:
        print("Stopped")

if __name__ == "__main__":
    main()
