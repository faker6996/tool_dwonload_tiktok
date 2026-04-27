@echo off
REM Build script for Windows with FFmpeg bundled

echo 🪟 Building Video Editor for Windows...

REM Get script directory
set "PROJECT_DIR=%~dp0.."
cd /d "%PROJECT_DIR%"

REM Create bin directory
if not exist "bin" mkdir bin

REM Download FFmpeg for Windows if not exists
if not exist "bin\ffmpeg.exe" (
    echo 📥 Downloading FFmpeg for Windows...
    
    REM Download FFmpeg from gyan.dev (trusted Windows FFmpeg builds)
    powershell -Command "Invoke-WebRequest -Uri 'https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip' -OutFile 'bin\ffmpeg.zip'"
    powershell -Command "Expand-Archive -Path 'bin\ffmpeg.zip' -DestinationPath 'bin\ffmpeg_temp' -Force"
    
    REM Find and move ffmpeg.exe
    for /d %%i in (bin\ffmpeg_temp\ffmpeg-*) do (
        copy "%%i\bin\ffmpeg.exe" "bin\ffmpeg.exe"
    )
    
    REM Cleanup
    rmdir /s /q bin\ffmpeg_temp
    del bin\ffmpeg.zip
    
    echo ✅ FFmpeg downloaded!
)

REM Create virtual environment if not exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install dependencies
echo 📦 Installing dependencies...
pip install -r requirements.txt
pip install pyinstaller

echo 🦀 Building native Rust core...
python -m maturin build --manifest-path rust/video_core/Cargo.toml --features extension-module --out rust/video_core/dist
for %%f in (rust\video_core\dist\video_core-*.whl) do python -m pip install --force-reinstall "%%f"
python main.py --smoke-native-core

REM Build with PyInstaller
echo 🔨 Building app...
pyinstaller --name "VideoEditor" ^
    --windowed ^
    --onefile ^
    --add-data "assets;assets" ^
    --add-binary "bin\ffmpeg.exe;bin" ^
    --hidden-import "PyQt6.QtCore" ^
    --hidden-import "PyQt6.QtGui" ^
    --hidden-import "PyQt6.QtWidgets" ^
    --hidden-import "PyQt6.QtMultimedia" ^
    --hidden-import "PyQt6.QtMultimediaWidgets" ^
    --hidden-import "yt_dlp" ^
    --hidden-import "PIL" ^
    --hidden-import "PIL.Image" ^
    --hidden-import "PIL.ImageDraw" ^
    --hidden-import "PIL.ImageFont" ^
    --hidden-import "mutagen" ^
    --hidden-import "mutagen.mp3" ^
    --hidden-import "deep_translator" ^
    --hidden-import "edge_tts" ^
    --hidden-import "whisper" ^
    --hidden-import "video_core" ^
    --exclude-module "matplotlib" ^
    --exclude-module "pandas" ^
    --exclude-module "jupyter" ^
    --noconfirm ^
    main.py

python scripts\smoke_package.py dist\VideoEditor.exe

echo.
echo ✅ Build complete!
echo 📁 Exe location: dist\VideoEditor.exe
echo.
echo To run: double-click dist\VideoEditor.exe
echo To distribute: zip the VideoEditor.exe file
pause
