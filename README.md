# 🎵 Music-eco — Floating Lyric Cards Player

Tái hiện trào lưu lập trình **"Thẻ lời bài hát nổi bồng bềnh trên màn hình" (Floating Sticky Notes Lyrics)** cực hot trên TikTok / Reels.

Chương trình phát nhạc kèm hiệu ứng thẻ ghi chú pastel bay lên trên màn hình Desktop, mỗi thẻ hiển thị lời bài hát với hiệu ứng gõ chữ máy đánh chữ (typewriter) — đồng bộ chính xác từng mili-giây theo nhịp bài hát.

---

## 🌟 Tính năng chính

* **Đồng bộ chuẩn xác** lời bài hát theo từng mili-giây với file nhạc `.mp3`.
* **Hiệu ứng máy gõ chữ (typewriter)** — lời bài hát gõ từng ký tự theo thời gian thực.
* **Hiệu ứng trôi bồng bềnh (rise)** — thẻ ghi chú pastel bay nhẹ nhàng từ dưới lên trên màn hình.
* **Bảng màu pastel aesthetic** — 7 bảng màu giấy ghi chú nghệ thuật ngẫu nhiên.
* **Kéo thả thẻ bằng chuột** — bạn có thể di chuyển thẻ note đến bất kỳ vị trí nào trên màn hình.
* **Luôn nổi trên cùng (Always on Top)** — thẻ đè lên VS Code, Chrome, Desktop...
* **Phím tắt ESC** để dừng bất cứ lúc nào.

---

## 📁 Cấu trúc dự án

```
Music-eco/
├── README.md
├── SweetBoy/                ← Bài Sweet Boy - Malcolm Todd
│   ├── SweetBoy.py
│   ├── SweetBoy.mp3
│   └── lyrics.txt (26 câu đồng bộ)
│
└── Earrings/                ← Bài Earrings - Malcolm Todd
    ├── Earrings.py
    ├── Earrings.mp3
    └── lyrics.txt (39 câu đồng bộ)
```

---

## 🚀 Cách chạy

### Yêu cầu
- Python 3.10+
- `pip install pygame`

### Phát bài Sweet Boy
```powershell
cd SweetBoy
python SweetBoy.py
```

### Phát bài Earrings
```powershell
cd Earrings
python Earrings.py
```

---

## 🎶 Thêm bài hát mới

Mỗi bài hát chỉ cần 1 thư mục riêng gồm 3 file:

1. **TenBai.py** — Copy từ bất kỳ file `.py` có sẵn, sửa tên file nhạc mặc định.
2. **TenBai.mp3** — File nhạc của bạn.
3. **lyrics.txt** — Lời bài hát với cú pháp:
   ```
   [giây_bắt_đầu|tốc_độ_gõ_ms] Lời bài hát
   ```

---

## 🛠 Công nghệ sử dụng

| Thành phần | Công nghệ |
| :--- | :--- |
| GUI / Cửa sổ nổi | Python Tkinter (Toplevel, overrideredirect) |
| Phát nhạc | Pygame (pygame.mixer) |
| Đồng bộ thời gian | LRCLIB API (synced lyrics) |
| Hiệu ứng | Typewriter + Rise animation |

---

*Made with ❤️ and Python*
