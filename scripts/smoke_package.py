#!/usr/bin/env python3
"""Smoke-test a packaged app without starting the PyQt UI."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def _project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _default_candidates(project_root: Path) -> list[Path]:
    return [
        project_root / "dist" / "VideoEditor.app" / "Contents" / "MacOS" / "VideoEditor",
        project_root / "dist" / "VideoEditor" / "VideoEditor.exe",
        project_root / "dist" / "VideoEditor" / "VideoEditor",
        project_root / "dist" / "VideoEditor.exe",
        project_root / "dist" / "VideoDownloader.app" / "Contents" / "MacOS" / "VideoDownloader",
        project_root / "dist" / "VideoDownloader" / "VideoDownloader.exe",
        project_root / "dist" / "VideoDownloader" / "VideoDownloader",
        project_root / "dist" / "VideoDownloader.exe",
    ]


def _resolve_executable(args: list[str], project_root: Path) -> Path:
    if args:
        candidate = Path(args[0])
        if not candidate.is_absolute():
            candidate = project_root / candidate
        return candidate

    for candidate in _default_candidates(project_root):
        if candidate.exists():
            return candidate

    searched = "\n".join(f"- {path}" for path in _default_candidates(project_root))
    raise FileNotFoundError(f"No packaged executable found. Searched:\n{searched}")


def main(argv: list[str]) -> int:
    project_root = _project_root()
    executable = _resolve_executable(argv[1:], project_root)
    if not executable.exists():
        raise FileNotFoundError(f"Packaged executable does not exist: {executable}")

    subprocess.run([str(executable), "--smoke-native-core"], check=True)
    print(f"Packaged smoke ok: {executable}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
