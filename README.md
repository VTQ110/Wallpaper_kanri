# Wallpaper Kanri

Trang web (Python/Flask) để upload và quản lý hình ảnh dùng làm hình nền.

## Tính năng

- **Sidebar menu**: upload nhiều ảnh cùng lúc (bấm chọn hoặc kéo thả), xem trước trước khi upload, thống kê số ảnh/dung lượng, chọn số ảnh mỗi trang (6/12/24/48).
- **Thư viện ảnh**: hiển thị dạng lưới có **phân trang** (paging), tự tạo thumbnail để tải nhanh.
- **Xem từng ảnh**: mỗi ảnh là một trang riêng, chuyển trang bằng nút ‹ › / thanh số trang / phím mũi tên ← →.
- **Xem thử làm hình nền** (toàn màn hình), tải về, xóa ảnh.
- Kiểm tra định dạng ảnh hợp lệ (png, jpg, jpeg, gif, webp, bmp), giới hạn 50 MB mỗi lần upload.

## Cài đặt & chạy

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Mở trình duyệt tại http://localhost:5000

Ảnh được lưu trong thư mục `uploads/`.
