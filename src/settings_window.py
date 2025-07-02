import tkinter as tk
import json
import os
from tkinter import messagebox
from tkinter import simpledialog
from tkinter import filedialog
from tkinter import PhotoImage
from PIL import Image, ImageTk

# Beállítások fájl helye (projekt gyökér)
SETTINGS_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'settings.json')
ERROR_LOG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'error_log.txt')
LOGO_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets', 'images', 'logo.png')
LOGO_ICON_PATH = LOGO_PATH  # Ugyanazt a képet használjuk ikonként is

# Alapértelmezett beállítások
def default_settings():
    return {
        'volume': 50,
        'window_x': None,
        'window_y': None,
        'ai_model': 'openai/whisper-large-v3-turbo',
    }

# Beállítások globális cache
_current_settings = None


def load_settings():
    """
    Betölti a beállításokat a fájlból, vagy alapértelmezettet ad vissza.
    """
    global _current_settings
    if _current_settings is not None:
        return _current_settings
    if os.path.exists(SETTINGS_PATH):
        try:
            with open(SETTINGS_PATH, 'r', encoding='utf-8') as f:
                _current_settings = json.load(f)
        except Exception:
            _current_settings = default_settings()
    else:
        _current_settings = default_settings()
    # Biztosítjuk, hogy minden kulcs meglegyen
    for k, v in default_settings().items():
        if k not in _current_settings:
            _current_settings[k] = v
    return _current_settings


def save_settings(settings):
    """
    Elmenti a beállításokat a fájlba.
    """
    global _current_settings
    _current_settings = settings
    try:
        with open(SETTINGS_PATH, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[WARNING] Beállítások mentése sikertelen: {e}")


def get_settings():
    """
    Visszaadja az aktuális beállításokat.
    """
    return load_settings()

# --- Hiba napló kezelés ---
def append_error_log(msg):
    """
    Hozzáfűzi az üzenetet a hibanaplóhoz.
    """
    try:
        with open(ERROR_LOG_PATH, 'a', encoding='utf-8') as f:
            f.write(msg + '\n')
    except Exception as e:
        print(f"[WARNING] Hibanapló írása sikertelen: {e}")

def load_error_log():
    """
    Betölti a hibanapló tartalmát.
    """
    if not os.path.exists(ERROR_LOG_PATH):
        return ''
    try:
        with open(ERROR_LOG_PATH, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"[Hiba a napló olvasásakor: {e}]"

def clear_error_log():
    """
    Törli a hibanaplót.
    """
    try:
        with open(ERROR_LOG_PATH, 'w', encoding='utf-8') as f:
            f.write('')
    except Exception as e:
        print(f"[WARNING] Hibanapló törlése sikertelen: {e}")


def open_settings_window(on_volume_change=None):
    """
    Opens the settings window. The window is non-blocking.
    The on_volume_change callback is called when the volume changes.
    """
    settings = load_settings()
    window = tk.Toplevel()
    window.title('Settings')
    window.geometry('360x320')
    window.resizable(False, False)
    # Ablak pozíció visszaállítása
    x = settings.get('window_x')
    y = settings.get('window_y')
    if x is not None and y is not None:
        window.geometry(f'+{x}+{y}')
    else:
        window.update_idletasks()
        x = (window.winfo_screenwidth() // 2) - (360 // 2)
        y = (window.winfo_screenheight() // 2) - (320 // 2)
        window.geometry(f'+{x}+{y}')
    # Logo beállítása ablak ikonként és fejlécben kicsiben
    logo_img = None
    try:
        if os.path.exists(LOGO_ICON_PATH):
            # Ablak ikon beállítása (fejléc ikon)
            logo_img = Image.open(LOGO_ICON_PATH)
            logo_icon = logo_img.resize((32, 32), Image.LANCZOS)
            logo_icon_tk = ImageTk.PhotoImage(logo_icon)
            window.wm_iconphoto(True, logo_icon_tk)
            # Fejlécben kis logó
            header_frame = tk.Frame(window)
            header_frame.pack(pady=(8, 0))
            logo_header = logo_img.resize((32, 32), Image.LANCZOS)
            logo_header_tk = ImageTk.PhotoImage(logo_header)
            logo_label = tk.Label(header_frame, image=logo_header_tk)
            logo_label.image = logo_header_tk  # referenciát tartani kell
            logo_label.pack(side=tk.LEFT, padx=(0, 8))
            title_label = tk.Label(header_frame, text='Settings', font=('Arial', 14, 'bold'))
            title_label.pack(side=tk.LEFT)
        else:
            # Ha nincs logó, csak cím
            title_label = tk.Label(window, text='Settings', font=('Arial', 14, 'bold'))
            title_label.pack(pady=(12, 0))
    except Exception as e:
        print(f"[WARNING] Logo betöltése vagy beállítása sikertelen: {e}")
        title_label = tk.Label(window, text='Settings', font=('Arial', 14, 'bold'))
        title_label.pack(pady=(12, 0))
    # Hangerő slider
    label = tk.Label(window, text='Volume:', font=('Arial', 12))
    label.pack(pady=(10, 2))
    volume_var = tk.IntVar(value=settings.get('volume', 50))
    slider = tk.Scale(window, from_=0, to=100, orient=tk.HORIZONTAL, variable=volume_var, length=220)
    slider.pack()
    value_label = tk.Label(window, text=f"{volume_var.get()}%", font=('Arial', 10))
    value_label.pack(pady=(0, 8))
    def on_slider_change(val):
        v = int(float(val))
        value_label.config(text=f"{v}%")
        settings['volume'] = v
        save_settings(settings)
        if on_volume_change:
            on_volume_change(v)
    slider.config(command=on_slider_change)
    # AI modell szabad szöveg mező
    ai_label = tk.Label(window, text='AI model:', font=('Arial', 12))
    ai_label.pack(pady=(5, 2))
    ai_var = tk.StringVar(value=settings.get('ai_model', default_settings()['ai_model']))
    ai_entry = tk.Entry(window, textvariable=ai_var, width=32, font=('Arial', 10))
    ai_entry.pack()
    def on_ai_entry_change(*args):
        settings['ai_model'] = ai_var.get()
        save_settings(settings)
    ai_var.trace_add('write', on_ai_entry_change)
    # Hibanapló gomb
    def show_error_log():
        log = load_error_log()
        log_window = tk.Toplevel(window)
        log_window.title('Error log')
        log_window.geometry('500x350')
        log_window.resizable(True, True)
        text = tk.Text(log_window, wrap=tk.WORD, font=('Consolas', 10))
        text.insert('1.0', log)
        text.config(state=tk.DISABLED)
        text.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)
        def clear_log():
            clear_error_log()
            text.config(state=tk.NORMAL)
            text.delete('1.0', tk.END)
            text.config(state=tk.DISABLED)
        clear_btn = tk.Button(log_window, text='Clear error log', command=clear_log)
        clear_btn.pack(pady=(0, 10))
    error_btn = tk.Button(window, text='Open error log', command=show_error_log)
    error_btn.pack(pady=(12, 0))
    # Ablak pozíció mentése bezáráskor
    def on_close():
        try:
            geo = window.geometry()
            # formátum: WxH+X+Y
            if '+' in geo:
                parts = geo.split('+')
                if len(parts) >= 3:
                    settings['window_x'] = int(parts[1])
                    settings['window_y'] = int(parts[2])
                    save_settings(settings)
        except Exception as e:
            print(f"[WARNING] Ablak pozíció mentése sikertelen: {e}")
        window.destroy()
    window.protocol('WM_DELETE_WINDOW', on_close)
    # Az ablak mindig felül legyen
    window.attributes('-topmost', True)
    window.after(100, lambda: window.attributes('-topmost', False)) 