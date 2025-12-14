import uasyncio
import os
import ujson
import led_manager

# Global State
custom_message = ""

async def send_response(writer, code, content_type, body):
    header = f"HTTP/1.1 {code}\r\nContent-Type: {content_type}\r\nContent-Length: {len(body)}\r\nConnection: close\r\n\r\n"
    await writer.awrite(header.encode())
    await writer.awrite(body)

async def handle_client(reader, writer):
    global custom_message
    try:
        request = await reader.read(1024)
        if not request:
            writer.close()
            await writer.wait_closed()
            return

        req_str = request.decode('utf-8')
        try:
            method, path, _ = req_str.split(' ', 2)
        except ValueError:
            # Malformed request
            writer.close()
            await writer.wait_closed()
            return
        
        # --- API: Get/Set Message ---
        if path.startswith("/api/message"):
            if method == "POST":
                try:
                    headers, body = req_str.split("\r\n\r\n", 1)
                    data = ujson.loads(body)
                    custom_message = data.get("message", "")
                    print(f"New Message: {custom_message}")
                    await send_response(writer, "200 OK", "application/json", '{"status": "ok"}'.encode())
                except:
                    await send_response(writer, "400 Bad Request", "application/json", '{"error": "invalid json"}'.encode())
            else:
                resp = ujson.dumps({"message": custom_message})
                await send_response(writer, "200 OK", "application/json", resp.encode())
            
            writer.close()
            await writer.wait_closed()
            return
            
        # --- API: Settings (LED) ---
        if path.startswith("/api/settings"):
            if method == "POST":
                try:
                    headers, body = req_str.split("\r\n\r\n", 1)
                    data = ujson.loads(body)
                    if "led" in data:
                        led_manager.toggle(data["led"])
                    await send_response(writer, "200 OK", "application/json", '{"status": "ok"}'.encode())
                except:
                    await send_response(writer, "400 Bad Request", "application/json", '{"error": "invalid json"}'.encode())
            else:
                resp = ujson.dumps({"led": led_manager.ENABLED})
                await send_response(writer, "200 OK", "application/json", resp.encode())
                
            writer.close()
            await writer.wait_closed()
            return

        # --- Static File Serving ---
        if path == "/" or path == "/index.html":
            file_path = "index.html"
        else:
            file_path = path.lstrip("/")
            if ".." in file_path:
                await send_response(writer, "403 Forbidden", "text/plain", b"Forbidden")
                writer.close()
                await writer.wait_closed()
                return

        # Try to serve file
        try:
            os.stat(file_path) 
            
            ctype = "text/plain"
            if file_path.endswith(".html"): ctype = "text/html"
            elif file_path.endswith(".css"): ctype = "text/css"
            elif file_path.endswith(".js"): ctype = "application/javascript"
            elif file_path.endswith(".json"): ctype = "application/json"
            
            # Send Header
            # We don't send Content-Length for streamed files usually, or we calculate it first
            # Simplified header for streaming
            header = f"HTTP/1.1 200 OK\r\nContent-Type: {ctype}\r\nConnection: close\r\n\r\n"
            await writer.awrite(header.encode())
            
            # Stream file
            with open(file_path, "rb") as f:
                while True:
                    chunk = f.read(512)
                    if not chunk: break
                    await writer.awrite(chunk)
                    
        except OSError:
            await send_response(writer, "404 Not Found", "text/plain", b"File Not Found")

    except Exception as e:
        print(f"Web Error: {e}")
    finally:
        writer.close()
        await writer.wait_closed()

async def start_server():
    print("Starting Async Web Server on Port 80...")
    await uasyncio.start_server(handle_client, "0.0.0.0", 80)

