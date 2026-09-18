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
# Cửa sổ vừa đủ, nền bầu trời đêm tĩnh lặng, hiệu ứng sao dịu nhẹ
# ==============================================================================
WINDOW_W = 1200          # Chiều rộng cửa sổ
WINDOW_H = 700           # Chiều cao cửa sổ
FRAME_DELAY_MS = 33       # ~30 FPS
TYPEWRITER_SPEED = 55     # Tốc độ gõ chữ mặc định (ms/ký tự)
NUM_STARS = 80            # Số ngôi sao
BG_HUE_START = 225        # Tông màu nền (xanh navy)
BG_HUE_RANGE = 40         # Phạm vi đổi màu nền
BG_CYCLE_SECONDS = 180    # 3 phút cho 1 vòng đổi màu

MOOD_ACCENTS = {
    "longing": "#67E8F9",
    "pain":    "#C084FC",
    "plea":    "#FBBF24",
    "storm":   "#FB7185",
    "hope":    "#34D399",
    "release": "#A78BFA",
}

FONT_LARGE = "Segoe UI"
FONT_SMALL = "Segoe UI"
FONT_TIME = "Segoe UI"


def hsl_to_hex(h, s, l):
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
    def __init__(self, audio_file="Stay.mp3", lyrics_file="lyrics.txt"):
        self.root = tk.Tk()
        self.root.title("Stay - Justin Bieber & The Kid LAROI")
        self.root.resizable(False, False)

        self.screen_w = self.root.winfo_screenwidth()
        self.screen_h = self.root.winfo_screenheight()
        self.win_x = (self.screen_w - WINDOW_W) // 2
        self.win_y = (self.screen_h - WINDOW_H) // 2
        self.root.geometry(f"{WINDOW_W}x{WINDOW_H}+{self.win_x}+{self.win_y}")
        self.root.config(bg="#06060C")
        self.root.protocol("WM_DELETE_WINDOW", self.quit)

        self.audio_file = audio_file
        self.lyrics_file = lyrics_file
        self.has_audio = os.path.exists(self.audio_file)

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
        self.generate_stars()
        self.build_ui()
        self.init_audio()

        self.start_wall_time = time.time()
        self.update()

    def build_ui(self):
        self.main_canvas = tk.Canvas(
            self.root, bg="#06060C", highlightthickness=0
        )
        self.main_canvas.pack(fill="both", expand=True)

        self.gradient_rects = []
        num_layers = 30
        for i in range(num_layers):
            y = int(i * WINDOW_H / num_layers)
            h = int(WINDOW_H / num_layers) + 2
            rect_id = self.main_canvas.create_rectangle(
                0, y, WINDOW_W, y + h,
                fill="#06060C", outline=""
            )
            self.gradient_rects.append(rect_id)

        self.star_items = []

        bar_y = WINDOW_H - 3
        self.progress_bar_bg = self.main_canvas.create_rectangle(
            0, bar_y, WINDOW_W, WINDOW_H,
            fill="#0C0C14", outline=""
        )
        self.progress_bar_fill = self.main_canvas.create_rectangle(
            0, bar_y, 0, WINDOW_H,
            fill=self.accent_color, outline=""
        )

        self.time_text = self.main_canvas.create_text(
            WINDOW_W - 25, bar_y - 8,
            text="0:00 / 0:00",
            font=(FONT_TIME, 10),
            fill="#3A3A4A",
            anchor="se"
        )

        self.title_text = self.main_canvas.create_text(
            WINDOW_W // 2, 16,
            text="STAY",
            font=(FONT_SMALL, 12, "bold"),
            fill="#2A2A38",
            anchor="center"
        )
        self.artist_text = self.main_canvas.create_text(
            WINDOW_W // 2, 34,
            text="Justin Bieber & The Kid LAROI",
            font=(FONT_SMALL, 10),
            fill="#2A2A38",
            anchor="center"
        )

        self.prev_label_id = self.main_canvas.create_text(
            WINDOW_W // 2, 0,
            text="",
            font=(FONT_LARGE, 19, "normal"),
            fill="#252535",
            anchor="center"
        )

        self.current_label_id = self.main_canvas.create_text(
            WINDOW_W // 2, 0,
            text="",
            font=(FONT_LARGE, 24, "bold"),
            fill=self.accent_color,
            anchor="center"
        )

        self.next_label_id = self.main_canvas.create_text(
            WINDOW_W // 2, 0,
            text="",
            font=(FONT_LARGE, 15, "normal"),
            fill="#252535",
            anchor="center"
        )

        self.hint_text = self.main_canvas.create_text(
            15, bar_y - 8,
            text="[ESC] Exit  |  [Space] Pause  |  Drop Stay.mp3 to play audio",
            font=(FONT_SMALL, 8),
            fill="#1E1E2A",
            anchor="sw"
        )

        self.create_stars()

    def create_stars(self):
        for star in self._stars:
            r = star["size"]
            x = star["x"]
            y = star["y"]
            star_id = self.main_canvas.create_oval(
                x - r, y - r, x + r, y + r,
                fill=star["color"], outline=""
            )
            self.star_items.append((star_id, star))

    def generate_stars(self):
        self._stars = []
        for _ in range(NUM_STARS):
            sx = random.uniform(20, WINDOW_W - 20)
            sy = random.uniform(60, WINDOW_H - 50)
            size = random.choice([1, 1, 1, 1, 2, 2, 3])
            brightness = random.uniform(0.08, 0.35)
            cr = min(255, int(30 * (1 + brightness)))
            cg = min(255, int(30 * (1 + brightness)))
            cb = min(255, int(50 * (1 + brightness * 1.2)))

            self._stars.append({
                "x": sx,
                "y": sy,
                "size": size,
                "color": "#{:02x}{:02x}{:02x}".format(cr, cg, cb),
                "fade_phase": random.uniform(0, 2 * math.pi),
                "fade_speed": random.uniform(0.001, 0.004),
                "base_brightness": brightness,
                "drift_x": random.uniform(-0.04, 0.04),
                "drift_y": random.uniform(-0.08, -0.01),
            })

    def load_lyrics(self):
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
        pygame.mixer.init()
        if self.has_audio:
            pygame.mixer.music.load(self.audio_file)
            print(f"[Music] Audio ready: {os.path.basename(self.audio_file)}")
        else:
            print(f"[Info] No audio file found. Timer sync active.")
            print(f"[Tip] Place Stay.mp3 in this folder to enable audio playback.")

    def toggle_pause(self):
        if self.is_paused:
            if pygame.mixer.get_init() and pygame.mixer.music.get_busy():
                pygame.mixer.music.unpause()
            if self.pause_start_time:
                self.total_paused_duration += time.time() - self.pause_start_time
                self.pause_start_time = None
            self.is_paused = False
        else:
            if pygame.mixer.get_init() and pygame.mixer.music.get_busy():
                pygame.mixer.music.pause()
            self.pause_start_time = time.time()
            self.is_paused = True

    def get_current_music_time(self):
        if pygame.mixer.get_init():
            if pygame.mixer.music.get_busy() or (self.is_paused and self.has_audio):
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
        elapsed = self.current_time
        hue_progress = (elapsed / BG_CYCLE_SECONDS) % 1.0
        hue = BG_HUE_START + BG_HUE_RANGE * math.sin(hue_progress * math.pi)
        sat = 0.08
        light = 0.035

        for i, rect_id in enumerate(self.gradient_rects):
            layer_ratio = i / len(self.gradient_rects)
            l = light + layer_ratio * 0.02
            color = hsl_to_hex(hue, sat, l)
            self.main_canvas.itemconfig(rect_id, fill=color)

    def update_stars(self):
        for star_id, star in self.star_items:
            star["x"] += star["drift_x"]
            star["y"] += star["drift_y"]

            if star["x"] < 5:
                star["x"] = WINDOW_W - 5
            elif star["x"] > WINDOW_W - 5:
                star["x"] = 5
            if star["y"] < 5:
                star["y"] = WINDOW_H - 5
            elif star["y"] > WINDOW_H - 5:
                star["y"] = 5

            star["fade_phase"] += star["fade_speed"]
            alpha = 0.5 + 0.5 * math.sin(star["fade_phase"])
            brightness = star["base_brightness"] * alpha
            cr = min(255, int(30 * (1 + brightness * 4)))
            cg = min(255, int(30 * (1 + brightness * 4)))
            cb = min(255, int(50 * (1 + brightness * 4.5)))
            color = "#{:02x}{:02x}{:02x}".format(cr, cg, cb)
            self.main_canvas.itemconfig(star_id, fill=color)

    def update(self):
        if not self.is_running:
            return

        if not self.is_paused:
            self.current_time = self.get_current_music_time()

            self.update_background()
            self.update_stars()

            while self.next_index < len(self.lyrics_timeline):
                line = self.lyrics_timeline[self.next_index]
                if self.current_time >= line["time_sec"]:
                    if self.next_index != self.current_line_index:
                        self.current_line_index = self.next_index
                        self.typewriter_index = 0
                        self.typewriter_text = ""
                        self.current_mood = line["mood"]
                        self.accent_color = MOOD_ACCENTS.get(self.current_mood, self.accent_color)
                        self.main_canvas.itemconfig(self.current_label_id, fill=self.accent_color)
                        self.main_canvas.itemconfig(self.progress_bar_fill, fill=self.accent_color)
                    self.next_index += 1
                else:
                    break

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

                lyric_y = WINDOW_H // 2 - 20
                line_spacing = int(WINDOW_H * 0.065)

                prev_text = ""
                if self.current_line_index > 0:
                    prev_text = self.lyrics_timeline[self.current_line_index - 1]["eng"]
                self.main_canvas.coords(self.prev_label_id, WINDOW_W // 2, lyric_y - line_spacing)
                self.main_canvas.itemconfig(self.prev_label_id, text=prev_text)

                self.main_canvas.coords(self.current_label_id, WINDOW_W // 2, lyric_y)

                next_text = ""
                if self.current_line_index + 1 < len(self.lyrics_timeline):
                    next_text = self.lyrics_timeline[self.current_line_index + 1]["eng"]
                self.main_canvas.coords(self.next_label_id, WINDOW_W // 2, lyric_y + line_spacing)
                self.main_canvas.itemconfig(self.next_label_id, text=next_text)

                total = self.get_total_duration()
                progress = min(self.current_time / max(total, 1), 1.0)
                bar_x = progress * WINDOW_W
                bar_y = WINDOW_H - 3
                self.main_canvas.coords(self.progress_bar_fill, 0, bar_y, bar_x, WINDOW_H)

                current_str = self.format_time(self.current_time)
                total_str = self.format_time(total)
                self.main_canvas.itemconfig(self.time_text, text=f"{current_str} / {total_str}")

            if (self.next_index >= len(self.lyrics_timeline) and
                    self.current_line_index >= len(self.lyrics_timeline) - 1 and
                    (not pygame.mixer.get_init() or not pygame.mixer.music.get_busy())):
                self.quit()
                return

        self.root.after(FRAME_DELAY_MS, self.update)

    def quit(self):
        self.is_running = False
        try:
            if pygame.mixer.get_init():
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
        print("=" * 60)
        print("  🎵 STAY - SINGLE SCREEN LYRIC PLAYER")
        print("  [ESC] Exit  |  [Space] Pause")
        print("=" * 60)
        if self.has_audio:
            pygame.mixer.music.play()
        self.root.mainloop()


if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    audio = os.path.join(current_dir, "Stay.mp3")
    lyrics = os.path.join(current_dir, "lyrics.txt")

    app = StarFieldApp(audio_file=audio, lyrics_file=lyrics)
    app.start()
