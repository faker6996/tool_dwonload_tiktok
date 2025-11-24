from downloader import VideoDownloader
import os

def test_download():
    url = "https://www.tiktok.com/@zachking/video/7573719179098869006?is_from_webapp=1&sender_device=pc"
    print(f"Testing URL: {url}")
    
    dl = VideoDownloader()
    
    print("1. Getting info...")
    info = dl.get_video_info(url)
    print(f"Info: {info}")
    
    if info['status'] == 'success':
        video_url = info['url']
        print(f"2. Attempting download from: {video_url[:50]}...")
        
        filename = "test_download.mp4"
        if os.path.exists(filename):
            os.remove(filename)
            
        cookies = info.get('cookies')
        success = dl.download_video(video_url, filename, 'tiktok', cookies)
        
        if success:
            print(f"✅ Download success! Size: {os.path.getsize(filename)} bytes")
        else:
            print("❌ Download failed!")
    else:
        print("❌ Could not get video info")

if __name__ == "__main__":
    test_download()
