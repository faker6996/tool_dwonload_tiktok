# Module 8: Export & Delivery (Xuất bản)

## 1. Tổng quan

Module xử lý quá trình render video cuối cùng và phân phối lên các nền tảng.

## 2. Tính năng Chi tiết

### 8.1 Export Settings

- **Mô tả**: Cấu hình xuất file (Resolution, FPS, Codec).
- **Yêu cầu kỹ thuật**:
  - FFmpeg pipeline builder.
  - Hỗ trợ H.264, H.265 (HEVC), ProRes.
  - Container: MP4, MOV.

### 8.2 Smart Bitrate Control

- **Mô tả**: Tự động tính toán bitrate tối ưu.
- **Yêu cầu kỹ thuật**:
  - Presets cho YouTube, TikTok (Recommended settings).
  - CBR/VBR control.

### 8.3 Direct Publishing

- **Mô tả**: Upload trực tiếp lên MXH.
- **Yêu cầu kỹ thuật**:
  - OAuth 2.0 authentication (YouTube, TikTok APIs).
  - Upload session management.
  - Metadata injection (Title, Description, Tags).

### 8.4 Thumbnail Editor

- **Mô tả**: Tạo thumbnail từ frame video.
- **Yêu cầu kỹ thuật**:
  - Frame capture tool.
  - Basic image editor (Text overlay, Stroke).

## 3. Lộ trình Triển khai

1.  **Phase 1**: Basic Export (MP4, H.264, Presets).
2.  **Phase 2**: Advanced Settings (Codec, Bitrate control).
3.  **Phase 3**: Thumbnail Editor.
4.  **Phase 4**: Direct Publishing APIs.
