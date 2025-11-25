import sys
import os

# Add src to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.core.manager import DownloaderManager

def test_platform(name, url):
    print(f"\n--- Testing {name} ---")
    print(f"URL: {url}")
    manager = DownloaderManager()
    try:
        info = manager.get_video_info(url)
        if info.get('status') == 'success':
            print(f"✅ SUCCESS")
            print(f"Title: {info.get('title')}")
            print(f"Video URL: {info.get('url')[:50]}...")
            return True
        else:
            print(f"❌ FAILED: {info.get('message')}")
            return False
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False

if __name__ == "__main__":
    # Sample URLs (Public videos)
    samples = {
        "YouTube": "https://www.youtube.com/watch?v=jNQXAC9IVRw", # Me at the zoo
        "Douyin": "https://www.douyin.com/video/7315433748366462243", # Random Douyin ID (might be dead, but structure check)
        # Note: FB/Insta often fail without cookies/auth on servers, but let's try
        "Twitter/X": "https://twitter.com/SpaceX/status/1712803584852934896", # SpaceX video
    }

    results = {}
    for name, url in samples.items():
        results[name] = test_platform(name, url)

    print("\n=== SUMMARY ===")
    for name, success in results.items():
        print(f"{name}: {'✅ OK' if success else '❌ FAILED (Might need cookies)'}")
