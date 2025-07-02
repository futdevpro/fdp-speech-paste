import torch
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline
from datasets import load_dataset
from .tools import bcolors
import os
from pydub import AudioSegment

class SpeechRecognitionError(Exception):
    """Kivétel osztály a beszédfelismerési hibák kezelésére"""
    pass

device = "cuda:0" if torch.cuda.is_available() else "cpu"
torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32

model_id = "openai/whisper-large-v3-turbo"

model = AutoModelForSpeechSeq2Seq.from_pretrained(
    model_id, torch_dtype=torch_dtype, low_cpu_mem_usage=True, use_safetensors=True
)
model.to(device)

processor = AutoProcessor.from_pretrained(model_id)

pipe = pipeline(
    "automatic-speech-recognition",
    model=model,
    tokenizer=processor.tokenizer,
    feature_extractor=processor.feature_extractor,
    torch_dtype=torch_dtype,
    device=device,
)

def process_audio(file_path):
  try:
    print(f"{bcolors.OKBLUE}[INFO] Loading audio file: {file_path}{bcolors.ENDC}")
    if not os.path.exists(file_path):
      raise FileNotFoundError(f"Audio file not found: {file_path}")
    
    if os.path.getsize(file_path) == 0:
      raise ValueError(f"Audio file is empty: {file_path}")
      
    # Determine audio duration
    audio = AudioSegment.from_file(file_path)
    duration_sec = len(audio) / 1000.0
    print(f"{bcolors.OKBLUE}[INFO] Audio duration: {duration_sec:.2f} seconds{bcolors.ENDC}")
    
    print(f"{bcolors.OKBLUE}[INFO] Starting speech recognition...{bcolors.ENDC}")
    if duration_sec > 30:
      print(f"{bcolors.WARNING}[INFO] Audio longer than 30s, enabling return_timestamps=True for long-form recognition{bcolors.ENDC}")
      result = pipe(file_path, return_timestamps=True)
    else:
      result = pipe(file_path)
    print(f"{bcolors.OKBLUE}[INFO] Speech recognition completed{bcolors.ENDC}")
    if result.get("status") == "failed":
        print(f"{bcolors.FAIL}[ERROR] Speech recognition failed with status: failed{bcolors.ENDC}")
        print(f"{bcolors.FAIL}[ERROR] Result: {result}{bcolors.ENDC}")
        raise SpeechRecognitionError(f"Speech recognition failed: {result.get('error', result)}")
        
    return {
        "file_path": file_path,
        "result": result,
        "status": "processed",
        "message": "Audio processing completed successfully"
    }
  except Exception as e:
    print(f'\n{bcolors.FAIL}[ERROR] Failed to process audio!')
    print(f'Error type: {type(e).__name__}')
    print(f'Error message: {str(e)}')
    print(f'Error details: {repr(e)}{bcolors.ENDC}\n')
    
    return {
        "file_path": file_path,
        "status": "failed",
        "error": str(e),
        "error_type": type(e).__name__
    }
