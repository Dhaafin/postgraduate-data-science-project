import urllib.request
import json

def lookup_ip():
    ip = "2406:da18:1f7e:b102:4e27:cdf4:465f:f29b"
    url = f"http://ip-api.com/json/{ip}"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            print(json.dumps(data, indent=2))
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    lookup_ip()
