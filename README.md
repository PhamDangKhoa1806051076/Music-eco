# 🎵 Music-eco — Floating Lyric Cards Player

Ứng dụng phát nhạc kèm **thẻ lời bài hát nổi bồng bềnh (Floating Lyric Cards)** trên màn hình theo phong cách TikTok / Reels.

---

## ✨ Tính năng nổi bật
- **Đồng bộ lời bài hát**: Khớp chuẩn xác từng mili-giây theo file `.mp3`.
- **Hiệu ứng độc đáo**: Gõ chữ máy đánh chữ (*typewriter*) & thẻ bay lơ lửng (*rise*).
- **Giao diện Aesthetic**: 7 tone màu pastel ngẫu nhiên, bo góc mềm mại, luôn nổi trên cùng (*Always on Top*).
- **Tương tác linh hoạt**: Dùng chuột kéo thả thẻ tùy ý, nhấn phím `ESC` để dừng.

---

## 📁 Cấu trúc thư mục
```text
Music-eco/
├── SweetBoy/       # Sweet Boy - Malcolm Todd (26 câu)
│   ├── SweetBoy.py
│   ├── SweetBoy.mp3
│   └── lyrics.txt
└── Earrings/       # Earrings - Malcolm Todd (39 câu)
    ├── Earrings.py
    ├── Earrings.mp3
    └── lyrics.txt
```

---

## 🚀 Cài đặt & Khởi chạy

1. **Cài đặt thư viện:**
   ```bash
   pip install pygame
   ```

2. **Chạy bài hát:**
   ```bash
   # Bài Sweet Boy
   cd SweetBoy
   python SweetBoy.py

   # Bài Earrings
   cd Earrings
   python Earrings.py
   ```

---

## 🛠 Công nghệ sử dụng
- **Ngôn ngữ:** Python 3
- **Giao diện:** Tkinter (Toplevel, transparent/borderless cards)
- **Âm thanh:** Pygame (pygame.mixer)
- **Đồng bộ lời:** LRCLIB (synced lyrics)
