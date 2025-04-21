import requests
import yt_dlp
CLIENT_ID = "8b958168"

# def get_access_token():
#         url = "https://accounts.spotify.com/api/token"
#         headers = {
#             "Content-Type": "application/x-www-form-urlencoded"
#         }
#         data = {
#             "grant_type": "client_credentials"
#         }
#         response = requests.post(url, data=data, auth=(CLIENT_ID, CLIENT_SECRET), headers=headers)
#         if response.status_code == 200:
#             return response.json().get("access_token")
#         else:
#             return None


# Function to get playlist tracks
def get_pakistan_related_tracks():
    client_id = "8b958168"  # Replace with your actual client_id
    url = f"https://api.jamendo.com/v3.0/tracks"
    params = {
        "client_id": client_id,
        "format": "json",
        "tags": "love",
        "order": "popularity_total",
        "limit": 22
    }
    response = requests.get(url, params=params)
    
    return response.json()
def get_new_songs():
    client_id = "8b958168"  # Replace with your actual client_id
    url = f"https://api.jamendo.com/v3.0/tracks"
    params = {
        "client_id": client_id,
        "format": "json",
        "tags": "sad",
        "order": "popularity_total",
        "limit": 22
    }
    response = requests.get(url, params=params)
    
    return response.json()
def get_audio_info(query):
    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'noplaylist': True,
        'default_search': 'ytsearch1',
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(query, download=False)
        if 'entries' in info:
            info = info['entries'][0]

        result = {
            "title": info.get("title"),
            "artist": info.get("uploader"),
            "thumbnail": info.get("thumbnail"),
            "audio_url": info.get("url"),
            "video_url": info.get("webpage_url"),
            "duration": info.get("duration"),
        }

        return result

# Example usage
track = get_audio_info("Jhol Coke Studio")
print("🎵 Title:", track["title"])
print("🧑‍🎤 Artist:", track["artist"])
print("🖼️ Thumbnail:", track["thumbnail"])
print("🔗 Audio URL:", track["audio_url"])
print("📺 Video URL:", track["video_url"])