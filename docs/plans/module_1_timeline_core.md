# Module 1: Timeline & Core Editing (Cốt lõi)

## 1. Tổng quan

Đây là module quan trọng nhất ("trái tim") của ứng dụng, chịu trách nhiệm quản lý luồng thời gian, sắp xếp clip và thao tác cắt ghép cơ bản.

## 2. Tính năng Chi tiết

### 1.1 Magnetic Timeline (Trục thời gian từ tính)

- **Mô tả**: Các clip trên Main Track tự động kết dính. Xóa clip -> clip sau tự động trượt lên (Ripple Delete).
- **Yêu cầu kỹ thuật**:
  - **Data Structure**: Sử dụng **Doubly Linked List** hoặc **Gap Buffer** cho Main Track để tối ưu hiệu năng Ripple Delete (tránh dịch chuyển mảng lớn).
  - **UI Virtualization**: Chỉ render các clip đang nằm trong vùng nhìn thấy (Viewport) để đảm bảo hiệu suất với timeline dài.
  - Xử lý va chạm (Collision detection): Main track không cho phép đè (tự đẩy ra), Overlay track cho phép đè.
  - Toggle bật/tắt chế độ Magnetic (Phím tắt P).

### 1.2 Multi-Track Layering (Đa lớp)

- **Mô tả**: Hỗ trợ không giới hạn (hoặc tối thiểu 10+) track video/audio.
- **Yêu cầu kỹ thuật**:
  - **Track Types**: Phân biệt rõ **Main Track** (Magnetic logic) và **Overlay Tracks** (Linear logic).
  - Z-index management: Track trên che track dưới.
  - Auto-creation: Tự động tạo track mới khi kéo clip đè lên nhau.
  - Track Controls: Mute, Solo, Lock, Hide/Show.

### 1.3 History Management (Undo/Redo)

- **Mô tả**: Hệ thống hoàn tác toàn cục cho mọi thao tác trên timeline.
- **Yêu cầu kỹ thuật**:
  - **Command Pattern**: Đóng gói mọi hành động (Add, Remove, Move, Split) thành các Command object có phương thức `execute()` và `undo()`.
  - **State Management**: Quản lý ngăn xếp (Stack) lịch sử.
  - Giới hạn bộ nhớ (ví dụ: 50 bước gần nhất).

### 1.4 Auto-Snapping (Bắt dính thông minh)

- **Mô tả**: Playhead/Clip tự động "hít" vào điểm cắt, marker, đầu/cuối clip khác.
- **Yêu cầu kỹ thuật**:
  - Tính toán khoảng cách (threshold ~5-10px) để kích hoạt snap.
  - Visual feedback: Hiển thị đường kẻ dọc khi snap.

### 1.5 Group / Ungroup Clips

- **Mô tả**: Nhóm nhiều clip thành một khối để di chuyển/effect chung.
- **Yêu cầu kỹ thuật**:
  - Logic cha-con (Parent-Child relationship).
  - Phím tắt: Ctrl/Cmd + G (Group), Ctrl/Cmd + Shift + G (Ungroup).

### 1.6 Compound Clip (Clip hỗn hợp)

- **Mô tả**: Gộp nhiều layer thành 1 object (Nested Sequence).
- **Yêu cầu kỹ thuật**:
  - Render riêng compound clip hoặc xử lý như một container ảo.
  - Cho phép "Step in" để chỉnh sửa nội dung bên trong.

## 3. Lộ trình Triển khai (Phased Implementation)

1.  **Phase 1**: Xây dựng **Magnetic Timeline** cho Main Track (Drag, Drop, Split, Ripple Delete) & Hệ thống **Undo/Redo** cơ bản.
2.  **Phase 2**: Phát triển Multi-track System (Overlay layers - Linear logic) & Logic trộn hình (Compositing).
3.  **Phase 3**: Hoàn thiện Snapping & Điều hướng nâng cao (Zoom, Scroll, Virtualization).
4.  **Phase 4**: Grouping & Compound Clips.
