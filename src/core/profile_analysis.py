import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List


@dataclass(frozen=True)
class ProfileHotspot:
    name: str
    count: int
    total_ms: float
    avg_ms: float
    max_ms: float
    category: str
    rust_candidate: bool
    recommendation: str


_EXTERNAL_EVENT_PREFIXES = (
    "download.",
    "media_ingestion.ffprobe",
    "media_ingestion.generate_thumbnail",
    "media_ingestion.generate_waveform",
    "media_ingestion.generate_proxy",
    "export.ffmpeg_render",
)

_POTENTIAL_RUST_EVENT_NAMES = {
    "export.render_prepare": "Profile export planner/filter/input assembly in detail; port only CPU-heavy pure planning.",
}

_INSPECT_EVENT_NAMES = {
    "media_ingestion.probe_file": "Broad wrapper includes ffprobe, thumbnail, and waveform; inspect child scopes before porting.",
    "queue.process_task": "Inspect task metadata; queue wrapper time is broad and often dominated by handler IO/model work.",
}


def classify_profile_event(name: str) -> tuple[str, bool, str]:
    if name in _POTENTIAL_RUST_EVENT_NAMES:
        return "python_cpu_candidate", True, _POTENTIAL_RUST_EVENT_NAMES[name]

    if name in _INSPECT_EVENT_NAMES:
        return "inspect", False, _INSPECT_EVENT_NAMES[name]

    if name.startswith(_EXTERNAL_EVENT_PREFIXES):
        return "external_bound", False, "Do not port to Rust; optimize provider, FFmpeg, caching, or concurrency."

    return "unknown", False, "Add narrower profiling before choosing an optimization target."


def analyze_profile_summary(summary_rows: Iterable[Dict[str, object]], limit: int = 20) -> List[ProfileHotspot]:
    hotspots: List[ProfileHotspot] = []
    for row in summary_rows:
        name = str(row.get("name", ""))
        count = int(row.get("count") or 0)
        total_ms = float(row.get("total_ms") or 0.0)
        max_ms = float(row.get("max_ms") or 0.0)
        avg_ms = float(row.get("avg_ms") or (total_ms / count if count else 0.0))
        category, rust_candidate, recommendation = classify_profile_event(name)
        hotspots.append(
            ProfileHotspot(
                name=name,
                count=count,
                total_ms=total_ms,
                avg_ms=avg_ms,
                max_ms=max_ms,
                category=category,
                rust_candidate=rust_candidate,
                recommendation=recommendation,
            )
        )

    hotspots.sort(key=lambda item: item.total_ms, reverse=True)
    return hotspots[:limit]


def analyze_profile_report(report: Dict[str, object], limit: int = 20) -> List[ProfileHotspot]:
    return analyze_profile_summary(report.get("summary", []), limit=limit)


def load_profile_report(path: str) -> Dict[str, object]:
    with Path(path).expanduser().open(encoding="utf-8") as report_file:
        return json.load(report_file)


def format_hotspot_table(hotspots: Iterable[ProfileHotspot]) -> str:
    rows = [
        "rank | total_ms | avg_ms | max_ms | count | category | rust | name",
        "--- | ---: | ---: | ---: | ---: | --- | --- | ---",
    ]
    for index, hotspot in enumerate(hotspots, start=1):
        rows.append(
            " | ".join(
                [
                    str(index),
                    f"{hotspot.total_ms:.1f}",
                    f"{hotspot.avg_ms:.1f}",
                    f"{hotspot.max_ms:.1f}",
                    str(hotspot.count),
                    hotspot.category,
                    "yes" if hotspot.rust_candidate else "no",
                    hotspot.name,
                ]
            )
        )
    return "\n".join(rows)
