import base64
import hashlib
import hmac
import os
import time
import tempfile
import requests
import sounddevice as sd
from scipy.io.wavfile import write

# === ACRCloud credentials ===
ACR_ACCESS_KEY = "acdd72326d7fd3c7c2a8638964513f47"
ACR_ACCESS_SECRET = "cEGCBk3jR7fN6eoZux5qCFABoM2QEiPhIOm0lCP8"
ACR_REQURL = "https://identify-ap-southeast-1.acrcloud.com/v1/identify"

# === Spotify credentials ===
SPOTIFY_CLIENT_ID = "5c2fcd03261d47199284a7219dfc6fea"
SPOTIFY_CLIENT_SECRET = "58c0438e935348d78aa4facfc8ea8e48"

class AudioRecognizer:
    def __init__(self, duration=5, sample_rate=44100):
        self.duration = duration
        self.sample_rate = sample_rate
        self.recorded_file = None
        self.result = None
        self.spotify_token = None
        self.spotify_track_info = None

    # === Record audio ===
    def record_audio(self):
        print(f"🎤 Recording {self.duration} seconds of audio...")
        audio = sd.rec(int(self.duration * self.sample_rate), samplerate=self.sample_rate, channels=1)
        sd.wait()

        # Save to temp file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
        write(temp_file.name, self.sample_rate, audio)
        self.recorded_file = temp_file.name
        print(f"✅ Audio recorded: {temp_file.name}")
    
    # === Recognize song with ACRCloud ===
    def recognize_audio(self):
        http_method = "POST"
        http_uri = "/v1/identify"
        data_type = "audio"
        signature_version = "1"
        timestamp = time.time()

        string_to_sign = "\n".join([
            http_method,
            http_uri,
            ACR_ACCESS_KEY,
            data_type,
            signature_version,
            str(timestamp)
        ])

        sign = base64.b64encode(
            hmac.new(ACR_ACCESS_SECRET.encode('ascii'), string_to_sign.encode('ascii'), digestmod=hashlib.sha1).digest()
        ).decode('ascii')

        sample_bytes = os.path.getsize(self.recorded_file)

        with open(self.recorded_file, "rb") as audio_file:
            files = [
                ('sample', ('sample.wav', audio_file, 'audio/wav'))
            ]
            data = {
                'access_key': ACR_ACCESS_KEY,
                'sample_bytes': sample_bytes,
                'timestamp': str(timestamp),
                'signature': sign,
                'data_type': data_type,
                "signature_version": signature_version
            }
            response = requests.post(ACR_REQURL, files=files, data=data)
            response.encoding = "utf-8"
            self.result = response.json()
    
    # === Get Spotify Access Token ===
    def get_spotify_access_token(self):
        url = "https://accounts.spotify.com/api/token"
        auth_string = f"{SPOTIFY_CLIENT_ID}:{SPOTIFY_CLIENT_SECRET}"
        auth_base64 = base64.b64encode(auth_string.encode('utf-8')).decode('utf-8')

        headers = {
            "Authorization": f"Basic {auth_base64}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        data = {
            "grant_type": "client_credentials"
        }

        response = requests.post(url, headers=headers, data=data)
        if response.status_code == 200:
            self.spotify_token = response.json()['access_token']
        else:
            raise Exception(f"Failed to get Spotify token: {response.status_code} {response.text}")

    # === Get Spotify Track Details ===
    def get_spotify_track_info(self):
        if not self.result:
            raise Exception("No result from ACRCloud. Please recognize the audio first.")
        
        metadata = self.result['metadata']['music'][0]
        spotify_track_id = metadata.get('external_metadata', {}).get('spotify', {}).get('track', {}).get('id')

        if spotify_track_id:
            url = f"https://api.spotify.com/v1/tracks/{spotify_track_id}"
            headers = {
                "Authorization": f"Bearer {self.spotify_token}"
            }
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                self.spotify_track_info = response.json()
            else:
                raise Exception(f"Failed to fetch track info: {response.status_code} {response.text}")
        else:
            raise Exception("No Spotify track ID found in ACRCloud response.")

    # === Main method to run everything ===
    def process_audio(self):
        self.record_audio()
        self.recognize_audio()

        # Safely parse result
        if self.result.get('status', {}).get('code') == 0:
            metadata = self.result['metadata']['music'][0]

            song_title = metadata['title']
            artist_name = metadata['artists'][0]['name']
            print(f"🎶 Song: {song_title}")
            print(f"👤 Artist: {artist_name}")

            # Get Spotify token and track info
            self.get_spotify_access_token()
            self.get_spotify_track_info()

            album_name = self.spotify_track_info['album']['name']
            album_image = self.spotify_track_info['album']['images'][0]['url']  # Get biggest image

            print(f"💿 Album: {album_name}")
            print(f"🖼️ Album Image URL: {album_image}")

            return {
                "song_title": song_title,
                "artist_name": artist_name,
                "album_name": album_name,
                "album_image_url": album_image
            }
        else:
            raise Exception(f"❌ Recognition failed: {self.result['status']['msg']}")

    # === Clean up temp file ===
    def clean_up(self):
        if self.recorded_file and os.path.exists(self.recorded_file):
            os.remove(self.recorded_file)
            print(f"🗑️ Temp file {self.recorded_file} cleaned up.")
