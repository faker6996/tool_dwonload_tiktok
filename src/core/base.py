from abc import ABC, abstractmethod
import os
from typing import Callable, Dict, Optional
from .logging_utils import get_logger
from .media_io import atomic_replace_validated, make_temp_path, remove_file_quietly
from .media_validation import infer_media_kind

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

        temp_path = make_temp_path(filename)

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

            result = atomic_replace_validated(
                temp_path,
                filename,
                expected_kind=infer_media_kind(filename),
            )
            if not result.ok:
                logger.warning("Downloaded media validation failed: %s", result.reason)
                return False

            if progress_callback:
                try:
                    progress_callback(result.size, result.size)
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
            remove_file_quietly(temp_path)
