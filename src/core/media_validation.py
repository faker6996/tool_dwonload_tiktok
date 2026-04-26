from __future__ import annotations

from dataclasses import dataclass
import os
from typing import Optional


TEXT_ERROR_KEYWORDS = (
    "error",
    "forbidden",
    "access denied",
    "not found",
    "captcha",
    "unauthorized",
    "permission denied",
)

MEDIA_EXTENSIONS = {
    ".mp4",
    ".mov",
    ".avi",
    ".mkv",
    ".mp3",
    ".wav",
    ".m4a",
    ".aac",
    ".png",
    ".jpg",
    ".jpeg",
}


@dataclass(frozen=True)
class MediaValidationResult:
    ok: bool
    reason: str = ""
    size: int = 0


def validate_media_file(
    path: str,
    *,
    min_bytes: int = 1,
    expected_kind: Optional[str] = None,
) -> MediaValidationResult:
    if not path:
        return MediaValidationResult(False, "missing path")
    if not os.path.exists(path):
        return MediaValidationResult(False, "file does not exist")
    if not os.path.isfile(path):
        return MediaValidationResult(False, "path is not a file")

    try:
        size = os.path.getsize(path)
    except OSError as exc:
        return MediaValidationResult(False, f"cannot stat file: {exc}")

    if size < max(1, min_bytes):
        return MediaValidationResult(False, f"file too small: {size} bytes", size)

    head = _read_head(path)
    if not head:
        return MediaValidationResult(False, "file is empty or unreadable", size)

    extension = os.path.splitext(path)[1].lower()
    if _looks_like_html(head):
        return MediaValidationResult(False, "downloaded content looks like HTML", size)
    if (extension in MEDIA_EXTENSIONS or expected_kind in {"audio", "video", "media"}) and _looks_like_text_error(head):
        return MediaValidationResult(False, "downloaded content looks like a text error page", size)

    if expected_kind == "image" and not _looks_like_image(head):
        return MediaValidationResult(False, "file does not look like an image", size)

    return MediaValidationResult(True, "", size)


def infer_media_kind(path: str) -> Optional[str]:
    extension = os.path.splitext(path)[1].lower()
    if extension in {".mp4", ".mov", ".avi", ".mkv"}:
        return "video"
    if extension in {".mp3", ".wav", ".m4a", ".aac"}:
        return "audio"
    if extension in {".png", ".jpg", ".jpeg"}:
        return "image"
    return None


def validate_or_remove(
    path: str,
    *,
    min_bytes: int = 1,
    expected_kind: Optional[str] = None,
) -> MediaValidationResult:
    result = validate_media_file(path, min_bytes=min_bytes, expected_kind=expected_kind)
    if not result.ok:
        try:
            if path and os.path.exists(path):
                os.remove(path)
        except OSError:
            pass
    return result


def _read_head(path: str, limit: int = 1024) -> bytes:
    try:
        with open(path, "rb") as file_obj:
            return file_obj.read(limit)
    except OSError:
        return b""


def _looks_like_html(head: bytes) -> bool:
    text = head.lstrip()[:512].lower()
    return (
        text.startswith(b"<!doctype html")
        or text.startswith(b"<html")
        or text.startswith(b"<?xml")
        or b"<html" in text[:256]
        or b"<body" in text[:256]
    )


def _looks_like_text_error(head: bytes) -> bool:
    if b"\x00" in head[:256]:
        return False

    try:
        text = head[:512].decode("utf-8", errors="strict").strip().lower()
    except UnicodeDecodeError:
        return False

    if not text:
        return False

    printable_count = sum(1 for char in text if char.isprintable() or char.isspace())
    printable_ratio = printable_count / max(1, len(text))
    if printable_ratio < 0.9:
        return False

    return any(keyword in text for keyword in TEXT_ERROR_KEYWORDS)


def _looks_like_image(head: bytes) -> bool:
    return (
        head.startswith(b"\x89PNG\r\n\x1a\n")
        or head.startswith(b"\xff\xd8\xff")
        or head.startswith(b"GIF87a")
        or head.startswith(b"GIF89a")
    )
