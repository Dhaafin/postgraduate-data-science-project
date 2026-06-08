import socket

def test_resolve():
    host = "aws-0-ap-southeast-3.pooler.supabase.com"
    try:
        ips = socket.getaddrinfo(host, 6543, socket.AF_INET)
        print(f"IPv4 addresses for {host}:")
        for ip in ips:
            print(f"  {ip[4][0]}")
    except Exception as e:
        print(f"Error resolving IPv4 for {host}: {e}")

if __name__ == "__main__":
    test_resolve()
