# Module 3: Audio Engineering (Kỹ thuật Âm thanh)

## 1. Tổng quan

Module xử lý mọi vấn đề liên quan đến âm thanh, từ chỉnh sửa cơ bản đến nâng cao và tích hợp AI.

## 2. Tính năng Chi tiết

### 3.1 Audio Separator (Tách âm)

- **Mô tả**: Tách track âm thanh khỏi video gốc.
- **Yêu cầu kỹ thuật**:
  - FFmpeg command để demux audio stream.
  - Tạo track audio mới liên kết hoặc độc lập với video.

### 3.2 Vocal Isolation (Tách giọng AI)

- **Mô tả**: Loại bỏ nhạc nền giữ giọng nói, hoặc ngược lại (Karaoke mode).
- **Yêu cầu kỹ thuật**:
  - Tích hợp thư viện AI (ví dụ: Spleeter hoặc model tương tự).
  - Xử lý background (không block UI chính).

### 3.3 Loudness Normalization

- **Mô tả**: Cân bằng âm lượng về mức chuẩn (ví dụ -14 LUFS).
- **Yêu cầu kỹ thuật**:
  - Phân tích độ lớn âm thanh (Audio analysis).
  - Tự động điều chỉnh Gain.

### 3.4 Noise Reduction (Khử ồn)

- **Mô tả**: Lọc bỏ tiếng ồn môi trường.
- **Yêu cầu kỹ thuật**:
  - DSP filters (Low-pass, High-pass, Noise gate).
  - AI-based denoising (nếu có thể).

### 3.5 Beat Sync (Bắt nhịp)

- **Mô tả**: Tự động đánh dấu điểm nhịp mạnh (Bass/Drum).
- **Yêu cầu kỹ thuật**:
  - Onset detection algorithm.
  - Tự động tạo Marker trên timeline tại các điểm beat.
  - Snap clip vào beat marker.

## 3. Lộ trình Triển khai

1.  **Phase 1**: Volume control, Fade In/Out, Audio Separator.
2.  **Phase 2**: Waveform visualization (hiển thị sóng âm trên timeline).
3.  **Phase 3**: Noise Reduction & Normalization cơ bản.
4.  **Phase 4**: AI features (Vocal Isolation, Beat Sync).
