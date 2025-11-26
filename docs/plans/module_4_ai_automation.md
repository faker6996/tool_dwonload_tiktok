# Module 4: AI & Automation (AI Suite)

## 1. Tổng quan

Module này tích hợp các tính năng Trí tuệ Nhân tạo để tự động hóa các quy trình tẻ nhạt và nâng cao khả năng sáng tạo.

## 2. Tính năng Chi tiết

### 4.1 Auto Captions (Phụ đề tự động)

- **Mô tả**: Speech-to-Text (STT) để tạo phụ đề.
- **Yêu cầu kỹ thuật**:
  - Tích hợp OpenAI Whisper hoặc Google Cloud Speech-to-Text API.
  - Tự động tạo layer Text trên timeline đồng bộ với timecode.
  - Batch Edit: Giao diện sửa lỗi chính tả hàng loạt.

### 4.2 Text-to-Speech (Chuyển văn bản thành giọng nói)

- **Mô tả**: Nhập văn bản -> Tạo file audio giọng đọc AI.
- **Yêu cầu kỹ thuật**:
  - Tích hợp API (Google TTS, Azure TTS, hoặc ElevenLabs).
  - Tùy chọn giọng đọc (Nam/Nữ, Cảm xúc).
  - Điều chỉnh Pitch/Speed.

### 4.3 Auto Cutout / Remove BG

- **Mô tả**: Xóa nền video chân dung không cần Green Screen.
- **Yêu cầu kỹ thuật**:
  - Sử dụng model AI Segmentation (ví dụ: MediaPipe Selfie Segmentation hoặc RVM).
  - Xử lý từng frame để tạo Alpha mask.

### 4.4 Auto Reframe

- **Mô tả**: Tự động chuyển đổi tỷ lệ khung hình (16:9 -> 9:16) giữ chủ thể ở giữa.
- **Yêu cầu kỹ thuật**:
  - Object Detection / Tracking để xác định chủ thể chính.
  - Tự động tính toán và keyframe vị trí X,Y của video gốc.

## 3. Lộ trình Triển khai

1.  **Phase 1**: Auto Captions (Whisper integration).
2.  **Phase 2**: Text-to-Speech cơ bản.
3.  **Phase 3**: Auto Cutout (Static images first, then Video).
4.  **Phase 4**: Auto Reframe & Advanced TTS.
