import framebuf
import weather_api
import font_zh

# 5x7 bit patterns for numbers 0-9 and :
# Each tuple is 7 rows of 5 bits
BIG_DIGITS = {
    '0': (0x0E, 0x11, 0x13, 0x15, 0x19, 0x11, 0x0E),
    '1': (0x04, 0x0C, 0x04, 0x04, 0x04, 0x04, 0x0E),
    '2': (0x0E, 0x11, 0x01, 0x02, 0x04, 0x08, 0x1F),
    '3': (0x0E, 0x11, 0x01, 0x06, 0x01, 0x11, 0x0E),
    '4': (0x02, 0x06, 0x0A, 0x12, 0x1F, 0x02, 0x02),
    '5': (0x1F, 0x10, 0x1E, 0x01, 0x01, 0x11, 0x0E),
    '6': (0x06, 0x08, 0x10, 0x1E, 0x11, 0x11, 0x0E),
    '7': (0x1F, 0x01, 0x02, 0x04, 0x08, 0x08, 0x08),
    '8': (0x0E, 0x11, 0x11, 0x0E, 0x11, 0x11, 0x0E),
    '9': (0x0E, 0x11, 0x11, 0x0F, 0x01, 0x02, 0x0C),
    ':': (0x00, 0x0C, 0x0C, 0x00, 0x0C, 0x0C, 0x00),
    ' ': (0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00),
}

def draw_big_char(fb, char, x, y, scale=3):
    """Draws a single character from BIG_DIGITS scaled up."""
    if char not in BIG_DIGITS: return
    
    pattern = BIG_DIGITS[char]
    for row_idx, row_val in enumerate(pattern):
        for col_idx in range(5): # 5 bits wide
            # Check if bit is set (from left to right: bit 4 down to 0)
            if (row_val >> (4 - col_idx)) & 1:
                # Draw a rectangle of size 'scale'
                fb.fill_rect(x + col_idx * scale, y + row_idx * scale, scale, scale, 0x00)

def draw_big_text(fb, text, x, y, scale=3):
    """Draws a string of numbers/colons."""
    cursor_x = x
    for char in text:
        draw_big_char(fb, char, cursor_x, y, scale)
        cursor_x += (6 * scale) # Advance cursor (5 width + 1 spacing)

def draw_screen(epd, time_str, date_str, message=""):
    print(f"Drawing: {time_str} Msg: {message}")
    
    # Create a buffer (128 * 296 / 8 = 4736 bytes)
    buf = bytearray(128 * 296 // 8)
    fb = framebuf.FrameBuffer(buf, 128, 296, framebuf.MONO_HLSB)
    fb.fill(0xFF) # White background

    # Top Bar (Date)
    fb.fill_rect(0, 0, 128, 24, 0x00)
    fb.text(date_str, 25, 8, 0xFF)

    # Big Time (Always Visible)
    draw_big_text(fb, time_str, 19, 40, scale=3)

    if message:
        # --- MESSAGE MODE ---
        # Draw a box
        fb.rect(5, 90, 118, 180, 0x00)
        
        # Word wrap logic is complex, so for now we just draw 
        # multiple lines if it's long (manual splitting) or just truncate.
        # Let's assume the user sends "Line1 Line2" separated by spaces or newlines?
        # Actually `font_zh` doesn't support newlines.
        
        # Simple Center Draw
        font_zh.draw_text(fb, "Message:", 10, 100)
        
        # Split by spaces to fake wrapping
        words = message.split(' ')
        y = 130
        x = 10
        for word in words:
            if x + (len(word)*16) > 118:
                x = 10
                y += 20
            font_zh.draw_text(fb, word, x, y)
            x += (len(word) * 16) + 8 # +8 for space
            
    else:
        # --- WEATHER MODE ---
        # Weather Box
        fb.rect(10, 80, 108, 60, 0x00)
        
        # Location: Beijing
        font_zh.draw_text(fb, "北京", 15, 90)
        
        # Temp
        fb.text(f"{weather_api.cache['temp']} C", 60, 94, 0x00)
        
        # Condition (Chinese)
        desc = weather_api.cache["desc"]
        font_zh.draw_text(fb, desc, 15, 115)
        
        # Forecast Section (Start at Y=150)
        y_pos = 150
        # Title: Weather Forecast
        font_zh.draw_text(fb, "天气预报", 10, y_pos)
        
        fb.hline(10, y_pos + 20, 108, 0x00)
        y_pos += 25
        
        for day in weather_api.cache.get("forecast", []):
            d_str, t_max, t_min = day
            line = f"{d_str}: {t_min}/{t_max}C"
            fb.text(line, 10, y_pos, 0x00)
            y_pos += 15

    # Footer (System Status)
    fb.hline(0, 280, 128, 0x00)
    import gc
    mem_free = gc.mem_free() // 1024
    
    font_zh.draw_text(fb, "剩余内存:", 5, 282)
    fb.text(f"{mem_free}k", 75, 285, 0x00)

    # Send to Display
    epd._command(0x4E, bytearray([0x00]))
    epd._command(0x4F, bytearray([0x00, 0x00]))
    
    epd.set_frame_memory(buf)
    epd.display_frame()
