import os
import json
import time
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from threading import Lock
from typing import Dict, Iterator, List, Optional

from .logging_utils import get_logger

logger = get_logger(__name__)

_ENABLED_ENV_NAMES = ("VIDEO_TOOL_PROFILE", "VIDEO_TOOL_PROFILING")
_THRESHOLD_ENV_NAME = "VIDEO_TOOL_PROFILE_THRESHOLD_MS"
_OUTPUT_ENV_NAME = "VIDEO_TOOL_PROFILE_OUTPUT"
_DEFAULT_THRESHOLD_MS = 50.0


@dataclass(frozen=True)
class ProfileEvent:
    name: str
    elapsed_ms: float
    metadata: Dict[str, object]


class ProfileCollector:
    def __init__(self) -> None:
        self._events: List[ProfileEvent] = []
        self._lock = Lock()

    def record(self, name: str, elapsed_ms: float, metadata: Optional[Dict[str, object]] = None) -> None:
        event = ProfileEvent(
            name=name,
            elapsed_ms=elapsed_ms,
            metadata=dict(metadata or {}),
        )
        with self._lock:
            self._events.append(event)

    def snapshot(self) -> List[ProfileEvent]:
        with self._lock:
            return list(self._events)

    def reset(self) -> None:
        with self._lock:
            self._events.clear()

    def summary(self, limit: int = 20) -> List[Dict[str, object]]:
        totals: Dict[str, Dict[str, object]] = {}
        for event in self.snapshot():
            row = totals.setdefault(
                event.name,
                {
                    "name": event.name,
                    "count": 0,
                    "total_ms": 0.0,
                    "max_ms": 0.0,
                    "last_metadata": {},
                },
            )
            row["count"] = int(row["count"]) + 1
            row["total_ms"] = float(row["total_ms"]) + event.elapsed_ms
            row["max_ms"] = max(float(row["max_ms"]), event.elapsed_ms)
            row["last_metadata"] = event.metadata

        rows = sorted(
            totals.values(),
            key=lambda item: float(item["total_ms"]),
            reverse=True,
        )
        for row in rows:
            count = int(row["count"])
            row["avg_ms"] = float(row["total_ms"]) / count if count else 0.0
        return rows[:limit]


collector = ProfileCollector()


def is_profiling_enabled() -> bool:
    for env_name in _ENABLED_ENV_NAMES:
        value = os.getenv(env_name, "").strip().lower()
        if value in {"1", "true", "yes", "on"}:
            return True
    return False


def profile_threshold_ms() -> float:
    raw_value = os.getenv(_THRESHOLD_ENV_NAME, "").strip()
    if not raw_value:
        return _DEFAULT_THRESHOLD_MS
    try:
        return max(0.0, float(raw_value))
    except ValueError:
        return _DEFAULT_THRESHOLD_MS


def profile_output_path() -> Optional[str]:
    raw_value = os.getenv(_OUTPUT_ENV_NAME, "").strip()
    return raw_value or None


def record_profile_event(name: str, elapsed_ms: float, **metadata: object) -> None:
    collector.record(name, elapsed_ms, metadata)
    if elapsed_ms < profile_threshold_ms():
        return

    metadata_text = " ".join(
        f"{key}={value}" for key, value in sorted(metadata.items()) if value is not None
    )
    if metadata_text:
        logger.info("[profile] %s %.1fms %s", name, elapsed_ms, metadata_text)
    else:
        logger.info("[profile] %s %.1fms", name, elapsed_ms)


@contextmanager
def profile_scope(name: str, **metadata: object) -> Iterator[None]:
    if not is_profiling_enabled():
        yield
        return

    start_time = time.perf_counter()
    try:
        yield
    finally:
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        record_profile_event(name, elapsed_ms, **metadata)


def build_profile_report(limit: int = 20) -> Dict[str, object]:
    events = collector.snapshot()
    return {
        "event_count": len(events),
        "summary": collector.summary(limit=limit),
        "events": [
            {
                "name": event.name,
                "elapsed_ms": event.elapsed_ms,
                "metadata": event.metadata,
            }
            for event in events
        ],
    }


def write_profile_report(path: str, limit: int = 20) -> None:
    output_path = Path(path).expanduser()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as report_file:
        json.dump(build_profile_report(limit=limit), report_file, ensure_ascii=False, indent=2, default=str)
        report_file.write("\n")


def emit_profile_report(limit: int = 20) -> None:
    if not is_profiling_enabled():
        return

    report = build_profile_report(limit=limit)
    if int(report["event_count"]) == 0:
        logger.info("[profile] no events recorded")
        return

    logger.info("[profile] summary event_count=%s", report["event_count"])
    for row in report["summary"]:
        logger.info(
            "[profile] total=%0.1fms avg=%0.1fms max=%0.1fms count=%s name=%s",
            float(row["total_ms"]),
            float(row["avg_ms"]),
            float(row["max_ms"]),
            int(row["count"]),
            row["name"],
        )

    output_path = profile_output_path()
    if output_path:
        write_profile_report(output_path, limit=limit)
        logger.info("[profile] report written to %s", output_path)
