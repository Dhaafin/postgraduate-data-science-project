import urllib.request
import urllib.error

def get_region():
    url = "https://twpqzogmdzurinnwilvk.supabase.co/rest/v1/"
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as response:
            headers = response.info()
            for k, v in headers.items():
                print(f"  {k}: {v}")
    except urllib.error.HTTPError as e:
        print("HTTPError Headers:")
        for k, v in e.headers.items():
            print(f"  {k}: {v}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    get_region()
