"""Download único dos modelos oficiais; a transcrição funciona offline depois."""
from pathlib import Path
import whisper

directory = Path(__file__).resolve().parent / "modelos"
directory.mkdir(exist_ok=True)
for name in ("base", "small"):
    print(f"Preparando modelo {name}…", flush=True)
    model = whisper.load_model(name, device="cpu", download_root=str(directory))
    del model
    print(f"Modelo {name} pronto.", flush=True)
print("Tudo pronto. Abra Whisper - Ditado de ocorrências.")
