import pyaudio
import wave
import threading
import time
import requests
import json
import tempfile
import os
import sys
import signal
import subprocess
from pynput import keyboard
from pynput.keyboard import Key, KeyCode
import pyperclip
from src.tools import bcolors
import tkinter as tk
import queue
from pydub import AudioSegment
from src.indicator import StatusIndicator
from src.recognition import process_audio
from src.settings_window import open_settings_window, get_settings

class SpeechRecognitionDesktopApp:
    """
    Asztali alkalmazás a beszédfelismeréshez globális billentyűkombinációval.
    Ctrl+Win billentyűkombinációval aktiválja a mikrofont, majd a felismerés után
    automatikusan beilleszti a szöveget a vágólapra és Ctrl+V-vel beilleszti.
    """
    
    def __init__(self):
        """Inicializálja az alkalmazást"""
        self.is_recording = False
        self.audio_frames = []
        self.recording_thread = None
        self.audio = pyaudio.PyAudio()
        self.stream = None
        # Billentyű kombináció követés
        self.ctrl_pressed = False
        self.win_pressed = False
        self.was_combo_pressed = False  # Prevent retriggering while held
        # Alkalmazás állapot
        self.running = True
        self.listener = None
        # Audio beállítások
        self.CHUNK = 1024
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 2
        self.RATE = 44100
        print(f"{bcolors.OKGREEN}[INFO] Beszédfelismerés asztali alkalmazás elindítva{bcolors.ENDC}")
        print(f"{bcolors.OKBLUE}[INFO] Nyomja meg a Ctrl+Win billentyűkombinációt a mikrofon aktiválásához{bcolors.ENDC}")
        print(f"{bcolors.OKBLUE}[INFO] Engedje el a billentyűket a felismerés befejezéséhez{bcolors.ENDC}")
        print(f"{bcolors.OKBLUE}[INFO] Nyomja meg a Ctrl+C billentyűkombinációt a kilépéshez{bcolors.ENDC}")
        signal.signal(signal.SIGINT, self.signal_handler)
        # Hangerő beállítása indításkor
        initial_volume = get_settings().get('volume', 50)
        self.indicator = StatusIndicator(on_click=lambda: open_settings_window(on_volume_change=self.indicator.sound_manager.set_volume if hasattr(self, 'indicator') else None))
        # A SoundManager példányt csak az indicator létrehozása után érjük el
        self.indicator.start()
        self.indicator.sound_manager.set_volume(initial_volume)
        self.indicator.sound_manager.play_sound('app_start')
        # Warm-up: open and close a dummy stream
        try:
            dummy_stream = self.audio.open(
                format=self.FORMAT,
                channels=self.CHANNELS,
                rate=self.RATE,
                input=True,
                frames_per_buffer=self.CHUNK
            )
            dummy_stream.close()
            print(f"{bcolors.OKBLUE}[INFO] Mikrofon előmelegítve (warm-up){bcolors.ENDC}")
        except Exception as e:
            print(f"{bcolors.WARNING}[WARNING] Mikrofon warm-up sikertelen: {e}{bcolors.ENDC}")
        
    def signal_handler(self, signum, frame):
        """Signal handler a Ctrl+C kezeléséhez"""
        # Csak SIGINT (Ctrl+C) jelre reagálunk
        if signum == signal.SIGINT:
            print(f"\n{bcolors.OKBLUE}[INFO] Kilépési jel fogadva (Ctrl+C){bcolors.ENDC}")
            self.running = False
            self.cleanup()
            sys.exit(0)
        
    def on_press(self, key):
        """Billentyű lenyomásakor meghívott függvény"""
        try:
            changed = False
            # Ctrl billentyű követése (több lehetséges formátum)
            if key == Key.ctrl or key == Key.ctrl_l or key == Key.ctrl_r:
                if not self.ctrl_pressed:
                    print(f"{bcolors.OKBLUE}[INFO] Ctrl billentyű lenyomva{bcolors.ENDC}")
                    self.ctrl_pressed = True
                    changed = True

            # Windows billentyű követése (több lehetséges formátum)
            elif (hasattr(key, 'vk') and key.vk == 91) or key == Key.cmd or key == Key.cmd_l or key == Key.cmd_r:
                if not self.win_pressed:
                    print(f"{bcolors.OKBLUE}[INFO] Windows billentyű lenyomva{bcolors.ENDC}")
                    self.win_pressed = True
                    changed = True

            # Alternatív Windows key detektálás
            elif hasattr(key, 'name') and key.name == 'cmd':
                if not self.win_pressed:
                    print(f"{bcolors.OKBLUE}[INFO] Windows billentyű lenyomva (name){bcolors.ENDC}")
                    self.win_pressed = True
                    changed = True

            # Ellenőrizzük a Ctrl+Win kombinációt csak egyszer, amikor mindkettő először lenyomva
            if self.ctrl_pressed and self.win_pressed and not self.was_combo_pressed:
                print(f"{bcolors.OKGREEN}[INFO] Ctrl+Win kombináció lenyomva - felvétel indítása!{bcolors.ENDC}")
                self.was_combo_pressed = True
                if not self.is_recording:
                    self.start_recording()

            # Debug: log state
            if changed:
                print(f"[DEBUG] State: ctrl_pressed={self.ctrl_pressed}, win_pressed={self.win_pressed}, was_combo_pressed={self.was_combo_pressed}")

        except AttributeError as e:
            print(f"{bcolors.WARNING}[WARNING] Billentyű detektálási hiba: {e}{bcolors.ENDC}")

        except Exception as e:
            print(f"{bcolors.FAIL}[ERROR] Váratlan hiba a billentyű detektálás során: {e}{bcolors.ENDC}")
            
    def on_release(self, key):
        """Billentyű felengedéskor meghívott függvény"""
        try:
            changed = False
            # Ctrl billentyű felengedés követése (több lehetséges formátum)
            if key == Key.ctrl or key == Key.ctrl_l or key == Key.ctrl_r:
                if self.ctrl_pressed:
                    self.ctrl_pressed = False
                    print(f"{bcolors.OKBLUE}[INFO] Ctrl billentyű felengedve{bcolors.ENDC}")
                    changed = True

            # Windows billentyű felengedés követése (több lehetséges formátum)
            elif (hasattr(key, 'vk') and key.vk == 91) or key == Key.cmd or key == Key.cmd_l or key == Key.cmd_r:
                if self.win_pressed:
                    self.win_pressed = False
                    print(f"{bcolors.OKBLUE}[INFO] Windows billentyű felengedve{bcolors.ENDC}")
                    changed = True

            # Alternatív Windows key felengedés detektálás
            elif hasattr(key, 'name') and key.name == 'cmd':
                if self.win_pressed:
                    self.win_pressed = False
                    print(f"{bcolors.OKBLUE}[INFO] Windows billentyű felengedve (name){bcolors.ENDC}")
                    changed = True

            # Ha bármelyik billentyű felengedődik és felvétel folyik, leállítjuk
            if (not self.ctrl_pressed or not self.win_pressed) and self.is_recording:
                print(f"{bcolors.OKGREEN}[INFO] Billentyűk felengedve - felvétel leállítása!{bcolors.ENDC}")
                self.stop_recording()

            # Reset combo flag if either key is released
            if not self.ctrl_pressed or not self.win_pressed:
                self.was_combo_pressed = False

            # Debug: log state
            if changed:
                print(f"[DEBUG] State: ctrl_pressed={self.ctrl_pressed}, win_pressed={self.win_pressed}, was_combo_pressed={self.was_combo_pressed}")
                
        except AttributeError as e:
            print(f"{bcolors.WARNING}[WARNING] Billentyű felengedés detektálási hiba: {e}{bcolors.ENDC}")

        except Exception as e:
            print(f"{bcolors.FAIL}[ERROR] Váratlan hiba a billentyű felengedés detektálás során: {e}{bcolors.ENDC}")
            
    def start_recording(self):
        """Elindítja az audio felvételt"""
        if self.is_recording:
            return
        print(f"{bcolors.OKGREEN}[INFO] Mikrofon aktiválva - felvétel kezdete...{bcolors.ENDC}")
        self.is_recording = True
        self.audio_frames = []
        self.stream = self.audio.open(
            format=self.FORMAT,
            channels=self.CHANNELS,
            rate=self.RATE,
            input=True,
            frames_per_buffer=self.CHUNK
        )
        self.recording_thread = threading.Thread(target=self.record_audio)
        self.recording_thread.start()
        self.indicator.set_status('listening')
        
    def stop_recording(self):
        """Leállítja az audio felvételt és feldolgozza a hangot"""
        if not self.is_recording:
            return
            
        print(f"{bcolors.OKBLUE}[INFO] Mikrofon deaktiválva - felvétel befejezése...{bcolors.ENDC}")
        
        # Play end sound
        self.indicator.sound_manager.play_sound('end')
        
        self.is_recording = False
        # Reset key states to avoid stuck keys
        self.ctrl_pressed = False
        self.win_pressed = False
        self.was_combo_pressed = False
        
        # Várjuk meg a felvételi szál befejezését
        if self.recording_thread:
            self.recording_thread.join()
            
        # Audio stream lezárása
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None
            
        # Audio feldolgozása
        if self.audio_frames:
            self.process_audio()
            
        self.indicator.set_status('idle')
        
    def record_audio(self):
        """Audio felvételi szál"""
        try:
            while self.is_recording and self.running:
                data = self.stream.read(self.CHUNK, exception_on_overflow=False)
                self.audio_frames.append(data)
                time.sleep(0.01)  # Rövid várakozás a CPU terhelés csökkentésére
        except Exception as e:
            print(f"{bcolors.FAIL}[ERROR] Hiba az audio felvétel során: {str(e)}{bcolors.ENDC}")
            
    def process_audio(self):
        """Feldolgozza a felvett hangot"""
        try:
            print(f"{bcolors.OKBLUE}[INFO] Audio feldolgozás kezdete...{bcolors.ENDC}")
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_wav_path = temp_file.name
            with wave.open(temp_wav_path, 'wb') as wf:
                wf.setnchannels(self.CHANNELS)
                wf.setsampwidth(self.audio.get_sample_size(self.FORMAT))
                wf.setframerate(self.RATE)
                wf.writeframes(b''.join(self.audio_frames))
            audio = AudioSegment.from_wav(temp_wav_path)
            duration_sec = len(audio) / 1000.0
            # --- ÚJ: Néma ellenőrzés ---
            # Ha az RMS vagy dBFS túl alacsony, akkor a felvétel néma
            if audio.rms < 100 or audio.dBFS < -100:
                print(f"{bcolors.WARNING}[WARNING] A felvétel néma vagy túl halk, nem küldjük a felismerésnek.{bcolors.ENDC}")
                self.indicator.set_status('error')
                return
            # --- Vége: Néma ellenőrzés ---
            if duration_sec > 30:
                print(f"{bcolors.WARNING}[WARNING] A felvétel {duration_sec:.1f} másodperc, vágás 30 másodpercre!{bcolors.ENDC}")
                audio = audio[:30_000]
                audio.export(temp_wav_path, format='wav')
            else:
                print(f"{bcolors.OKBLUE}[INFO] Felvétel hossza: {duration_sec:.1f} másodperc{bcolors.ENDC}")
            print(f"{bcolors.OKBLUE}[INFO] Audio fájl mentve: {temp_wav_path}{bcolors.ENDC}")
            # Directly call process_audio from recognition.py
            self.send_audio_to_recognition(temp_wav_path)
        except Exception as e:
            print(f"{bcolors.FAIL}[ERROR] Hiba az audio feldolgozás során: {str(e)}{bcolors.ENDC}")
        finally:
            if 'temp_wav_path' in locals() and os.path.exists(temp_wav_path):
                try:
                    os.unlink(temp_wav_path)
                except:
                    pass
                    
    def send_audio_to_recognition(self, audio_file_path):
        """Feldolgozza a hangot közvetlenül a process_audio-val"""
        try:
            self.indicator.set_status('sending')
            print(f"{bcolors.OKBLUE}[INFO] Hang feldolgozása helyben...{bcolors.ENDC}")
            result = process_audio(audio_file_path)
            if result.get('status') == 'processed':
                recognized_text = ''
                # Try to extract recognized text from result['result']
                if isinstance(result.get('result'), dict):
                    recognized_text = result['result'].get('text', '')
                elif isinstance(result.get('result'), str):
                    recognized_text = result['result']
                if recognized_text.strip():
                    self.indicator.set_status('done')
                    print(f"{bcolors.OKGREEN}[SUCCESS] Felismert szöveg: {recognized_text}{bcolors.ENDC}")
                    self.paste_to_clipboard(recognized_text)
                else:
                    self.indicator.set_status('error')
                    print(f"{bcolors.WARNING}[WARNING] Nem sikerült szöveget felismerni{bcolors.ENDC}")
            else:
                self.indicator.set_status('error')
                print(f"{bcolors.FAIL}[ERROR] Beszédfelismerés sikertelen: {result.get('error', 'Ismeretlen hiba')}{bcolors.ENDC}")
        except Exception as e:
            self.indicator.set_status('error')
            print(f"{bcolors.FAIL}[ERROR] Hiba a beszédfelismerés során: {str(e)}{bcolors.ENDC}")
            
    def paste_to_clipboard(self, text):
        """Beilleszti a szöveget a vágólapra és automatikusan beilleszti"""
        try:
            # Szöveg másolása a vágólapra
            pyperclip.copy(text)
            print(f"{bcolors.OKGREEN}[SUCCESS] Szöveg másolva a vágólapra{bcolors.ENDC}")
            
            # Rövid várakozás
            time.sleep(0.1)
            
            # Ctrl+V automatikus beillesztés
            keyboard_controller = keyboard.Controller()
            keyboard_controller.press(Key.ctrl)
            keyboard_controller.press('v')
            keyboard_controller.release('v')
            keyboard_controller.release(Key.ctrl)
            
            print(f"{bcolors.OKGREEN}[SUCCESS] Szöveg automatikusan beillesztve!{bcolors.ENDC}")
            
        except Exception as e:
            print(f"{bcolors.FAIL}[ERROR] Hiba a vágólap használata során: {str(e)}{bcolors.ENDC}")
            
    def run(self):
        """Elindítja az alkalmazást"""
        try:
            # Globális billentyű listener létrehozása
            self.listener = keyboard.Listener(
                on_press=self.on_press,
                on_release=self.on_release,
                suppress=False  # Ne blokkolja a billentyűket más alkalmazásoktól
            )
            
            print(f"{bcolors.OKGREEN}[INFO] Billentyű figyelő elindítva{bcolors.ENDC}")
            print(f"{bcolors.OKBLUE}[INFO] Várakozás a billentyűkombinációra...{bcolors.ENDC}")
            
            # Listener indítása
            self.listener.start()
            
            # Fő ciklus - ellenőrzi a running flag-et
            while self.running:
                time.sleep(0.1)  # Rövid várakozás
                
                # Ha a listener leállt, kilépünk
                if not self.listener.running:
                    break
                    
        except KeyboardInterrupt:
            print(f"\n{bcolors.OKBLUE}[INFO] Alkalmazás leállítva (KeyboardInterrupt){bcolors.ENDC}")
        except Exception as e:
            print(f"{bcolors.FAIL}[ERROR] Váratlan hiba: {str(e)}{bcolors.ENDC}")
        finally:
            self.cleanup()
            
    def cleanup(self):
        """Tisztítja fel az erőforrásokat"""
        try:
            # Felvétel leállítása
            if self.is_recording:
                self.stop_recording()
                
            # Listener leállítása
            if self.listener and self.listener.running:
                self.listener.stop()
                print(f"{bcolors.OKBLUE}[INFO] Billentyű figyelő leállítva{bcolors.ENDC}")
                
            # Audio erőforrások felszabadítása
            if self.stream:
                self.stream.stop_stream()
                self.stream.close()
            if self.audio:
                self.audio.terminate()
                
            print(f"{bcolors.OKBLUE}[INFO] Erőforrások felszabadítva{bcolors.ENDC}")
            
            self.indicator.stop()
            
        except Exception as e:
            print(f"{bcolors.WARNING}[WARNING] Hiba a cleanup során: {str(e)}{bcolors.ENDC}")

if __name__ == "__main__":
    app = SpeechRecognitionDesktopApp()
    app.run() 