import threading
import tkinter as tk
import queue
import os
import time
from src.tools import bcolors
from src.settings_window import get_settings

# Always define these at the top
SIMPLEAUDIO_AVAILABLE = False
WINSOUND_AVAILABLE = False

# Try to import simpleaudio, fallback to winsound if not available
try:
    import simpleaudio as sa
    SIMPLEAUDIO_AVAILABLE = True
except ImportError:
    pass
try:
    import winsound
    WINSOUND_AVAILABLE = True
except ImportError:
    pass

# Always import pydub and pyaudio for robust fallback
from pydub import AudioSegment
import pyaudio

ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets', 'audio')

class SoundManager:
    """Manages beeping sounds for different application states using WAV files from assets/"""
    def __init__(self):
        self.enabled = True
        self.sounds = {
            'start': os.path.join(ASSETS_DIR, 'start.wav'),
            'end': os.path.join(ASSETS_DIR, 'end.wav'),
            'success': os.path.join(ASSETS_DIR, 'success.wav'),
            'error': os.path.join(ASSETS_DIR, 'error.wav'),
            'app_start': os.path.join(ASSETS_DIR, 'app_start.wav'),
        }
        # Hangerő beállítása (0-100)
        self.volume = get_settings().get('volume', 30)

    def set_volume(self, volume):
        """
        Beállítja a hangerőt (0-100).
        """
        self.volume = volume

    def play_sound(self, sound_type):
        if not self.enabled or sound_type not in self.sounds:
            return
        sound_path = self.sounds[sound_type]
        if not os.path.exists(sound_path):
            print(f"{bcolors.WARNING}[WARNING] Sound file not found: {sound_path}{bcolors.ENDC}")
            return
        # Try simpleaudio, then pydub+pyaudio
        try:
            if SIMPLEAUDIO_AVAILABLE:
                try:
                    wave_obj = sa.WaveObject.from_wave_file(sound_path)
                    # Hangerő alkalmazása simpleaudio-nál (csak ha támogatott)
                    # Nincs natív hangerő, ezért pydubbal módosítjuk, ha nem 100%
                    if self.volume != 100:
                        audio = AudioSegment.from_file(sound_path)
                        change_db = 20 * (self.volume / 100.0 - 1) if self.volume > 0 else -120
                        audio = audio + change_db
                        raw = audio.raw_data
                        play_obj = sa.play_buffer(raw, audio.channels, audio.sample_width, audio.frame_rate)
                    else:
                        play_obj = wave_obj.play()
                    return
                except Exception as e:
                    print(f"{bcolors.WARNING}[WARNING] simpleaudio failed: {e}{bcolors.ENDC}")
            # Always try pydub + pyaudio as the final fallback
            try:
                audio = AudioSegment.from_file(sound_path)
                # Hangerő alkalmazása pydubnál
                if self.volume != 100:
                    change_db = 20 * (self.volume / 100.0 - 1) if self.volume > 0 else -120
                    audio = audio + change_db
                p = pyaudio.PyAudio()
                stream = p.open(format=p.get_format_from_width(audio.sample_width),
                                channels=audio.channels,
                                rate=audio.frame_rate,
                                output=True)
                stream.write(audio.raw_data)
                stream.stop_stream()
                stream.close()
                p.terminate()
                return
            except Exception as e:
                print(f"{bcolors.WARNING}[WARNING] pydub+pyaudio failed: {e}{bcolors.ENDC}")
            print(f"{bcolors.WARNING}[WARNING] All sound playback methods failed for {sound_path}{bcolors.ENDC}")
        except Exception as e:
            print(f"{bcolors.WARNING}[WARNING] Sound playback failed: {e}{bcolors.ENDC}")

class StatusIndicator(threading.Thread):
    COLORS = {
        'idle': '#888888',      # szürke
        'active': '#888888',    # szürke (alias)
        'listening': '#0074D9', # kék
        'sending': '#FFDC00',   # sárga
        'done': '#2ECC40',      # zöld
        'error': '#FF4136',     # piros
        'running': '#00BFFF',   # világoskék (pörgés)
    }
    TRANSITION_DURATION = 300  # ms
    TRANSITION_STEPS = 15
    SPIN_INTERVAL = 30  # ms
    SPIN_ARC_WIDTH = 4
    SPIN_ARC_RADIUS = 14
    SPIN_ARC_EXTENT = 90
    BASE_SIZE = 24
    BIG_SIZE = 48
    SIZE_TRANSITION_STEPS = 10
    SIZE_TRANSITION_DURATION = 200  # ms összesen

    def __init__(self, size=24, y_offset=30, on_click=None):
        super().__init__(daemon=True)
        self.size = size
        self.target_size = size
        self.size_transitioning = False
        self.size_transition_step = 0
        self.start_size = size
        self.end_size = size
        self.y_offset = y_offset
        self.status = 'idle'
        self.status_queue = queue.Queue()
        self.root = None
        self.dot = None
        self.running = True
        self.sound_manager = SoundManager()
        self.current_color = self.COLORS['idle']
        self.target_color = self.COLORS['idle']
        self.transition_step = 0
        self.transitioning = False
        self.spin_angle = 0
        self.is_spinning = False
        self.on_click = on_click

    def run(self):
        self.root = tk.Tk()
        self.root.overrideredirect(True)
        self.root.attributes('-topmost', True)
        self.root.attributes('-alpha', 0.9)
        self.root.configure(bg='black')
        self.root.wm_attributes('-transparentcolor', 'black')
        self.root.geometry(self._get_geometry())
        self.dot = tk.Canvas(
            self.root,
            width=self.size,
            height=self.size,
            highlightthickness=0,
            bg='black'
        )
        self.dot.pack()
        self._draw_dot(self.COLORS['idle'])
        if self.on_click:
            self.dot.bind('<Button-1>', lambda event: self.on_click())
        self.root.after(100, self._poll_status)
        self.root.mainloop()

    def _get_geometry(self, size=None):
        # Az ablak pozícióját és méretét adja vissza
        s = size if size is not None else self.size
        try:
            import screeninfo
            screen = screeninfo.get_monitors()[0]
            x = screen.x + (screen.width - s) // 2
            y = screen.y + screen.height - s - self.y_offset - 40 - 20
        except Exception:
            x = (self.root.winfo_screenwidth() - s) // 2
            y = self.root.winfo_screenheight() - s - self.y_offset - 40 - 20
        return f"{s}x{s}+{x}+{y}"

    def _hex_to_rgb(self, hex_color):
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    def _rgb_to_hex(self, rgb):
        return '#{:02x}{:02x}{:02x}'.format(*rgb)

    def _interpolate_color(self, c1, c2, t):
        return tuple(int(a + (b - a) * t) for a, b in zip(c1, c2))

    def _draw_dot(self, color):
        self.dot.delete('all')
        # A vászon méretét megnöveljük, hogy a pörgő ív mindig beleférjen
        arc_margin = max(6, self.size // 8)  # Ív margója
        canvas_size = self.size + arc_margin * 2
        self.dot.config(width=canvas_size, height=canvas_size)
        self.root.geometry(self._get_geometry(canvas_size))
        # Fő pont kirajzolása középre
        self.dot.create_oval(
            arc_margin, arc_margin,
            arc_margin + self.size - 2, arc_margin + self.size - 2,
            fill=color, outline='white', width=1
        )
        # Pörgő ív kirajzolása, ha szükséges
        if self.is_spinning:
            center = canvas_size // 2
            r = (self.size // 2) + (arc_margin // 2)
            self.dot.create_arc(
                center - r, center - r, center + r, center + r,
                start=self.spin_angle, extent=self.SPIN_ARC_EXTENT,
                style=tk.ARC, outline='white', width=max(2, self.size // 12)
            )

    def _start_size_transition(self, new_size):
        self.size_transitioning = True
        self.size_transition_step = 0
        self.start_size = self.size
        self.end_size = new_size
        self._do_size_transition()

    def _do_size_transition(self):
        if not self.size_transitioning:
            return
        t = self.size_transition_step / self.SIZE_TRANSITION_STEPS
        new_size = int(self.start_size + (self.end_size - self.start_size) * t)
        self.size = new_size
        self._draw_dot(self.current_color)
        if self.size_transition_step < self.SIZE_TRANSITION_STEPS:
            self.size_transition_step += 1
            self.root.after(self.SIZE_TRANSITION_DURATION // self.SIZE_TRANSITION_STEPS, self._do_size_transition)
        else:
            self.size_transitioning = False
            self.size = self.end_size
            self._draw_dot(self.current_color)

    def _start_transition(self, new_color):
        self.transitioning = True
        self.transition_step = 0
        self.start_rgb = self._hex_to_rgb(self.current_color)
        self.end_rgb = self._hex_to_rgb(new_color)
        self._do_transition()

    def _do_transition(self):
        if not self.transitioning:
            return
        t = self.transition_step / self.TRANSITION_STEPS
        rgb = self._interpolate_color(self.start_rgb, self.end_rgb, t)
        hex_color = self._rgb_to_hex(rgb)
        self._draw_dot(hex_color)
        self.current_color = hex_color
        if self.transition_step < self.TRANSITION_STEPS:
            self.transition_step += 1
            self.root.after(self.TRANSITION_DURATION // self.TRANSITION_STEPS, self._do_transition)
        else:
            self.transitioning = False
            self.current_color = self._rgb_to_hex(self.end_rgb)
            self._draw_dot(self.current_color)

    def _start_spinning(self):
        if not self.is_spinning:
            self.is_spinning = True
            self._spin()

    def _stop_spinning(self):
        self.is_spinning = False
        self._draw_dot(self.current_color)

    def _spin(self):
        if self.is_spinning:
            self.spin_angle = (self.spin_angle + 12) % 360
            self._draw_dot(self.current_color)
            self.root.after(self.SPIN_INTERVAL, self._spin)

    def _poll_status(self):
        try:
            while not self.status_queue.empty():
                status = self.status_queue.get_nowait()
                self.status = status
                color = self.COLORS.get(status, '#888888')
                # Pörgés: 'sending' vagy 'running' állapotban
                if status in ('sending', 'running'):
                    self._start_spinning()
                else:
                    self._stop_spinning()
                # Méretváltás: 'listening' vagy 'sending' -> nagyobb, egyébként alapméret
                if status in ('listening', 'sending'):
                    if self.size != self.BIG_SIZE:
                        self._start_size_transition(self.BIG_SIZE)
                else:
                    if self.size != self.BASE_SIZE:
                        self._start_size_transition(self.BASE_SIZE)
                if color != self.current_color:
                    self._start_transition(color)
                else:
                    self._draw_dot(color)
                if status == 'listening':
                    self.sound_manager.play_sound('start')
                elif status == 'done':
                    self.sound_manager.play_sound('success')
                elif status == 'error':
                    self.sound_manager.play_sound('error')
                if status in ('done', 'error'):
                    self.root.after(1000, lambda: self.set_status('idle'))
        except Exception:
            pass
        if self.running:
            self.root.after(100, self._poll_status)
    def set_status(self, status):
        self.status_queue.put(status)
    def stop(self):
        self.running = False
        if self.root:
            self.root.destroy() 