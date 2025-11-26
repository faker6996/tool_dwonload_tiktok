# Module 2: Visual Manipulation (Xử lý Hình ảnh)

## 1. Tổng quan

Module này cung cấp các công cụ để biến đổi tính chất vật lý và hiển thị của các đối tượng hình ảnh (Video, Image, Text, Sticker).

## 2. Tính năng Chi tiết

### 2.1 Transform Controls (Biến đổi)

- **Mô tả**: Điều chỉnh Vị trí (X,Y), Tỷ lệ (Scale), Xoay (Rotation), Lật (Flip).
- **Yêu cầu kỹ thuật**:
  - On-screen Controls (OSC): Khung bao (Bounding box) trực quan trên màn hình Preview để kéo thả/xoay.
  - Inspector Panel: Nhập thông số chính xác.

### 2.2 Advanced Keyframing (Khung hình chính)

- **Mô tả**: Tạo chuyển động hoạt hình cho các thông số theo thời gian.
- **Yêu cầu kỹ thuật**:
  - Hệ thống lưu trữ Keyframe (Time, Value, Interpolation Type).
  - Nội suy (Interpolation): Linear, Bezier (Ease-in/Ease-out).
  - UI hiển thị điểm keyframe trên clip trong timeline.

### 2.3 Smart Masking (Mặt nạ)

- **Mô tả**: Cắt video theo hình dạng (Circle, Rectangle, Star, Heart) hoặc vẽ tự do.
- **Yêu cầu kỹ thuật**:
  - Alpha masking.
  - Thuộc tính Feather (làm mềm viền).
  - Invert mask (đảo ngược).

### 2.4 Blending Modes (Chế độ hòa trộn)

- **Mô tả**: Hòa trộn layer trên với layer dưới.
- **Yêu cầu kỹ thuật**:
  - Hỗ trợ các mode chuẩn: Normal, Screen, Multiply, Overlay, Soft Light, Darken, Lighten.
  - Shader processing (GLSL) để đảm bảo hiệu suất realtime.

### 2.5 Speed Curve (Đường cong tốc độ)

- **Mô tả**: Thay đổi tốc độ video không tuyến tính (Speed Ramping).
- **Yêu cầu kỹ thuật**:
  - Time remapping.
  - Optical Flow: Thuật toán nội suy frame để slow-motion mượt mà.
  - Presets: Montage, Bullet Time, Hero.

## 3. Lộ trình Triển khai

1.  **Phase 1**: Transform cơ bản (Scale, Position, Rotate) & Blending Modes.
2.  **Phase 2**: Hệ thống Keyframe cơ bản (Linear interpolation).
3.  **Phase 3**: Masking & Feathering.
4.  **Phase 4**: Advanced Keyframe (Bezier) & Speed Ramping.
