import requests
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
import threading
import os
import signal
import sys

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
#             print(f"Error fetching access token: {response.status_code}")
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
        "limit": 10
    }
    response = requests.get(url, params=params)
    
    return response.json()

tracs=get_pakistan_related_tracks()