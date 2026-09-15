import os
import sys
import time
import math
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
# CẤU HÌNH GIAO DIỆN & HIỆU ỨNG THẺ GHI CHÚ NGHỆ THUẬT (ROMANTIC FLOATING NOTES)
# ==============================================================================
BOX_W = 310           # Chiều rộng thẻ ghi chú (pixels)
BOX_H = 195           # Chiều cao thẻ ghi chú (pixels)
RISE_SPEED = 0.85     # Tốc độ bay lên lững lờ, lãng mạn (pixels mỗi frame)
FRAME_DELAY_MS = 25   # Chu kỳ làm mới animation (~40 FPS)

# Bảng màu nghệ thuật theo phong cách hoài niệm (Vintage Ballad)
# Chia vai rõ rệt cho màn song ca kinh điển: Bruno Mars vs Lady Gaga vs Duet
SINGER_THEMES = {
    "Bruno": {
        "badge": "🎸 BRUNO MARS",
        "badge_bg": "#FEF3C7",
        "badge_fg": "#92400E",
        "bg": "#FFFBEB",
        "fg": "#1E293B",
        "border": "#F59E0B",
        "accent": "#D97706",
        "heart": "#F59E0B"
    },
    "Gaga": {
        "badge": "🌹 LADY GAGA",
        "badge_bg": "#FFE4E6",
        "badge_fg": "#9F1239",
        "bg": "#FFF1F2",
        "fg": "#4C0519",
        "border": "#FB7185",
        "accent": "#E11D48",
        "heart": "#E11D48"
    },
    "Duet": {
        "badge": "✨ BRUNO & GAGA • HARMONY",
        "badge_bg": "#F3E8FF",
        "badge_fg": "#6B21A8",
        "bg": "#FAF5FF",
        "fg": "#3B0764",
        "border": "#C084FC",
        "accent": "#9333EA",
        "heart": "#A855F7"
    }
}

FONT_FAMILY = "Segoe UI"
FONT_SIZE = 12


class RomanticLyricCard:
    """
    Thẻ ghi chú ballad cao cấp:
    - Hiển thị badge nhận diện ca sĩ (Bruno Mars / Lady Gaga / Song ca).
    - Hiệu ứng đung đưa hình sin (Sway Motion) lơ lửng như cánh hoa trong gió.
    - Hiệu ứng typewriter với con trỏ nhấp nháy như thư tay tình yêu.
    - Cho phép kéo thả mượt mà bằng chuột.
    """
    def __init__(self, master, lyric_data, x, y, on_close=None):
        self.master = master
        self.full_text = lyric_data["text"]
        self.speed_ms = lyric_data.get("speed_ms", 65)
        self.singer_key = lyric_data.get("singer", "Duet")
        self.theme = SINGER_THEMES.get(self.singer_key, SINGER_THEMES["Duet"])
        self.on_close = on_close

        # Tọa độ cơ sở và hiệu ứng lắc lư hình sin (Sway)
        self.base_x = float(x)
        self.y = float(y)
        self.sway_phase = random.uniform(0, math.pi * 2)
        self.sway_amp = random.uniform(12.0, 20.0)
        self.sway_speed = random.uniform(1.8, 2.4)
        self.created_time = time.time()

        # Tạo cửa sổ Toplevel không viền, nổi trên mọi ứng dụng
        self.win = tk.Toplevel(master)
        self.win.overrideredirect(True)
        self.win.attributes("-topmost", True)
        self.win.geometry(f"{BOX_W}x{BOX_H}+{int(self.base_x)}+{int(self.y)}")
        self.win.config(bg=self.theme["border"])

        # Khung viền ngoài mô phỏng tấm thiệp tình thư
        self.inner_frame = tk.Frame(
            self.win,
            bg=self.theme["bg"],
            highlightthickness=0,
            padx=12,
            pady=10
        )
        self.inner_frame.pack(fill="both", expand=True, padx=2, pady=2)

        # 1. Thanh chỉ báo màu sắc nghệ thuật ở đỉnh thẻ (Accent Strip)
        self.accent_bar = tk.Frame(self.inner_frame, bg=self.theme["accent"], height=3)
        self.accent_bar.pack(fill="x", side="top", pady=(0, 6))

        # 2. Header Frame: Badge ca sĩ + Icon trái tim
        self.header_frame = tk.Frame(self.inner_frame, bg=self.theme["bg"])
        self.header_frame.pack(fill="x", side="top")

        self.singer_badge = tk.Label(
            self.header_frame,
            text=f" {self.theme['badge']} ",
            font=(FONT_FAMILY, 9, "bold"),
            bg=self.theme["badge_bg"],
            fg=self.theme["badge_fg"],
            padx=6,
            pady=2
        )
        self.singer_badge.pack(side="left")

        self.heart_icon = tk.Label(
            self.header_frame,
            text="♥",
            font=(FONT_FAMILY, 11, "bold"),
            bg=self.theme["bg"],
            fg=self.theme["heart"]
        )
        self.heart_icon.pack(side="right")

        # 3. Nội dung lời bài hát
        self.label = tk.Label(
            self.inner_frame,
            text="",
            wraplength=BOX_W - 36,
            justify="center",
            font=(FONT_FAMILY, FONT_SIZE, "bold"),
            fg=self.theme["fg"],
            bg=self.theme["bg"]
        )
        self.label.pack(expand=True, fill="both", pady=(6, 4))

        # Hỗ trợ kéo thả bằng chuột
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.is_dragging = False

        for widget in (self.win, self.inner_frame, self.label, self.header_frame, self.singer_badge, self.heart_icon):
            widget.bind("<ButtonPress-1>", self.start_drag)
            widget.bind("<B1-Motion>", self.do_drag)
            widget.bind("<ButtonRelease-1>", self.stop_drag)
            widget.bind("<Button-3>", lambda e: self.destroy())

        # Bắt đầu hiệu ứng gõ máy chữ
        self.typewriter_index = 0
        self.is_alive = True
        self.typewriter()

    def start_drag(self, event):
        self.is_dragging = True
        self.drag_start_x = event.x
        self.drag_start_y = event.y

    def do_drag(self, event):
        dx = event.x - self.drag_start_x
        dy = event.y - self.drag_start_y
        self.base_x += dx
        self.y += dy
        self.win.geometry(f"{BOX_W}x{BOX_H}+{int(self.base_x)}+{int(self.y)}")

    def stop_drag(self, event):
        self.is_dragging = False

    def typewriter(self):
        """Gõ từng ký tự với con trỏ nhấp nháy chân thực như thư tay."""
        if not self.is_alive:
            return
        if self.typewriter_index <= len(self.full_text):
            # Hiển thị ký tự kèm con trỏ nhấp nháy
            cursor = " ▌" if self.typewriter_index < len(self.full_text) else ""
            self.label.config(text=self.full_text[:self.typewriter_index] + cursor)
            self.typewriter_index += 1
            self.win.after(self.speed_ms, self.typewriter)
        else:
            # Gõ xong: giữ chữ sạch sẽ không còn con trỏ
            self.label.config(text=self.full_text)

    def rise(self, dy):
        """Bay dần lên trên kết hợp đung đưa hình sin (Sway Animation)."""
        if not self.is_alive:
            return
        self.y -= dy

        if not self.is_dragging:
            elapsed = time.time() - self.created_time
            sway_offset = math.sin(elapsed * self.sway_speed + self.sway_phase) * self.sway_amp
            current_x = self.base_x + sway_offset
        else:
            current_x = self.base_x

        self.win.geometry(f"{BOX_W}x{BOX_H}+{int(current_x)}+{int(self.y)}")

    def is_offscreen(self):
        """Kiểm tra thẻ đã trôi khuất hẳn khỏi đỉnh màn hình chưa."""
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
    Ứng dụng phát nhạc & điều phối các thẻ ghi chú nổi cho bài hát Die With A Smile.
    """
    def __init__(self, audio_file="DieWithASmile.mp3", lyrics_file="lyrics.txt"):
        self.root = tk.Tk()
        self.root.withdraw()

        self.screen_w = self.root.winfo_screenwidth()
        self.screen_h = self.root.winfo_screenheight()

        self.audio_file = audio_file
        self.lyrics_file = lyrics_file
        
        self.cards = []
        self.next_index = 0
        self.lyrics_timeline = []
        self.last_x_slot = 1

        # 1. Nạp danh sách câu hát
        self.load_lyrics()

        # 2. Khởi tạo pygame mixer
        self.init_audio()

        # 3. Phím tắt ESC thoát nhanh
        self.root.bind_all("<Escape>", lambda e: self.quit())

        self.start_wall_time = None
        self.is_running = True

    def init_audio(self):
        """Khởi động pygame mixer và tải file nhạc."""
        pygame.mixer.init()
        if os.path.exists(self.audio_file):
            print(f"[Music] Loading audio file: {os.path.basename(self.audio_file)}")
            pygame.mixer.music.load(self.audio_file)
        else:
            print(f"[Warning] Audio '{self.audio_file}' not found. Falling back to timer.")

    def load_lyrics(self):
        """
        Đọc file lyrics.txt với định dạng mở rộng:
        [thời_gian_giây|tốc_độ_gõ_ms|ca_sĩ] Lời bài hát
        """
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
                        speed_ms = int(parts[1].strip()) if len(parts) > 1 else 65
                        singer = parts[2].strip() if len(parts) > 2 else "Duet"
                        self.lyrics_timeline.append({
                            "time_sec": time_sec,
                            "speed_ms": speed_ms,
                            "singer": singer,
                            "text": text
                        })
                    except ValueError:
                        continue

        self.lyrics_timeline.sort(key=lambda item: item["time_sec"])
        print(f"[Lyrics] Successfully loaded {len(self.lyrics_timeline)} synchronized lines with singer roles.")

    def random_safe_x(self):
        """Phân bổ tọa độ X theo luân phiên các vùng để tránh các thẻ đè lên nhau."""
        margin = 70
        usable_width = self.screen_w - BOX_W - (margin * 2)
        num_slots = 3
        slot_width = usable_width / num_slots

        available_slots = [s for s in range(num_slots) if s != self.last_x_slot]
        chosen_slot = random.choice(available_slots)
        self.last_x_slot = chosen_slot

        slot_start = margin + int(chosen_slot * slot_width)
        slot_end = int(slot_start + slot_width - 30)
        return random.randint(slot_start, max(slot_start + 10, slot_end))

    def spawn_card(self, lyric_data):
        """Tạo thẻ card mới nổi lên từ đáy màn hình."""
        spawn_x = self.random_safe_x()
        spawn_y = self.screen_h - BOX_H - random.randint(50, 90)

        card = RomanticLyricCard(
            master=self.root,
            lyric_data=lyric_data,
            x=spawn_x,
            y=spawn_y,
            on_close=lambda c: self.cards.remove(c) if c in self.cards else None
        )
        self.cards.append(card)
        role = lyric_data.get("singer", "Duet")
        print(f"[{lyric_data['time_sec']:5.1f}s] [{role:5s}] Spawning: \"{lyric_data['text']}\"")

    def get_current_music_time(self):
        """Lấy mốc thời gian bài hát chính xác từ pygame."""
        if pygame.mixer.music.get_busy():
            pos_ms = pygame.mixer.music.get_pos()
            if pos_ms >= 0:
                return pos_ms / 1000.0
        if self.start_wall_time:
            return time.time() - self.start_wall_time
        return 0.0

    def update(self):
        """Vòng lặp animation: kiểm tra mốc thời gian và cập nhật chuyển động đung đưa."""
        if not self.is_running:
            return

        current_time = self.get_current_music_time()

        # 1. Sinh thẻ mới khi đến mốc thời gian
        while self.next_index < len(self.lyrics_timeline):
            next_lyric = self.lyrics_timeline[self.next_index]
            if current_time >= next_lyric["time_sec"]:
                self.spawn_card(next_lyric)
                self.next_index += 1
            else:
                break

        # 2. Cập nhật bay lên và đung đưa lơ lửng cho các thẻ
        for card in list(self.cards):
            card.rise(RISE_SPEED)
            if card.is_offscreen():
                card.destroy()

        # 3. Kết thúc khi bài hát hết và thẻ đã trôi hết
        if self.next_index >= len(self.lyrics_timeline) and not self.cards:
            if not pygame.mixer.music.get_busy():
                print("\n[App] Song completed and all romantic lyric cards finished. Exiting.")
                self.quit()
                return

        self.root.after(FRAME_DELAY_MS, self.update)

    def start(self):
        """Bắt đầu phát nhạc và chạy giao diện."""
        print("=" * 68)
        print("  🌹 DIE WITH A SMILE - LADY GAGA & BRUNO MARS 🌹")
        print("  Tính năng độc quyền:")
        print("  - Phân loại màu sắc & Badge theo ca sĩ: Bruno Mars / Lady Gaga / Duet")
        print("  - Chuyển động uốn lượn hình sin (Sway Motion) lơ lửng như lá rơi")
        print("  - Hiệu ứng máy đánh chữ kèm con trỏ nhấp nháy như viết thư tay")
        print("  - Kéo thả thẻ tùy ý bằng chuột, nhấn [ESC] để dừng bất cứ lúc nào")
        print("=" * 68)

        if os.path.exists(self.audio_file):
            pygame.mixer.music.play()

        self.start_wall_time = time.time()
        self.root.after(10, self.update)
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self.quit()

    def quit(self):
        """Dừng âm thanh và đóng tất cả cửa sổ."""
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
    """Tự động ưu tiên tìm file DieWithASmile.mp3 trong thư mục hiện tại."""
    dir_path = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(dir_path, "DieWithASmile.mp3"),
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    for f in os.listdir(dir_path):
        if f.lower().endswith((".mp3", ".wav")):
            return os.path.join(dir_path, f)
    return os.path.join(dir_path, "DieWithASmile.mp3")


if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    audio = find_audio_file()
    lyrics = os.path.join(current_dir, "lyrics.txt")
    
    app = LyricFloatApp(audio_file=audio, lyrics_file=lyrics)
    app.start()
