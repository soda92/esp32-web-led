import usocket
import os
import ujson

# Global State
custom_message = ""

def setup():
    s = usocket.socket(usocket.AF_INET, usocket.SOCK_STREAM)
    s.setsockopt(usocket.SOL_SOCKET, usocket.SO_REUSEADDR, 1)
    s.bind(('', 80))
    s.listen(1)
    s.settimeout(0) # Non-blocking
    print("Web Server Started on Port 80")
    return s

def send_response(client, code, content_type, body):
    header = f"HTTP/1.1 {code}\r\nContent-Type: {content_type}\r\nContent-Length: {len(body)}\r\nConnection: close\r\n\r\n"
    client.write(header.encode())
    client.write(body)

def handle_request(client):
    global custom_message
    try:
        # Read Request (First 1KB is usually enough for headers)
        request = client.read(1024)
        if not request:
            return

        req_str = request.decode('utf-8')
        method, path, _ = req_str.split(' ', 2)
        
        # --- API: Get/Set Message ---
        if path.startswith("/api/message"):
            if method == "POST":
                # Find body
                headers, body = req_str.split("\r\n\r\n", 1)
                try:
                    data = ujson.loads(body)
                    custom_message = data.get("message", "")
                    print(f"New Message: {custom_message}")
                    send_response(client, "200 OK", "application/json", '{"status": "ok"}'.encode())
                except:
                    send_response(client, "400 Bad Request", "application/json", '{"error": "invalid json"}'.encode())
            else:
                # GET
                resp = ujson.dumps({"message": custom_message})
                send_response(client, "200 OK", "application/json", resp.encode())
            return

        # --- Static File Serving ---
        if path == "/" or path == "/index.html":
            file_path = "index.html"
        else:
            # Simple security: don't allow going up directories
            file_path = path.lstrip("/")
            if ".." in file_path:
                send_response(client, "403 Forbidden", "text/plain", b"Forbidden")
                return

        # Try to serve file
        try:
            # Check if file exists
            os.stat(file_path) 
            
            # Determine content type
            ctype = "text/plain"
            if file_path.endswith(".html"):
                ctype = "text/html"
            elif file_path.endswith(".css"):
                ctype = "text/css"
            elif file_path.endswith(".js"):
                ctype = "application/javascript"
            elif file_path.endswith(".json"):
                ctype = "application/json"
            
            # Serve file (streamed in chunks to save RAM)
            client.write(f"HTTP/1.1 200 OK\r\nContent-Type: {ctype}\r\nConnection: close\r\n\r\n".encode())
            with open(file_path, "rb") as f:
                while True:
                    chunk = f.read(512)
                    if not chunk:
                        break
                    client.write(chunk)
                    
        except OSError:
            send_response(client, "404 Not Found", "text/plain", b"File Not Found")

    except Exception as e:
        print(f"Web Error: {e}")
    finally:
        client.close()

def check(server_socket):
    """Call this frequently in the main loop"""
    try:
        client, addr = server_socket.accept()
        # client.settimeout(2.0) # Give client 2s to send data
        handle_request(client)
        return True 
    except OSError:
        return False
