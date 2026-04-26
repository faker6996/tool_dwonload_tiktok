from __future__ import annotations

from dataclasses import dataclass
import hashlib
import os
import shutil
import tempfile
from typing import Callable, Optional

from .media_validation import infer_media_kind, validate_media_file


ProgressCallback = Callable[[int, int], None]


@dataclass(frozen=True)
class CopyResult:
    ok: bool
    path: str = ""
    reason: str = ""
    size: int = 0


def make_temp_path(destination_path: str, suffix: str = ".part") -> str:
    destination_dir = os.path.dirname(os.path.abspath(destination_path)) or "."
    os.makedirs(destination_dir, exist_ok=True)
    temp_fd, temp_path = tempfile.mkstemp(
        prefix=f"{os.path.basename(destination_path)}_",
        suffix=suffix,
        dir=destination_dir,
    )
    os.close(temp_fd)
    return temp_path


def atomic_replace_validated(
    temp_path: str,
    destination_path: str,
    *,
    expected_kind: Optional[str] = None,
    min_bytes: int = 1,
) -> CopyResult:
    validation = validate_media_file(
        temp_path,
        min_bytes=min_bytes,
        expected_kind=expected_kind or infer_media_kind(destination_path),
    )
    if not validation.ok:
        remove_file_quietly(temp_path)
        return CopyResult(False, reason=validation.reason, size=validation.size)

    os.makedirs(os.path.dirname(os.path.abspath(destination_path)) or ".", exist_ok=True)
    os.replace(temp_path, destination_path)
    return CopyResult(True, path=destination_path, size=validation.size)


def copy_file_atomic(
    source_path: str,
    destination_path: str,
    *,
    expected_kind: Optional[str] = None,
    progress_callback: Optional[ProgressCallback] = None,
    chunk_size: int = 1024 * 1024,
) -> CopyResult:
    source_validation = validate_media_file(
        source_path,
        expected_kind=expected_kind or infer_media_kind(source_path),
    )
    if not source_validation.ok:
        return CopyResult(False, reason=source_validation.reason, size=source_validation.size)

    temp_path = make_temp_path(destination_path)
    copied = 0
    try:
        with open(source_path, "rb") as source_file, open(temp_path, "wb") as output_file:
            while True:
                chunk = source_file.read(chunk_size)
                if not chunk:
                    break
                output_file.write(chunk)
                copied += len(chunk)
                _emit_progress(progress_callback, copied, source_validation.size)

        result = atomic_replace_validated(
            temp_path,
            destination_path,
            expected_kind=expected_kind or infer_media_kind(destination_path),
        )
        if result.ok:
            _emit_progress(progress_callback, result.size, result.size)
        return result
    except OSError as exc:
        remove_file_quietly(temp_path)
        return CopyResult(False, reason=str(exc), size=copied)


def copy_file_best_effort(source_path: str, destination_path: str) -> bool:
    try:
        os.makedirs(os.path.dirname(os.path.abspath(destination_path)) or ".", exist_ok=True)
        temp_path = make_temp_path(destination_path, suffix=".tmp")
        shutil.copy2(source_path, temp_path)
        os.replace(temp_path, destination_path)
        return True
    except OSError:
        try:
            remove_file_quietly(temp_path)
        except UnboundLocalError:
            pass
        return False


def stable_file_cache_key(path: str) -> str:
    try:
        stat = os.stat(path)
        return f"{os.path.abspath(path)}:{stat.st_mtime_ns}:{stat.st_size}"
    except OSError:
        return os.path.abspath(path)


def stable_file_hash(path: str, length: Optional[int] = None) -> str:
    digest = hashlib.md5(stable_file_cache_key(path).encode()).hexdigest()
    if length is None:
        return digest
    return digest[: max(0, length)]


def remove_file_quietly(path: str) -> None:
    try:
        if path and os.path.exists(path):
            os.remove(path)
    except OSError:
        pass


def _emit_progress(
    progress_callback: Optional[ProgressCallback],
    downloaded: int,
    total: int,
) -> None:
    if not progress_callback:
        return
    try:
        progress_callback(downloaded, total)
    except Exception:
        pass
