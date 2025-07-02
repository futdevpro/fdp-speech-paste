import os
import subprocess
from pydub import AudioSegment
from .tools import bcolors

def convert_to_mp3(input_path, output_dir):
    """
    Konvertálja a bemeneti hangfájlt MP3 formátumra.
    Támogatott bemeneti formátumok:
    - Tömörített: mp3, mp4, m4a, aac, ogg, wma, wmv, flac, alac
    - Nem tömörített: wav, aiff, pcm, raw
    - Webes: webm, opus
    - Egyéb: amr, mid, midi, wavpack, ape, tta, ac3, dts
    """
    try:
        print(f"{bcolors.OKBLUE}[INFO] Konvertálás kezdése: {input_path}{bcolors.ENDC}")
        
        # Ellenőrizzük, hogy létezik-e a bemeneti fájl
        if not os.path.exists(input_path):
            print(f"{bcolors.FAIL}[ERROR] A bemeneti fájl nem létezik: {input_path}{bcolors.ENDC}")
            return None
            
        # Ellenőrizzük a bemeneti fájl méretét
        input_size = os.path.getsize(input_path)
        print(f"{bcolors.OKBLUE}[INFO] Bemeneti fájl mérete: {input_size} bytes{bcolors.ENDC}")
        
        if input_size == 0:
            print(f"{bcolors.FAIL}[ERROR] A bemeneti fájl üres!{bcolors.ENDC}")
            return None

        # Ha már MP3, nem kell konvertálni
        if input_path.lower().endswith('.mp3'):
            print(f"{bcolors.OKBLUE}[INFO] A fájl már MP3 formátumban van{bcolors.ENDC}")
            return input_path

        # Kimeneti fájl neve
        output_filename = os.path.splitext(os.path.basename(input_path))[0] + '.mp3'
        output_path = os.path.join(output_dir, output_filename)
        
        print(f"{bcolors.OKBLUE}[INFO] Konvertálás{bcolors.ENDC}")
        
        # FFmpeg parancs az MP3-ba konvertáláshoz
        cmd = [
            'ffmpeg',
            '-y',  # Felülírja a kimeneti fájlt ha létezik
            '-i', input_path,
            '-vn',  # Csak az audio stream
            '-acodec', 'libmp3lame',  # MP3 kodek
            '-ab', '192k',  # Bitrate
            '-ar', '44100',  # Mintavételi frekvencia
            '-ac', '2',  # Sztereó
            '-map', '0:a',  # Csak az audio streameket használja
            '-map_metadata', '-1',  # Törli a metadata-t
            '-loglevel', 'error',  # Csak a hibákat mutatja
            output_path
        ]
        
        try:
            print(f"{bcolors.OKBLUE}[INFO] FFmpeg parancs: {' '.join(cmd)}{bcolors.ENDC}")
            
            # Futtatjuk az FFmpeg-et és rögzítjük a kimenetet
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            
            # Várjuk meg a befejezést és olvassuk a kimenetet
            stdout, stderr = process.communicate()
            
            if process.returncode != 0:
                print(f"{bcolors.FAIL}[ERROR] FFmpeg hiba: {stderr}{bcolors.ENDC}")
                return None
                
            print(f"{bcolors.OKGREEN}[SUCCESS] Konvertálás sikeres{bcolors.ENDC}")
            
        except Exception as e:
            print(f"{bcolors.FAIL}[ERROR] FFmpeg hiba: {str(e)}{bcolors.ENDC}")
            return None

        # Ellenőrizzük a kimeneti fájl méretét
        if os.path.exists(output_path):
            output_size = os.path.getsize(output_path)
            print(f"{bcolors.OKBLUE}[INFO] Kimeneti fájl mérete: {output_size} bytes{bcolors.ENDC}")
            
            if output_size == 0:
                print(f"{bcolors.FAIL}[ERROR] A kimeneti fájl üres!{bcolors.ENDC}")
                return None
                
            return output_path
        else:
            print(f"{bcolors.FAIL}[ERROR] A kimeneti fájl nem jött létre!{bcolors.ENDC}")
            return None

    except Exception as e:
        print(f"{bcolors.FAIL}[ERROR] Váratlan hiba a konvertálás során: {str(e)}{bcolors.ENDC}")
        return None 