import os
import sys
import time
import random
import tkinter as tk
import pygame

# Đảm bảo console Windows hỗ trợ UTF-8 mượt mà
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# ==============================================================================
# CẤU HÌNH GIAO DIỆN & HIỆU ỨNG THẺ GHI CHÚ NỔI (FLOATING STICKY NOTES)
# ==============================================================================
BOX_W = 280           # Chiều rộng thẻ ghi chú (pixels)
BOX_H = 180           # Chiều cao thẻ ghi chú (pixels)
RISE_SPEED = 0.9      # Tốc độ bay lên từ tốn, mượt mà (pixels mỗi frame)
FRAME_DELAY_MS = 25   # Thời gian giữa các khung hình animation (~40 FPS)

# Bảng màu pastel thẩm mỹ phong cách giấy ghi chú nghệ thuật
PASTEL_COLORS = [
    {"bg": "#FFFBEB", "fg": "#2D3748", "border": "#FDE68A", "name": "Kem sữa ấm"},
    {"bg": "#FEF3C7", "fg": "#1F2937", "border": "#FCD34D", "name": "Vàng bơ nhạt"},
    {"bg": "#FFE4E6", "fg": "#881337", "border": "#FDA4AF", "name": "Hồng phấn dịu"},
    {"bg": "#EDE9FE", "fg": "#4C1D95", "border": "#DDD6FE", "name": "Tím Lavender"},
    {"bg": "#E0F2FE", "fg": "#0369A1", "border": "#BAE6FD", "name": "Xanh baby blue"},
    {"bg": "#DCFCE7", "fg": "#166534", "border": "#BBF7D0", "name": "Xanh mint tươi mát"},
    {"bg": "#FFEDD5", "fg": "#7C2D12", "border": "#FED7AA", "name": "Cam đào pastel"},
]

FONT_FAMILY = "Segoe UI"
FONT_SIZE = 12


class LyricCard:
    """
    Thẻ ghi chú nổi hiển thị từng câu lời bài hát với hiệu ứng gõ chữ (typewriter)
    và bay dần từ dưới lên trên màn hình (rise).
    """
    def __init__(self, master, text, x, y, speed_ms=70, color_theme=None, on_close=None):
        self.master = master
        self.full_text = text
        self.x = float(x)
        self.y = float(y)
        self.speed_ms = speed_ms
        self.on_close = on_close
        
        if color_theme is None:
            color_theme = random.choice(PASTEL_COLORS)
        self.color_theme = color_theme

        # Tạo cửa sổ cấp cao Toplevel không viền, luôn nằm trên cùng màn hình
        self.win = tk.Toplevel(master)
        self.win.overrideredirect(True)         # Gỡ bỏ viền xám và thanh tiêu đề Windows
        self.win.attributes("-topmost", True)     # Luôn nổi đè lên trên mọi cửa sổ (VS Code, Chrome...)
        
        # Đặt kích thước và vị trí ban đầu
        self.win.geometry(f"{BOX_W}x{BOX_H}+{int(self.x)}+{int(self.y)}")
        self.win.config(bg=self.color_theme["border"])

        # Khung viền mô phỏng viền giấy note có lề
        self.inner_frame = tk.Frame(
            self.win,
            bg=self.color_theme["bg"],
            highlightthickness=0,
            padx=14,
            pady=14
        )
        self.inner_frame.pack(fill="both", expand=True, padx=2, pady=2)

        # Nhãn hiển thị nội dung câu hát
        self.label = tk.Label(
            self.inner_frame,
            text="",
            wraplength=BOX_W - 35,
            justify="center",
            font=(FONT_FAMILY, FONT_SIZE, "bold"),
            fg=self.color_theme["fg"],
            bg=self.color_theme["bg"]
        )
        self.label.pack(expand=True, fill="both")

        # Cho phép kéo thả thẻ note bằng chuột để điều chỉnh vị trí theo ý thích
        self.drag_start_x = 0
        self.drag_start_y = 0
        for widget in (self.win, self.inner_frame, self.label):
            widget.bind("<ButtonPress-1>", self.start_drag)
            widget.bind("<B1-Motion>", self.do_drag)
            # Nhấp chuột phải để đóng thẻ note sớm nếu muốn
            widget.bind("<Button-3>", lambda e: self.destroy())

        # Bắt đầu hiệu ứng gõ máy chữ
        self.typewriter_index = 0
        self.is_alive = True
        self.typewriter()

    def start_drag(self, event):
        self.drag_start_x = event.x
        self.drag_start_y = event.y

    def do_drag(self, event):
        dx = event.x - self.drag_start_x
        dy = event.y - self.drag_start_y
        self.x += dx
        self.y += dy
        self.win.geometry(f"{BOX_W}x{BOX_H}+{int(self.x)}+{int(self.y)}")

    def typewriter(self):
        """Hiển thị từng ký tự như máy đánh chữ theo thời gian thực."""
        if not self.is_alive:
            return
        if self.typewriter_index <= len(self.full_text):
            self.label.config(text=self.full_text[:self.typewriter_index])
            self.typewriter_index += 1
            self.win.after(self.speed_ms, self.typewriter)

    def rise(self, dy):
        """Di chuyển thẻ card dần lên phía trên màn hình."""
        if not self.is_alive:
            return
        self.y -= dy
        self.win.geometry(f"{BOX_W}x{BOX_H}+{int(self.x)}+{int(self.y)}")

    def is_offscreen(self):
        """Kiểm tra thẻ đã trôi khuất hẳn khỏi cạnh trên màn hình chưa."""
        return self.y + BOX_H < -40

    def destroy(self):
        """Dọn dẹp và đóng thẻ ghi chú."""
        if self.is_alive:
            self.is_alive = False
            try:
                self.win.destroy()
            except Exception:
                pass
            if self.on_close:
                self.on_close(self)


class LyricFloatApp:
    """
    Ứng dụng quản lý phát nhạc & đồng bộ thẻ lời bài hát nổi trên màn hình.
    """
    def __init__(self, audio_file="Earrings.mp3", lyrics_file="lyrics.txt"):
        self.root = tk.Tk()
        self.root.withdraw()  # Ẩn cửa sổ gốc, chỉ để các thẻ note hiển thị

        self.screen_w = self.root.winfo_screenwidth()
        self.screen_h = self.root.winfo_screenheight()

        self.audio_file = audio_file
        self.lyrics_file = lyrics_file
        
        self.cards = []
        self.next_index = 0
        self.lyrics_timeline = []
        self.last_x_slot = 1  # Giúp phân bổ vị trí xuất hiện luân phiên đều hai bên màn hình

        # 1. Tải danh sách lời bài hát
        self.load_lyrics()

        # 2. Khởi tạo âm thanh pygame
        self.init_audio()

        # 3. Phím tắt ESC để thoát nhanh bất cứ lúc nào
        self.root.bind_all("<Escape>", lambda e: self.quit())

        self.start_wall_time = None
        self.is_running = True

    def init_audio(self):
        """Khởi động pygame mixer và nạp file nhạc."""
        pygame.mixer.init()
        if os.path.exists(self.audio_file):
            print(f"[Music] Loading audio file: {os.path.basename(self.audio_file)}")
            pygame.mixer.music.load(self.audio_file)
        else:
            print(f"[Warning] Audio '{self.audio_file}' not found. Falling back to timer.")

    def load_lyrics(self):
        """Đọc file lyrics.txt với định dạng [thời_gian_giây|tốc_độ_gõ_ms] Lời hát."""
        if not os.path.exists(self.lyrics_file):
            print(f"[Error] File '{self.lyrics_file}' not found.")
            return

        with open(self.lyrics_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if line.startswith("[") and "]" in line:
                    tag, text = line[1:].split("]", 1)
                    text = text.strip()
                    parts = tag.split("|")
                    try:
                        time_sec = float(parts[0].strip())
                        speed_ms = int(parts[1].strip()) if len(parts) > 1 else 70
                        self.lyrics_timeline.append({
                            "time_sec": time_sec,
                            "speed_ms": speed_ms,
                            "text": text
                        })
                    except ValueError:
                        continue

        # Sắp xếp theo thứ tự thời gian tăng dần
        self.lyrics_timeline.sort(key=lambda item: item["time_sec"])
        print(f"[Lyrics] Successfully loaded {len(self.lyrics_timeline)} synchronized lines.")

    def random_safe_x(self):
        """
        Phân bổ tọa độ trục X thông minh thành nhiều vùng (trái, giữa, phải)
        để các thẻ note không bị đè lên nhau, tạo bố cục ngẫu nhiên và hài hòa.
        """
        margin = 80
        usable_width = self.screen_w - BOX_W - (margin * 2)
        num_slots = 3
        slot_width = usable_width / num_slots

        # Chọn slot tiếp theo khác với slot vừa rồi để tạo sự so le sinh động
        available_slots = [s for s in range(num_slots) if s != self.last_x_slot]
        chosen_slot = random.choice(available_slots)
        self.last_x_slot = chosen_slot

        slot_start = margin + int(chosen_slot * slot_width)
        slot_end = int(slot_start + slot_width - 20)
        return random.randint(slot_start, max(slot_start + 10, slot_end))

    def spawn_card(self, lyric_data):
        """Sinh một thẻ card mới ở đáy màn hình và bắt đầu bay lên."""
        spawn_x = self.random_safe_x()
        # Xuất hiện ở khoảng phía dưới màn hình (cách đáy 50 - 100 px)
        spawn_y = self.screen_h - BOX_H - random.randint(50, 100)

        card = LyricCard(
            master=self.root,
            text=lyric_data["text"],
            x=spawn_x,
            y=spawn_y,
            speed_ms=lyric_data.get("speed_ms", 70),
            on_close=lambda c: self.cards.remove(c) if c in self.cards else None
        )
        self.cards.append(card)
        print(f"[{lyric_data['time_sec']:5.1f}s] Spawning: \"{lyric_data['text']}\"")

    def get_current_music_time(self):
        """Lấy mốc thời gian bài hát chính xác từng mili-giây từ pygame."""
        if pygame.mixer.music.get_busy():
            pos_ms = pygame.mixer.music.get_pos()
            if pos_ms >= 0:
                return pos_ms / 1000.0
        # Dự phòng theo đồng hồ hệ thống nếu âm thanh chưa bắt đầu
        if self.start_wall_time:
            return time.time() - self.start_wall_time
        return 0.0

    def update(self):
        """Vòng lặp animation chính: kiểm tra mốc thời gian và di chuyển thẻ."""
        if not self.is_running:
            return

        current_time = self.get_current_music_time()

        # 1. Kiểm tra xem có câu hát nào đến giờ hiển thị chưa
        while self.next_index < len(self.lyrics_timeline):
            next_lyric = self.lyrics_timeline[self.next_index]
            if current_time >= next_lyric["time_sec"]:
                self.spawn_card(next_lyric)
                self.next_index += 1
            else:
                break

        # 2. Cập nhật vị trí bay lên cho tất cả các thẻ đang hiển thị
        for card in list(self.cards):
            card.rise(RISE_SPEED)
            if card.is_offscreen():
                card.destroy()

        # 3. Khi bài hát kết thúc và tất cả card đã bay khỏi màn hình
        if self.next_index >= len(self.lyrics_timeline) and not self.cards:
            if not pygame.mixer.music.get_busy():
                print("\n[App] Song completed and all lyric cards finished. Exiting.")
                self.quit()
                return

        # Lặp lại sau FRAME_DELAY_MS (~40 FPS)
        self.root.after(FRAME_DELAY_MS, self.update)

    def start(self):
        """Bắt đầu phát nhạc và chạy vòng lặp Tkinter."""
        print("=" * 65)
        print("  🎵 FLOATING LYRICS PLAYER - MALCOLM TODD (EARRINGS)")
        print("  Phím tắt: Nhấn [ESC] bất kỳ lúc nào để dừng.")
        print("  Mẹo: Bạn có thể dùng chuột kéo thả các thẻ ghi chú trên màn hình!")
        print("=" * 65)

        if os.path.exists(self.audio_file):
            pygame.mixer.music.play()

        self.start_wall_time = time.time()
        self.root.after(10, self.update)
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self.quit()

    def quit(self):
        """Dừng âm thanh và đóng tất cả cửa sổ sạch sẽ."""
        self.is_running = False
        try:
            pygame.mixer.music.stop()
        except Exception:
            pass
        for card in list(self.cards):
            card.destroy()
        try:
            self.root.destroy()
        except Exception:
            pass
        print("[App] Stopped successfully.")
        sys.exit(0)


def find_audio_file():
    """Tự động ưu tiên tìm file Earrings.mp3 trong thư mục hiện tại."""
    dir_path = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(dir_path, "Earrings.mp3"),
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    for f in os.listdir(dir_path):
        if f.lower().endswith((".mp3", ".wav")):
            return os.path.join(dir_path, f)
    return os.path.join(dir_path, "Earrings.mp3")


if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    audio = find_audio_file()
    lyrics = os.path.join(current_dir, "lyrics.txt")
    
    app = LyricFloatApp(audio_file=audio, lyrics_file=lyrics)
    app.start()
