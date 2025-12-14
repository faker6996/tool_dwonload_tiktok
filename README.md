# 🎬 Video Editor - Universal Video Tool

A modern desktop application combining video downloading capabilities with a powerful video editing suite. Built with Python and PyQt6, featuring AI-powered subtitles and professional export.

[![Build Status](https://github.com/faker6996/tool_dwonload_tiktok/actions/workflows/build.yml/badge.svg)](https://github.com/faker6996/tool_dwonload_tiktok/actions)

## ✨ Highlights

- 🎥 **Download videos** from TikTok, Douyin, YouTube, and more
- 🤖 **AI Auto Caption** with translation support (Chinese → Vietnamese)
- ⚡ **MLX Whisper** acceleration on Apple Silicon (M1/M2/M3)
- 📝 **Live subtitle preview** on video player
- 🎯 **Burn subtitles** into exported videos
- 📦 **One-click installers** for macOS and Windows

---

## 📥 Download & Install

### macOS

Download `VideoEditor-macOS.dmg` → Open → Drag to Applications

### Windows

Download `VideoEditor-Setup.exe` → Run → Next → Install

**[Download Latest Release →](https://github.com/faker6996/tool_dwonload_tiktok/releases)**

---

## 🎬 Features

### 📥 Video Downloader

| Platform           | Status | Notes                |
| ------------------ | ------ | -------------------- |
| TikTok             | ✅     | No watermark         |
| Douyin             | ✅     | Auto cookie handling |
| YouTube            | ✅     | Shorts + Videos      |
| Threads            | ✅     | Meta's platform      |
| Facebook/Instagram | ⚠️     | May need cookies     |

### ✂️ Video Editor

- **Timeline**: Multi-track editing with magnetic snapping
- **Transform**: Position, Scale, Rotation controls
- **Audio**: Volume, Fade, Waveform visualization
- **Color**: Brightness, Contrast, Saturation, Hue
- **Effects**: Filters & Stickers library

### 🤖 AI Features

| Feature            | Description                                 |
| ------------------ | ------------------------------------------- |
| **Auto Caption**   | Speech-to-text using Whisper AI             |
| **Translation**    | Auto translate to Vietnamese, English, etc. |
| **MLX Whisper**    | 5-10x faster on Apple Silicon               |
| **Live Preview**   | See subtitles on video while playing        |
| **Burn-in Export** | Subtitles embedded in final video           |

### 📤 Export

- Resolution: 720p / 1080p / 4K
- FPS: 24 / 30 / 60
- FFmpeg bundled (no external install needed)
- ASS subtitles with custom styling

---

## 🛠️ Development Setup

### Prerequisites

- Python 3.9+
- FFmpeg (bundled in releases, optional for dev)

### Install

```bash
git clone https://github.com/faker6996/tool_dwonload_tiktok.git
cd tool_dwonload_tiktok

python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

pip install -r requirements.txt
playwright install
```

### Run

```bash
python main.py
```

### Optional: MLX Whisper (Apple Silicon only)

```bash
pip install mlx-whisper  # 5-10x faster transcription
```

---

## 📦 Building

### Automatic (GitHub Actions)

Push to `main` or create a tag:

```bash
git tag v1.0.0
git push --tags
```

Releases will have:

- `VideoEditor-macOS.dmg` - macOS installer
- `VideoEditor-Setup.exe` - Windows installer

### Manual Build

```bash
# macOS
./scripts/build_mac.sh

# Windows
scripts\build_windows.bat
```

---

## 📁 Project Structure

```
├── src/
│   ├── core/           # Business logic
│   │   ├── ai/         # Whisper, TTS, Translation
│   │   ├── export/     # FFmpeg renderer
│   │   ├── platforms/  # TikTok, Douyin, YouTube
│   │   └── timeline/   # Timeline, Track, Clip
│   └── ui/             # PyQt6 UI
│       ├── panels/     # Player, Timeline, Inspector
│       ├── dialogs/    # Export, Settings
│       └── pages/      # Download, Edit pages
├── scripts/            # Build scripts
├── assets/             # Icons, resources
└── .github/workflows/  # CI/CD
```

---

## 🗺️ Roadmap

**✅ Completed:**

- Multi-platform video download
- Timeline-based video editor
- AI auto caption with Whisper
- Translation (Chinese → Vietnamese)
- Live subtitle preview
- Subtitle burn-in export
- MLX Whisper for Apple Silicon
- Professional installers (DMG/EXE)

**🔜 Future:**

- Cloud sync
- More effects & transitions
- Keyframe animation
- Mobile companion app

---

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Submit pull request

---

## 📄 License

Educational purposes only.

---

**Made with ❤️ for video creators**
