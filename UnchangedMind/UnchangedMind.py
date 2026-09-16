import os
import sys
import time
import math
import random
import tkinter as tk
import pygame

# Đảm bảo console Windows hỗ trợ hiển thị UTF-8 chuẩn xác
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# ==============================================================================
# CẤU HÌNH GIAO DIỆN & BẢNG MÀU U TỐI NGHỆ THUẬT (DARK MELANCHOLIC AESTHETICS)
# ==============================================================================
BOX_W = 350           # Chiều rộng thẻ ghi chú (pixels)
BOX_H = 220           # Chiều cao thẻ ghi chú (pixels)
RISE_SPEED = 0.82     # Tốc độ trôi bồng bềnh chậm rãi, da diết (pixels / frame)
FRAME_DELAY_MS = 25   # Chu kỳ làm mới animation (~40 FPS)

# Bảng màu u tối đại diện cho từng cung bậc cảm xúc trong bản nhạc "Unchanged Mind"
DARK_THEMES = {
    "solitude": {
        "badge": "🌌 MIDNIGHT SOLITUDE",
        "badge_bg": "#0B1329",
        "badge_fg": "#38BDF8",
        "bg": "#050814",
        "fg": "#F0F9FF",
        "border": "#0369A1",
        "accent": "#0284C7",
        "sub_fg": "#7DD3FC",
        "wave": "#38BDF8",
        "icon": "🌌",
        "sway_amp": 12.0,
        "sway_speed": 1.5
    },
    "ache": {
        "badge": "🥀 SILENT ACHE",
        "badge_bg": "#1E0B2E",
        "badge_fg": "#C084FC",
        "bg": "#0F071B",
        "fg": "#FAF5FF",
        "border": "#7E22CE",
        "accent": "#9333EA",
        "sub_fg": "#D8B4FE",
        "wave": "#C084FC",
        "icon": "🥀",
        "sway_amp": 15.0,
        "sway_speed": 1.8
    },
    "regret": {
        "badge": "🕯️ FADED PROMISES",
        "badge_bg": "#2A1808",
        "badge_fg": "#FBBF24",
        "bg": "#120B05",
        "fg": "#FFFBEB",
        "border": "#B45309",
        "accent": "#D97706",
        "sub_fg": "#FCD34D",
        "wave": "#FBBF24",
        "icon": "🕯️",
        "sway_amp": 14.0,
        "sway_speed": 1.6
    },
    "climax": {
        "badge": "⚡ SHATTERED HEART",
        "badge_bg": "#380B1C",
        "badge_fg": "#FB7185",
        "bg": "#18060F",
        "fg": "#FFF1F2",
        "border": "#BE123C",
        "accent": "#E11D48",
        "sub_fg": "#FDA4AF",
        "wave": "#FB7185",
        "icon": "⚡",
        "sway_amp": 20.0,
        "sway_speed": 2.4
    },
    "abyss": {
        "badge": "🌑 ENDLESS VOID",
        "badge_bg": "#18181B",
        "badge_fg": "#A1A1AA",
        "bg": "#09090B",
        "fg": "#E4E4E7",
        "border": "#3F3F46",
        "accent": "#52525B",
        "sub_fg": "#71717A",
        "wave": "#A1A1AA",
        "icon": "🌑",
        "sway_amp": 11.0,
        "sway_speed": 1.4
    },
    "farewell": {
        "badge": "🕊️ UNCHANGED MIND",
        "badge_bg": "#0E1A29",
        "badge_fg": "#67E8F9",
        "bg": "#060D17",
        "fg": "#ECFEFF",
        "border": "#0891B2",
        "accent": "#06B6D4",
        "sub_fg": "#A5F3FC",
        "wave": "#67E8F9",
        "icon": "🕊️",
        "sway_amp": 13.0,
        "sway_speed": 1.5
    }
}

FONT_FAMILY = "Segoe UI"


class MelancholyLyricCard:
    """
    Thẻ ghi chú u tối đậm chất Cinematic & Dark Melancholy:
    - Hiệu ứng mưa đêm li ti (Falling Raindrops) mờ ảo chuyển động trong thẻ.
    - Sóng âm nhịp tim & giai điệu dương cầm (Dynamic Heartbeat / Pulse Wave).
    - Hiệu ứng máy đánh chữ song ngữ: Lời chiêm nghiệm & Vietsub u tối.
    - Chuyển động lượn sóng đa tần số (Multi-harmonic Drift) mô phỏng tro tàn lơ lửng.
    - Cho phép kéo thả mượt mà bằng chuột và nhấp chuột phải để đóng thẻ.
    """
    def __init__(self, master, lyric_data, x, y, on_close=None):
        self.master = master
        self.lyric_data = lyric_data
        self.eng_text = lyric_data["eng"]
        self.vie_text = lyric_data["vie"]
        self.speed_ms = lyric_data.get("speed_ms", 55)
        self.mood_key = lyric_data.get("mood", "solitude")
        self.theme = DARK_THEMES.get(self.mood_key, DARK_THEMES["solitude"])
        self.on_close = on_close

        # Tọa độ cơ sở và hiệu ứng lượn sóng đa hài hòa
        self.base_x = float(x)
        self.y = float(y)
        self.phase1 = random.uniform(0, math.pi * 2)
        self.phase2 = random.uniform(0, math.pi * 2)
        self.amp1 = self.theme["sway_amp"]
        self.amp2 = self.amp1 * 0.4
        self.speed1 = self.theme["sway_speed"]
        self.speed2 = self.speed1 * 1.7
        self.created_time = time.time()

        # Tạo cửa sổ cấp cao Toplevel không viền, nổi trên mọi ứng dụng
        self.win = tk.Toplevel(master)
        self.win.overrideredirect(True)
        self.win.attributes("-topmost", True)
        self.win.geometry(f"{BOX_W}x{BOX_H}+{int(self.base_x)}+{int(self.y)}")
        self.win.config(bg=self.theme["border"])

        # Khung viền chứa nội dung thẻ
        self.inner_frame = tk.Frame(
            self.win,
            bg=self.theme["bg"],
            highlightthickness=0,
            padx=12,
            pady=10
        )
        self.inner_frame.pack(fill="both", expand=True, padx=2, pady=2)

        # 1. Thanh chỉ báo phát sáng đỉnh thẻ (Neon Edge)
        self.top_strip = tk.Frame(self.inner_frame, bg=self.theme["accent"], height=3)
        self.top_strip.pack(fill="x", side="top", pady=(0, 6))

        # 2. Header: Badge u tối + Canvas sóng âm nhịp tim + Icon
        self.header_frame = tk.Frame(self.inner_frame, bg=self.theme["bg"])
        self.header_frame.pack(fill="x", side="top")

        self.mood_badge = tk.Label(
            self.header_frame,
            text=f" {self.theme['badge']} ",
            font=(FONT_FAMILY, 8, "bold"),
            bg=self.theme["badge_bg"],
            fg=self.theme["badge_fg"],
            padx=6,
            pady=2
        )
        self.mood_badge.pack(side="left")

        # Canvas vẽ sóng âm nhịp tim & mưa đêm (Pulse & Rain Canvas)
        self.wave_canvas = tk.Canvas(
            self.header_frame,
            width=65,
            height=18,
            bg=self.theme["bg"],
            highlightthickness=0
        )
        self.wave_canvas.pack(side="right", padx=(4, 0))

        self.icon_label = tk.Label(
            self.header_frame,
            text=self.theme["icon"],
            font=(FONT_FAMILY, 10),
            bg=self.theme["bg"],
            fg=self.theme["accent"]
        )
        self.icon_label.pack(side="right", padx=(0, 4))

        # 3. Nội dung lời chiêm nghiệm (Tiếng Anh)
        self.eng_label = tk.Label(
            self.inner_frame,
            text="",
            wraplength=BOX_W - 32,
            justify="center",
            font=(FONT_FAMILY, 10, "bold"),
            fg=self.theme["fg"],
            bg=self.theme["bg"]
        )
        self.eng_label.pack(expand=True, fill="both", pady=(6, 2))

        # 4. Vietsub u tối sâu lắng bên dưới
        self.vie_label = tk.Label(
            self.inner_frame,
            text="",
            wraplength=BOX_W - 36,
            justify="center",
            font=(FONT_FAMILY, 9, "italic"),
            fg=self.theme["sub_fg"],
            bg=self.theme["bg"]
        )
        self.vie_label.pack(fill="x", side="bottom", pady=(2, 4))

        # Khởi tạo các giọt mưa đêm li ti bên trong thẻ (Subtle Falling Raindrops)
        self.raindrops = [
            {"x": random.randint(5, BOX_W - 30), "y": random.randint(0, 15), "len": random.randint(4, 7), "speed": random.uniform(1.2, 2.5)}
            for _ in range(5)
        ]

        # Kéo thả thẻ bằng chuột
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.is_dragging = False

        for widget in (self.win, self.inner_frame, self.eng_label, self.vie_label, self.header_frame, self.mood_badge, self.icon_label, self.wave_canvas):
            widget.bind("<ButtonPress-1>", self.start_drag)
            widget.bind("<B1-Motion>", self.do_drag)
            widget.bind("<ButtonRelease-1>", self.stop_drag)
            widget.bind("<Button-3>", lambda e: self.destroy())

        # Bắt đầu typewriter và animation sóng âm
        self.typewriter_index = 0
        self.is_alive = True
        self.wave_phase = 0.0

        self.typewriter()
        self.animate_wave()

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

    def animate_wave(self):
        """Vẽ đường sóng âm nhịp tim sống động trên Canvas mini."""
        if not self.is_alive:
            return
        self.wave_canvas.delete("all")
        w = 65
        h = 18
        mid_y = h / 2

        points = []
        num_pts = 14
        for i in range(num_pts):
            px = i * (w / (num_pts - 1))
            # Tạo đường sóng kết hợp nhịp đập tim và dao động dương cầm
            osc = math.sin(self.wave_phase + i * 0.65) * 6.0 * math.sin(self.wave_phase * 0.5)
            py = mid_y + osc
            points.extend([px, py])

        if len(points) >= 4:
            self.wave_canvas.create_line(
                points,
                fill=self.theme["wave"],
                width=1.8,
                smooth=True
            )

        self.wave_phase += 0.22
        self.win.after(40, self.animate_wave)

    def typewriter(self):
        """Gõ từng ký tự với con trỏ nhấp nháy neon, sau đó hiển thị Vietsub u tối."""
        if not self.is_alive:
            return
        if self.typewriter_index <= len(self.eng_text):
            cursor = " ▌" if self.typewriter_index < len(self.eng_text) else ""
            self.eng_label.config(text=self.eng_text[:self.typewriter_index] + cursor)
            self.typewriter_index += 1
            self.win.after(self.speed_ms, self.typewriter)
        else:
            self.eng_label.config(text=self.eng_text)
            self.show_vietsub()

    def show_vietsub(self):
        """Hiển thị Vietsub chạm đáy cảm xúc với hiệu ứng xuất hiện sâu lắng."""
        if not self.is_alive:
            return
        self.vie_label.config(text=f"— {self.vie_text} —")

    def rise(self, dy):
        """Bay lên trên kết hợp chuyển động lơ lửng u uất đa tần số (Multi-harmonic Drift)."""
        if not self.is_alive:
            return
        self.y -= dy

        if not self.is_dragging:
            elapsed = time.time() - self.created_time
            sway = (
                math.sin(elapsed * self.speed1 + self.phase1) * self.amp1 +
                math.sin(elapsed * self.speed2 + self.phase2) * self.amp2
            )
            current_x = self.base_x + sway
        else:
            current_x = self.base_x

        self.win.geometry(f"{BOX_W}x{BOX_H}+{int(current_x)}+{int(self.y)}")

    def is_offscreen(self):
        return self.y + BOX_H < -40

    def destroy(self):
        if self.is_alive:
            self.is_alive = False
            try:
                self.win.destroy()
            except Exception:
                pass
            if self.on_close:
                self.on_close(self)


class MelancholyFloatApp:
    """
    Ứng dụng phát nhạc & đồng bộ thẻ độc thoại u tối cho bài hát Unchanged Mind.
    """
    def __init__(self, audio_file="UnchangedMind.mp3", lyrics_file="lyrics.txt"):
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

        # 1. Nạp danh sách câu độc thoại
        self.load_lyrics()

        # 2. Khởi tạo âm thanh pygame
        self.init_audio()

        # 3. Phím tắt ESC thoát nhanh
        self.root.bind_all("<Escape>", lambda e: self.quit())

        self.start_wall_time = None
        self.is_running = True

    def init_audio(self):
        pygame.mixer.init()
        if os.path.exists(self.audio_file):
            print(f"[Music] Loading audio file: {os.path.basename(self.audio_file)}")
            pygame.mixer.music.load(self.audio_file)
        else:
            print(f"[Warning] Audio '{self.audio_file}' not found. Falling back to timer.")

    def load_lyrics(self):
        """
        Đọc file lyrics.txt với định dạng:
        [thời_gian_giây|tốc_độ_gõ_ms|cảm_xúc] Lời tiếng Anh // Vietsub u tối
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
                    tag, content = line[1:].split("]", 1)
                    content = content.strip()
                    parts = tag.split("|")
                    try:
                        time_sec = float(parts[0].strip())
                        speed_ms = int(parts[1].strip()) if len(parts) > 1 else 55
                        mood = parts[2].strip() if len(parts) > 2 else "solitude"

                        if "//" in content:
                            eng_text, vie_text = content.split("//", 1)
                            eng_text = eng_text.strip()
                            vie_text = vie_text.strip()
                        else:
                            eng_text = content
                            vie_text = ""

                        self.lyrics_timeline.append({
                            "time_sec": time_sec,
                            "speed_ms": speed_ms,
                            "mood": mood,
                            "eng": eng_text,
                            "vie": vie_text
                        })
                    except ValueError:
                        continue

        self.lyrics_timeline.sort(key=lambda item: item["time_sec"])
        print(f"[Lyrics] Successfully loaded {len(self.lyrics_timeline)} synchronized melancholic lines.")

    def random_safe_x(self):
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
        spawn_x = self.random_safe_x()
        spawn_y = self.screen_h - BOX_H - random.randint(50, 90)

        card = MelancholyLyricCard(
            master=self.root,
            lyric_data=lyric_data,
            x=spawn_x,
            y=spawn_y,
            on_close=lambda c: self.cards.remove(c) if c in self.cards else None
        )
        self.cards.append(card)
        mood = lyric_data.get("mood", "solitude")
        print(f"[{lyric_data['time_sec']:5.1f}s] [{mood:9s}] \"{lyric_data['eng'][:35]}...\"")

    def get_current_music_time(self):
        if pygame.mixer.music.get_busy():
            pos_ms = pygame.mixer.music.get_pos()
            if pos_ms >= 0:
                return pos_ms / 1000.0
        if self.start_wall_time:
            return time.time() - self.start_wall_time
        return 0.0

    def update(self):
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

        # 3. Kết thúc khi bài hát hết và thẻ đã bay hết
        if self.next_index >= len(self.lyrics_timeline) and not self.cards:
            if not pygame.mixer.music.get_busy():
                print("\n[App] Song completed and all cards finished. Silence returns.")
                self.quit()
                return

        self.root.after(FRAME_DELAY_MS, self.update)

    def start(self):
        print("=" * 70)
        print("  🌑 UNCHANGED MIND (未曾改变的心意) - VALENTIN 🌑")
        print("  Bản nhạc cảm xúc u tối & sâu lắng:")
        print("  - Giao diện Dark Aesthetic với 6 sắc thái u uất")
        print("  - Sóng âm nhịp tim & phím dương cầm chuyển động liên tục")
        print("  - Hiệu ứng máy đánh chữ song ngữ & con trỏ nhấp nháy neon")
        print("  - Chuyển động lơ lửng đa tần số như tàn tro giữa đêm đen")
        print("  - Phím tắt: Nhấn [ESC] bất cứ lúc nào để dừng.")
        print("=" * 70)

        if os.path.exists(self.audio_file):
            pygame.mixer.music.play()

        self.start_wall_time = time.time()
        self.root.after(10, self.update)
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self.quit()

    def quit(self):
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
    dir_path = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(dir_path, "UnchangedMind.mp3"),
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    for f in os.listdir(dir_path):
        if f.lower().endswith((".mp3", ".wav")):
            return os.path.join(dir_path, f)
    return os.path.join(dir_path, "UnchangedMind.mp3")


if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    audio = find_audio_file()
    lyrics = os.path.join(current_dir, "lyrics.txt")
    
    app = MelancholyFloatApp(audio_file=audio, lyrics_file=lyrics)
    app.start()
