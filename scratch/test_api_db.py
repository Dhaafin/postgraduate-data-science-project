import socket

def test_ports():
    host = "twpqzogmdzurinnwilvk.supabase.co"
    ports = [5432, 6543]
    for port in ports:
        print(f"Testing {host}:{port}...")
        try:
            # Get IPv4 address of twpqzogmdzurinnwilvk.supabase.co
            ips = socket.getaddrinfo(host, port, socket.AF_INET)
            ip = ips[0][4][0]
            print(f"  Resolved to IPv4: {ip}")
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(5)
            s.connect((ip, port))
            print(f"  SUCCESS: Connected to {host}:{port}")
            s.close()
        except Exception as e:
            print(f"  FAILED: {e}")

if __name__ == "__main__":
    test_ports()
