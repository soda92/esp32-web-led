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

def draw_screen(epd, time_str, date_str):
    print(f"Drawing: {time_str}")
    
    # Create a buffer (128 * 296 / 8 = 4736 bytes)
    buf = bytearray(128 * 296 // 8)
    fb = framebuf.FrameBuffer(buf, 128, 296, framebuf.MONO_HLSB)
    fb.fill(0xFF) # White background

    # Top Bar (Date)
    fb.fill_rect(0, 0, 128, 24, 0x00)
    fb.text(date_str, 25, 8, 0xFF)

    # Big Time (Using Custom Scaled Font)
    # Scale 3 makes each digit 15x21 pixels
    # 5 chars (HH:MM) * 18px width = ~90px total width
    # Centered: (128 - 90) / 2 = 19
    draw_big_text(fb, time_str, 19, 40, scale=3)

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
        # Format: "10-27: 10/22 C"
        d_str, t_max, t_min = day
        line = f"{d_str}: {t_min}/{t_max}C"
        fb.text(line, 10, y_pos, 0x00)
        y_pos += 15

    # Footer (System Status)
    # Simple line at bottom
    fb.hline(0, 280, 128, 0x00)
    import gc
    mem_free = gc.mem_free() // 1024
    
    # "剩余内存" (Free Memory)
    font_zh.draw_text(fb, "剩余内存:", 5, 282)
    # Draw number after the text (4 chars * 16px = 64px offset)
    fb.text(f"{mem_free}k", 75, 285, 0x00)

    # Send to Display
    epd._command(0x4E, bytearray([0x00]))
    epd._command(0x4F, bytearray([0x00, 0x00]))
    
    epd.set_frame_memory(buf)
    epd.display_frame()
