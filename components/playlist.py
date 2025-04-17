import requests 

CLIENT_ID = "5c2fcd03261d47199284a7219dfc6fea"
CLIENT_SECRET = "58c0438e935348d78aa4facfc8ea8e48"

def get_access_token():
        url = "https://accounts.spotify.com/api/token"
        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }
        data = {
            "grant_type": "client_credentials"
        }
        response = requests.post(url, data=data, auth=(CLIENT_ID, CLIENT_SECRET), headers=headers)
        if response.status_code == 200:
            return response.json().get("access_token")
        else:
            print(f"Error fetching access token: {response.status_code}")
            return None

def get_playlist_tracks(playlist_id, access_token):
        url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        data = response.json()
        return data
