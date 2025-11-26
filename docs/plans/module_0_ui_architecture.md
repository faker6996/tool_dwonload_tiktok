# Module 0: UI Architecture & Media Ingestion (Kiến trúc Giao diện & Nhập liệu)

## 1. Tổng quan Điều hành

Module này thiết lập nền tảng giao diện người dùng (UI) và quy trình nhập liệu (Ingestion Pipeline) cho ứng dụng. Dựa trên phân tích chuyên sâu về công thái học thị giác và hiệu năng hệ thống, module này định hình không gian làm việc chuyên nghiệp (Professional Workspace) và cơ chế xử lý dữ liệu đầu vào.

## 2. Kiến trúc Giao diện (UI Architecture)

### 2.1 Triết lý Thiết kế: Dark Mode Công thái học

- **Màu nền cơ sở (Surface Color)**: Sử dụng màu xám đậm (#121212 - #1F1F1F) thay vì đen thuần (#000000) để giảm mỏi mắt và tránh hiện tượng "black smear" trên màn hình OLED.
- **Hệ thống màu sắc**:
  - **Surface**: #121212 (Nền chính), #1E1E1E (Panel công cụ).
  - **Text**: #E0E0E0 (Chính), #A0A0A0 (Phụ/Metadata).
  - **Accent**: #90CAF9 (Active state - Xanh lam giảm bão hòa).
  - **Error**: #CF6679 (Đỏ giảm bão hòa).
- **Độ cao (Elevation)**: Sử dụng độ sáng (lightness) để thể hiện chiều sâu thay vì border.

### 2.2 Bố cục Không gian làm việc (Workspace Layout)

- **Mô hình**: "Three-Pane" (Ba Bảng) tiêu chuẩn công nghiệp.
  1.  **Zone A (Trái trên) - Media Pool**: Quản lý tài nguyên, thư viện effect.
  2.  **Zone B (Giữa trên) - Player**: Màn hình Preview trung tâm.
  3.  **Zone C (Phải trên) - Inspector**: Bảng thuộc tính động (Context-aware).
  4.  **Zone D (Dưới cùng) - Timeline**: Khu vực sắp xếp clip (Magnetic/Linear).
- **Công nghệ**: Sử dụng `react-resizable-panels` (hoặc tương đương trong PyQt6: `QSplitter`) để cho phép người dùng thay đổi kích thước linh hoạt.
- **Lưu trữ trạng thái**: Lưu cấu hình layout (kích thước panel) vào `localStorage` hoặc file config để khôi phục khi khởi động lại.

## 3. Quy trình Nhập liệu Media (Media Ingestion Pipeline)

### 3.1 Luồng xử lý (Workflow)

1.  **Trigger**: Kéo thả (Drag & Drop) hoặc Dialog chọn file.
2.  **Validation**: Kiểm tra định dạng (Extension/MIME type).
3.  **Extraction**: Sử dụng **FFmpeg/FFprobe** để trích xuất metadata (Codec, Duration, Frame Rate, Timebase).
4.  **Generation**: Tạo Thumbnail tối ưu bằng kỹ thuật "Fast Seeking" (`-ss` flag).
5.  **Registration**: Lưu vào Global State (Redux/State Management) với UUID duy nhất.

### 3.2 Kỹ thuật Chi tiết

- **IPC Strategy**: Xử lý FFmpeg trên Main Process (hoặc Worker Thread trong Python) để không chặn UI Thread.
- **Metadata Parsing**:
  - `format.duration` -> Duration.
  - `streams.r_frame_rate` -> FPS (xử lý phân số 30000/1001).
  - `streams.codec_name` -> Cảnh báo nếu là HEVC/H.265 (cần Proxy).
- **Thumbnail Optimization**:
  - Lệnh: `ffmpeg -ss 00:00:05.000 -i input.mp4 -frames:v 1 -vf "scale=320:-1" -q:v 2 thumb.jpg`
  - Caching: Lưu thumbnail vào thư mục cache với tên file là hash của đường dẫn gốc.

### 3.3 Mô hình Dữ liệu (Asset Schema)

Tuân thủ tư tưởng **OpenTimelineIO (OTIO)**:

```json
"asset-uuid": {
  "id": "uuid",
  "name": "clip.mp4",
  "target_url": "file:///path/to/clip.mp4",
  "metadata": {
    "width": 1920,
    "height": 1080,
    "frameRate": 29.97,
    "codec": "h264",
    "thumbnailPath": "/cache/thumb_1.jpg"
  },
  "status": "ready" // ready, offline, processing, error
}
```

## 4. Lộ trình Triển khai (Phasing)

### Phase 1: Skeleton & Ingestion Core

- Thiết lập cấu trúc Layout 3-pane (sử dụng `QSplitter` trong PyQt6).
- Cấu hình Theme system (Dark Mode variables).
- Xây dựng lớp Wrapper cho FFmpeg/FFprobe.
- Implement Drag & Drop và File Dialog.

### Phase 2: Asset Management & State

- Xây dựng Media Pool UI (Grid/List view).
- Implement logic tạo Thumbnail bất đồng bộ (Async).
- Quản lý State cho danh sách Assets (Redux/State Store).

### Phase 3: Advanced UI Features

- Lưu/Khôi phục trạng thái Layout.
- Xử lý các trường hợp biên (File lỗi, Offline media).
- Tối ưu hiệu năng (Virtualization cho danh sách file lớn).
