"""Verifica o pacote sem gravar áudio nem acessar a rede."""
import json
import os
from pathlib import Path
import struct
import subprocess
import sys

root = Path(__file__).resolve().parent
os.environ["PATH"] = str(root / "bin") + os.pathsep + os.environ.get("PATH", "")
try:
    assert sys.platform == "win32" and struct.calcsize("P") == 8, "Windows de 64 bits necessário"
    import tkinter
    import torch
    import whisper
    import sounddevice
    import pystray
    from PIL import Image
    from integracao_windows import GlobalHotkey, SingleInstance
    for name in ("base", "small"):
        assert (root / "modelos" / f"{name}.pt").is_file(), f"Modelo {name} ausente"
    subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True,
                   creationflags=subprocess.CREATE_NO_WINDOW)
    print(json.dumps({"ok": True, "python": sys.version.split()[0], "torch": torch.__version__,
          "microfones": sum(d["max_input_channels"] > 0 for d in sounddevice.query_devices())}, ensure_ascii=False))
except Exception as error:
    print(json.dumps({"ok": False, "erro": str(error)}, ensure_ascii=False))
    sys.exit(1)
