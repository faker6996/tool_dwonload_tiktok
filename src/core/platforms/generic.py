from ..base import BaseDownloader
import yt_dlp

class GenericDownloader(BaseDownloader):
    def __init__(self, platform_name="generic"):
        self.platform_name = platform_name

    def extract_info(self, url):
        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'format': 'best',
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                video_url = info.get('url')
                title = info.get('title', 'Unknown')
                if video_url:
                    return {
                        'status': 'success', 
                        'url': video_url, 
                        'platform': self.platform_name, 
                        'title': title,
                        'cookies': None
                    }
        except Exception as e:
            print(f"yt-dlp error for {self.platform_name}: {e}")
            return {'status': 'error', 'message': f'{self.platform_name} download failed: {str(e)}'}
            
        return {'status': 'error', 'message': f'Could not retrieve video URL for {self.platform_name}'}
