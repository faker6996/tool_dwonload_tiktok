#!/usr/bin/env python3
"""Rank profiling hotspots and flag realistic Rust candidates."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.core.profile_analysis import (  # noqa: E402
    analyze_profile_report,
    format_hotspot_table,
    load_profile_report,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", help="Path to JSON report written by VIDEO_TOOL_PROFILE_OUTPUT")
    parser.add_argument("--limit", type=int, default=20, help="Maximum number of hotspots to print")
    args = parser.parse_args(argv)

    report = load_profile_report(args.report)
    hotspots = analyze_profile_report(report, limit=args.limit)
    print(format_hotspot_table(hotspots))

    rust_candidates = [hotspot for hotspot in hotspots if hotspot.rust_candidate]
    if rust_candidates:
        print("\nRust candidates:")
        for hotspot in rust_candidates:
            print(f"- {hotspot.name}: {hotspot.recommendation}")
    else:
        print("\nRust candidates: none from current report")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
