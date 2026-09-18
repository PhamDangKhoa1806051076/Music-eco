import os
import sys
import time
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
# ==============================================================================
FRAME_DELAY_MS = 20           # Chu kỳ làm mới (~50 FPS)
TYPEWRITER_SPEED = 55         # Tốc độ gõ chữ mặc định (ms/ký tự)
MAX_VISIBLE_LYRICS = 3        # Số dòng lyrics hiển thị tối đa
BG_COLOR = "#080810"           # Nền tối đen
FG_COLOR = "#E8E8F0"           # Chữ sáng
DIM_COLOR = "#4A4A5A"          # Chữ mờ (preview/trước đó)
ACTIVE_COLOR = "#67E8F9"       # Chữ đang gõ (cyan neon)
PROGRESS_COLOR = "#67E8F9"     # Màu thanh tiến trình
GLOW_COLOR = "#67E8F9"         # Màu glow

# Bảng màu theo cảm xúc (đổi nền theo từng section)
MOOD_THEMES = {
    "longing": {"bg": "#080810", "fg": "#E8E8F0", "glow": "#67E8F9", "accent": "#67E8F9"},
    "pain":    {"bg": "#0A0810", "fg": "#E8E0E8", "glow": "#C084FC", "accent": "#C084FC"},
    "plea":    {"bg": "#0C0A08", "fg": "#F0E8E0", "glow": "#FBBF24", "accent": "#FBBF24"},
    "storm":   {"bg": "#080610", "fg": "#F0F0FF", "glow": "#FB7185", "accent": "#FB7185"},
    "hope":    {"bg": "#080C0A", "fg": "#E0F0E8", "glow": "#34D399", "accent": "#34D399"},
    "release": {"bg": "#060810", "fg": "#D8D8E8", "glow": "#A78BFA", "accent": "#A78BFA"},
}

FONT_LYRIC = "Segoe UI"
FONT_LARGE = "Segoe UI"
FONT_SMALL = "Segoe UI"
FONT_TIME = "Segoe UI"


class SingleScreenLyricApp:
    """
    Ứng dụng phát nhạc & lyrics trên 1 màn hình duy nhất.
    - Lyrics hiện dạng typewriter, đồng bộ với nhạc.
    - Dòng hiện tại sáng, dòng trước mờ, dòng sau preview mờ nhạt.
    - Thanh tiến trình ở dưới cùng.
    - Glow animation phía sau lyrics.
    - ESC để thoát.
    """
    def __init__(self, audio_file="Stay.mp3", lyrics_file="lyrics.txt"):
        self.root = tk.Tk()
        self.root.attributes("-fullscreen", True)
        self.root.attributes("-topmost", True)
        self.root.config(bg=BG_COLOR)
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
        self.last_mood = None
        self.glow_alpha = 0.05
        self.glow_direction = 1

        self.is_running = True
        self.is_paused = False
        self.start_wall_time = None
        self.pause_start_time = None
        self.total_paused_duration = 0.0
        self.current_time = 0.0

        # 1. Nạp lyrics
        self.load_lyrics()

        # 2. Khởi tạo âm thanh
        self.init_audio()

        # 3. Phím tắt
        self.root.bind_all("<Escape>", lambda e: self.quit())
        self.root.bind_all("<space>", lambda e: self.toggle_pause())

        # 4. Thiết lập giao diện
        self.build_ui()

        # 5. Bắt đầu vòng lặp
        self.start_wall_time = time.time()
        self.update()

    def build_ui(self):
        """Xây dựng giao diện single-screen."""
        # === Canvas chính (toàn màn hình) ===
        self.main_canvas = tk.Canvas(
            self.root,
            bg=BG_COLOR,
            highlightthickness=0
        )
        self.main_canvas.pack(fill="both", expand=True)

        # === Glow circle phía sau lyrics ===
        self.glow_item = self.main_canvas.create_oval(
            0, 0, 0, 0,
            fill=GLOW_COLOR,
            outline="",
            stipple="gray50"
        )

        # === Thanh tiến trình (bottom) ===
        bar_h = 4
        bar_y = self.screen_h - bar_h - 2
        self.progress_bar_bg = self.main_canvas.create_rectangle(
            0, bar_y, self.screen_w, self.screen_h,
            fill="#1A1A2E", outline=""
        )
        self.progress_bar_fill = self.main_canvas.create_rectangle(
            0, bar_y, 0, self.screen_h,
            fill=PROGRESS_COLOR, outline=""
        )

        # === Thời gian hiển thị (góc dưới phải) ===
        self.time_text = self.main_canvas.create_text(
            self.screen_w - 30, bar_y - 8,
            text="0:00 / 0:00",
            font=(FONT_TIME, 10),
            fill=DIM_COLOR,
            anchor="se"
        )

        # === Dòng lyrics trước đó (trên, mờ) ===
        self.prev_label_id = self.main_canvas.create_text(
            self.screen_w // 2, 0,
            text="",
            font=(FONT_LARGE, 22, "normal"),
            fill=DIM_COLOR,
            anchor="center"
        )

        # === Dòng lyrics hiện tại (giữa, sáng) ===
        self.current_label_id = self.main_canvas.create_text(
            self.screen_w // 2, 0,
            text="",
            font=(FONT_LARGE, 26, "bold"),
            fill=ACTIVE_COLOR,
            anchor="center"
        )

        # === Dòng lyrics tiếp theo (dưới, mờ preview) ===
        self.next_label_id = self.main_canvas.create_text(
            self.screen_w // 2, 0,
            text="",
            font=(FONT_LARGE, 18, "normal"),
            fill=DIM_COLOR,
            anchor="center"
        )

        # === Title & Artist (trên cùng) ===
        self.title_text = self.main_canvas.create_text(
            self.screen_w // 2, 20,
            text="STAY",
            font=(FONT_SMALL, 12, "bold"),
            fill=DIM_COLOR,
            anchor="center"
        )
        self.artist_text = self.main_canvas.create_text(
            self.screen_w // 2, 40,
            text="Justin Bieber & The Kid LAROI",
            font=(FONT_SMALL, 10),
            fill=DIM_COLOR,
            anchor="center"
        )

        # === Controls hint (góc dưới trái) ===
        self.hint_text = self.main_canvas.create_text(
            20, bar_y - 8,
            text="[ESC] Thoát  |  [Space] Tạm dừng",
            font=(FONT_SMALL, 8),
            fill="#2A2A3A",
            anchor="sw"
        )

    def load_lyrics(self):
        """Đọc lyrics.txt: [giây|tốc_độ_gõ|cảm_xúc] Lời EN // Vietsub"""
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

                        if "//" in content:
                            eng, vie = content.split("//", 1)
                            eng = eng.strip()
                            vie = vie.strip()
                        else:
                            eng = content
                            vie = ""

                        self.lyrics_timeline.append({
                            "time_sec": time_sec,
                            "speed_ms": speed_ms,
                            "mood": mood,
                            "eng": eng,
                            "vie": vie
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
        else:
            print(f"[Warning] Audio not found. Timer fallback.")

    def toggle_pause(self):
        """Tạm dừng / tiếp tục."""
        if self.is_paused:
            pygame.mixer.music.unpause()
            if self.pause_start_time:
                self.total_paused_duration += time.time() - self.pause_start_time
                self.pause_start_time = None
            self.is_paused = False
        else:
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
        """Định dạng thời gian mm:ss."""
        m = int(seconds // 60)
        s = int(seconds % 60)
        return f"{m}:{s:02d}"

    def get_total_duration(self):
        """Ước lượng tổng thời gian từ lyrics cuối."""
        if self.lyrics_timeline:
            return self.lyrics_timeline[-1]["time_sec"] + 10
        return 0

    def update(self):
        """Vòng lặp chính: sync lyrics + animation."""
        if not self.is_running:
            return

        if not self.is_paused:
            self.current_time = self.get_current_music_time()

            # === 1. Kiểm tra xem có dòng lyrics mới cần hiển thị không ===
            while self.next_index < len(self.lyrics_timeline):
                line = self.lyrics_timeline[self.next_index]
                if self.current_time >= line["time_sec"]:
                    if self.next_index != self.current_line_index:
                        self.current_line_index = self.next_index
                        self.typewriter_index = 0
                        self.typewriter_text = ""
                        self.line_start_time = self.current_time
                        self.last_mood = line["mood"]
                    self.next_index += 1
                else:
                    break

            # === 2. Typewriter animation (dựa trên thời gian kể từ dòng bắt đầu) ===
            if self.current_line_index >= 0 and self.current_line_index < len(self.lyrics_timeline):
                line = self.lyrics_timeline[self.current_line_index]
                speed = line.get("speed_ms", TYPEWRITER_SPEED)
                target_text = f"{line['eng']}\n— {line['vie']} —" if line["vie"] else line["eng"]

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

                # Cập nhật mood/theme background khi đổi section
                theme = MOOD_THEMES.get(self.last_mood, MOOD_THEMES["longing"])
                self.main_canvas.config(bg=theme["bg"])

                # === 3. Glow animation ===
                self.glow_alpha += 0.02 * self.glow_direction
                if self.glow_alpha > 0.15:
                    self.glow_direction = -1
                elif self.glow_alpha < 0.02:
                    self.glow_direction = 1
                glow_size = int(800 + self.glow_alpha * 2000)
                cx = self.screen_w // 2
                cy = self.screen_h // 2 - 40
                self.main_canvas.coords(
                    self.glow_item,
                    cx - glow_size // 2, cy - glow_size // 2,
                    cx + glow_size // 2, cy + glow_size // 2
                )
                self.main_canvas.itemconfig(
                    self.glow_item,
                    fill=theme["glow"]
                )

                # === 4. Cập nhật vị trí các dòng lyrics ===
                lyric_y = self.screen_h // 2 - 40
                line_height = 48

                # Dòng trước đó (mờ)
                prev_text = ""
                if self.current_line_index > 0:
                    prev_line = self.lyrics_timeline[self.current_line_index - 1]
                    prev_text = prev_line["eng"]
                    if prev_line["vie"]:
                        prev_text += f"\n— {prev_line['vie']} —"
                self.main_canvas.coords(self.prev_label_id, self.screen_w // 2, lyric_y - line_height * 1.5)
                self.main_canvas.itemconfig(self.prev_label_id, text=prev_text)

                # Dòng hiện tại (sáng)
                self.main_canvas.coords(self.current_label_id, self.screen_w // 2, lyric_y)

                # Dòng tiếp theo (preview mờ)
                next_text = ""
                if self.current_line_index + 1 < len(self.lyrics_timeline):
                    next_line = self.lyrics_timeline[self.current_line_index + 1]
                    next_text = next_line["eng"]
                    if next_line["vie"]:
                        next_text += f"\n— {next_line['vie']} —"
                self.main_canvas.coords(self.next_label_id, self.screen_w // 2, lyric_y + line_height * 1.5)
                self.main_canvas.itemconfig(self.next_label_id, text=next_text)

                # === 5. Thanh tiến trình ===
                total = self.get_total_duration()
                progress = min(self.current_time / max(total, 1), 1.0)
                bar_x = progress * self.screen_w
                bar_y = self.screen_h - 4 - 2
                self.main_canvas.coords(
                    self.progress_bar_fill,
                    0, bar_y, bar_x, self.screen_h
                )

                # Thời gian
                current_str = self.format_time(self.current_time)
                total_str = self.format_time(total)
                self.main_canvas.itemconfig(self.time_text, text=f"{current_str} / {total_str}")

            # === 6. Kết thúc ===
            if (self.next_index >= len(self.lyrics_timeline) and
                    self.current_line_index >= len(self.lyrics_timeline) - 1 and
                    not pygame.mixer.music.get_busy()):
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
        print("  [ESC] Thoát  |  [Space] Tạm dừng")
        print("=" * 60)
        if os.path.exists(self.audio_file):
            pygame.mixer.music.play()
        self.root.mainloop()


if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    audio = os.path.join(current_dir, "Stay.mp3")
    lyrics = os.path.join(current_dir, "lyrics.txt")

    app = SingleScreenLyricApp(audio_file=audio, lyrics_file=lyrics)
    app.start()
