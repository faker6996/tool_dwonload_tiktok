# Universal Video Downloader & Editor

A modern desktop application combining video downloading capabilities with a powerful video editing suite. Built with Python and PyQt6, inspired by professional tools like CapCut and Final Cut Pro.

## 🎬 Features

### 📥 Video Downloader

- **Multi-Platform Support**: Download videos from popular social media platforms:
  - ✅ **TikTok** (No watermark, supports private videos with cookies)
  - ✅ **Douyin** (Chinese TikTok - Auto Captcha/Cookie handling)
  - ✅ **YouTube** (Shorts and regular videos)
  - ✅ **Threads** (Meta's Threads.net)
  - ⚠️ **Facebook / Instagram / X (Twitter)** (Basic support, may require cookies)
- **Video Preview**: Play videos directly in-app before downloading
- **Smart Link Detection**: Automatic platform detection and optimal download method selection

### ✂️ Video Editor (MVP)

A comprehensive video editing suite with 8 major modules:

#### 1. **Timeline & Core Editing**

- **Magnetic Timeline**: Clips auto-snap together, preventing gaps
- **Multi-Track Support**: Video, Audio, and Subtitle tracks
- **Basic Editing**: Cut, Split, Delete, Move clips
- **Undo/Redo**: Command pattern implementation (Module 1)

#### 2. **Visual Manipulation**

- **Transform Controls**: Position (X, Y), Scale, Rotation in Inspector panel
- **Interactive Overlay**: Drag handles in Player preview
- **Opacity & Blend Modes**: Control transparency and layer blending
- **Real-time Preview**: See changes instantly in Player

#### 3. **Audio Engineering**

- **Volume Control**: Per-clip volume adjustment
- **Fade In/Out**: Audio transitions
- **Waveform Visualization**: Visual audio representation on timeline
- **Mute Toggle**: Quick audio on/off

#### 4. **AI Automation** (Mock Implementation)

- **Auto Captions**: Speech-to-text subtitle generation
- **Text-to-Speech**: Generate AI voiceovers from text
- **Smart Subtitles**: Auto-positioning on timeline

#### 5. **VFX & Color Grading**

- **Color Correction**: Brightness, Contrast, Saturation, Hue sliders
- **Effects Panel**: Filters and Stickers library (UI)
- **Real-time Adjustment**: See color changes instantly

#### 6. **System & Performance**

- **Proxy Workflow**: Toggle for low-res editing preview
- **Custom Shortcuts**: View and customize key bindings in Settings
- **Optimized UI**: Smooth performance with complex projects

#### 7. **Asset Management**

- **Enhanced Media Pool**: Import local files with drag & drop
- **Search & Filter**: Find assets by name or type (Video/Audio/Image)
- **Stock Integration**: Search online stock media (Pexels/Unsplash mock)
- **Dual Tabs**: Separate "Local" and "Stock" asset browsers

#### 8. **Export & Delivery**

- **Export Dialog**: Configure resolution (1080p, 720p, 4K), FPS (24, 30, 60)
- **Format Support**: MP4 output (H.264)
- **Progress Tracking**: Visual progress bar during rendering
- **Smart Presets**: Quality and codec selection

## 🎨 Design System

**Color Palette:**

- Primary: Blue-Purple gradient (`#58a6ff` → `#8b5cf6`)
- Background: Dark theme (`#121212`, `#1E1E1E`, `#252526`)
- Accent: Purple variations for feature distinction

**UI Philosophy:**

- Modern dark theme with vibrant gradients
- Consistent spacing and typography
- Smooth transitions and hover states
- Professional video editing aesthetic

## 📦 Installation

### Prerequisites

- Python 3.9+
- FFmpeg (for video processing)
- Playwright browsers (for downloads)

### Setup

1. **Clone the repository**:

   ```bash
   git clone <your-repo-url>
   cd tool_dwonload_tiktok
   ```

2. **Create virtual environment & install dependencies**:

   ```bash
   # Create virtual environment
   python3 -m venv venv

   # Activate
   source venv/bin/activate  # Mac/Linux
   # or
   .\venv\Scripts\activate  # Windows

   # Install dependencies
   pip install -r requirements.txt

   # Install Playwright browsers
   playwright install
   ```

## 🚀 Usage

### Running the Application

```bash
# From source
python main.py

# Or with virtual environment active
./venv/bin/python main.py
```

### Quick Start Guide

#### Download Mode:

1. Navigate to **Download** tab
2. Paste video URL from supported platform
3. Click **Check Video** to preview
4. Click **Save Video** to download

#### Edit Mode:

1. Navigate to **Edit** tab
2. Import media files via drag & drop or **Import Media** button
3. Drag clips to Timeline
4. Select clip to edit in **Inspector**
5. Adjust Transform, Audio, Color properties
6. Use **AI Tools** for captions or TTS
7. Click **Export Video** when ready

## 📁 Project Structure

```
tool_dwonload_tiktok/
├── src/
│   ├── core/              # Core business logic
│   │   ├── timeline/      # Timeline, Track, Clip models
│   │   ├── ai/            # AI services (Transcription, TTS)
│   │   ├── api/           # External API integrations (Stock)
│   │   ├── export/        # Rendering engine
│   │   ├── settings/      # App settings & shortcuts
│   │   ├── ingestion.py   # Media import & metadata
│   │   └── state.py       # State management
│   ├── ui/                # PyQt6 UI components
│   │   ├── panels/        # Media Pool, Player, Inspector, Timeline, Effects
│   │   ├── timeline/      # Timeline widgets (ClipWidget, TrackWidget)
│   │   ├── pages/         # Download, Edit, Document pages
│   │   ├── dialogs/       # Export, Settings dialogs
│   │   ├── main_window.py # Main application window
│   │   └── styles.py      # QSS styling
│   └── utils/             # Utility functions
├── docs/                  # Documentation & plans
├── tests/                 # Unit tests
└── main.py               # Application entry point
```

## 🧪 Testing

Run unit tests:

```bash
# All tests
python -m pytest tests/

# Specific module
python tests/test_timeline.py
python tests/test_audio_features.py
python tests/test_export.py
```

## 🛠️ Build Executable

Package the application using PyInstaller:

```bash
# Install PyInstaller
pip install pyinstaller

# Build for Mac/Linux
pyinstaller --noconfirm --onedir --windowed \
  --name "VideoEditor" \
  --icon "app_icon.png" \
  --add-data "src:src" \
  main.py

# Build for Windows (run on Windows)
pyinstaller --noconfirm --onedir --windowed ^
  --name "VideoEditor" ^
  --icon "app_icon.png" ^
  --add-data "src;src" ^
  main.py
```

Executable location: `dist/VideoEditor/`

## 🗺️ Roadmap

**Completed (MVP):**

- ✅ Module 0: UI Architecture
- ✅ Module 1: Timeline Core
- ✅ Module 2: Visual Manipulation
- ✅ Module 3: Audio Engineering
- ✅ Module 4: AI Automation (Mock)
- ✅ Module 5: VFX & Color
- ✅ Module 6: System Performance
- ✅ Module 7: Asset Management
- ✅ Module 8: Export & Delivery

**Future Enhancements:**

- Real AI integration (OpenAI Whisper, Azure TTS, ElevenLabs)
- Actual FFmpeg rendering pipeline
- Advanced keyframing with curves
- Chroma key (green screen)
- Cloud sync & collaboration
- Mobile app companion

## 📚 Documentation

Detailed documentation available in `docs/`:

- `TÀI LIỆU YÊU CẦU SẢN PHẨM copy.txt` - Product requirements
- `danh_sach_tinh_nang.txt` - Feature specifications
- `plans/module_*.md` - Individual module plans

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Submit a pull request

## 📄 License

This project is for educational purposes.

## 🙏 Acknowledgments

- Inspired by CapCut, Final Cut Pro, and Adobe Premiere Pro
- Built with PyQt6, FFmpeg, and Python
- UI design influenced by modern dark themes (VS Code, Discord)

---

**Made with ❤️ for video creators**
