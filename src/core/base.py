from abc import ABC, abstractmethod

class BaseDownloader(ABC):
    @abstractmethod
    def extract_info(self, url):
        """
        Extract video information.
        Returns dict: {'status': 'success'/'error', 'url': direct_url, 'platform': '...', 'cookies': ...}
        """
        pass

    def download(self, video_url, filename, cookies=None, user_agent=None):
        """
        Download video from direct URL.
        Default implementation using requests.
        """
        import requests
        try:
            headers = {}
            if user_agent:
                headers["User-Agent"] = user_agent
            
            response = requests.get(video_url, headers=headers, cookies=cookies, stream=True, timeout=30)
            
            if response.status_code in [200, 206]:
                with open(filename, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                return True
            else:
                print(f"Download failed with status: {response.status_code}")
                return False
        except Exception as e:
            print(f"Download error: {e}")
            return False
