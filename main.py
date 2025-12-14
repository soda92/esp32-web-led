import machine
import time
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

def main():
    print("Init System...")
    epd.init()

    server = None

    # Try to connect
    if wifi_manager.connect():
        led_manager.led_syncing()
        time_manager.sync()
        weather_api.update()
        
        # Start Web Server
        server = web_server.setup()
        
        led_manager.led_off()

    # Initial Draw
    time_str, date_str, _ = time_manager.get_local_time()
    display_ui.draw_screen(epd, time_str, date_str, web_server.custom_message)

    last_time_str = time_str
    last_msg_str = web_server.custom_message

    while True:
        # --- LOOP REACTION: Heartbeat ---
        led_manager.led_heartbeat()

        # Check Web Server frequently (during the 5s sleep)
        # Instead of one big sleep(4.9), we slice it up
        for _ in range(50): # 50 * 0.1s = 5 seconds
            if server:
                web_server.check(server)
            time.sleep(0.1)
            
            # Immediate update if message changes
            if web_server.custom_message != last_msg_str:
                print("Message Changed!")
                last_msg_str = web_server.custom_message
                # Trigger update
                t_str, d_str, _ = time_manager.get_local_time()
                display_ui.draw_screen(epd, t_str, d_str, last_msg_str)
                led_manager.led_web_request()

        t_str, d_str, sec = time_manager.get_local_time()

        if t_str != last_time_str:
            # --- LOOP REACTION: Update Start ---
            led_manager.led_minute_update()

            last_time_str = t_str

            # If weather updates, it might take longer
            if time.time() - weather_api.cache["last_update"] >= 900:
                led_manager.led_web_request()

            weather_api.update()
            display_ui.draw_screen(epd, t_str, d_str, web_server.custom_message)

            # --- LOOP REACTION: Update Done ---
            led_manager.led_off()

if __name__ == "__main__":
    main()