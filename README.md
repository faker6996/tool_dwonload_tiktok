# Universal Video Downloader

A modern desktop application for downloading videos from TikTok and Douyin without watermarks. Built with Python and PyQt6.

## Features

- **Universal Support**: Works with both TikTok and Douyin links.
- **Video Preview**: Watch the video inside the app before downloading.
- **No Watermark**: Tries to fetch the clean version of the video.
- **Modern UI**: Clean, dark-themed interface.

## Installation

1.  **Clone the repository**:

    ```bash
    git clone <your-repo-url>
    cd tool_download_tiktok
    ```

2.  **Setup Virtual Environment & Install Dependencies**:

    ```bash
    # Create virtual environment
    python3 -m venv venv

    # Install dependencies
    ./venv/bin/pip install -r requirements.txt
    ./venv/bin/playwright install
    ```

## Usage

### Option 1: Run from Source

Run the application using the virtual environment's Python:

```bash
./venv/bin/python main.py
```

### Option 2: Run Executable

If you have built the app (see below), you can run the standalone executable:

```bash
./dist/TikTokDownloader
```

1.  Paste a TikTok or Douyin link.
2.  Click **Check Video**.
3.  Wait for the preview to load.
4.  Click **Save Video** to download.

## Structure

- `src/core`: Core logic (downloader, platform detection).
- `src/ui`: User interface (PyQt6).
- `src/utils`: Helper functions.

## Build App (Executable)

You can package the application into a standalone executable using `pyinstaller`.

1.  **Install PyInstaller**:

    ```bash
    pip install pyinstaller
    ```

2.  **Build the App**:

    ```bash
    # For Mac/Linux (Run this on Mac/Linux)
    pyinstaller --noconfirm --onefile --windowed --name "TikTokDownloader" --icon "app_icon.png" --add-data "src:src" main.py

    # For Windows (Run this ON WINDOWS only)
    # pyinstaller --noconfirm --onefile --windowed --name "TikTokDownloader" --icon "app_icon.png" --add-data "src;src" main.py
    ```

3.  **Run**:
    The executable will be in the `dist` folder as `TikTokDownloader`.

    _Note: The built app still requires Playwright browsers. On a new machine, you may need to run the app from a terminal first to see the "playwright install" prompt or bundle the browsers (advanced)._
