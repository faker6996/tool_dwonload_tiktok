# Universal Video Downloader – Kiến trúc hệ thống

## 1. Mục tiêu sản phẩm

Ứng dụng desktop giúp người dùng tải video **không watermark** từ nhiều nền tảng (TikTok, Douyin, YouTube, Threads, Facebook, Instagram, X/Twitter), xem trước (preview), chỉnh sửa cơ bản trên timeline và xuất (export).  
Ứng dụng được xây dựng bằng **Python + PyQt6**, có thể đóng gói thành executable bằng **PyInstaller**.

---

## 2. Kiến trúc tổng thể

Hệ thống được chia thành 3 lớp chính:

- **UI Layer** – `src/ui`
  - Chịu trách nhiệm giao diện người dùng (PyQt6).
  - Các màn hình chính:
    - `MainWindow` – `src/ui/main_window.py`: cửa sổ chính, chứa sidebar + header + vùng nội dung.
    - `DownloadPage` – `src/ui/pages/download_page.py`: nhập URL, preview, download.
    - `EditPage` – `src/ui/pages/edit_page.py`: giao diện timeline, chỉnh sửa clip.
    - `DocumentPage` – `src/ui/pages/document_page.py`: tài liệu / hướng dẫn.
    - Dialogs: `SettingsDialog`, `ExportDialog`, ...
  - Styling tập trung tại `src/ui/styles.py` sử dụng QSS cho Dark Theme.

- **Core Layer** – `src/core`
  - Chứa toàn bộ **business logic**:
    - Downloader base, quản lý state, project, export.
    - Timeline engine (Clip / Track / Command / History).
    - Media ingestion (ffmpeg/ffprobe).
    - AI features, hiệu năng, asset management (theo các module trong `docs/plans`).
  - Là cầu nối giữa UI và lớp Platforms.

- **Platforms Layer** – `src/core/platforms`
  - Hiện thực cụ thể cho từng nền tảng:
    - `tiktok.py`, `douyin.py`, `generic.py`, ...
  - Mỗi class kế thừa từ `BaseDownloader` (`src/core/base.py`).
  - Sử dụng **Playwright** hoặc request HTTP để:
    - Mở URL, lắng nghe network response.
    - Trích xuất direct video URL (mp4, `video/tos`, ...).
    - Thu thập cookies nếu cần.
  - Trả kết quả cho core dưới dạng dict:  
    `{"status", "url", "platform", "cookies", ...}`.

**Luồng chính:**  
`UI (DownloadPage) → Core Manager/Detector → Platform Downloader → Core (download + ingestion) → UI (preview/progress/timeline)`

---

## 3. Timeline Engine

### 3.1. Mục đích

Timeline engine cho phép:

- Biểu diễn clip trên trục thời gian (video / audio / text).
- Thao tác thêm / xóa / sắp xếp clip với logic **magnetic timeline**.
- Hỗ trợ **undo/redo** thông qua lịch sử lệnh (Command pattern).

### 3.2. Các thành phần chính

#### `Clip` – `src/core/timeline/clip.py`

Dataclass biểu diễn một clip trên timeline:

- Thông tin cơ bản:
  - `asset_id`, `name`, `duration`
  - `start_time`, `in_point`, `out_point`, `track_index`, `id`
- Transform:
  - `position_x`, `position_y`, `scale_x`, `scale_y`, `rotation`, `opacity`, `blend_mode`
- Audio:
  - `volume`, `muted`, `fade_in`, `fade_out`, `waveform_path`
- Text:
  - `clip_type`, `text_content`, `font_size`, `font_color`
- Color correction:
  - `brightness`, `contrast`, `saturation`, `hue`
- Performance:
  - `proxy_path`

Hành vi:

- Trong `__post_init__`, nếu `out_point == 0.0` thì tự gán `out_point = duration`.
- Property `length` = `out_point - in_point` là độ dài hiệu dụng trên timeline.

#### `Track` & `MagneticTrack` – `src/core/timeline/track.py`

- `Track`:
  - Quản lý danh sách `self.clips: List[Clip]`.
  - `add_clip(clip, position=None)`:
    - Nếu `position` là `None` → append cuối track.
    - Tự tính `start_time` dựa trên clip cuối.
  - `remove_clip(clip_id)`:
    - Xóa clip theo `id`, trả về clip đã xóa (hoặc `None` nếu không tìm thấy).

- `MagneticTrack(Track)`:
  - Timeline kiểu “nam châm”:
    - Thêm clip: các clip nối sát nhau (snap).
    - Xóa clip: các clip phía sau dồn lại để lấp khoảng trống (ripple delete).
  - `add_clip` override:
    - Nếu `position` là `None` hoặc track trống → dùng logic append của `Track`.
    - Nếu có `position`:
      - Tìm `insert_index` dựa trên `start_time`.
      - Tính `shift_amount = clip.length`.
      - Cộng `shift_amount` vào `start_time` của toàn bộ clip phía sau.
      - Đặt `clip.start_time` bằng **cuối clip trước** (snap).
      - Insert clip vào đúng vị trí.
  - `remove_clip` override:
    - Tìm clip theo `clip_id`, lưu `removed_clip` và vị trí index.
    - Xóa khỏi danh sách.
    - Tính `shift_amount = removed_clip.length`.
    - Trừ `shift_amount` khỏi `start_time` của các clip phía sau → **ripple delete**.

#### Command Pattern & History – `src/core/commands`, `src/core/history.py`

- Interface `Command` – `src/core/commands/base.py`:
  - Mỗi thao tác chỉnh sửa (thêm/xóa/move clip, ...) được đóng gói thành một lệnh có `execute()` và `undo()`.

- Timeline commands – `src/core/commands/timeline_commands.py`:
  - `AddClipCommand(track, clip, position=None)`:
    - `execute()`: `track.add_clip(clip, position)`
    - `undo()`: `track.remove_clip(clip.id)`
  - `RemoveClipCommand(track, clip_id)`:
    - `execute()`:
      - Tìm clip để biết `start_time` ban đầu (`removed_position`).
      - Gọi `track.remove_clip(clip_id)` và lưu `removed_clip`.
    - `undo()`:
      - Thêm lại `removed_clip` vào `removed_position`.

- **HistoryManager** – `src/core/history.py`:
  - Trường:
    - `undo_stack: List[Command]`
    - `redo_stack: List[Command]`
    - `max_history: int`
  - Hành vi:
    - `execute(command)`:
      - Gọi `command.execute()`.
      - Đẩy command vào `undo_stack`.
      - Xóa `redo_stack`.
      - Nếu `undo_stack` dài hơn `max_history` thì pop phần tử cũ nhất.
    - `undo()`:
      - Pop command từ `undo_stack`.
      - Gọi `command.undo()`.
      - Đẩy sang `redo_stack`.
    - `redo()`:
      - Pop command từ `redo_stack`.
      - Gọi lại `command.execute()`.
      - Đẩy sang `undo_stack`.
  - Có instance global: `history_manager` dùng chung cho toàn bộ app.

#### Tests timeline – `tests/test_timeline.py`

File test này là **tài liệu sống** mô tả expected behavior của timeline engine:

- `test_magnetic_append`:
  - Thêm 2 clip liên tiếp bằng `AddClipCommand` qua `history_manager`.
  - Clip 1: `start_time = 0.0`.
  - Clip 2: `start_time` phải bằng `duration` của clip 1 (append đúng).
- `test_ripple_delete`:
  - Tạo track với Clip 1 (0–5) và Clip 2 (5–8).
  - Xóa Clip 1 bằng `RemoveClipCommand`.
  - Expect:
    - Còn 1 clip.
    - Clip còn lại là Clip 2.
    - `start_time` Clip 2 = `0.0` (ripple delete).
- `test_undo_redo`:
  - Thêm Clip 1, sau đó:
    - `undo()` → track rỗng.
    - `redo()` → clip được thêm lại.

---

## 4. Media Ingestion – `src/core/ingestion.py`

### 4.1. Mục đích

`MediaIngestion` phân tích file media local (sau khi tải xuống hoặc import) để:

- Đọc metadata (duration, độ phân giải, fps, codec, ...).
- Tạo ảnh thumbnail.
- Tạo waveform (để hiển thị wave audio trên timeline).
- Chuẩn bị proxy video (low-res) phục vụ playback mượt hơn.

### 4.2. Các chức năng chính

- **`probe_file(file_path) -> Optional[Dict]`**
  - Gọi `ffprobe` với `-print_format json -show_format -show_streams`.
  - Parse JSON:
    - `duration`
    - `width`, `height`
    - `r_frame_rate` → tính `fps`
    - `codec_name`
  - Tạo thumbnail qua `_generate_thumbnail(file_path)`.
  - Nếu có audio stream → tạo waveform qua `generate_waveform(file_path)`.
  - Trả về dict dạng asset:
    ```python
    {
      "id": md5(file_path),
      "name": basename(file_path),
      "target_url": file_path,
      "metadata": {
        "width": ...,
        "height": ...,
        "frameRate": ...,
        "duration": ...,
        "codec": ...,
        "thumbnailPath": ...,
        "waveformPath": ...
      },
      "status": "ready"
    }
    ```

- **`_generate_thumbnail(file_path) -> str`**
  - Sử dụng `ffmpeg`:
    - Seek nhanh đến 5s: `-ss 00:00:05.000`.
    - Lấy 1 frame: `-frames:v 1`.
    - Scale width = 320: `-vf scale=320:-1`.
    - Chất lượng cao: `-q:v 2`.
  - Lưu file `.jpg` trong thư mục cache:  
    `~/.video_downloader/cache/thumb_<hash>.jpg`
  - Nếu thumbnail đã tồn tại → dùng lại (cache).

- **`generate_waveform(file_path) -> str`**
  - Sử dụng `ffmpeg` với filter `showwavespic`:
    - `showwavespic=s=640x120:colors=cyan|blue`
    - Xuất 1 frame PNG.
  - Lưu file `.png` trong thư mục cache cùng cách tính hash theo path + mtime.
  - Nếu đã tồn tại → dùng lại.

- **`generate_proxy(file_path) -> str`**
  - Dự kiến tạo proxy low-res cho playback.
  - Hiện tại: tạo file dummy trong  
    `~/.video_downloader_cache/proxies/<hash>_proxy.mp4`.
  - Có thể nâng cấp thành lệnh `ffmpeg` thật (downscale + CRF cao).

---

## 5. Platforms & Downloader – `src/core/platforms`

### 5.1. Vai trò

Lớp này hiện thực logic **trích xuất URL video** cho từng nền tảng cụ thể, tách biệt khỏi UI và core chung:

- Mỗi platform là một file riêng (`tiktok.py`, `douyin.py`, ...).
- Mỗi downloader kế thừa `BaseDownloader` (`src/core/base.py`) và implement `extract_info(url)`.

### 5.2. Ví dụ: TikTok – `src/core/platforms/tiktok.py`

- Dùng `sync_playwright`:
  - Mở browser Chromium headless với `user_agent` desktop (`UA_DESKTOP`).
  - Tạo `context` + `page`.
  - Gắn handler:
    ```python
    page.on("response", handle_response)
    ```
    để bắt mọi HTTP response.
  - Trong `handle_response`, nếu URL chứa `'video/tos'` hoặc `.mp4` và status 200, thêm vào `video_urls`.
- Điều hướng:
  - `page.goto(url, wait_until="domcontentloaded", timeout=30000)`
  - Chờ thêm vài giây, scroll nhẹ để kích hoạt loading.
- Thu thập cookies:
  - `cookies = context.cookies()`
  - Map về `cookie_dict = {name: value, ...}`
- Chọn URL phù hợp:
  - Ưu tiên URL chứa `.mp4` hoặc `'video/tos'`.
  - Trả về:
    ```python
    {
      "status": "success",
      "url": best_url,
      "platform": "tiktok",
      "cookies": cookie_dict
    }
    ```
- Nếu có exception:
  - In log error.
  - Trả:
    ```python
    {
      "status": "error",
      "message": "Could not retrieve TikTok video URL for preview"
    }
    ```

---

## 6. UI Layer – `src/ui`

### 6.1. `main.py`

- Tạo `QApplication`, khởi tạo và hiển thị `MainWindow`.

### 6.2. `MainWindow` – `src/ui/main_window.py`

- Layout:
  - Sidebar (trái): `QListWidget` với các mục:
    - `📥 Download`
    - `✂️ Edit`
    - `📚 Document`
    - `⚙️ Settings`
  - Header (phải, trên): hiển thị tiêu đề page hiện tại + version.
  - Content (phải, dưới): `QStackedWidget` chứa các page:
    - `DownloadPage`
    - `EditPage`
    - `DocumentPage`
- Hành vi:
  - Chọn item sidebar → đổi index của `QStackedWidget` (trừ Settings).
  - Chọn `⚙️ Settings` → mở `SettingsDialog` (không phải page riêng trong stack).
  - `apply_styles()` → set `DARK_THEME` từ `src/ui/styles.py`.
  - `closeEvent`:
    - Gọi `self.download_page.cleanup()` trước khi đóng.

### 6.3. Styles – `src/ui/styles.py`

- Định nghĩa `DARK_THEME` bằng QSS:
  - Màu nền, text, button, input, scrollbar, tab, checkbox, progressbar, dialog, spinbox, ...
  - Sidebar gradient, hiệu ứng hover/selected cho `QListWidget`.
  - Button primary dùng gradient blue-purple.

---

## 7. Định hướng mở rộng

Các file trong `docs/plans/` mô tả roadmap chi tiết theo module:

- `module_1_timeline_core.md`: mở rộng timeline (multi-track, trimming, snapping nâng cao).
- `module_2_visual_manipulation.md`: hiệu ứng visual, transform nâng cao, keyframe.
- `module_3_audio_engineering.md`: audio mixer, EQ, automation.
- `module_4_ai_automation.md`: AI auto-cut, auto-caption, scene detection.
- `module_5_vfx_color.md`: VFX, color grading (phù hợp với các trường trong `Clip`).
- `module_6_system_performance.md`: tối ưu caching, proxy, threading.
- `module_7_asset_management.md`: quản lý asset/project library.
- `module_8_export_delivery.md`: preset export, queue, profile.

Tài liệu này nên được cập nhật cùng với code và test (đặc biệt là `tests/test_timeline.py`, `tests/test_ingestion.py`, ...) để luôn phản ánh đúng kiến trúc hiện tại của hệ thống.

