from flask import Flask, request, jsonify
import os
import subprocess
import threading
import shutil
from werkzeug.utils import secure_filename
from .recognition import process_audio  # Updated import
from .tools import bcolors  # Updated import
from .audio_utils import convert_to_mp3  # New import
from pydub import AudioSegment
from werkzeug.serving import WSGIRequestHandler

app = Flask(__name__)

# Globális lock a feldolgozáshoz
processing_lock = threading.Lock()

# Get the project root directory (one level up from src)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

UPLOAD_FOLDER = os.path.join(PROJECT_ROOT, "uploads")
PROCESSED_FOLDER = os.path.join(PROJECT_ROOT, "processed")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)  # Létrehozza a könyvtárat, ha nem létezik
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["PROCESSED_FOLDER"] = PROCESSED_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB

# Támogatott hangformátumok
ALLOWED_EXTENSIONS = {
    # Tömörített formátumok
    "mp3", "mp4", "m4a", "aac", "ogg", "wma", "wmv", "flac", "alac",
    # Nem tömörített formátumok
    "wav", "aiff", "pcm", "raw",
    # Webes formátumok
    "webm", "opus",
    # Egyéb formátumok
    "amr", "mid", "midi", "wavpack", "ape", "tta", "ac3", "dts"
}

WSGIRequestHandler.timeout = 300  # 5 perc

def cleanup_uploads_directory():
    """Törli az uploads könyvtár tartalmát"""
    try:
        # Töröljük az összes fájlt az uploads könyvtárból
        for filename in os.listdir(UPLOAD_FOLDER):
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            try:
                if os.path.isfile(file_path):
                    os.remove(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print(f"{bcolors.WARNING}[WARNING] Fájl törlése sikertelen: {file_path} - {str(e)}{bcolors.ENDC}")
        
        print(f"{bcolors.OKBLUE}[INFO] Uploads könyvtár törölve{bcolors.ENDC}")
    except Exception as e:
        print(f"{bcolors.WARNING}[WARNING] Uploads könyvtár törlése sikertelen: {str(e)}{bcolors.ENDC}")

def cleanup_files(*files):
    """Törli a megadott fájlokat, ha léteznek"""
    for file_path in files:
        if file_path and os.path.exists(file_path):
            try:
                file_size = os.path.getsize(file_path)
                os.remove(file_path)
                print(f"{bcolors.OKBLUE}[INFO] Fájl törölve: {file_path} (méret: {file_size} bytes){bcolors.ENDC}")
            except Exception as e:
                print(f"{bcolors.WARNING}[WARNING] Fájl törlése sikertelen: {file_path} - {str(e)}{bcolors.ENDC}")

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    
@app.before_request
def before_request():
    """Minden kérés előtt futtatjuk"""
    # Ha az uploads könyvtár túl nagy (pl. több mint 1GB), töröljük
    total_size = sum(os.path.getsize(os.path.join(UPLOAD_FOLDER, f)) 
                    for f in os.listdir(UPLOAD_FOLDER) 
                    if os.path.isfile(os.path.join(UPLOAD_FOLDER, f)))
    
    if total_size > 1024 * 1024 * 1024:  # 1GB
        print(f"{bcolors.WARNING}[WARNING] Uploads könyvtár túl nagy ({total_size / (1024*1024*1024):.2f}GB), törlés...{bcolors.ENDC}")
        cleanup_uploads_directory()

@app.after_request
def after_request(response):
    """Minden válasz után futtatjuk"""
    # Töröljük az uploads könyvtárat
    cleanup_uploads_directory()
    return response

@app.route("/health", methods=["GET"])
def health_check():
    """Egészség ellenőrzés endpoint"""
    return jsonify({"status": "healthy", "service": "speech-recognition"}), 200

@app.route("/recognition", methods=["POST"])
def upload_audio():
    print(f"{bcolors.OKBLUE}[INFO] Új bejövő kérés...{bcolors.ENDC}")
    
    # Várjuk meg, amíg a lock felszabadul
    if not processing_lock.acquire(blocking=True, timeout=30):  # 30 másodperc timeout
        print(f"{bcolors.FAIL}[ERROR] Időtúllépés a feldolgozás várakozásakor{bcolors.ENDC}")
        return jsonify({"error": "Server is busy, please try again later"}), 503

    file_path = None
    converted_path = None

    try:
        raw_data = request.get_data()
        print(f"{bcolors.OKBLUE}[INFO] Raw data size: {len(raw_data)} bytes{bcolors.ENDC}")

        if "audio" in request.files:
            print(f"{bcolors.OKCYAN}[INFO] Fájl fogadása FormData módban...{bcolors.ENDC}")
            file = request.files["audio"]

            # Content type ellenőrzés
            content_type = file.content_type
            print(f"{bcolors.OKBLUE}[INFO] Content-Type: {content_type}{bcolors.ENDC}")
            
            if not content_type or not (content_type.startswith('audio/') or content_type == 'application/octet-stream'):
                print(f"{bcolors.FAIL}[ERROR] Érvénytelen content type: {content_type}{bcolors.ENDC}")
                return jsonify({"error": f"Invalid content type: {content_type}"}), 400

            if file.filename == "":
                print(f"{bcolors.FAIL}[ERROR] Nincs fájlnév megadva{bcolors.ENDC}")
                return jsonify({"error": "No selected file"}), 400

            if not allowed_file(file.filename):
                print(f"{bcolors.FAIL}[ERROR] Nem támogatott fájlformátum: {file.filename}{bcolors.ENDC}")
                return jsonify({"error": f"File format not supported. Allowed formats: {', '.join(ALLOWED_EXTENSIONS)}"}), 400

            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)

            print(f"{bcolors.WARNING}[INFO] Várakozás a fájl feltöltésére: {filename}{bcolors.ENDC}")
            file.save(file_path)

            if not os.path.exists(file_path):
                print(f"{bcolors.FAIL}[ERROR] Fájl mentése sikertelen: {file_path}{bcolors.ENDC}")
                return jsonify({"error": "Failed to save file"}), 500

            if os.path.getsize(file_path) == 0:
                cleanup_files(file_path)
                print(f"{bcolors.FAIL}[ERROR] Feltöltött fájl üres!{bcolors.ENDC}")
                return jsonify({"error": "Uploaded file is empty"}), 400

            print(f"{bcolors.OKGREEN}[SUCCESS] Fájl mentve: {file_path} ({os.path.getsize(file_path)} bytes){bcolors.ENDC}")

        elif request.data:
            print(f"{bcolors.OKCYAN}[INFO] Nyers bináris adat érkezett...{bcolors.ENDC}")
            
            content_type = request.headers.get('Content-Type', '')
            print(f"{bcolors.OKBLUE}[INFO] Content-Type: {content_type}{bcolors.ENDC}")

            if not content_type or not (content_type.startswith('audio/') or content_type == 'application/octet-stream'):
                print(f"{bcolors.FAIL}[ERROR] Érvénytelen content type: {content_type}{bcolors.ENDC}")
                return jsonify({"error": f"Invalid content type: {content_type}"}), 400

            filename = request.headers.get("Filename", "uploaded_audio.mp3")
            if not allowed_file(filename):
                print(f"{bcolors.FAIL}[ERROR] Nem támogatott fájlformátum: {filename}{bcolors.ENDC}")
                return jsonify({"error": f"File format not supported. Allowed formats: {', '.join(ALLOWED_EXTENSIONS)}"}), 400

            file_path = os.path.join(app.config["UPLOAD_FOLDER"], secure_filename(filename))

            with open(file_path, "wb") as f:
                f.write(request.data)

            if not os.path.exists(file_path):
                print(f"{bcolors.FAIL}[ERROR] Fájl mentése sikertelen: {file_path}{bcolors.ENDC}")
                return jsonify({"error": "Failed to save file"}), 500

            if os.path.getsize(file_path) == 0:
                cleanup_files(file_path)
                print(f"{bcolors.FAIL}[ERROR] Nyers bináris fájl üres!{bcolors.ENDC}")
                return jsonify({"error": "Binary upload is empty"}), 400

            print(f"{bcolors.OKGREEN}[SUCCESS] Nyers adat mentve: {file_path} ({os.path.getsize(file_path)} bytes){bcolors.ENDC}")

        else:
            print(f"{bcolors.FAIL}[ERROR] Nincs érvényes audio adat{bcolors.ENDC}")
            return jsonify({"error": "No audio data found"}), 400

        # **MP3 Konverzió**
        if file_path and not file_path.endswith(".mp3"):
            print(f"{bcolors.OKBLUE}[INFO] Konvertálás kezdése: {file_path}{bcolors.ENDC}")
            converted_path = convert_to_mp3(file_path, app.config["PROCESSED_FOLDER"])

            if converted_path is None:
                cleanup_files(file_path)
                print(f"{bcolors.FAIL}[ERROR] MP3 konvertálás sikertelen!{bcolors.ENDC}")
                return jsonify({"error": "Failed to convert audio"}), 500

            file_path = converted_path

        print(f"{bcolors.OKGREEN}[SUCCESS] File processed: {file_path}{bcolors.ENDC}")
        # A hangfájl feldolgozása egy másik fájlban történik
        print(f"{bcolors.OKBLUE}[INFO] Starting audio processing...{bcolors.ENDC}")
        try:
            result = process_audio(file_path)
            print(f"{bcolors.OKBLUE}[INFO] Audio processing result: {result}{bcolors.ENDC}")
        except Exception as e:
            print(f"{bcolors.FAIL}[ERROR] Audio processing failed: {str(e)}{bcolors.ENDC}")
            import traceback
            print(f"{bcolors.FAIL}[ERROR] Stack trace: {traceback.format_exc()}{bcolors.ENDC}")
            return jsonify({"error": "Audio processing failed", "details": str(e), "traceback": traceback.format_exc()}), 500

        # Sikeres feldolgozás után töröljük a fájlokat
        print(f"{bcolors.OKBLUE}[INFO] Feldolgozás befejezve, fájlok törlése...{bcolors.ENDC}")
        cleanup_files(file_path)
        if converted_path and converted_path != file_path:
            cleanup_files(converted_path)
        
        # Töröljük az uploads könyvtárat is
        cleanup_uploads_directory()

        return jsonify(result)

    except Exception as e:
        # Hiba esetén is töröljük a fájlokat
        print(f"{bcolors.FAIL}[ERROR] Váratlan hiba történt, fájlok törlése...{bcolors.ENDC}")
        cleanup_files(file_path)
        if converted_path and converted_path != file_path:
            cleanup_files(converted_path)
        
        # Töröljük az uploads könyvtárat is
        cleanup_uploads_directory()
            
        print(f"{bcolors.FAIL}[ERROR] Váratlan hiba: {str(e)}{bcolors.ENDC}")
        import traceback
        print(f"{bcolors.FAIL}[ERROR] Stack trace: {traceback.format_exc()}{bcolors.ENDC}")
        return jsonify({"error": "Unexpected server error", "details": str(e)}), 500
    finally:
        # Mindenképpen felszabadítjuk a lock-ot
        processing_lock.release()
        print(f"{bcolors.OKBLUE}[INFO] Feldolgozás befejezve, lock felszabadítva{bcolors.ENDC}")


def start_api():
    app.run(port=38321, debug=True)
