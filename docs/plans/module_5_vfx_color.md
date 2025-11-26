# Module 5: VFX & Color (Hiệu ứng & Màu sắc)

## 1. Tổng quan

Module cung cấp các công cụ chỉnh sửa màu sắc chuyên sâu và thư viện hiệu ứng hình ảnh.

## 2. Tính năng Chi tiết

### 5.1 Chroma Key (Phông xanh)

- **Mô tả**: Xóa phông xanh/lục.
- **Yêu cầu kỹ thuật**:
  - Color difference keying algorithm.
  - Controls: Color Picker, Intensity, Shadow/Spill suppression.

### 5.2 Color Wheels & Curves

- **Mô tả**: Chỉnh màu chuyên nghiệp (Color Grading).
- **Yêu cầu kỹ thuật**:
  - 3-way Color Wheels (Lift, Gamma, Gain).
  - RGB Curves (Spline interpolation).
  - Histogram/Vectorscope scope view.

### 5.3 Filters & LUTs Support

- **Mô tả**: Áp dụng bộ lọc màu và file LUT (.cube).
- **Yêu cầu kỹ thuật**:
  - 3D LUT processing engine.
  - Library management cho Filters.

### 5.4 Sticker & Text Effects

- **Mô tả**: Nhãn dán động và hiệu ứng chữ.
- **Yêu cầu kỹ thuật**:
  - Hỗ trợ định dạng Lottie/WebP/GIF cho stickers.
  - Text rendering engine hỗ trợ Stroke, Shadow, Glow.
  - Text Animations (Typewriter, Fade, Bounce).

## 3. Lộ trình Triển khai

1.  **Phase 1**: Basic Color Correction (Brightness, Contrast, Saturation) & Filters.
2.  **Phase 2**: Text Engine & Sticker support.
3.  **Phase 3**: Chroma Key.
4.  **Phase 4**: Advanced Color Grading (Wheels, Curves, LUTs).
