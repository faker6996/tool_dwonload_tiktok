# Rust Integration Plan

## Goal

Keep Python/PyQt responsible for UI, downloads, AI orchestration, and FFmpeg process control. Add a Rust core for deterministic, data-heavy logic where speed, validation, and thread safety matter.

## Current Status

| Phase | Status | Scope | Notes |
| --- | --- | --- | --- |
| Phase 1 | Completed | Rust crate + Python boundary skeleton | `rust/video_core` exists with PyO3-compatible API and Rust tests. |
| Phase 2 | Completed | Timeline core | Rust core is split into clean modules and `MagneticTrack` delegates through an optional Python adapter when `video_core` is installed. |
| Phase 3 | Partially completed | Export planner | Rust `ExportPlan` now validates clips, overlay inputs, gaps, speed, fps, resolution, and filter/output command requirements before Python builds FFmpeg commands. |
| Phase 4 | Not started | Media validation + IO | Validate downloaded media, atomic copy/move, cache keys, file scanning. |
| Phase 5 | Not started | Queue core | Safer task state machine, cancellation, progress contracts. |
| Phase 6 | Partially completed | Build and packaging | Local `maturin build` path works. CI and PyInstaller bundling are still pending. |

## Design Rules

- Do not rewrite the PyQt UI.
- Do not replace `yt-dlp`, Playwright, Whisper, OCR, TTS, or translation providers.
- Do not encode/decode media in Rust; keep FFmpeg as the media engine.
- Rust APIs must use plain data structures that serialize cleanly to Python dicts/lists.
- Each phase must land with tests and must not break the existing Python test suite.

## Phase 1: Boundary Skeleton

Deliverables:
- Added `rust/video_core` crate.
- Exposed a small `video_core` Python module via PyO3.
- Added Rust-side `CoreClip` and Python-facing `Clip` as the first stable boundary.
- Verified with `cargo test`.

Acceptance criteria:
- `cargo test --manifest-path rust/video_core/Cargo.toml` passes.
- Existing `QT_QPA_PLATFORM=offscreen pytest -q` passes.
- The plan file is updated with actual status after verification.

Verification:
- `cargo test --manifest-path rust/video_core/Cargo.toml`: 2 passed.
- `QT_QPA_PLATFORM=offscreen pytest -q`: 50 passed.

Build note:
- Local Rust unit tests use default Cargo features.
- Python extension builds should use `--features extension-module` because PyO3 extension modules link differently from native Rust tests on macOS.

## Phase 2: Timeline Core

Status:
- Phase 2A completed: Rust-side timeline core and tests.
- Phase 2B completed: Python runtime delegation through a compatibility adapter.

Scope:
- Port pure timeline logic from Python to Rust:
  - `Clip`
  - `Track`
  - `MagneticTrack`
  - add/remove/split/trim/ripple
  - validation for overlap and invalid trim ranges
- Keep Python UI-facing APIs compatible while internally delegating to Rust.

Acceptance criteria:
- Existing timeline tests pass through the Rust-backed implementation.
- Add parity tests comparing existing Python behavior to Rust behavior before replacing the Python path.

Completed in Phase 2A:
- Added Rust `CoreTrack` and `CoreMagneticTrack`.
- Added Rust implementations for append, insert, remove, split, trim, ripple shifting, locked-track rejection, and no-overlap validation.
- Exposed Python-facing PyO3 `MagneticTrack` wrapper for the future native module path.
- Added Rust parity tests mirroring existing Python timeline behavior.

Completed in Phase 2B:
- Split Rust into `core` and `bindings` modules instead of keeping all logic in `lib.rs`.
- Added `src/core/timeline/rust_adapter.py` to keep existing Python `Clip` objects stable while delegating timeline mutations to Rust.
- Updated Python `MagneticTrack` to use Rust when `video_core` is installed and fallback to Python when it is unavailable.
- Added adapter tests covering add, split, remove, and Python object sync.

Verification:
- `cargo fmt --manifest-path rust/video_core/Cargo.toml --check`: passed.
- `cargo test --manifest-path rust/video_core/Cargo.toml`: 11 passed.
- `python -m maturin build --manifest-path rust/video_core/Cargo.toml --features extension-module --out rust/video_core/dist`: passed.
- `python -m pip install --force-reinstall rust/video_core/dist/video_core-0.1.0-cp311-cp311-macosx_11_0_arm64.whl`: passed.
- Python `import video_core` smoke test: passed.
- `QT_QPA_PLATFORM=offscreen pytest -q`: 53 passed.

## Phase 3: Export Planner

Status:
- Phase 3A completed: export timing and concat plan validation.
- Phase 3B completed: overlay/audio/subtitle/filter-complex decisions are represented in structured plans.
- Phase 3C completed: timeline gaps and filter steps are explicit typed plan data.
- Phase 3D completed: FFmpeg filter graph string assembly is isolated from the renderer.
- Phase 3E completed: gap reject policy and typed FFmpeg output command options are planned outside the renderer.
- Phase 3F completed: FFmpeg input files and temporary export assets are planned outside the renderer.

Scope:
- Create a Rust `ExportPlan` from timeline data.
- Validate:
  - missing files
  - invalid durations
  - timeline gaps
  - trim ranges
  - speed values
  - audio offsets
- Return a structured plan consumed by Python FFmpeg renderer.

Acceptance criteria:
- Export planner tests cover concat ordering, gaps, audio delay, text/subtitle layers, and speed.
- Python renderer stops building critical timing decisions ad hoc.

Completed in Phase 3A:
- Added Rust `ExportPlan`, `ExportClipPlan`, and `ExportPlanSettings`.
- Added native `build_export_plan_json` Python binding.
- Added Python `src/core/export/planner.py` adapter with native Rust path and Python fallback.
- Updated renderer concat generation to consume the export plan instead of doing timing normalization inline.
- Added Rust and Python tests for clip ordering, trim normalization, speed, missing paths, and invalid clip rejection.

Completed in Phase 3B:
- Added structured Rust plan data for stickers, subtitles, audio tracks, and filter-complex requirements.
- Added native `build_export_plan_full_json` binding for clip + overlay export planning.
- Updated Python export planner to normalize overlays/audio through native Rust when available and fallback to Python otherwise.
- Updated renderer to consume planned stickers, subtitles, audio tracks, and filter flags instead of raw UI payloads.

Completed in Phase 3C:
- Added `ExportGapPlan` with explicit `omit` policy for current concat behavior.
- Added `ExportFilterStep` entries for video subtitles, speed, overlays, audio mix, and audio speed.
- Updated Python export planner to expose `gaps`, `filter_steps`, and `has_filter_step()`.
- Updated renderer to consume typed filter steps for speed filters.

Completed in Phase 3D:
- Added `src/core/export/filter_graph.py` as the single place that builds `filter_complex` and map args.
- Updated renderer to pass planned filters/resources into `build_filter_graph()`.
- Added filter graph tests for speed-only export and overlay/audio-mix/audio-speed export.

Completed in Phase 3E:
- Added `gap_policy` to export settings with `omit` as the default and `reject` for strict validation.
- Added native Rust and Python fallback behavior that rejects timeline gaps before FFmpeg command creation when requested.
- Added `src/core/export/command_plan.py` to plan output size, fps, audio codec, and video codec args outside the renderer.
- Updated renderer to consume `OutputCommandPlan` instead of assembling those output args inline.
- Added tests for command planning and gap-policy behavior.

Completed in Phase 3F:
- Added `src/core/export/input_plan.py` to plan concat input, additional FFmpeg inputs, temporary files, sticker overlays, audio input counts, render size, and source-audio probing.
- Added `src/core/export/subtitle_asset.py` for ASS subtitle temp-file generation.
- Added `src/core/export/media_probe.py` for source resolution and audio probing.
- Updated renderer to consume `InputAssetPlan` instead of creating concat files, stickers, subtitles, audio inputs, and media probes inline.
- Added input-plan tests for concat trims, audio inputs, subtitle assets, ASS time formatting, and sticker input planning.

Deferred after Phase 3F:
- Black-filled timeline gaps remain optional. Current supported gap policies are `omit` and `reject`; black fill needs synthetic video generation and should be handled as a separate feature.

Verification:
- `cargo fmt --manifest-path rust/video_core/Cargo.toml --check`: passed.
- `cargo test --manifest-path rust/video_core/Cargo.toml`: 15 passed.
- Native `video_core.build_export_plan_full_json` gap-reject smoke test: passed.
- `QT_QPA_PLATFORM=offscreen pytest -q`: 66 passed.

## Phase 4: Media Validation And IO

Scope:
- Validate output files after download:
  - container signatures
  - minimum byte size
  - reject HTML/error pages saved as media
- Provide atomic copy/move helpers with progress.
- Create stable cache keys from path, size, and mtime.

Acceptance criteria:
- Bulk/import cannot save HTML as `.mp4`.
- Download validation tests cover success, HTTP error pages, partial files, and unknown content-length.

## Phase 5: Queue Core

Scope:
- Move task claiming and state transitions into Rust.
- Provide atomic task claim to avoid duplicate execution with multiple workers.
- Standardize cancel token and progress event payload.

Acceptance criteria:
- Multi-worker race tests pass.
- Running task cancellation semantics are explicit and tested.

## Phase 6: Build And Packaging

Status:
- Local build path completed.
- `maturin` added to Python requirements.
- CI wheel builds and PyInstaller native-extension bundling remain pending.

Scope:
- Add `maturin` build path.
- Build native wheels in CI for macOS and Windows.
- Bundle native extension in PyInstaller.
- Add smoke test that imports `video_core` from packaged artifact.

Acceptance criteria:
- CI runs Python tests before packaging.
- CI builds Rust extension and PyInstaller artifact.
- Packaged app can import and use `video_core`.

Local build commands:
- `python -m maturin build --manifest-path rust/video_core/Cargo.toml --features extension-module --out rust/video_core/dist`
- `python -m pip install --force-reinstall rust/video_core/dist/video_core-0.1.0-cp311-cp311-macosx_11_0_arm64.whl`

## Immediate Next Steps

1. Start Phase 4 by adding media validation helpers for downloaded/imported files.
2. Add CI jobs for `cargo test`, Python tests, and `maturin build`.
3. Add PyInstaller packaging checks for the native `video_core` extension.
