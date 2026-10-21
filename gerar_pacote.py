"""Prepara o payload offline para gerar_instalador.ps1."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import time

ROOT = Path(__file__).resolve().parent
VERSION = (ROOT / "VERSAO.txt").read_text(encoding="utf-8").strip()
DESTINATION = ROOT / "distribuicao" / f"WhisperDitado-{VERSION}"
PAYLOAD = DESTINATION / "aplicativo"


def digest(path):
    hasher = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()


def copy_tree(source, destination):
    shutil.copytree(source, destination, dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo"))


def main():
    started = time.monotonic()
    PAYLOAD.mkdir(parents=True, exist_ok=True)
    print("Copiando Python portatil...", flush=True)
    copy_tree(Path(sys.base_prefix), PAYLOAD / "runtime")
    print("Copiando dependencias...", flush=True)
    copy_tree(Path(sys.prefix) / "Lib" / "site-packages", PAYLOAD / "runtime" / "Lib" / "site-packages")
    system32 = Path(os.environ["SystemRoot"]) / "System32"
    for name in ("msvcp140.dll", "msvcp140_1.dll", "msvcp140_2.dll", "msvcp140_atomic_wait.dll",
                 "msvcp140_codecvt_ids.dll", "vcruntime140.dll", "vcruntime140_1.dll",
                 "vcruntime140_threads.dll", "concrt140.dll", "vcomp140.dll"):
        if (system32 / name).is_file():
            shutil.copy2(system32 / name, PAYLOAD / "runtime" / name)
    print("Copiando modelos e FFmpeg...", flush=True)
    copy_tree(ROOT / "modelos", PAYLOAD / "modelos")
    ffmpeg_root = Path(r"C:\ProgramData\chocolatey\lib\ffmpeg\tools\ffmpeg")
    (PAYLOAD / "bin").mkdir(exist_ok=True)
    shutil.copy2(ffmpeg_root / "bin" / "ffmpeg.exe", PAYLOAD / "bin" / "ffmpeg.exe")
    for name in ("LICENSE", "README.txt"):
        shutil.copy2(ffmpeg_root / name, PAYLOAD / "bin" / ("FFmpeg-" + name))
    for name in ("transcritor.py", "integracao_windows.py", "diagnostico.py", "LEIA-ME.txt", "LICENCAS.txt"):
        shutil.copy2(ROOT / name, PAYLOAD / name)
    from transcritor import DictationApp
    DictationApp.tray_image("#116b61").save(PAYLOAD / "whisper.ico", sizes=[(16, 16), (32, 32), (48, 48), (64, 64)])
    shutil.copy2(ROOT / "IMPLANTACAO.txt", PAYLOAD / "IMPLANTACAO.txt")
    (PAYLOAD / "Abrir.cmd").write_text('@echo off\nstart "" "%~dp0runtime\\pythonw.exe" -B -X utf8 "%~dp0transcritor.py"\n', encoding="ascii")
    print("Calculando integridade do pacote...", flush=True)
    files = [{"caminho": str(path.relative_to(PAYLOAD)), "sha256": digest(path)}
             for path in sorted(PAYLOAD.rglob("*")) if path.is_file() and path.name != "pacote.json"]
    (PAYLOAD / "pacote.json").write_text(json.dumps({"produto": "Ditado", "versao": VERSION, "arquivos": files}, indent=2), encoding="utf-8")
    print(f"Payload pronto: {PAYLOAD}, {time.monotonic() - started:.0f} s", flush=True)
    print("Para criar o instalador com desinstalacao pelo Windows, execute gerar_instalador.ps1.", flush=True)


if __name__ == "__main__":
    main()
