import sounddevice as sd
import numpy as np
from scipy.io.wavfile import write
import asyncio
from shazamio import Shazam

# Record audio
fs = 44100  # Sample rate
seconds = 10  # Duration of the recording in seconds
filename = "recorded_audio.wav"

print("🎤 Recording...")
recording = sd.rec(int(seconds * fs), samplerate=fs, channels=1)
sd.wait()
recording = np.int16(recording * 32767)  # Ensure correct format (16-bit PCM)
write(filename, fs, recording)  # Save the recording as a .wav file
print("✅ Recording complete.")

# Recognize with Shazam
async def recognize():
    shazam = Shazam()
    out = await shazam.recognize_song(filename)  # Use the raw WAV file for recognition
    print("🎵 Result:", out)

# Run the recognition
asyncio.run(recognize())
