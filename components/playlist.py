import requests
import yt_dlp
youtube_api_key="AIzaSyDMNhU8ZpkIOV1wAuPo6dc7yarfLnqEC0A1"
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


def get_audio_info_by_id(video_id):
    url = f"https://www.youtube.com/watch?v={video_id}"
    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'noplaylist': True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        result = {
            "title": info.get("title"),
            "artist": info.get("uploader"),
            "thumbnail": info.get("thumbnail"),
            "audio_url": info.get("url"),
            "video_url": info.get("webpage_url"),
        }
        return result

def search_youtube(query, max_results=5):
    search_url = "https://www.googleapis.com/youtube/v3/search"

    params = {
        "part": "snippet",
        "q": query,
        "type": "video",
        "maxResults": max_results,
        "key": youtube_api_key,
    }

    response = requests.get(search_url, params=params)
    data = response.json()
    results = []
    for item in data.get("items", []):
        snippet = item["snippet"]
        results.append({
            "name": snippet["channelTitle"],
            "title": snippet["title"],
            "thumbnail": snippet["thumbnails"]["high"]["url"],
            "video_id": item["id"]["videoId"],
        })

    return results
