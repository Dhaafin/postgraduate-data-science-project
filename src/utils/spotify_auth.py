"""
Spotify Authentication Helper.
This script handles the OAuth2 client credentials flow to get an access token.
Stored tokens are saved to data/spotify_token.json for other scripts to use.
"""

import os
import json
import requests

def create_spotify_token():
    """
    Hits Spotify's token endpoint and saves the response locally.
    """
    url = "https://accounts.spotify.com/api/token"
    
    # Auth header uses the Base64 encoded 'client_id:client_secret'
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": "Basic NTMzNzAyNjE2NjViNDk1YWEzMDk5ZDFkZTJjNGNkODM6N2EzZWM5OGJiNDk4NGE4ZGI4OTFhNzhjZjFhNGE4YmM="
    }
    
    data = {
        "grant_type": "client_credentials"
    }

    print("Fetching token from Spotify API...")
    response = requests.post(url, headers=headers, data=data)
    
    if response.status_code == 200:
        token_data = response.json()
        
        # Store the token in a specific folder inside src/
        base_dir = os.path.dirname(os.path.abspath(__file__))
        # This resolves to src/token_data/
        data_dir = os.path.normpath(os.path.join(base_dir, "../token_data"))
        
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
        
        # Dump the whole response so we can check 'expires_in' later if needed
        token_file_path = os.path.join(data_dir, "spotify_token.json")
        with open(token_file_path, "w") as f:
            json.dump(token_data, f, indent=4)
            
        print(f"Success! Token stored in: {token_file_path}")
        print(f"Token snippet: {token_data.get('access_token')[:15]}...")
        
        return token_data
    else:
        print(f"Failed to get token. Status: {response.status_code}")
        print(f"Response: {response.text}")
        return None

if __name__ == "__main__":
    create_spotify_token()
