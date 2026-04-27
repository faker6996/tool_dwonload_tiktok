from ..base import BaseDownloader
import yt_dlp
import os
import glob
import copy
from ..logging_utils import get_logger
from ..media_validation import validate_or_remove
from ..profiling import profile_scope

logger = get_logger(__name__)

class GenericDownloader(BaseDownloader):
    def __init__(self, platform_name="generic"):
        self.platform_name = platform_name

    def extract_info(self, url, status_callback=None):
        def _notify(message: str):
            if not status_callback:
                return
            try:
                status_callback(message)
            except Exception:
                pass

        try:
            _notify("Preparing extractor...")
            base_opts = {
                'quiet': True,
                'no_warnings': True,
                'format': 'best',
                'noplaylist': True,
                'socket_timeout': 15,
                'retries': 3,
            }
            attempts = self._build_attempts(base_opts)

            last_error = None
            for attempt_name, ydl_opts in attempts:
                try:
                    _notify(f"Requesting video metadata ({attempt_name})...")
                    with profile_scope(
                        "download.extract_info_attempt",
                        platform=self.platform_name,
                        attempt=attempt_name,
                    ):
                        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                            info = ydl.extract_info(url, download=False)
                    video_url = (info or {}).get('url')
                    title = (info or {}).get('title', 'Unknown')
                    if video_url:
                        _notify("Metadata ready")
                        return {
                            'status': 'success',
                            'url': video_url,
                            'platform': self.platform_name,
                            'title': title,
                            'cookies': None,
                        }
                except Exception as exc:
                    last_error = exc
                    logger.warning(
                        "yt-dlp extract attempt failed for %s (%s): %s",
                        self.platform_name,
                        attempt_name,
                        exc,
                    )

            if last_error:
                raise last_error
        except Exception as e:
            logger.warning("yt-dlp error for %s: %s", self.platform_name, e)
            return {'status': 'error', 'message': f'{self.platform_name} download failed: {str(e)}'}
            
        return {'status': 'error', 'message': f'Could not retrieve video URL for {self.platform_name}'}

    def _build_attempts(self, base_opts: dict):
        if self.platform_name != "youtube":
            return [("default", copy.deepcopy(base_opts))]

        attempts = []
        youtube_headers = {
            "Referer": "https://www.youtube.com/",
            "Origin": "https://www.youtube.com",
        }

        client_fallback = copy.deepcopy(base_opts)
        existing_headers = dict(client_fallback.get("http_headers") or {})
        client_fallback["http_headers"] = {**youtube_headers, **existing_headers}
        client_fallback["extractor_args"] = {
            "youtube": {"player_client": ["android", "web", "tv_embedded"]},
        }
        attempts.append(("youtube-client-fallback", client_fallback))

        default_attempt = copy.deepcopy(base_opts)
        existing_headers = dict(default_attempt.get("http_headers") or {})
        default_attempt["http_headers"] = {**youtube_headers, **existing_headers}
        attempts.append(("default", default_attempt))

        for browser in ["chrome", "firefox", "safari"]:
            browser_attempt = copy.deepcopy(base_opts)
            existing_headers = dict(browser_attempt.get("http_headers") or {})
            browser_attempt["http_headers"] = {**youtube_headers, **existing_headers}
            browser_attempt["cookiesfrombrowser"] = (browser,)
            browser_attempt["extractor_args"] = {
                "youtube": {"player_client": ["android", "web"]},
            }
            attempts.append((f"cookies-from-{browser}", browser_attempt))
        return attempts

    def _apply_progress_hook(self, ydl_opts: dict, progress_callback=None):
        if not progress_callback:
            return ydl_opts

        def _hook(status_data: dict):
            try:
                status = status_data.get("status")
                downloaded = int(status_data.get("downloaded_bytes") or 0)
                total = int(
                    status_data.get("total_bytes")
                    or status_data.get("total_bytes_estimate")
                    or 0
                )
                if status == "finished":
                    final_total = total or downloaded
                    progress_callback(final_total, final_total)
                else:
                    progress_callback(downloaded, total)
            except Exception:
                pass

        hooked_opts = dict(ydl_opts)
        hooks = list(hooked_opts.get("progress_hooks") or [])
        hooks.append(_hook)
        hooked_opts["progress_hooks"] = hooks
        return hooked_opts

    def _finalize_downloaded_file(
        self,
        base_no_ext: str,
        output_path: str,
        preferred_ext: str = "",
        allow_any_extension: bool = False,
        expected_kind: str = "",
    ) -> bool:
        if os.path.exists(output_path):
            return self._validate_final_file(output_path, expected_kind)

        if preferred_ext:
            preferred_path = f"{base_no_ext}{preferred_ext}"
            if os.path.exists(preferred_path):
                if preferred_path != output_path:
                    os.replace(preferred_path, output_path)
                return self._validate_final_file(output_path, expected_kind)

        if not allow_any_extension:
            return False

        candidates = sorted(glob.glob(f"{base_no_ext}.*"))
        for candidate in candidates:
            if os.path.isfile(candidate) and not candidate.endswith(".part"):
                if candidate != output_path:
                    os.replace(candidate, output_path)
                return os.path.exists(output_path) and self._validate_final_file(
                    output_path,
                    expected_kind,
                )
        return False

    def _validate_final_file(self, output_path: str, expected_kind: str = "") -> bool:
        validation = validate_or_remove(
            output_path,
            expected_kind=expected_kind or None,
        )
        if not validation.ok:
            logger.warning(
                "Downloaded media validation failed for %s: %s",
                output_path,
                validation.reason,
            )
        return validation.ok

    def download(self, video_url, filename, cookies=None, user_agent=None, progress_callback=None):
        if self.platform_name == "youtube":
            return self.download_video_by_source(
                video_url,
                filename,
                user_agent=user_agent,
                progress_callback=progress_callback,
            )
        return super().download(
            video_url,
            filename,
            cookies,
            user_agent,
            progress_callback=progress_callback,
        )

    def download_video_by_source(self, source_url, filename, user_agent=None, progress_callback=None):
        if not source_url or not filename:
            return False

        output_path = os.path.abspath(filename)
        output_dir = os.path.dirname(output_path) or "."
        os.makedirs(output_dir, exist_ok=True)

        base_no_ext, _ = os.path.splitext(output_path)
        base_opts = {
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
            "socket_timeout": 15,
            "retries": 3,
            "fragment_retries": 3,
            "format": "bv*+ba/b",
            "outtmpl": f"{base_no_ext}.%(ext)s",
            "merge_output_format": "mp4",
        }

        if user_agent:
            base_opts["http_headers"] = {"User-Agent": user_agent}

        attempts = self._build_attempts(base_opts)
        last_error = None
        try:
            for attempt_name, ydl_opts in attempts:
                try:
                    run_opts = self._apply_progress_hook(ydl_opts, progress_callback=progress_callback)
                    with profile_scope(
                        "download.video_attempt",
                        platform=self.platform_name,
                        attempt=attempt_name,
                    ):
                        with yt_dlp.YoutubeDL(run_opts) as ydl:
                            ydl.download([source_url])
                    if self._finalize_downloaded_file(
                        base_no_ext,
                        output_path,
                        preferred_ext=".mp4",
                        allow_any_extension=True,
                        expected_kind="video",
                    ):
                        if progress_callback:
                            try:
                                final_size = os.path.getsize(output_path)
                            except OSError:
                                final_size = 0
                            try:
                                progress_callback(final_size, final_size)
                            except Exception:
                                pass
                        return True
                except Exception as exc:
                    last_error = exc
                    logger.warning(
                        "Video download attempt failed for %s (%s): %s",
                        self.platform_name,
                        attempt_name,
                        exc,
                    )
            if last_error:
                raise last_error
            return self._finalize_downloaded_file(
                base_no_ext,
                output_path,
                preferred_ext=".mp4",
                allow_any_extension=True,
                expected_kind="video",
            )
        except Exception as e:
            logger.warning("Video download failed for %s: %s", self.platform_name, e)
            return False

    def download_audio(self, source_url, filename, cookies=None, user_agent=None, progress_callback=None):
        """
        Download audio and convert to MP3 using yt-dlp + ffmpeg.
        """
        if not source_url or not filename:
            return False

        output_path = os.path.abspath(filename)
        output_dir = os.path.dirname(output_path) or "."
        os.makedirs(output_dir, exist_ok=True)

        base_no_ext, _ = os.path.splitext(output_path)
        mp3_path = f"{base_no_ext}.mp3"

        base_opts = {
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
            "socket_timeout": 15,
            "retries": 3,
            "fragment_retries": 3,
            "format": "bestaudio/best",
            "outtmpl": f"{base_no_ext}.%(ext)s",
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }
            ],
        }

        if user_agent:
            base_opts["http_headers"] = {"User-Agent": user_agent}

        attempts = self._build_attempts(base_opts)
        last_error = None
        try:
            for attempt_name, ydl_opts in attempts:
                try:
                    run_opts = self._apply_progress_hook(ydl_opts, progress_callback=progress_callback)
                    with profile_scope(
                        "download.audio_attempt",
                        platform=self.platform_name,
                        attempt=attempt_name,
                    ):
                        with yt_dlp.YoutubeDL(run_opts) as ydl:
                            ydl.download([source_url])
                    if os.path.exists(output_path) or os.path.exists(mp3_path):
                        final_path = mp3_path if os.path.exists(mp3_path) else output_path
                        if not self._validate_final_file(final_path, "audio"):
                            continue
                        if progress_callback:
                            try:
                                final_size = os.path.getsize(final_path)
                            except OSError:
                                final_size = 0
                            try:
                                progress_callback(final_size, final_size)
                            except Exception:
                                pass
                        return True
                except Exception as exc:
                    last_error = exc
                    logger.warning(
                        "Audio download attempt failed for %s (%s): %s",
                        self.platform_name,
                        attempt_name,
                        exc,
                    )
            if last_error:
                raise last_error
            final_path = mp3_path if os.path.exists(mp3_path) else output_path
            return os.path.exists(final_path) and self._validate_final_file(final_path, "audio")
        except Exception as e:
            logger.warning("Audio download failed for %s: %s", self.platform_name, e)
            return False
