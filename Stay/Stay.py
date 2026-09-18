import os
import sys
import time
import math
import random
import pygame
import tkinter as tk

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# ==============================================================================
# CẤU HÌNH GIAO DIỆN SINGLE-SCREEN LYRIC SYNC PLAYER
# Thiết kế: Bầu trời đêm tĩnh lặng, hiệu ứng sao dịu nhẹ
# ==============================================================================
FRAME_DELAY_MS = 33             # ~30 FPS (mượt mà, nhẹ máy)
TYPEWRITER_SPEED = 55           # Tốc độ gõ chữ mặc định (ms/ký tự)
NUM_STARS = 80                  # Số ngôi sao trên màn hình
BG_HUE_START = 225              # Tông màu nền ban đầu (xanh navy)
BG_HUE_RANGE = 40               # Phạm vi đổi màu nền (225° → 265° → 225°)
BG_CYCLE_SECONDS = 180          # 3 phút cho 1 vòng đổi màu nền

# Bảng màu theo cảm xúc (chỉ thay đổi accent, nền luôn tối)
MOOD_ACCENTS = {
    "longing": "#67E8F9",    # Cyan nhẹ
    "pain":    "#C084FC",    # Lavender
    "plea":    "#FBBF24",    # Amber ấm
    "storm":   "#FB7185",    # Rose đỏ
    "hope":    "#34D399",    # Mint xanh
    "release": "#A78BFA",    # Tím nhạt
}

FONT_LARGE = "Segoe UI"
FONT_SMALL = "Segoe UI"
FONT_TIME = "Segoe UI"
FONT_TIME_BG = "#111118"


def hsl_to_hex(h, s, l):
    """Chuyển HSL sang hex color."""
    c = (1 - abs(2 * l - 1)) * s
    x = c * (1 - abs((h / 60) % 2 - 1))
    m = l - c / 2
    if h < 60:
        r, g, b = c, x, 0
    elif h < 120:
        r, g, b = x, c, 0
    elif h < 180:
        r, g, b = 0, c, x
    elif h < 240:
        r, g, b = 0, x, c
    elif h < 300:
        r, g, b = x, 0, c
    else:
        r, g, b = c, 0, x
    return "#{:02x}{:02x}{:02x}".format(
        int((r + m) * 255), int((g + m) * 255), int((b + m) * 255)
    )


class StarFieldApp:
    """
    Single-screen lyric sync player với bầu trời đêm tĩnh lặng.
    - Sao drift cực chậm, fade nhẹ nhàng.
    - Nền đổi màu cực chậm (3 phút/vòng).
    - Lyrics typewriter đồng bộ nhạc.
    - Thanh tiến trình ở cuối.
    - [ESC] thoát | [Space] tạm dừng.
    """
    def __init__(self, audio_file="Stay.mp3", lyrics_file="lyrics.txt"):
        self.root = tk.Tk()
        self.root.attributes("-fullscreen", True)
        self.root.attributes("-topmost", True)
        self.root.config(bg="#06060C")
        self.root.protocol("WM_DELETE_WINDOW", self.quit)

        self.screen_w = self.root.winfo_screenwidth()
        self.screen_h = self.root.winfo_screenheight()

        self.audio_file = audio_file
        self.lyrics_file = lyrics_file

        self.lyrics_timeline = []
        self.next_index = 0
        self.current_line_index = -1
        self.typewriter_text = ""
        self.typewriter_index = 0
        self.line_start_time = 0.0
        self.current_mood = "longing"
        self.accent_color = MOOD_ACCENTS["longing"]

        self.is_running = True
        self.is_paused = False
        self.start_wall_time = None
        self.pause_start_time = None
        self.total_paused_duration = 0.0
        self.current_time = 0.0

        self.load_lyrics()
        self.init_audio()
        self.build_ui()
        self.generate_stars()

        self.start_wall_time = time.time()
        self.update()

    def build_ui(self):
        """Xây dựng giao diện single-screen."""
        self.main_canvas = tk.Canvas(
            self.root, bg="#06060C", highlightthickness=0
        )
        self.main_canvas.pack(fill="both", expand=True)

        # === Nền gradient (nhiều rectangle xếp chồng, sau đó đổi màu dần) ===
        self.gradient_rects = []
        num_layers = 40
        for i in range(num_layers):
            y = int(i * self.screen_h / num_layers)
            h = int(self.screen_h / num_layers) + 2
            rect_id = self.main_canvas.create_rectangle(
                0, y, self.screen_w, y + h,
                fill="#06060C", outline=""
            )
            self.gradient_rects.append(rect_id)

        # === Ngôi sao ===
        self.star_items = []
        # (Tạo sau khi có screen size, nhưng gọi ngay - sẽ dùng values đã có)

        # === Thanh tiến trình ===
        bar_y = self.screen_h - 3
        self.progress_bar_bg = self.main_canvas.create_rectangle(
            0, bar_y, self.screen_w, self.screen_h,
            fill="#0C0C14", outline=""
        )
        self.progress_bar_fill = self.main_canvas.create_rectangle(
            0, bar_y, 0, self.screen_h,
            fill=self.accent_color, outline=""
        )

        # === Thời gian ===
        self.time_text = self.main_canvas.create_text(
            self.screen_w - 25, bar_y - 8,
            text="0:00 / 0:00",
            font=(FONT_TIME, 10),
            fill="#3A3A4A",
            anchor="se"
        )

        # === Title & Artist ===
        self.title_text = self.main_canvas.create_text(
            self.screen_w // 2, 20,
            text="STAY",
            font=(FONT_SMALL, 12, "bold"),
            fill="#2A2A38",
            anchor="center"
        )
        self.artist_text = self.main_canvas.create_text(
            self.screen_w // 2, 40,
            text="Justin Bieber & The Kid LAROI",
            font=(FONT_SMALL, 10),
            fill="#2A2A38",
            anchor="center"
        )

        # === Dòng lyrics trước đó (mờ) ===
        self.prev_label_id = self.main_canvas.create_text(
            self.screen_w // 2, 0,
            text="",
            font=(FONT_LARGE, 20, "normal"),
            fill="#252535",
            anchor="center"
        )

        # === Dòng lyrics hiện tại (sáng) ===
        self.current_label_id = self.main_canvas.create_text(
            self.screen_w // 2, 0,
            text="",
            font=(FONT_LARGE, 26, "bold"),
            fill=self.accent_color,
            anchor="center"
        )

        # === Dòng lyrics tiếp theo (preview mờ) ===
        self.next_label_id = self.main_canvas.create_text(
            self.screen_w // 2, 0,
            text="",
            font=(FONT_LARGE, 17, "normal"),
            fill="#252535",
            anchor="center"
        )

        # === Hint (góc dưới trái) ===
        self.hint_text = self.main_canvas.create_text(
            20, bar_y - 8,
            text="[ESC] Exit  |  [Space] Pause",
            font=(FONT_SMALL, 8),
            fill="#1E1E2A",
            anchor="sw"
        )

        # Tạo stars sau khi canvas đã có
        self.create_stars()

    def create_stars(self):
        """Tạo các ngôi sao trên canvas."""
        for star in self._stars:
            r = star["size"]
            x = star["x"]
            y = star["y"]
            color = star["color"]
            star_id = self.main_canvas.create_oval(
                x - r, y - r, x + r, y + r,
                fill=color, outline=""
            )
            self.star_items.append((star_id, star))

    def generate_stars(self):
        """Tạo danh sách sao với thuộc tính ngẫu nhiên."""
        self._stars = []
        for _ in range(NUM_STARS):
            sx = random.uniform(0, self.screen_w)
            sy = random.uniform(0, self.screen_h)
            size = random.choice([1, 1, 1, 1, 2, 2, 3])
            brightness = random.uniform(0.08, 0.35)
            # Tạo màu nền + brightness
            base_r, base_g, base_b = 26, 26, 42  # #1A1A2A
            cr = int(base_r * (1 + brightness))
            cg = int(base_g * (1 + brightness))
            cb = int(base_b * (1 + brightness * 1.2))
            cr = min(255, cr)
            cg = min(255, cg)
            cb = min(255, cb)

            star = {
                "x": sx,
                "y": sy,
                "size": size,
                "color": "#{:02x}{:02x}{:02x}".format(cr, cg, cb),
                "fade_phase": random.uniform(0, 2 * math.pi),
                "fade_speed": random.uniform(0.001, 0.004),
                "base_brightness": brightness,
                "drift_x": random.uniform(-0.04, 0.04),
                "drift_y": random.uniform(-0.08, -0.01),
                "current_alpha": 1.0,
            }
            self._stars.append(star)

    def load_lyrics(self):
        """Đọc lyrics.txt: [giây|tốc_độ_gõ|cảm_xúc] Lời tiếng Anh"""
        if not os.path.exists(self.lyrics_file):
            print(f"[Error] File '{self.lyrics_file}' not found.")
            return

        with open(self.lyrics_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if line.startswith("[") and "]" in line:
                    tag, content = line[1:].split("]", 1)
                    content = content.strip()
                    parts = tag.split("|")
                    try:
                        time_sec = float(parts[0].strip())
                        speed_ms = int(parts[1].strip()) if len(parts) > 1 else TYPEWRITER_SPEED
                        mood = parts[2].strip() if len(parts) > 2 else "longing"
                        self.lyrics_timeline.append({
                            "time_sec": time_sec,
                            "speed_ms": speed_ms,
                            "mood": mood,
                            "eng": content,
                        })
                    except ValueError:
                        continue

        self.lyrics_timeline.sort(key=lambda item: item["time_sec"])
        print(f"[Lyrics] Loaded {len(self.lyrics_timeline)} lines.")

    def init_audio(self):
        """Khởi tạo pygame mixer."""
        pygame.mixer.init()
        if os.path.exists(self.audio_file):
            pygame.mixer.music.load(self.audio_file)
            print(f"[Music] Audio ready: {os.path.basename(self.audio_file)}")
            print(f"[Note] Placeholder audio - replace Stay.mp3 with the original track.")
        else:
            print(f"[Info] No audio file. Timer sync active (press any key to start timer).")
            self.timer_start = time.time()

    def toggle_pause(self):
        """Tạm dừng / tiếp tục."""
        if self.is_paused:
            if pygame.mixer.music.get_busy():
                pygame.mixer.music.unpause()
            if self.pause_start_time:
                self.total_paused_duration += time.time() - self.pause_start_time
                self.pause_start_time = None
            self.is_paused = False
        else:
            if pygame.mixer.music.get_busy():
                pygame.mixer.music.pause()
            self.pause_start_time = time.time()
            self.is_paused = True

    def get_current_music_time(self):
        """Lấy thời gian bài hát hiện tại (giây)."""
        if pygame.mixer.music.get_busy() or self.is_paused:
            pos_ms = pygame.mixer.music.get_pos()
            if pos_ms >= 0:
                return pos_ms / 1000.0
        if self.start_wall_time:
            elapsed = time.time() - self.start_wall_time - self.total_paused_duration
            return max(0.0, elapsed)
        return 0.0

    def format_time(self, seconds):
        m = int(seconds // 60)
        s = int(seconds % 60)
        return f"{m}:{s:02d}"

    def get_total_duration(self):
        if self.lyrics_timeline:
            return self.lyrics_timeline[-1]["time_sec"] + 10
        return 0

    def update_background(self):
        """Cập nhật nền: đổi màu gradient cực chậm."""
        elapsed = self.current_time
        hue_progress = (elapsed / BG_CYCLE_SECONDS) % 1.0

        # Oscillate hue: 225° → 265° → 225°
        hue = BG_HUE_START + BG_HUE_RANGE * math.sin(hue_progress * math.pi)
        sat = 0.08
        light = 0.035

        base_color = hsl_to_hex(hue, sat, light)

        for i, rect_id in enumerate(self.gradient_rects):
            layer_ratio = i / len(self.gradient_rects)
            l = light + layer_ratio * 0.02
            color = hsl_to_hex(hue, sat, l)
            self.main_canvas.itemconfig(rect_id, fill=color)

    def update_stars(self):
        """Cập nhật vị trí & độ sáng sao (drift chậm, fade nhẹ)."""
        for star_id, star in self.star_items:
            star["x"] += star["drift_x"]
            star["y"] += star["drift_y"]

            # Wrap around
            if star["x"] < -5:
                star["x"] = self.screen_w + 5
            elif star["x"] > self.screen_w + 5:
                star["x"] = -5
            if star["y"] < -5:
                star["y"] = self.screen_h + 5
            elif star["y"] > self.screen_h + 5:
                star["y"] = -5

            # Fade in/out (very slow)
            star["fade_phase"] += star["fade_speed"]
            alpha = 0.5 + 0.5 * math.sin(star["fade_phase"])
            star["current_alpha"] = alpha

            brightness = star["base_brightness"] * alpha
            base_r, base_g, base_b = 30, 30, 50
            cr = min(255, int(base_r * (1 + brightness * 4)))
            cg = min(255, int(base_g * (1 + brightness * 4)))
            cb = min(255, int(base_b * (1 + brightness * 4.5)))
            color = "#{:02x}{:02x}{:02x}".format(cr, cg, cb)

            self.main_canvas.itemconfig(star_id, fill=color)

    def update(self):
        """Vòng lặp chính."""
        if not self.is_running:
            return

        if not self.is_paused:
            self.current_time = self.get_current_music_time()

            # Cập nhật nền + sao (mỗi frame)
            self.update_background()
            self.update_stars()

            # === Lyrics sync ===
            while self.next_index < len(self.lyrics_timeline):
                line = self.lyrics_timeline[self.next_index]
                if self.current_time >= line["time_sec"]:
                    if self.next_index != self.current_line_index:
                        self.current_line_index = self.next_index
                        self.typewriter_index = 0
                        self.typewriter_text = ""
                        self.current_mood = line["mood"]
                        self.accent_color = MOOD_ACCENTS.get(
                            self.current_mood, self.accent_color
                        )
                        self.main_canvas.itemconfig(
                            self.current_label_id, fill=self.accent_color
                        )
                        self.main_canvas.itemconfig(
                            self.progress_bar_fill, fill=self.accent_color
                        )
                    self.next_index += 1
                else:
                    break

            # Typewriter
            if self.current_line_index >= 0 and self.current_line_index < len(self.lyrics_timeline):
                line = self.lyrics_timeline[self.current_line_index]
                speed = line.get("speed_ms", TYPEWRITER_SPEED)
                target_text = line["eng"]

                time_since_start = self.current_time - self.line_start_time
                chars_per_second = 1000.0 / max(speed, 1)
                chars_to_show = int(time_since_start * chars_per_second)
                target_len = len(target_text)

                self.typewriter_index = min(chars_to_show, target_len)
                self.typewriter_text = target_text[:self.typewriter_index]

                display_text = self.typewriter_text.rstrip()
                if self.typewriter_index < target_len:
                    display_text += " ▌"

                self.main_canvas.itemconfig(self.current_label_id, text=display_text)

                # Vị trí các dòng lyrics
                lyric_y = self.screen_h // 2 - 20
                line_spacing = int(self.screen_h * 0.065)

                prev_text = ""
                if self.current_line_index > 0:
                    prev_line = self.lyrics_timeline[self.current_line_index - 1]
                    prev_text = prev_line["eng"]
                self.main_canvas.coords(self.prev_label_id, self.screen_w // 2, lyric_y - line_spacing)
                self.main_canvas.itemconfig(self.prev_label_id, text=prev_text)

                self.main_canvas.coords(self.current_label_id, self.screen_w // 2, lyric_y)

                next_text = ""
                if self.current_line_index + 1 < len(self.lyrics_timeline):
                    next_line = self.lyrics_timeline[self.current_line_index + 1]
                    next_text = next_line["eng"]
                self.main_canvas.coords(self.next_label_id, self.screen_w // 2, lyric_y + line_spacing)
                self.main_canvas.itemconfig(self.next_label_id, text=next_text)

                # === Progress bar ===
                total = self.get_total_duration()
                progress = min(self.current_time / max(total, 1), 1.0)
                bar_x = progress * self.screen_w
                bar_y = self.screen_h - 3
                self.main_canvas.coords(
                    self.progress_bar_fill,
                    0, bar_y, bar_x, self.screen_h
                )

                current_str = self.format_time(self.current_time)
                total_str = self.format_time(total)
                self.main_canvas.itemconfig(self.time_text, text=f"{current_str} / {total_str}")

            # === Kết thúc ===
            if (self.next_index >= len(self.lyrics_timeline) and
                    self.current_line_index >= len(self.lyrics_timeline) - 1 and
                    (not pygame.mixer.music.get_busy() or not os.path.exists(self.audio_file))):
                self.quit()
                return

        self.root.after(FRAME_DELAY_MS, self.update)

    def quit(self):
        """Dọn dẹp và thoát."""
        self.is_running = False
        try:
            pygame.mixer.music.stop()
            pygame.mixer.quit()
        except Exception:
            pass
        try:
            self.root.destroy()
        except Exception:
            pass
        try:
            sys.exit(0)
        except SystemExit:
            raise
        except Exception:
            pass

    def start(self):
        """Khởi chạy."""
        print("=" * 60)
        print("  🎵 STAY - SINGLE SCREEN LYRIC PLAYER")
        print("  [ESC] Exit  |  [Space] Pause")
        print("=" * 60)
        if os.path.exists(self.audio_file):
            pygame.mixer.music.play()
        self.root.mainloop()


if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    audio = os.path.join(current_dir, "Stay.mp3")
    lyrics = os.path.join(current_dir, "lyrics.txt")

    app = StarFieldApp(audio_file=audio, lyrics_file=lyrics)
    app.start()
