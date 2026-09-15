# 🎵 Music-eco — Floating Lyric Cards Player

Ứng dụng phát nhạc kèm **thẻ lời bài hát nổi bồng bềnh (Floating Lyric Cards)** trên màn hình theo phong cách TikTok / Reels.

---

## ✨ Tính năng nổi bật
- **Đồng bộ lời bài hát**: Khớp chuẩn xác từng mili-giây theo file `.mp3`.
- **Hiệu ứng độc đáo**: Gõ chữ máy đánh chữ (*typewriter*) kèm con trỏ nhấp nháy & thẻ bay lơ lửng (*rise*).
- **Chuyển động đung đưa (Sway Motion)**: Thẻ chuyển động hình sin nhẹ nhàng lơ lửng trong gió.
- **Phân vai ca sĩ thông minh (Singer Role Theming)**: Đổi màu sắc, phong cách và gắn badge riêng cho từng ca sĩ (Bruno Mars, Lady Gaga, Duet).
- **Giao diện Aesthetic**: Tone màu pastel và vintage thẩm mỹ, luôn nổi trên cùng (*Always on Top*).
- **Tương tác linh hoạt**: Dùng chuột kéo thả thẻ tùy ý, nhấn phím `ESC` để dừng.

---

## 📁 Cấu trúc thư mục
```text
Music-eco/
├── SweetBoy/           # Sweet Boy - Malcolm Todd (26 câu)
│   ├── SweetBoy.py
│   ├── SweetBoy.mp3
│   └── lyrics.txt
├── Earrings/           # Earrings - Malcolm Todd (39 câu)
│   ├── Earrings.py
│   ├── Earrings.mp3
│   └── lyrics.txt
├── Starboy/            # Starboy - The Weeknd ft. Daft Punk (64 câu)
│   ├── Starboy.py
│   ├── Starboy.mp3
│   └── lyrics.txt
└── DieWithASmile/      # Die With A Smile - Lady Gaga & Bruno Mars (40 câu)
    ├── DieWithASmile.py
    ├── DieWithASmile.mp3
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

   # Bài Starboy
   cd Starboy
   python Starboy.py

   # Bài Die With A Smile (Bản đặc biệt song ca & uốn lượn)
   cd DieWithASmile
   python DieWithASmile.py
   ```

---

## 🛠 Công nghệ sử dụng
- **Ngôn ngữ:** Python 3
- **Giao diện:** Tkinter (Toplevel, transparent/borderless cards)
- **Âm thanh:** Pygame (pygame.mixer)
- **Đồng bộ lời:** LRCLIB (synced lyrics)
