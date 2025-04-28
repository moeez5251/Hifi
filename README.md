# 🎧 HiFi Music Player

A modern desktop music player application built with Python and PySide6, featuring music recognition, search, and streaming capabilities.

## ✨ Features

- 🎵 Music streaming from YouTube
- 🎤 Music recognition using ACRCloud
- 🔍 Search songs and artists
- 📱 Modern responsive UI with dark theme
- 🎨 Beautiful animations and visualizations
- 📋 Curated playlists and genres
- 🎶 Weekly top songs and new releases
- 🎼 Multiple music categories:
  - 🎸 Rock Music
  - 🎺 Pop Music
  - 😊 Mood Songs
  - 🔝 Most Played
- 🌙 Dark mode support
- ⚡ Fast and responsive
- 🎵 High-quality audio streaming
- 📊 Music visualizations

## 🛠️ Technology Stack

- 🐍 Python 3.8+
- 🖼️ PySide6 (Qt for Python)
- 📺 yt-dlp for YouTube integration
- 🎤 ACRCloud for music recognition
- 🌐 Requests for API handling
- 👀 watchdog for development auto-reload

## 📥 Installation

1. Clone the repository:

```sh
git clone https://github.com/moeez5251/hifi.git

```

2. Create and activate virtual environment:

```sh
python -m venv venv
venv\Scripts\activate     # Windows
source venv/bin/activate  # Linux/Mac
```

3. Install dependencies:

```sh
pip install -r requirements.txt
```

4. Create a `.env` file with your API keys:

```
YOUTUBE_API_KEY=your_youtube_api_key
ACR_ACCESS_KEY = your_key
ACR_ACCESS_SECRET = your_secret
ACR_REQURL = your_url
```

## 💻 Development

To run the application in development mode with auto-reload:

```sh
python watcher.py
```

To run the application directly:

```sh
python main.py
```

## 🏗️ Building

To create an executable:

```sh
pyinstaller main.spec
```

The executable will be created in the `dist` folder.

## 📁 Project Structure

```
├── assets/            # 🖼️ Images, SVGs, and fonts
├── components/        # 🧩 UI components
├── main.py           # 🎯 Main application
├── watcher.py        # 👀 Development auto-reloader
├── style.css         # 🎨 Application styling
└── requirements.txt  # 📦 Python dependencies
```

## 🔧 System Requirements

- 💻 Windows 10/11, macOS, or Linux
- 🐍 Python 3.8 or higher
- 🎵 Audio output device
- 🌐 Internet connection for streaming

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- 🎨 PySide6 for the UI framework
- 🎵 ACRCloud for music recognition
- 📺 YouTube for music content
- 🌟 Open source community
- 🎨 Icons by [Icons8](https://icons8.com)
- 🖼️ Design inspiration from Spotify and YouTube Music
