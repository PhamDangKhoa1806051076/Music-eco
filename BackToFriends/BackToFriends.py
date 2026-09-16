import os
import sys
import time
import math
import random
import tkinter as tk
import pygame

# Đảm bảo console Windows hỗ trợ UTF-8 chuẩn xác
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# ==============================================================================
# CẤU HÌNH GIAO DIỆN & BẢNG MÀU CẢM XÚC (EMOTIONAL PALETTES - SOMBR)
# ==============================================================================
BOX_W = 340           # Chiều rộng thẻ ghi chú (pixels)
BOX_H = 210           # Chiều cao thẻ ghi chú (pixels)
RISE_SPEED = 0.88     # Tốc độ trôi bồng bềnh lên trên (pixels / frame)
FRAME_DELAY_MS = 25   # Chu kỳ làm mới animation (~40 FPS)

# Bảng màu đại diện cho từng cung bậc cảm xúc trong bài hát "back to friends"
EMOTION_THEMES = {
    "tender": {
        "badge": "🌧️ TENDER MEMORY",
        "badge_bg": "#1E293B",
        "badge_fg": "#38BDF8",
        "bg": "#0B132B",
        "fg": "#E0E7FF",
        "border": "#38BDF8",
        "accent": "#0284C7",
        "sub_fg": "#94A3B8",
        "icon": "🌧️",
        "sway_amp": 12.0,
        "sway_speed": 1.7
    },
    "ache": {
        "badge": "💔 HEARTBROKEN",
        "badge_bg": "#2E1065",
        "badge_fg": "#C084FC",
        "bg": "#140C24",
        "fg": "#FAF5FF",
        "border": "#A855F7",
        "accent": "#9333EA",
        "sub_fg": "#D8B4FE",
        "icon": "💔",
        "sway_amp": 16.0,
        "sway_speed": 2.2
    },
    "memory": {
        "badge": "❄️ LAST DECEMBER",
        "badge_bg": "#1E3A5F",
        "badge_fg": "#7DD3FC",
        "bg": "#0B192C",
        "fg": "#F0F9FF",
        "border": "#0284C7",
        "accent": "#38BDF8",
        "sub_fg": "#93C5FD",
        "icon": "❄️",
        "sway_amp": 14.0,
        "sway_speed": 1.9
    },
    "betrayal": {
        "badge": "🥀 DEVIL IN YOUR EYES",
        "badge_bg": "#4C0519",
        "badge_fg": "#FB7185",
        "bg": "#1B0B11",
        "fg": "#FFF1F2",
        "border": "#E11D48",
        "accent": "#F43F5E",
        "sub_fg": "#FDA4AF",
        "icon": "🥀",
        "sway_amp": 18.0,
        "sway_speed": 2.5
    },
    "explosive": {
        "badge": "⚡ SHATTERED SOUL",
        "badge_bg": "#581C87",
        "badge_fg": "#F472B6",
        "bg": "#150624",
        "fg": "#FFFFFF",
        "border": "#F43F5E",
        "accent": "#EC4899",
        "sub_fg": "#F9A8D4",
        "icon": "⚡",
        "sway_amp": 22.0,
        "sway_speed": 3.0
    },
    "faded": {
        "badge": "🌫️ FORGOTTEN STRANGER",
        "badge_bg": "#27272A",
        "badge_fg": "#A1A1AA",
        "bg": "#121215",
        "fg": "#E4E4E7",
        "border": "#52525B",
        "accent": "#71717A",
        "sub_fg": "#71717A",
        "icon": "🌫️",
        "sway_amp": 10.0,
        "sway_speed": 1.4
    }
}

FONT_HEADING = "Segoe UI"
FONT_LYRIC = "Segoe UI"
FONT_SUBTITLE = "Segoe UI"


class DynamicLyricCard:
    """
    Thẻ lời bài hát nổi nghệ thuật với giao diện đậm chất Indie / Alt-Rock:
    - Hiệu ứng máy đánh chữ nhấp nháy con trỏ neon.
    - Hiển thị song ngữ (Lời gốc tiếng Anh & Vietsub cảm xúc đồng bộ).
    - Bộ giả lập Equalizer Soundwave nhảy múa theo nhịp ở góc thẻ.
    - Chuyển động lượn sóng đa tần số (Multi-harmonic Sway) mô phỏng chiếc lá trôi trong làn gió đêm.
    - Cho phép kéo thả chuột thoải mái và phím chuột phải để đóng thẻ.
    """
    def __init__(self, master, lyric_data, x, y, on_close=None):
        self.master = master
        self.lyric_data = lyric_data
        self.eng_text = lyric_data["eng"]
        self.vie_text = lyric_data["vie"]
        self.speed_ms = lyric_data.get("speed_ms", 55)
        self.mood_key = lyric_data.get("mood", "tender")
        self.theme = EMOTION_THEMES.get(self.mood_key, EMOTION_THEMES["tender"])
        self.on_close = on_close

        # Tọa độ cơ sở và hiệu ứng lượn sóng hình sin kép
        self.base_x = float(x)
        self.y = float(y)
        self.phase1 = random.uniform(0, math.pi * 2)
        self.phase2 = random.uniform(0, math.pi * 2)
        self.amp1 = self.theme["sway_amp"]
        self.amp2 = self.amp1 * 0.4
        self.speed1 = self.theme["sway_speed"]
        self.speed2 = self.speed1 * 1.6
        self.created_time = time.time()

        # Tạo cửa sổ cấp cao Toplevel không viền, luôn nổi trên cùng màn hình
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

        # 1. Thanh phát sáng ở đỉnh thẻ (Top Neon Strip)
        self.top_strip = tk.Frame(self.inner_frame, bg=self.theme["accent"], height=3)
        self.top_strip.pack(fill="x", side="top", pady=(0, 6))

        # 2. Header: Badge cảm xúc + Animated Equalizer Canvas + Icon
        self.header_frame = tk.Frame(self.inner_frame, bg=self.theme["bg"])
        self.header_frame.pack(fill="x", side="top")

        # Badge cảm xúc
        self.mood_badge = tk.Label(
            self.header_frame,
            text=f" {self.theme['badge']} ",
            font=(FONT_HEADING, 8, "bold"),
            bg=self.theme["badge_bg"],
            fg=self.theme["badge_fg"],
            padx=5,
            pady=2
        )
        self.mood_badge.pack(side="left")

        # Canvas vẽ thanh Equalizer nhảy nhót mini
        self.eq_canvas = tk.Canvas(
            self.header_frame,
            width=42,
            height=16,
            bg=self.theme["bg"],
            highlightthickness=0
        )
        self.eq_canvas.pack(side="right", padx=(4, 0))
        self.eq_bars = []
        for i in range(5):
            bx = i * 8 + 3
            bar_id = self.eq_canvas.create_rectangle(
                bx, 14, bx + 5, 14,
                fill=self.theme["accent"],
                outline=""
            )
            self.eq_bars.append(bar_id)

        # Icon cảm xúc
        self.icon_label = tk.Label(
            self.header_frame,
            text=self.theme["icon"],
            font=(FONT_HEADING, 10),
            bg=self.theme["bg"],
            fg=self.theme["accent"]
        )
        self.icon_label.pack(side="right", padx=(0, 4))

        # 3. Nội dung lời bài hát chính (Tiếng Anh)
        self.eng_label = tk.Label(
            self.inner_frame,
            text="",
            wraplength=BOX_W - 32,
            justify="center",
            font=(FONT_LYRIC, 11, "bold"),
            fg=self.theme["fg"],
            bg=self.theme["bg"]
        )
        self.eng_label.pack(expand=True, fill="both", pady=(6, 2))

        # 4. Vietsub cảm xúc tinh tế bên dưới
        self.vie_label = tk.Label(
            self.inner_frame,
            text="",
            wraplength=BOX_W - 32,
            justify="center",
            font=(FONT_SUBTITLE, 9, "italic"),
            fg=self.theme["sub_fg"],
            bg=self.theme["bg"]
        )
        self.vie_label.pack(fill="x", side="bottom", pady=(0, 4))

        # 5. Footer: Dấu ấn bài hát & thời gian
        self.footer_frame = tk.Frame(self.inner_frame, bg=self.theme["bg"])
        self.footer_frame.pack(fill="x", side="bottom")

        time_str = f"[{int(lyric_data['time_sec'] // 60):02d}:{int(lyric_data['time_sec'] % 60):02d}]"
        self.footer_text = tk.Label(
            self.footer_frame,
            text=f"sombr • back to friends  {time_str}",
            font=(FONT_HEADING, 7),
            fg=self.theme["sub_fg"],
            bg=self.theme["bg"]
        )
        self.footer_text.pack(side="left")

        # Hỗ trợ kéo thả bằng chuột mượt mà
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.is_dragging = False

        interactive_widgets = [
            self.win, self.inner_frame, self.top_strip, self.header_frame,
            self.mood_badge, self.eq_canvas, self.icon_label, self.eng_label,
            self.vie_label, self.footer_frame, self.footer_text
        ]
        for widget in interactive_widgets:
            widget.bind("<ButtonPress-1>", self.start_drag)
            widget.bind("<B1-Motion>", self.do_drag)
            widget.bind("<ButtonRelease-1>", self.stop_drag)
            widget.bind("<Button-3>", lambda e: self.destroy())

        # Bắt đầu hiệu ứng gõ chữ và equalizer
        self.typewriter_index = 0
        self.is_alive = True
        self.animate_eq()
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

    def animate_eq(self):
        """Vẽ hoạt ảnh các cột sóng âm nhảy ngẫu nhiên sống động."""
        if not self.is_alive:
            return
        for i, bar in enumerate(self.eq_bars):
            # Càng ở đoạn cao trào (explosive/betrayal), sóng nhảy càng cao
            max_h = 14 if self.mood_key in ("explosive", "betrayal") else 10
            h = random.randint(2, max_h)
            bx = i * 8 + 3
            self.eq_canvas.coords(bar, bx, 15 - h, bx + 5, 15)
        self.win.after(90, self.animate_eq)

    def typewriter(self):
        """Gõ từng ký tự tiếng Anh kèm con trỏ nhấp nháy, sau đó hiện Vietsub."""
        if not self.is_alive:
            return
        if self.typewriter_index <= len(self.eng_text):
            cursor = " ▌" if self.typewriter_index < len(self.eng_text) else ""
            self.eng_label.config(text=self.eng_text[:self.typewriter_index] + cursor)
            self.typewriter_index += 1
            self.win.after(self.speed_ms, self.typewriter)
        else:
            self.eng_label.config(text=self.eng_text)
            if self.vie_text:
                self.vie_label.config(text=f"~ {self.vie_text}")

    def rise(self, dy):
        """Bay dần lên kết hợp hiệu ứng lượn sóng đa tần số (Dual-harmonic Sway)."""
        if not self.is_alive:
            return
        self.y -= dy

        if not self.is_dragging:
            elapsed = time.time() - self.created_time
            sway = (math.sin(elapsed * self.speed1 + self.phase1) * self.amp1 +
                    math.cos(elapsed * self.speed2 + self.phase2) * self.amp2)
            current_x = self.base_x + sway
        else:
            current_x = self.base_x

        self.win.geometry(f"{BOX_W}x{BOX_H}+{int(current_x)}+{int(self.y)}")

    def is_offscreen(self):
        """Kiểm tra thẻ đã trôi hết qua cạnh trên màn hình chưa."""
        return self.y + BOX_H < -40

    def destroy(self):
        """Đóng thẻ và giải phóng bộ nhớ."""
        if self.is_alive:
            self.is_alive = False
            try:
                self.win.destroy()
            except Exception:
                pass
            if self.on_close:
                self.on_close(self)


class SombrLyricApp:
    """
    Ứng dụng chính phát nhạc & điều phối thẻ lời bài hát nổi "back to friends - sombr".
    """
    def __init__(self, audio_file="BackToFriends.mp3", lyrics_file="lyrics.txt"):
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
        self.is_paused = False
        self.volume = 0.85

        # 1. Tải danh sách lời bài hát
        self.load_lyrics()

        # 2. Khởi tạo âm thanh
        self.init_audio()

        # 3. Đăng ký phím tắt điều khiển
        self.root.bind_all("<Escape>", lambda e: self.quit())
        self.root.bind_all("q", lambda e: self.quit())
        self.root.bind_all("Q", lambda e: self.quit())
        self.root.bind_all("<space>", lambda e: self.toggle_pause())
        self.root.bind_all("<Up>", lambda e: self.change_volume(0.05))
        self.root.bind_all("<Down>", lambda e: self.change_volume(-0.05))

        self.start_wall_time = None
        self.pause_start_time = None
        self.total_paused_duration = 0.0
        self.is_running = True

    def init_audio(self):
        """Khởi động pygame mixer và thiết lập âm lượng."""
        pygame.mixer.init()
        if os.path.exists(self.audio_file):
            pygame.mixer.music.load(self.audio_file)
            pygame.mixer.music.set_volume(self.volume)
            print(f"[Music] Audio ready: {os.path.basename(self.audio_file)} (Volume: {int(self.volume*100)}%)")
        else:
            print(f"[Warning] Audio file '{self.audio_file}' not found. Timer fallback active.")

    def load_lyrics(self):
        """
        Đọc file lyrics.txt với định dạng:
        [thời_gian|tốc_độ_gõ|cảm_xúc] Lời tiếng Anh // Vietsub cảm xúc
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
                        speed_ms = int(parts[1].strip()) if len(parts) > 1 else 55
                        mood = parts[2].strip() if len(parts) > 2 else "tender"

                        # Tách lời tiếng Anh và Vietsub
                        if " // " in text:
                            eng, vie = text.split(" // ", 1)
                        else:
                            eng, vie = text, ""

                        self.lyrics_timeline.append({
                            "time_sec": time_sec,
                            "speed_ms": speed_ms,
                            "mood": mood,
                            "eng": eng.strip(),
                            "vie": vie.strip()
                        })
                    except ValueError:
                        continue

        self.lyrics_timeline.sort(key=lambda item: item["time_sec"])
        print(f"[Lyrics] Successfully loaded {len(self.lyrics_timeline)} synchronized lyric lines.")

    def random_safe_x(self):
        """Phân bổ vị trí ngang để tránh các thẻ ghi chú chồng chéo nhau."""
        margin = 60
        usable_width = self.screen_w - BOX_W - (margin * 2)
        num_slots = 3
        slot_width = usable_width / num_slots

        available_slots = [s for s in range(num_slots) if s != self.last_x_slot]
        chosen_slot = random.choice(available_slots)
        self.last_x_slot = chosen_slot

        slot_start = margin + int(chosen_slot * slot_width)
        slot_end = int(slot_start + slot_width - 25)
        return random.randint(slot_start, max(slot_start + 10, slot_end))

    def spawn_card(self, lyric_data):
        """Tạo thẻ ghi chú mới xuất hiện từ đáy màn hình."""
        spawn_x = self.random_safe_x()
        spawn_y = self.screen_h - BOX_H - random.randint(40, 80)

        card = DynamicLyricCard(
            master=self.root,
            lyric_data=lyric_data,
            x=spawn_x,
            y=spawn_y,
            on_close=lambda c: self.cards.remove(c) if c in self.cards else None
        )
        self.cards.append(card)

        # In thông tin câu hát ra terminal
        t = lyric_data["time_sec"]
        mood_badge = EMOTION_THEMES.get(lyric_data["mood"], {}).get("badge", lyric_data["mood"])
        print(f"[{t:5.1f}s] [{mood_badge[:18]:18s}] \"{lyric_data['eng']}\"")
        if lyric_data["vie"]:
            print(f"       {' '*18}  ↳ {lyric_data['vie']}")

    def get_current_music_time(self):
        """Lấy mốc thời gian phát bài hát chính xác từ pygame mixer."""
        if pygame.mixer.music.get_busy() or self.is_paused:
            pos_ms = pygame.mixer.music.get_pos()
            if pos_ms >= 0:
                return pos_ms / 1000.0
        if self.start_wall_time:
            elapsed = time.time() - self.start_wall_time - self.total_paused_duration
            return max(0.0, elapsed)
        return 0.0

    def toggle_pause(self):
        """Tạm dừng hoặc tiếp tục phát nhạc và hoạt ảnh."""
        if self.is_paused:
            pygame.mixer.music.unpause()
            if self.pause_start_time:
                self.total_paused_duration += time.time() - self.pause_start_time
                self.pause_start_time = None
            self.is_paused = False
            print("[Player] ▶ Resumed playback")
        else:
            pygame.mixer.music.pause()
            self.pause_start_time = time.time()
            self.is_paused = True
            print("[Player] ⏸ Paused playback (Press [Space] to resume)")

    def change_volume(self, delta):
        """Tăng hoặc giảm âm lượng bài hát."""
        self.volume = max(0.0, min(1.0, self.volume + delta))
        pygame.mixer.music.set_volume(self.volume)
        print(f"[Volume] {int(self.volume * 100)}%")

    def update(self):
        """Vòng lặp animation: kích hoạt câu hát mới và cập nhật chuyển động bay lên."""
        if not self.is_running:
            return

        if not self.is_paused:
            current_time = self.get_current_music_time()

            # 1. Sinh thẻ mới khi bài hát chạm mốc thời gian
            while self.next_index < len(self.lyrics_timeline):
                next_lyric = self.lyrics_timeline[self.next_index]
                if current_time >= next_lyric["time_sec"]:
                    self.spawn_card(next_lyric)
                    self.next_index += 1
                else:
                    break

            # 2. Cho các thẻ trôi dần lên trên
            for card in list(self.cards):
                card.rise(RISE_SPEED)
                if card.is_offscreen():
                    card.destroy()

            # 3. Tự động kết thúc khi hết bài hát và thẻ đã trôi hết
            if self.next_index >= len(self.lyrics_timeline) and not self.cards:
                if not pygame.mixer.music.get_busy():
                    print("\n[App] Song completed. All emotion cards finished. Exiting gracefully.")
                    self.quit()
                    return

        self.root.after(FRAME_DELAY_MS, self.update)

    def print_banner(self):
        """In giao diện chào đón nghệ thuật phong cách Indie Rock."""
        banner = """
========================================================================
   🎵  S O M B R  -  B A C K   T O   F R I E N D S  🎵
========================================================================
  🌌 Trải nghiệm giao diện lời bài hát nổi theo cảm xúc (Mood-Adaptive):
  - 🌧️ TENDER MEMORY: Ngập ngừng, yếu lòng trong đêm tối
  - 💔 HEARTBROKEN: Câu hỏi dằn vặt "How can we go back to being friends?"
  - ❄️ LAST DECEMBER: Ký ức mùa đông buốt giá
  - 🥀 DEVIL IN YOUR EYES: Phản bội & sự thật cay đắng
  - ⚡ SHATTERED SOUL: Bùng nổ Climax Rock dữ dội
  - 🌫️ FORGOTTEN STRANGER: Lặng lẽ tan biến vào hư vô

  ⌨️ Phím tắt điều khiển:
  - [Space]     : Tạm dừng / Tiếp tục phát
  - [↑ / ↓]     : Tăng / Giảm âm lượng
  - [Chuột trái]: Kéo thả thẻ tùy ý trên màn hình
  - [Chuột phải]: Đóng nhanh từng thẻ ghi chú
  - [Esc / Q]   : Dừng và thoát chương trình
========================================================================
"""
        print(banner)

    def start(self):
        """Bắt đầu phát nhạc và chạy vòng lặp giao diện Tkinter."""
        self.print_banner()

        if os.path.exists(self.audio_file):
            pygame.mixer.music.play()
        self.start_wall_time = time.time()

        self.update()
        self.root.mainloop()

    def quit(self):
        """Dừng âm thanh và dọn dẹp ứng dụng."""
        self.is_running = False
        try:
            pygame.mixer.music.stop()
            pygame.mixer.quit()
        except Exception:
            pass

        for card in list(self.cards):
            card.destroy()

        try:
            self.root.quit()
            self.root.destroy()
        except Exception:
            pass
        sys.exit(0)


if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    audio_path = os.path.join(current_dir, "BackToFriends.mp3")
    lyrics_path = os.path.join(current_dir, "lyrics.txt")

    app = SombrLyricApp(audio_file=audio_path, lyrics_file=lyrics_path)
    app.start()
