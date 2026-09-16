import os
import sys
import time
import math
import random
import tkinter as tk
import pygame

# Đảm bảo console Windows hỗ trợ UTF-8 trơn tru
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# ==============================================================================
# CẤU HÌNH GIAO DIỆN & BẢNG MÀU HOÀNG HÔN SUNSET (OLLY MURS - THAT GIRL)
# ==============================================================================
BOX_W = 345           # Chiều rộng thẻ lời bài hát (pixels)
BOX_H = 215           # Chiều cao thẻ (pixels)
RISE_SPEED = 0.86     # Tốc độ lơ lửng bay lên (pixels / frame)
FRAME_DELAY_MS = 25   # Chu kỳ làm mới animation (~40 FPS)

# Bảng màu nghệ thuật phong cách Golden Hour & Polaroid hoài niệm
SUNSET_THEMES = {
    "regret": {
        "badge": "🌇 BITTERSWEET REGRET",
        "badge_bg": "#3B1E10",
        "badge_fg": "#FBBF24",
        "bg": "#1C100B",
        "fg": "#FEF3C7",
        "border": "#F59E0B",
        "accent": "#D97706",
        "sub_fg": "#D1A47B",
        "icon": "📷",
        "sway_amp": 15.0,
        "sway_speed": 2.0
    },
    "longing": {
        "badge": "💭 LONGING FOR YOU",
        "badge_bg": "#3C152B",
        "badge_fg": "#F472B6",
        "bg": "#1D0C17",
        "fg": "#FCE7F3",
        "border": "#EC4899",
        "accent": "#DB2777",
        "sub_fg": "#F4A0C7",
        "icon": "💌",
        "sway_amp": 17.0,
        "sway_speed": 2.3
    },
    "anthem": {
        "badge": "📢 SPEAK UP & LOVE",
        "badge_bg": "#431C05",
        "badge_fg": "#FCD34D",
        "bg": "#200E04",
        "fg": "#FFFBEB",
        "border": "#F97316",
        "accent": "#EA580C",
        "sub_fg": "#FED7AA",
        "icon": "✨",
        "sway_amp": 20.0,
        "sway_speed": 2.8
    },
    "broken": {
        "badge": "💔 NO HOME FOR BROKEN HEART",
        "badge_bg": "#102142",
        "badge_fg": "#93C5FD",
        "bg": "#091224",
        "fg": "#EFF6FF",
        "border": "#3B82F6",
        "accent": "#2563EB",
        "sub_fg": "#BFDBFE",
        "icon": "💔",
        "sway_amp": 14.0,
        "sway_speed": 1.9
    },
    "blame": {
        "badge": "🥀 BLAMING MYSELF",
        "badge_bg": "#3B0E17",
        "badge_fg": "#FDA4AF",
        "bg": "#1B070C",
        "fg": "#FFF1F2",
        "border": "#E11D48",
        "accent": "#BE123C",
        "sub_fg": "#FECDD3",
        "icon": "🥀",
        "sway_amp": 16.0,
        "sway_speed": 2.1
    },
    "cherish": {
        "badge": "✨ CHERISH THE LOVE",
        "badge_bg": "#2A1445",
        "badge_fg": "#DDD6FE",
        "bg": "#140924",
        "fg": "#FAF5FF",
        "border": "#8B5CF6",
        "accent": "#7C3AED",
        "sub_fg": "#C4B5FD",
        "icon": "🌟",
        "sway_amp": 15.0,
        "sway_speed": 2.2
    }
}

FONT_HEADING = "Segoe UI"
FONT_LYRIC = "Segoe UI"
FONT_SUBTITLE = "Segoe UI"


class SunsetLyricCard:
    """
    Thẻ ghi chú lời bài hát Polaroid phong cách hoàng hôn lãng mạn:
    - Bảng màu ấm áp Sunset Amber pha chút nuối tiếc ngọt ngào.
    - Hoạt ảnh sóng âm Equalizer mini nhảy nhót theo giai điệu guitar acoustic.
    - Hiệu ứng gõ máy chữ typewriter kèm con trỏ ánh sáng ấm áp.
    - Chuyển động bồng bềnh dập dềnh (Buoyant Bob & Sway) vui tươi nhưng sâu lắng.
    - Hỗ trợ kéo thả tự do bằng chuột, nhấp chuột phải để đóng nhanh.
    """
    def __init__(self, master, lyric_data, x, y, on_close=None):
        self.master = master
        self.lyric_data = lyric_data
        self.eng_text = lyric_data["eng"]
        self.vie_text = lyric_data["vie"]
        self.speed_ms = lyric_data.get("speed_ms", 50)
        self.mood_key = lyric_data.get("mood", "regret")
        self.theme = SUNSET_THEMES.get(self.mood_key, SUNSET_THEMES["regret"])
        self.on_close = on_close

        # Tọa độ và chuyển động nhún nhảy âm vang acoustic
        self.base_x = float(x)
        self.base_y = float(y)
        self.cur_y = float(y)
        self.phase1 = random.uniform(0, math.pi * 2)
        self.phase2 = random.uniform(0, math.pi * 2)
        self.amp1 = self.theme["sway_amp"]
        self.amp2 = self.amp1 * 0.45
        self.speed1 = self.theme["sway_speed"]
        self.speed2 = self.speed1 * 1.5
        self.created_time = time.time()

        # Cửa sổ Toplevel không viền, nổi lên trên mọi tác vụ máy tính
        self.win = tk.Toplevel(master)
        self.win.overrideredirect(True)
        self.win.attributes("-topmost", True)
        self.win.geometry(f"{BOX_W}x{BOX_H}+{int(self.base_x)}+{int(self.cur_y)}")
        self.win.config(bg=self.theme["border"])

        # Khung viền chứa nội dung thẻ kiểu khung ảnh Polaroid
        self.inner_frame = tk.Frame(
            self.win,
            bg=self.theme["bg"],
            highlightthickness=0,
            padx=12,
            pady=10
        )
        self.inner_frame.pack(fill="both", expand=True, padx=2, pady=2)

        # 1. Dải ánh sáng hoàng hôn ở đỉnh thẻ
        self.top_strip = tk.Frame(self.inner_frame, bg=self.theme["accent"], height=3)
        self.top_strip.pack(fill="x", side="top", pady=(0, 6))

        # 2. Header: Badge cảm xúc + Bộ mô phỏng Equalizer + Icon
        self.header_frame = tk.Frame(self.inner_frame, bg=self.theme["bg"])
        self.header_frame.pack(fill="x", side="top")

        # Badge tâm trạng
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

        # Icon Polaroid / Sunset
        self.icon_label = tk.Label(
            self.header_frame,
            text=self.theme["icon"],
            font=(FONT_HEADING, 10),
            bg=self.theme["bg"],
            fg=self.theme["accent"]
        )
        self.icon_label.pack(side="right", padx=(0, 4))

        # 3. Lời bài hát tiếng Anh nổi bật
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

        # 4. Lời dịch thơ mộng tiếng Việt
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

        # 5. Footer thông tin bài hát
        self.footer_frame = tk.Frame(self.inner_frame, bg=self.theme["bg"])
        self.footer_frame.pack(fill="x", side="bottom")

        time_str = f"[{int(lyric_data['time_sec'] // 60):02d}:{int(lyric_data['time_sec'] % 60):02d}]"
        self.footer_text = tk.Label(
            self.footer_frame,
            text=f"Olly Murs • That Girl  {time_str}",
            font=(FONT_HEADING, 7),
            fg=self.theme["sub_fg"],
            bg=self.theme["bg"]
        )
        self.footer_text.pack(side="left")

        # Cho phép kéo thả thẻ dễ dàng
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

        # Khởi động typewriter và hoạt ảnh Equalizer
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
        self.cur_y += dy
        self.win.geometry(f"{BOX_W}x{BOX_H}+{int(self.base_x)}+{int(self.cur_y)}")

    def stop_drag(self, event):
        self.is_dragging = False

    def animate_eq(self):
        """Vẽ hoạt ảnh các thanh sóng âm nhảy múa theo tiết tấu pop acoustic."""
        if not self.is_alive:
            return
        for i, bar in enumerate(self.eq_bars):
            max_h = 14 if self.mood_key == "anthem" else 10
            h = random.randint(2, max_h)
            bx = i * 8 + 3
            self.eq_canvas.coords(bar, bx, 15 - h, bx + 5, 15)
        self.win.after(85, self.animate_eq)

    def typewriter(self):
        """Hiển thị từng chữ tiếng Anh rồi nhẹ nhàng bung lời dịch tiếng Việt."""
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
        """Bay dần lên kết hợp hiệu ứng dập dềnh bồng bềnh (Buoyant Bob & Sway)."""
        if not self.is_alive:
            return
        self.cur_y -= dy

        if not self.is_dragging:
            elapsed = time.time() - self.created_time
            sway = (math.sin(elapsed * self.speed1 + self.phase1) * self.amp1 +
                    math.cos(elapsed * self.speed2 + self.phase2) * self.amp2)
            # Nhún nhảy thẳng đứng nhẹ theo nhịp guitar acoustic
            bob = math.sin(elapsed * 3.2 + self.phase1) * 2.5
            current_x = self.base_x + sway
            current_y = self.cur_y + bob
        else:
            current_x = self.base_x
            current_y = self.cur_y

        self.win.geometry(f"{BOX_W}x{BOX_H}+{int(current_x)}+{int(current_y)}")

    def is_offscreen(self):
        """Kiểm tra thẻ đã trôi hết qua cạnh trên màn hình chưa."""
        return self.cur_y + BOX_H < -40

    def destroy(self):
        """Đóng thẻ và dọn dẹp bộ nhớ."""
        if self.is_alive:
            self.is_alive = False
            try:
                self.win.destroy()
            except Exception:
                pass
            if self.on_close:
                self.on_close(self)


class ThatGirlApp:
    """
    Ứng dụng quản lý phát nhạc và đồng bộ lời bài hát 'That Girl - Olly Murs'.
    """
    def __init__(self, audio_file="ThatGirl.mp3", lyrics_file="lyrics.txt"):
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

        # 1. Nạp danh sách lời bài hát
        self.load_lyrics()

        # 2. Khởi tạo âm thanh
        self.init_audio()

        # 3. Phím tắt tương tác
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
        """Khởi động pygame mixer và cấu hình âm lượng."""
        pygame.mixer.init()
        if os.path.exists(self.audio_file):
            pygame.mixer.music.load(self.audio_file)
            pygame.mixer.music.set_volume(self.volume)
            print(f"[Music] Audio loaded: {os.path.basename(self.audio_file)} (Volume: {int(self.volume*100)}%)")
        else:
            print(f"[Warning] Audio file '{self.audio_file}' not found. Timer fallback active.")

    def load_lyrics(self):
        """
        Đọc file lyrics.txt với cấu trúc:
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
                        speed_ms = int(parts[1].strip()) if len(parts) > 1 else 50
                        mood = parts[2].strip() if len(parts) > 2 else "regret"

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
        """Phân chia tọa độ X thành các cột để các thẻ phân bổ đều, không đè lên nhau."""
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
        """Tạo thẻ ghi chú mới xuất hiện từ phía dưới màn hình."""
        spawn_x = self.random_safe_x()
        spawn_y = self.screen_h - BOX_H - random.randint(40, 80)

        card = SunsetLyricCard(
            master=self.root,
            lyric_data=lyric_data,
            x=spawn_x,
            y=spawn_y,
            on_close=lambda c: self.cards.remove(c) if c in self.cards else None
        )
        self.cards.append(card)

        # In thông tin dòng hát ra terminal
        t = lyric_data["time_sec"]
        badge_name = SUNSET_THEMES.get(lyric_data["mood"], {}).get("badge", lyric_data["mood"])
        print(f"[{t:5.1f}s] [{badge_name[:20]:20s}] \"{lyric_data['eng']}\"")
        if lyric_data["vie"]:
            print(f"       {' '*20}  ↳ {lyric_data['vie']}")

    def get_current_music_time(self):
        """Lấy mốc thời gian bài hát chính xác từ pygame mixer."""
        if pygame.mixer.music.get_busy() or self.is_paused:
            pos_ms = pygame.mixer.music.get_pos()
            if pos_ms >= 0:
                return pos_ms / 1000.0
        if self.start_wall_time:
            elapsed = time.time() - self.start_wall_time - self.total_paused_duration
            return max(0.0, elapsed)
        return 0.0

    def toggle_pause(self):
        """Tạm dừng hoặc tiếp tục phát nhạc."""
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
        """Tăng hoặc giảm âm lượng."""
        self.volume = max(0.0, min(1.0, self.volume + delta))
        pygame.mixer.music.set_volume(self.volume)
        print(f"[Volume] {int(self.volume * 100)}%")

    def update(self):
        """Vòng lặp animation: kích hoạt câu hát mới và cập nhật chuyển động bay lên."""
        if not self.is_running:
            return

        if not self.is_paused:
            current_time = self.get_current_music_time()

            # 1. Sinh thẻ mới khi chạm mốc thời gian
            while self.next_index < len(self.lyrics_timeline):
                next_lyric = self.lyrics_timeline[self.next_index]
                if current_time >= next_lyric["time_sec"]:
                    self.spawn_card(next_lyric)
                    self.next_index += 1
                else:
                    break

            # 2. Cập nhật chuyển động bay lên cho các thẻ
            for card in list(self.cards):
                card.rise(RISE_SPEED)
                if card.is_offscreen():
                    card.destroy()

            # 3. Kết thúc khi bài hát hết và toàn bộ thẻ đã trôi hết
            if self.next_index >= len(self.lyrics_timeline) and not self.cards:
                if not pygame.mixer.music.get_busy():
                    print("\n[App] Song completed. All That Girl cards finished. Exiting gracefully.")
                    self.quit()
                    return

        self.root.after(FRAME_DELAY_MS, self.update)

    def print_banner(self):
        """In giao diện chào mừng ấm áp phong cách hoàng hôn."""
        banner = """
========================================================================
   🌅  O L L Y   M U R S  -  T H A T   G I R L  🌅
========================================================================
  🌇 Trải nghiệm thẻ lời bài hát nổi phong cách Polaroid hoàng hôn:
  - 🌇 BITTERSWEET REGRET: Day dứt khi để người mình thương bước đi
  - 💭 LONGING FOR YOU: Khao khát cơ hội đưa em trở lại bên anh
  - 📢 SPEAK UP & LOVE: Điệp khúc rực rỡ "Speak up if you want somebody!"
  - 💔 NO HOME FOR BROKEN HEART: Trái tim vụn vỡ không chốn nương thân
  - 🥀 BLAMING MYSELF: Chẳng thể trách ai ngoài chính bản thân mình
  - ✨ CHERISH THE LOVE: Đừng bao giờ dại dột đánh mất tình yêu

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
        """Bắt đầu phát nhạc và chạy vòng lặp Tkinter."""
        self.print_banner()

        if os.path.exists(self.audio_file):
            pygame.mixer.music.play()
        self.start_wall_time = time.time()

        self.update()
        self.root.mainloop()

    def quit(self):
        """Dọn dẹp và đóng ứng dụng."""
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
    audio_path = os.path.join(current_dir, "ThatGirl.mp3")
    lyrics_path = os.path.join(current_dir, "lyrics.txt")

    app = ThatGirlApp(audio_file=audio_path, lyrics_file=lyrics_path)
    app.start()
