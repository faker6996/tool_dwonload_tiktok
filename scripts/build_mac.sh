#!/bin/bash
# Build script for macOS with FFmpeg bundled

set -e

echo "🍎 Building Video Editor for macOS..."

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_DIR"

# Create bin directory for FFmpeg
mkdir -p bin

# Download FFmpeg for macOS if not exists
if [ ! -f "bin/ffmpeg" ]; then
    echo "📥 Downloading FFmpeg for macOS..."
    
    # Download from evermeet.cx (trusted macOS FFmpeg builds)
    curl -L "https://evermeet.cx/ffmpeg/getrelease/ffmpeg/zip" -o bin/ffmpeg.zip
    unzip -o bin/ffmpeg.zip -d bin/
    rm bin/ffmpeg.zip
    chmod +x bin/ffmpeg
    
    echo "✅ FFmpeg downloaded!"
fi

# Create virtual environment if not exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt
pip install pyinstaller

# Build with PyInstaller (including FFmpeg binary)
echo "🔨 Building app..."
pyinstaller --name "VideoEditor" \
    --windowed \
    --onedir \
    --add-data "assets:assets" \
    --add-binary "bin/ffmpeg:bin" \
    --hidden-import "PyQt6.QtCore" \
    --hidden-import "PyQt6.QtGui" \
    --hidden-import "PyQt6.QtWidgets" \
    --hidden-import "PyQt6.QtMultimedia" \
    --hidden-import "PyQt6.QtMultimediaWidgets" \
    --hidden-import "yt_dlp" \
    --hidden-import "PIL" \
    --hidden-import "PIL.Image" \
    --hidden-import "PIL.ImageDraw" \
    --hidden-import "PIL.ImageFont" \
    --hidden-import "mutagen" \
    --hidden-import "mutagen.mp3" \
    --hidden-import "deep_translator" \
    --hidden-import "edge_tts" \
    --hidden-import "mlx" \
    --hidden-import "mlx_whisper" \
    --hidden-import "whisper" \
    --hidden-import "openai" \
    --exclude-module "matplotlib" \
    --exclude-module "pandas" \
    --exclude-module "jupyter" \
    --noconfirm \
    main.py

echo ""
echo "✅ Build complete!"
echo "📁 App location: dist/VideoEditor.app"
echo ""
echo "To run: open dist/VideoEditor.app"
echo "To distribute: zip -r VideoEditor.zip dist/VideoEditor.app"
