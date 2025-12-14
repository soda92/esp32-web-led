import usocket
import uasyncio

class DNSServer:
    def __init__(self, ip):
        self.ip = ip
        self.sock = usocket.socket(usocket.AF_INET, usocket.SOCK_DGRAM)
        self.sock.setblocking(False)
        self.sock.bind(('', 53))

    async def run(self):
        print(f"DNS Server listening on 53 (Hijacking to {self.ip})")
        while True:
            try:
                data, addr = self.sock.recvfrom(1024)
                # Parse Packet (Skip Header)
                # Transaction ID (2), Flags (2), Questions (2), Answers (2)...
                # Just copy ID and set Flags to Response (0x8180)
                
                # Minimum DNS Packet
                if len(data) < 12: continue
                
                # Construct Response
                # Header: ID, Flags(Response, NoError), QDCOUNT=1, ANCOUNT=1
                response = data[:2] + b'\x81\x80' + data[4:6] + b'\x00\x01\x00\x00\x00\x00'
                
                # Question Section (Copy from request)
                # Find end of qname (0 byte)
                idx = 12
                while idx < len(data) and data[idx] != 0:
                    idx += data[idx] + 1
                idx += 5 # Skip 0 byte + QTYPE(2) + QCLASS(2)
                
                response += data[12:idx]
                
                # Answer Section
                # Name (Pointer to offset 12), TYPE(A=1), CLASS(IN=1), TTL(60), LEN(4), IP
                response += b'\xc0\x0c' # Pointer to QNAME
                response += b'\x00\x01\x00\x01' # Type A, Class IN
                response += b'\x00\x00\x00\x3c' # TTL 60s
                response += b'\x00\x04' # Data Length 4
                
                # IP Address
                response += bytes(map(int, self.ip.split('.')))
                
                self.sock.sendto(response, addr)
            except OSError:
                await uasyncio.sleep(0.1)
            except Exception as e:
                print(f"DNS Error: {e}")
                await uasyncio.sleep(1)

def start(ip):
    server = DNSServer(ip)
    uasyncio.create_task(server.run())
