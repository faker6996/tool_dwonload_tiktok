from downloader import VideoDownloader
import sys

def test_url():
    url = "https://www.tiktok.com/@zachking/video/7573719179098869006?is_from_webapp=1&sender_device=pc"
    print(f"Testing URL: {url}")
    
    dl = VideoDownloader()
    
    # 1. Detect Platform
    platform = dl.detect_platform(url)
    print(f"Platform: {platform}")
    
    # 2. Extract ID
    vid_id = dl.extract_video_id(url)
    print(f"Video ID: {vid_id}")
    
    # 3. Get Info
    print("Getting video info...")
    info = dl.get_video_info(url)
    print(f"Info Result: {info}")

if __name__ == "__main__":
    test_url()
