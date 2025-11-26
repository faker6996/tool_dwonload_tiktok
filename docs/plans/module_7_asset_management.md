# Module 7: Asset Management (Quản lý Tài nguyên)

## 1. Tổng quan

Module quản lý thư viện media, stock assets và templates.

## 2. Tính năng Chi tiết

### 7.1 Media & Asset Browser

- **Mô tả**: Quản lý file local và cloud assets.
- **Yêu cầu kỹ thuật**:
  - File system watcher (theo dõi thay đổi file).
  - Thumbnail generation & caching.
  - Metadata parsing (Duration, Resolution, Codec).

### 7.2 Built-in Asset Store

- **Mô tả**: Tích hợp kho Stock Video/Photo/Audio.
- **Yêu cầu kỹ thuật**:
  - API integration (Pexels, Unsplash, Pixabay).
  - Download manager & caching.
  - Search engine.

### 7.3 Brand Kit

- **Mô tả**: Quản lý Logo, Font, Color Palette thương hiệu.
- **Yêu cầu kỹ thuật**:
  - Global style settings.
  - Font manager.

## 3. Lộ trình Triển khai

1.  **Phase 1**: Local Media Browser (Import, Thumbnail, Metadata).
2.  **Phase 2**: Asset Store Integration (Basic API connection).
3.  **Phase 3**: Advanced Search & Filtering.
4.  **Phase 4**: Brand Kit & Templates.
