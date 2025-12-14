import machine
import uasyncio
import gc
import il3820
import wifi_manager
import weather_api
import display_ui
import led_manager
import web_server
import time
import config
import sd_manager
import logger

# --- Hardware Setup (Relocated for SD Card) ---
# SCK=4, MOSI=5, CS=6, DC=7, BUSY=16
spi = machine.SPI(1, baudrate=2000000, polarity=0, phase=0, sck=machine.Pin(4), mosi=machine.Pin(5))
cs = machine.Pin(6, machine.Pin.OUT)
dc = machine.Pin(7, machine.Pin.OUT)
busy = machine.Pin(16, machine.Pin.IN)

epd = il3820.EPD(spi, cs, dc, busy, rst=None)

def get_local_time():
    now = time.time() + config.UTC_OFFSET
    tm = time.localtime(now)
    # Return (HH:MM, YYYY-MM-DD, seconds)
    return (
        "{:02d}:{:02d}".format(tm[3], tm[4]),
        "{}-{:02d}-{:02d}".format(tm[0], tm[1], tm[2]),
        tm[5],
    )

async def heartbeat_task():
    while True:
        led_manager.led_heartbeat()
        await uasyncio.sleep(5)

async def weather_task():
    while True:
        await uasyncio.sleep(900) 
        led_manager.led_web_request()
        weather_api.update()
        led_manager.led_off()
        gc.collect()

async def ui_task():
    last_time_str = ""
    last_msg_str = ""
    
    while True:
        t_str, d_str, _ = get_local_time()
        msg_str = web_server.custom_message
        
        time_changed = (t_str != last_time_str)
        msg_changed = (msg_str != last_msg_str)
        
        if time_changed or msg_changed:
            if time_changed: led_manager.led_minute_update()
            if msg_changed: led_manager.led_web_request()
            
            display_ui.draw_screen(epd, t_str, d_str, msg_str)
            led_manager.led_off()
            
            last_time_str = t_str
            last_msg_str = msg_str
            gc.collect()
        
        await uasyncio.sleep(0.1)

async def main_loop():
    logger.info("Init System...")
    
    # Init SD Card
    if sd_manager.mount_sd():
        logger.info("SD Mounted")
    else:
        logger.info("SD Mount Failed (Skipping)")
    
    epd.init()

    # Initial Connection
    if wifi_manager.connect():
        led_manager.led_syncing()
        import ntptime
        try: 
            ntptime.settime()
            logger.info("Time Synced")
        except: 
            logger.error("Time Sync Failed")
        
        weather_api.update()
        led_manager.led_off()
    else:
        # AP Mode started
        import dnserver
        dnserver.start(wifi_manager.ip_address)
    
    # Start Web Server (Background Task)
    uasyncio.create_task(web_server.start_server())
    
    uasyncio.create_task(heartbeat_task())
    uasyncio.create_task(weather_task())
    uasyncio.create_task(ui_task())
    
    logger.info(f"System Running. Free RAM: {gc.mem_free()}")
    while True:
        await uasyncio.sleep(3600)
        gc.collect()

def main():
    try:
        uasyncio.run(main_loop())
    except KeyboardInterrupt:
        print("Stopped")
    except Exception as e:
        logger.error(f"CRASH: {e}")
        # Log traceback if possible?
        # sys.print_exception(e) # to stdout
        # We can't easily capture full traceback to string in MicroPython without io.StringIO
        time.sleep(5)
        machine.reset()

if __name__ == "__main__":
    main()
