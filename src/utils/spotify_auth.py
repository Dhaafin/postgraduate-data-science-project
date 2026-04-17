import os
import json
import requests

def create_spotify_token():
    url = "https://accounts.spotify.com/api/token"
    
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": "Basic NTMzNzAyNjE2NjViNDk1YWEzMDk5ZDFkZTJjNGNkODM6N2EzZWM5OGJiNDk4NGE4ZGI4OTFhNzhjZjFhNGE4YmM="
    }
    
    # Note: The Spotify API expects "client_credentials" (with an 's' at the end)
    data = {
        "grant_type": "client_credentials"
    }

    print("Fetching token from Spotify API...")
    response = requests.post(url, headers=headers, data=data)
    
    if response.status_code == 200:
        token_data = response.json()
        
        # Determine path relative to this script to store the token
        base_dir = os.path.dirname(os.path.abspath(__file__))
        data_dir = os.path.normpath(os.path.join(base_dir, "../../data"))
        
        # Ensure data directory exists
        os.makedirs(data_dir, exist_ok=True)
        
        # Store the token in a JSON file where it can be used later
        token_file_path = os.path.join(data_dir, "spotify_token.json")
        with open(token_file_path, "w") as f:
            json.dump(token_data, f, indent=4)
            
        print(f"Success! Token successfully fetched and stored in: {token_file_path}")
        print(f"Access Token: {token_data.get('access_token')[:15]}...")
        
        return token_data
    else:
        print(f"Failed to get token (Status {response.status_code}): {response.text}")
        return None

if __name__ == "__main__":
    create_spotify_token()
