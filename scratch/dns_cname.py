import socket

def test_dns():
    # Let's resolve the host name using socket.getaddrinfo to see the canonical name
    host = "db.twpqzogmdzurinnwilvk.supabase.co"
    try:
        # We look up the host with socket.AI_CANONNAME to see where it points
        res = socket.getaddrinfo(host, 5432, socket.AF_UNSPEC, socket.SOCK_STREAM, 0, socket.AI_CANONNAME)
        for r in res:
            print(f"Family: {r[0]}, CanonName: {r[3]}, Address: {r[4]}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_dns()
