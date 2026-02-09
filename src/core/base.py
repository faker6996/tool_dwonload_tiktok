from abc import ABC, abstractmethod
import os
import tempfile
from typing import Callable, Dict, Optional
from .logging_utils import get_logger

logger = get_logger(__name__)

class BaseDownloader(ABC):
    @abstractmethod
    def extract_info(self, url, status_callback=None):
        """
        Extract video information.
        Returns dict: {'status': 'success'/'error', 'url': direct_url, 'platform': '...', 'cookies': ...}
        """
        pass

    def download(
        self,
        video_url: str,
        filename: str,
        cookies=None,
        user_agent: Optional[str] = None,
        extra_headers: Optional[Dict[str, str]] = None,
        timeout: int = 30,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> bool:
        """
        Download video from direct URL.
        Default implementation using requests.
        Writes to a temporary file first, then atomically moves into place.
        """
        import requests

        if not video_url or not filename:
            return False

        destination_dir = os.path.dirname(os.path.abspath(filename)) or "."
        os.makedirs(destination_dir, exist_ok=True)

        temp_fd, temp_path = tempfile.mkstemp(
            prefix="download_",
            suffix=".part",
            dir=destination_dir,
        )
        os.close(temp_fd)

        try:
            headers = {}
            if user_agent:
                headers["User-Agent"] = user_agent
            if extra_headers:
                headers.update(extra_headers)

            with requests.get(
                video_url,
                headers=headers,
                cookies=cookies,
                stream=True,
                timeout=timeout,
            ) as response:
                if response.status_code not in (200, 206):
                    logger.warning("Download failed with status: %s", response.status_code)
                    return False

                total_size = 0
                try:
                    total_size = int(response.headers.get("content-length", 0))
                except Exception:
                    total_size = 0

                with open(temp_path, "wb") as file_obj:
                    downloaded = 0
                    if progress_callback:
                        try:
                            progress_callback(0, total_size)
                        except Exception:
                            pass
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            file_obj.write(chunk)
                            downloaded += len(chunk)
                            if progress_callback:
                                try:
                                    progress_callback(downloaded, total_size)
                                except Exception:
                                    pass

            # Atomic replace avoids leaving partially-written destination files.
            os.replace(temp_path, filename)
            if progress_callback:
                try:
                    final_size = os.path.getsize(filename)
                except OSError:
                    final_size = 0
                try:
                    progress_callback(final_size, final_size)
                except Exception:
                    pass
            return True
        except requests.RequestException as e:
            logger.warning("Download request error: %s", e)
            return False
        except OSError as e:
            logger.warning("Download file error: %s", e)
            return False
        except Exception as e:
            logger.exception("Download unexpected error: %s", e)
            return False
        finally:
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except OSError:
                    pass
