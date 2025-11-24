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

2.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    playwright install
    ```

## Usage

Run the application:

```bash
python main.py
```

1.  Paste a TikTok or Douyin link.
2.  Click **Check Video**.
3.  Wait for the preview to load.
4.  Click **Save Video** to download.

## Structure

- `src/core`: Core logic (downloader, platform detection).
- `src/ui`: User interface (PyQt6).
- `src/utils`: Helper functions.
