<p align="center">
  <img src="https://img.shields.io/badge/Python-3.9+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/PySide6-Qt6-41CD52?style=for-the-badge&logo=qt&logoColor=white" alt="PySide6">
  <img src="https://img.shields.io/badge/Supabase-Auth-3ECF8E?style=for-the-badge&logo=supabase&logoColor=white" alt="Supabase">
  <img src="https://img.shields.io/badge/Platform-Windows-0078D6?style=for-the-badge&logo=windows&logoColor=white" alt="Platform">
</p>

<h1 align="center">GalaxyStream</h1>

<p align="center">
  <b>Modern Multi-Source Entertainment Hub</b><br>
  <i>Stream Drama Videos, Watch Anime & Read Digital Comics in One Premium App</i>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Version-4.0-blue?style=flat-square" alt="Version">
  <img src="https://img.shields.io/badge/Status-Active-success?style=flat-square" alt="Status">
  <img src="https://img.shields.io/badge/License-Academic-orange?style=flat-square" alt="License">
</p>

---

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Architecture](#architecture)
- [Requirements](#requirements)
- [Installation](#installation)
  - [Development Setup](#development-setup)
  - [Supabase Authentication Setup](#supabase-authentication-setup)
  - [Running the Application](#running-the-application)
- [Building for Production](#building-for-production)
- [Usage Guide](#usage-guide)
- [Keyboard Shortcuts](#keyboard-shortcuts)
- [API Sources](#api-sources)
- [Project Structure](#project-structure)
- [Contributing](#contributing)
- [Troubleshooting](#troubleshooting)
- [License](#license)

---

## Features

### Video Streaming
- **DramaBox** - Korean/Chinese drama short videos
- **NetShort** - Short drama series with multiple episodes
- **Melolo** - Book-based drama content
- **ShortMax** - Premium short video content (AES-128-CBC encrypted)
- **Flic/FlickReels** - Short video platform

### Anime Streaming
- **Otakudesu** - Anime with Indonesian subtitles
- **Kuramanime** - Anime streaming with multiple quality options
- Built-in local API server (`wajik-anime-api.exe`) for anime sources

### Comic Reading
- **Komik** - Digital comics/manhwa reader
- Vertical scroll with zoom support (50%-200%)
- Chapter navigation

### Core Features
- **User Authentication** - Supabase-powered login (Email/Password & Google OAuth)
- **Watch History** - Resume watching from where you left off
- **Image Caching** - Smart local cache for faster loading
- **Dark Theme** - Premium dark space-themed interface
- **Async Loading** - Non-blocking UI with background data fetching
- **HEIC Support** - Automatic conversion of HEIC images to JPEG

---

## Tech Stack

| Category | Technology | Purpose |
|----------|------------|---------|
| **GUI Framework** | PySide6 (Qt6) | Cross-platform desktop UI |
| **Video Playback** | MPV (libmpv) | High-performance video player |
| **Authentication** | Supabase | User auth with email & OAuth |
| **Networking** | Requests, urllib3, httpx | API communication |
| **Image Processing** | Pillow, pillow-heif | Image handling & HEIC conversion |
| **Concurrency** | QThread | Background operations |
| **Data Storage** | QSettings | Local settings & session storage |
| **Build Tool** | PyInstaller | Executable packaging |
| **Installer** | Inno Setup | Windows installer creation |

---

## Architecture

```
GalaxyStream/
├── app/
│   ├── models/              # Data models
│   │   ├── __init__.py
│   │   └── movie.py         # Movie & Episode dataclasses
│   │
│   ├── services/            # Business logic & API clients
│   │   ├── __init__.py
│   │   ├── api_client.py    # Multi-source API client (DramaBox, NetShort, etc.)
│   │   ├── anime_client.py  # Anime API client (Otakudesu, Kuramanime)
│   │   ├── auth_client.py   # Supabase authentication
│   │   ├── image_cache.py   # Image caching service
│   │   └── history_service.py # Watch history management
│   │
│   ├── ui/                  # User interface components
│   │   ├── __init__.py
│   │   ├── main_window.py   # Main application window
│   │   ├── login_page.py    # Login/signup page
│   │   ├── home_page.py     # Home with hero banner
│   │   ├── browse_page.py   # Content browsing grid
│   │   ├── search_page.py   # Search functionality
│   │   ├── detail_page.py   # Content details & episodes
│   │   ├── player.py        # Video player with MPV
│   │   ├── comic_reader.py  # Vertical comic reader
│   │   ├── anime_page.py    # Anime listing
│   │   ├── anime_episode_page.py # Anime episode viewer
│   │   ├── history_page.py  # Watch history
│   │   ├── token_page.py    # API token settings
│   │   ├── source_selection.py # Source picker
│   │   ├── sidebar.py       # Navigation sidebar
│   │   ├── top_bar.py       # Top navigation bar
│   │   ├── cards.py         # Content card widgets
│   │   └── loading_overlay.py # Loading spinner
│   │
│   └── styles/              # QSS stylesheets
│       ├── __init__.py
│       ├── dark_space.qss   # Main dark theme
│       └── embedded_styles.py # Fallback embedded styles
│
├── cache/                   # Image cache directory (auto-created)
├── main.py                  # Application entry point
├── requirements.txt         # Python dependencies
├── GalaxyStream.spec        # PyInstaller configuration
├── GalaxyStream_Installer.iss # Inno Setup installer script
├── galaxystream_icon_fix.ico # Application icon
└── wajik-anime-api.exe      # Local anime API server
```

---

## Requirements

### System Requirements
- **Operating System**: Windows 10/11 (64-bit)
- **Python**: 3.9 or higher (3.13+ recommended)
- **RAM**: Minimum 4GB
- **Storage**: ~500MB for installation
- **Internet**: Required for streaming content

### Python Dependencies

```
# Core dependencies
PySide6>=6.5.0
requests>=2.31.0
urllib3>=2.0.0

# Authentication
supabase>=2.0.0

# Video playback (requires libmpv DLL separately)
mpv>=1.0.0

# Image processing
Pillow>=10.0.0

# HEIC support
pillow-heif>=0.13.0

# SSL certificates
certifi>=2023.0.0
```

### Additional Requirements
- **libmpv**: Required for video playback. Download from [mpv.io](https://mpv.io/installation/) or [sourceforge](https://sourceforge.net/projects/mpv-player-windows/files/libmpv/)

---

## Installation

### Development Setup

1. **Clone the Repository**
   ```bash
   git clone https://github.com/yourusername/GalaxyStream.git
   cd GalaxyStream
   ```

2. **Create Virtual Environment** (Recommended)
   ```bash
   python -m venv venv

   # Windows
   venv\Scripts\activate

   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install libmpv** (Windows)
   - Download `libmpv` from [mpv.io](https://mpv.io/installation/)
   - Extract `mpv-2.dll` (or `libmpv-2.dll`) to your Python installation directory or system PATH
   - Alternatively, place it in the same directory as `main.py`

5. **Configure Supabase** (See [Supabase Setup](#supabase-authentication-setup))

---

### Supabase Authentication Setup

GalaxyStream uses [Supabase](https://supabase.com) for user authentication. Follow these steps to set up your own Supabase project:

#### Step 1: Create a Supabase Project

1. Go to [supabase.com](https://supabase.com) and sign up/login
2. Click **"New Project"**
3. Fill in the details:
   - **Name**: GalaxyStream (or your preferred name)
   - **Database Password**: Create a strong password
   - **Region**: Choose the closest to your users
4. Click **"Create new project"** and wait for it to be ready

#### Step 2: Get Your API Credentials

1. In your Supabase dashboard, go to **Project Settings** (gear icon)
2. Click **API** in the sidebar
3. Copy these values:
   - **Project URL**: `https://xxxxx.supabase.co`
   - **anon/public key**: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`

#### Step 3: Configure Email Authentication

1. Go to **Authentication** > **Providers**
2. Enable **Email** provider
3. Configure settings:
   - **Enable email confirmations**: Toggle based on your preference
   - **Secure email change**: Recommended to enable

#### Step 4: Configure Google OAuth (Optional)

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Go to **APIs & Services** > **Credentials**
4. Click **Create Credentials** > **OAuth client ID**
5. Configure:
   - **Application type**: Web application
   - **Authorized redirect URIs**: Add your Supabase callback URL:
     ```
     https://your-project.supabase.co/auth/v1/callback
     ```
6. Copy the **Client ID** and **Client Secret**
7. In Supabase, go to **Authentication** > **Providers** > **Google**
8. Enable Google and paste your Client ID and Secret
9. Add redirect URL for local development:
   ```
   http://127.0.0.1:8765/callback
   ```

#### Step 5: Configure Redirect URLs

1. In Supabase, go to **Authentication** > **URL Configuration**
2. Add to **Redirect URLs**:
   ```
   http://127.0.0.1:8765/callback
   http://localhost:8765/callback
   ```

#### Step 6: Update Application Code

Edit `app/services/auth_client.py` and update the credentials:

```python
# Replace with your Supabase credentials
SUPABASE_URL = "https://your-project-id.supabase.co"
SUPABASE_ANON_KEY = "your-anon-key-here"
```

> **Security Note**: The `anon` key is designed to be public-facing. Security is handled by Row Level Security (RLS) policies in Supabase.

#### Step 7: (Optional) Using Environment Variables

For better security, you can use environment variables:

1. Create a `.env` file in the project root:
   ```env
   SUPABASE_URL=https://your-project-id.supabase.co
   SUPABASE_ANON_KEY=your-anon-key-here
   ```

2. Install python-dotenv:
   ```bash
   pip install python-dotenv
   ```

3. The application will automatically load these variables on startup.

---

### Running the Application

#### Development Mode
```bash
python main.py
```

#### With Environment Variables
```bash
# Windows
set SUPABASE_URL=https://your-project.supabase.co
set SUPABASE_ANON_KEY=your-key
python main.py

# Linux/macOS
SUPABASE_URL=https://your-project.supabase.co \
SUPABASE_ANON_KEY=your-key \
python main.py
```

#### Disable Local Anime Server
```bash
# If you don't need anime features
set GALAXY_NO_SERVER=1
python main.py
```

---

## Building for Production

### Step 1: Install Build Tools
```bash
pip install pyinstaller
```

### Step 2: Build Executable
```bash
pyinstaller GalaxyStream.spec
```

This will create:
- `dist/GalaxyStream/` - Directory with all files
- `dist/GalaxyStream/GalaxyStream.exe` - Main executable

### Step 3: Create Installer (Windows)

1. Download [Inno Setup](https://jrsoftware.org/isdl.php)
2. Open `GalaxyStream_Installer.iss` in Inno Setup
3. Click **Build** > **Compile**
4. Find the installer in `installer_output/GalaxyStream_Setup_v4.exe`

### Build Notes
- The `.spec` file includes all necessary hidden imports for Supabase
- libmpv DLL must be in the dist folder or system PATH
- The `wajik-anime-api.exe` is bundled for anime functionality

---

## Usage Guide

### First Time Setup

1. **Launch** the application
2. **Create Account** or **Sign In**:
   - Enter email and password, then click **Create Account**
   - Check your email for confirmation link (if email confirmation is enabled)
   - After confirming, return and **Sign In**
   - Or use **Sign in with Google** for OAuth

### Navigating the App

1. **Source Selection**: Choose your content source:
   - **DramaBox** - Korean/Chinese dramas
   - **NetShort** - Short drama series
   - **Melolo** - Book-based dramas
   - **ShortMax** - Premium short videos
   - **Flic** - FlickReels content
   - **Anime** - Japanese anime (Otakudesu/Kuramanime)
   - **Komik** - Digital comics

2. **Home Page**: Browse featured content
3. **Search**: Use the search bar to find specific content
4. **Detail Page**: Click any content to see details and episodes
5. **Watch/Read**: Select an episode to start watching or reading

### Switching Sources
- Click the profile menu (top-right)
- Select **Switch Source**
- Choose a new content source

### API Token (Advanced)
Some sources require authentication tokens:
1. Click profile menu > **Token Settings**
2. Enter your API token
3. Token is saved locally and used for authenticated requests

---

## Keyboard Shortcuts

### Video Player

| Key | Action |
|-----|--------|
| `Space` | Play / Pause |
| `F` | Toggle Fullscreen |
| `Esc` | Exit Fullscreen |
| `←` | Seek -10 seconds |
| `→` | Seek +10 seconds |
| `↑` | Volume Up |
| `↓` | Volume Down |
| `N` | Next Episode |
| `P` | Previous Episode |
| `M` | Mute / Unmute |

### Comic Reader

| Key | Action |
|-----|--------|
| `+` / `=` | Zoom In |
| `-` | Zoom Out |
| `0` | Reset Zoom (100%) |
| `←` | Previous Chapter |
| `→` | Next Chapter |
| `Home` | Go to First Page |
| `End` | Go to Last Page |
| `Page Up` | Scroll Up |
| `Page Down` | Scroll Down |

---

## API Sources

| Source | Type | Authentication | Notes |
|--------|------|---------------|-------|
| DramaBox | Video | None | Indonesian language support |
| NetShort | Video | Bearer Token | Requires captain.sapimu.au token |
| Melolo | Video | Bearer Token | Book-based content |
| ShortMax | Video | Bearer Token | AES-128-CBC encrypted streams |
| Flic | Video | None | Multiple quality options |
| Otakudesu | Anime | None | Requires local wajik-anime-api |
| Kuramanime | Anime | None | Requires local wajik-anime-api |
| Komik | Comics | None | Uses api.sansekai.my.id |

---

## Project Structure

### Data Models

```python
@dataclass
class Movie:
    id: str
    title: str
    poster_url: str
    synopsis: str = ""
    rating: float = 0.0
    year: str = ""
    source_type: str = "dramabox"
    genres: List[str] = field(default_factory=list)
    episodes: List[Episode] = field(default_factory=list)
    total_chapters: int = 0

@dataclass
class Episode:
    id: str
    title: str
    stream_url: str
    order: int
    duration: str = ""
```

### Service Layer

- **APIClient**: Unified interface for all video/comic sources
- **AnimeClient**: Specialized client for anime sources via local API
- **AuthClient**: Supabase authentication handling
- **ImageCache**: MD5-based caching with async downloads
- **HistoryService**: Watch history with QSettings persistence

### UI Components

- **MainWindow**: Central navigation & state management
- **LoginPage**: Email/password & Google OAuth login
- **HomePage**: Hero banner & categorized content sections
- **BrowsePage**: Grid-based content browsing
- **SearchPage**: Dynamic search with instant results
- **DetailPage**: Content metadata & episode list
- **PlayerPage**: MPV-based video player with controls
- **ComicReader**: Vertical comic reader with zoom
- **AnimePage/AnimeEpisodePage**: Anime-specific UI

---

## Contributing

1. **Fork** the repository
2. **Create** a feature branch:
   ```bash
   git checkout -b feature/AmazingFeature
   ```
3. **Commit** your changes:
   ```bash
   git commit -m 'Add AmazingFeature'
   ```
4. **Push** to the branch:
   ```bash
   git push origin feature/AmazingFeature
   ```
5. **Open** a Pull Request

### Code Style
- Follow PEP 8 guidelines
- Use type hints where possible
- Add docstrings for public methods
- Keep UI and business logic separated

---

## Troubleshooting

### Common Issues

**1. "Supabase client not configured"**
- Ensure `SUPABASE_URL` and `SUPABASE_ANON_KEY` are correctly set in `auth_client.py`
- Check your internet connection

**2. Video not playing**
- Ensure libmpv is installed and accessible
- Check if the stream URL is valid
- Try a different episode or source

**3. "wajik-anime-api not found"**
- Ensure `wajik-anime-api.exe` is in the application directory
- Anime features require this local server running on port 3001

**4. OAuth redirect not working**
- Verify redirect URLs are configured in Supabase
- Ensure `http://127.0.0.1:8765/callback` is in allowed redirects

**5. Images not loading**
- Check your internet connection
- Clear cache: The cache is auto-cleared on source switch
- For HEIC images, ensure `pillow-heif` is installed

**6. Application crashes on startup**
- Run from terminal to see error messages:
  ```bash
  python main.py
  ```
- Check Python version (3.9+ required)
- Reinstall dependencies

### Debug Mode
Run with console output for debugging:
```bash
python main.py
```

All debug messages are printed to the console with `[MODULE]` prefixes.

---

## License

This project is created for **academic purposes** - Visual Programming Course (Semester 3)

**Disclaimer**: This application is for educational demonstration only. All content is sourced from third-party APIs. The developers do not host or distribute any copyrighted content.

---

<p align="center">
  <b>GalaxyStream - Your Gateway to Endless Entertainment</b>
</p>

<p align="center">
  Made with Python & PySide6
</p>

<p align="center">
  <i>Visual Programming Course - Semester 3</i>
</p>
