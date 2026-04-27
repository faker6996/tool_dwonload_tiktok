# Rust Integration Plan

## Goal

Keep Python/PyQt responsible for UI, downloads, AI orchestration, and FFmpeg process control. Add a Rust core for deterministic, data-heavy logic where speed, validation, and thread safety matter.

## Current Status

| Phase | Status | Scope | Notes |
| --- | --- | --- | --- |
| Phase 1 | Completed | Rust crate + Python boundary skeleton | `rust/video_core` exists with PyO3-compatible API and Rust tests. |
| Phase 2 | Completed | Timeline core | Rust core is split into clean modules and `MagneticTrack` delegates through an optional Python adapter when `video_core` is installed. |
| Phase 3 | Completed | Export planner | Rust `ExportPlan` validates clips, overlay inputs, gaps, speed, fps, resolution, and filter/output command requirements before Python builds FFmpeg commands. |
| Phase 4 | Completed | Media validation + IO | Download/import validation, atomic copy/replace, and cache keys are covered by shared helpers and tests. |
| Phase 5 | Partially completed | Queue core | Deterministic queue state decisions are in Rust; long-running Qt worker cancellation integration tests are still deferred. |
| Phase 6 | Completed | Build and packaging | CI, local scripts, PyInstaller spec, and packaged smoke checks now include the native Rust extension. |
| Phase 7 | Partially completed | Profiling and hotspot selection | Lightweight profiling is available for download, ingestion, export, and queue task paths before choosing the next Rust target. |

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

Status:
- Phase 4A completed: downloaded/imported media files are validated before final save or ingestion.
- Phase 4B completed: shared atomic copy/replace and cache-key helpers are used by download, copy, and ingestion paths.

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

Completed in Phase 4A:
- Added `src/core/media_validation.py` with size checks, HTML/error-page detection, image signature validation, invalid-file cleanup, and extension-based kind inference.
- Updated direct URL downloads to validate temporary files before atomic replace.
- Updated yt-dlp video/audio finalization to validate the final media file and remove invalid outputs.
- Updated stock media downloads to validate `.part` files before atomic replace.
- Updated media ingestion and preview-file copying to reject invalid imported/copied media before use.
- Added tests for validation helpers, HTML/text-error rejection, and stock/download cleanup.

Completed in Phase 4B:
- Added `src/core/media_io.py` with temp-path creation, validated atomic replace, progress-aware atomic copy, best-effort proxy copy, quiet cleanup, and stable file cache hashing.
- Updated direct URL downloads and stock downloads to use shared temp-path and validated atomic replace helpers.
- Updated preview/source-file copy to use shared progress-aware atomic copy.
- Updated thumbnail, waveform, proxy, and asset ID cache keys to use a shared path/mtime/size hash helper.
- Added tests for atomic replace, invalid cleanup, progress copy, invalid source rejection, and cache hash stability.

Verification:
- `QT_QPA_PLATFORM=offscreen pytest -q tests/test_media_validation.py tests/test_base_downloader.py tests/test_stock_api.py tests/test_ingestion.py tests/test_audio_download_mode.py tests/test_youtube_video_flow.py`: 23 passed.
- `QT_QPA_PLATFORM=offscreen pytest -q tests/test_media_io.py tests/test_media_validation.py tests/test_base_downloader.py tests/test_stock_api.py tests/test_ingestion.py tests/test_ingestion_proxy.py tests/test_youtube_video_flow.py`: 29 passed.
- `cargo fmt --manifest-path rust/video_core/Cargo.toml --check`: passed.
- `cargo test --manifest-path rust/video_core/Cargo.toml`: 15 passed.
- `QT_QPA_PLATFORM=offscreen pytest -q`: 80 passed.

## Phase 5: Queue Core

Status:
- Phase 5A completed: task state-transition rules are isolated in a tested Python core module.
- Phase 5B completed: running tasks support cooperative cancellation tokens and compatible handler propagation.
- Phase 5C completed: deterministic queue state decisions are ported to Rust with Python fallback.

Scope:
- Move task claiming and state transitions into Rust.
- Provide atomic task claim to avoid duplicate execution with multiple workers.
- Standardize cancel token and progress event payload.

Acceptance criteria:
- Multi-worker race tests pass.
- Running task cancellation semantics are explicit and tested.

Completed in Phase 5A:
- Added `src/core/queue_core.py` with `TaskType`, `TaskStatus`, `QueueTask`, allowed transition rules, progress clamping, pending-task claiming, pending cancellation, terminal cleanup, and status counting.
- Updated `src/core/queue_manager.py` to re-export and consume the queue core instead of mutating task state ad hoc.
- Changed task claiming so a pending task is marked `running` while still under the queue lock, preventing duplicate claims with multiple workers.
- Added queue-core tests for claim uniqueness, invalid terminal transitions, pending-only cancellation, progress clamping, terminal cleanup, and status counts.
- Added queue-manager tests for lazy startup, handler registration, synchronous claim semantics, cancel rules, and terminal cleanup.

Completed in Phase 5B:
- Added `CancellationToken` to `QueueTask` and serialized `cancelRequested` into task dictionaries.
- Added `request_task_cancellation()` so pending tasks cancel immediately and running tasks receive a cancellation token with a reason.
- Updated `QueueManager.cancel_task()` to request cooperative cancellation for running tasks instead of only handling pending tasks.
- Updated `QueueWorker` to pass cancellation tokens to handlers that accept a third positional argument while keeping old two-argument handlers compatible.
- Updated transcription, OCR, TTS, and subtitle-removal queue handlers to accept and check cancellation tokens at safe checkpoints.
- Added tests for running cancellation, token serialization, cancel request propagation, and handler signature compatibility.

Completed in Phase 5C:
- Ported queue progress clamping, transition validation, cancellation decisions, and status counts to `rust/video_core/src/core/queue.rs`.
- Exposed queue core decisions through PyO3 functions in `video_core`.
- Updated `src/core/queue_core.py` to use native Rust queue decisions when available and fall back to Python logic otherwise.
- Kept PyQt worker/thread orchestration in Python; only deterministic state decisions moved to Rust.
- Added Rust queue tests and Python native-adapter coverage for applying native transition/cancellation/count results.

Pending after Phase 5:
- Add integration coverage for long-running worker cancellation once queue tests can safely run Qt worker threads in CI.

Verification:
- `QT_QPA_PLATFORM=offscreen pytest -q tests/test_queue_core.py tests/test_queue_manager.py`: 10 passed.
- `QT_QPA_PLATFORM=offscreen pytest -q tests/test_queue_core.py tests/test_queue_manager.py`: 14 passed.
- `cargo fmt --manifest-path rust/video_core/Cargo.toml --check`: passed.
- `cargo test --manifest-path rust/video_core/Cargo.toml`: 20 passed.
- `python -m maturin build --manifest-path rust/video_core/Cargo.toml --features extension-module --out rust/video_core/dist`: passed.
- `python -m pip install --force-reinstall rust/video_core/dist/video_core-0.1.0-cp311-cp311-macosx_11_0_arm64.whl`: passed.
- Native `video_core.queue_transition_json` smoke test: passed.
- `QT_QPA_PLATFORM=offscreen pytest -q`: 93 passed.

## Phase 6: Build And Packaging

Status:
- Local build path completed.
- `maturin` added to Python requirements.
- Phase 6A completed: CI now builds/tests Rust and Python, builds the native wheel, and smoke-tests `video_core`.
- Phase 6B completed: PyInstaller build paths include `video_core` and run packaged smoke checks.
- Phase 6C completed: local spec/script packaging paths are aligned with CI smoke checks.

Scope:
- Add `maturin` build path.
- Build native wheels in CI for macOS and Windows.
- Bundle native extension in PyInstaller.
- Add smoke test that imports `video_core` from packaged artifact.

Acceptance criteria:
- CI runs Python tests before packaging.
- CI builds Rust extension and PyInstaller artifact.
- Packaged app can import and use `video_core`.

Completed in Phase 6A:
- Added `test-native-core` GitHub Actions job for Rust format check, Rust tests, `maturin build`, native extension install, native smoke, and Python tests.
- Added `--smoke-native-core` CLI path in `main.py` that imports `video_core` and validates a queue transition without starting PyQt.

Completed in Phase 6B:
- Updated macOS, Linux, and Windows build jobs to install Rust, build/install the native extension before PyInstaller, include `video_core` as a hidden import, and run packaged smoke checks.
- Updated local macOS and Windows build scripts to build/install the native extension and smoke-test both Python and packaged app paths.
- Updated `VideoDownloader.spec` to include `video_core` as a hidden import.

Completed in Phase 6C:
- Added `scripts/smoke_package.py` as the shared packaged-app smoke check for CI and local builds.
- Updated CI packaged smoke steps and local macOS/Windows scripts to call the shared smoke script instead of hardcoding separate command behavior.
- Reconciled `VideoDownloader.spec` with the current `VideoEditor` app name, assets, optional bundled FFmpeg binary, PyInstaller hidden imports, and native `video_core` packaging.
- Reviewed release packaging: current release job only uploads already-smoked artifacts and does not transform them, so no additional release smoke step is required yet.

Local build commands:
- `python -m maturin build --manifest-path rust/video_core/Cargo.toml --features extension-module --out rust/video_core/dist`
- `python -m pip install --force-reinstall rust/video_core/dist/video_core-0.1.0-cp311-cp311-macosx_11_0_arm64.whl`

Verification:
- `ruby -e 'require "yaml"; YAML.load_file(".github/workflows/build.yml")'`: passed.
- `python -m py_compile main.py scripts/smoke_package.py src/core/queue_core.py src/core/queue_manager.py`: passed.
- `compile(Path("VideoDownloader.spec").read_text(), "VideoDownloader.spec", "exec")`: passed.
- `python main.py --smoke-native-core`: passed.
- `python scripts/smoke_package.py /bin/echo`: passed.
- `cargo fmt --manifest-path rust/video_core/Cargo.toml --check`: passed.
- `cargo test --manifest-path rust/video_core/Cargo.toml`: 20 passed.
- `QT_QPA_PLATFORM=offscreen pytest -q`: 93 passed.

## Phase 7: Profiling And Hotspot Selection

Status:
- Phase 7A completed: lightweight profiling hooks are available around high-latency paths.
- Phase 7B completed: profiling can emit ranked summaries and JSON reports after app exit.
- Phase 7C completed: profiling reports can be analyzed to separate Rust candidates from external-bound work.
- Phase 7D completed: local app startup and realistic ingest/export profiling flow were run successfully.

Scope:
- Measure real latency before porting more code to Rust.
- Keep profiling disabled by default and controlled by environment variables.
- Focus first on paths the user actually feels: metadata extraction, downloads, media ingestion, export planning/rendering, and queue handlers.

Acceptance criteria:
- Profiling adds negligible overhead when disabled.
- Profiling can be enabled without starting a different app mode.
- Collected events identify the next Rust target from measured hotspots, not guesses.

Completed in Phase 7A:
- Added `src/core/profiling.py` with `profile_scope`, a thread-safe collector, summaries, thresholded logging, and env toggles.
- Added profiling around YouTube/generic metadata extraction and audio/video download attempts.
- Added profiling around media probe, ffprobe, thumbnail, waveform, and proxy generation.
- Added profiling around export preparation, FFmpeg render execution, and queue task handler execution.
- Added tests for disabled/enabled profiling behavior, summary ordering, and env parsing.

Completed in Phase 7B:
- Added profile report generation with event count, ranked summary, raw events, and optional JSON output.
- Added app-exit report emission through `QApplication.aboutToQuit` after queue shutdown.
- Added `VIDEO_TOOL_PROFILE_OUTPUT` support for writing profiling reports to disk.
- Added tests for report generation, JSON writing, and configured app-exit emission.

Completed in Phase 7C:
- Added `src/core/profile_analysis.py` to classify profile hotspots as Rust candidates, external-bound work, broad inspection scopes, or unknown.
- Added `scripts/analyze_profile_report.py` to print ranked hotspot tables and explicit Rust-candidate recommendations from a JSON report.
- Added tests for event classification, report loading, hotspot ordering, and table formatting.

Completed in Phase 7D:
- Ran local app startup smoke with `QT_QPA_PLATFORM=offscreen`; `MainWindow` initialized and exited cleanly.
- Ran a realistic local flow: generated a 2-second FFmpeg source video, ingested it, generated thumbnail/waveform, exported at `speed=1.25` with original resolution/FPS and burned subtitle.
- Verified exported video resolution stayed `320x240`, render completed with progress `100`, and output duration was about `1.65s`.
- Found and fixed short-video thumbnail generation: seek no longer starts at `00:00:05.000` when media duration is shorter.
- Adjusted hotspot classification so broad `media_ingestion.probe_file` is `inspect` instead of an immediate Rust candidate.
- Current real-flow analyzer result: only `export.render_prepare` is marked `rust=yes`; FFmpeg render, thumbnail, waveform, and ffprobe are external-bound.

How to run profiling:
- `VIDEO_TOOL_PROFILE=1 python main.py`
- Optional noise control: `VIDEO_TOOL_PROFILE_THRESHOLD_MS=100 VIDEO_TOOL_PROFILE=1 python main.py`
- Optional JSON report: `VIDEO_TOOL_PROFILE=1 VIDEO_TOOL_PROFILE_OUTPUT=profile_report.json python main.py`
- Analyze report: `python scripts/analyze_profile_report.py profile_report.json`

Verification:
- `python -m py_compile src/core/profiling.py src/core/ingestion.py src/core/export/renderer.py src/core/platforms/generic.py src/core/queue_manager.py tests/test_profiling.py`: passed.
- `QT_QPA_PLATFORM=offscreen pytest -q tests/test_profiling.py tests/test_queue_manager.py tests/test_ingestion.py tests/test_export.py tests/test_audio_download_mode.py tests/test_youtube_video_flow.py`: 17 passed.
- `VIDEO_TOOL_PROFILE=1 VIDEO_TOOL_PROFILE_THRESHOLD_MS=0` profiling smoke: passed.
- `python -m py_compile main.py src/core/profiling.py tests/test_profiling.py`: passed.
- `QT_QPA_PLATFORM=offscreen pytest -q tests/test_profiling.py tests/test_queue_manager.py`: 12 passed.
- `VIDEO_TOOL_PROFILE=1 VIDEO_TOOL_PROFILE_OUTPUT=<tmp> VIDEO_TOOL_PROFILE_THRESHOLD_MS=0` report smoke: passed.
- `cargo fmt --manifest-path rust/video_core/Cargo.toml --check`: passed.
- `cargo test --manifest-path rust/video_core/Cargo.toml`: 20 passed.
- `QT_QPA_PLATFORM=offscreen pytest -q`: 99 passed.
- `python -m py_compile src/core/profile_analysis.py scripts/analyze_profile_report.py tests/test_profile_analysis.py`: passed.
- `QT_QPA_PLATFORM=offscreen pytest -q tests/test_profile_analysis.py tests/test_profiling.py`: 9 passed.
- `python scripts/analyze_profile_report.py <tmp-report> --limit 5`: passed.
- `cargo fmt --manifest-path rust/video_core/Cargo.toml --check`: passed.
- `cargo test --manifest-path rust/video_core/Cargo.toml`: 20 passed.
- `QT_QPA_PLATFORM=offscreen pytest -q`: 102 passed.
- `QT_QPA_PLATFORM=offscreen` app startup smoke: passed.
- Real local ingest/export/profile flow: passed; output `320x240`, duration about `1.65s`, progress `100`.
- `python -m py_compile src/core/ingestion.py tests/test_ingestion.py`: passed.
- `QT_QPA_PLATFORM=offscreen pytest -q tests/test_ingestion.py tests/test_profile_analysis.py tests/test_profiling.py`: 12 passed.
- `python scripts/analyze_profile_report.py /tmp/video_tool_real_profile.json --limit 20`: passed.
- `QT_QPA_PLATFORM=offscreen pytest -q`: 104 passed.

## Immediate Next Steps

1. Add narrower profiling inside `export.render_prepare` to split native planner, input plan, subtitle asset creation, audio probe, and filter graph assembly.
2. Use that narrower report before porting any more export code to Rust.
3. Add long-running Qt worker cancellation integration coverage when the queue test harness is safe for CI.
