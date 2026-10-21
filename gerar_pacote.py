"""Monta distribuição offline com Python portátil, dependências e modelos."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import time
import zipfile

ROOT = Path(__file__).resolve().parent
DESTINATION = ROOT / "distribuicao" / "WhisperDitado-2.0.0"
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
    for name in ("Instalar.cmd", "Instalar.ps1", "IMPLANTACAO.txt"):
        text = (ROOT / name).read_text(encoding="utf-8-sig")
        (DESTINATION / name).write_text(text, encoding="utf-8-sig" if name.endswith(".ps1") else "utf-8")
    (PAYLOAD / "Abrir.cmd").write_text('@echo off\nstart "" "%~dp0runtime\\pythonw.exe" -X utf8 "%~dp0transcritor.py"\n', encoding="ascii")
    print("Calculando integridade do pacote...", flush=True)
    files = [{"caminho": str(path.relative_to(PAYLOAD)), "sha256": digest(path)}
             for path in sorted(PAYLOAD.rglob("*")) if path.is_file() and path.name != "pacote.json"]
    (PAYLOAD / "pacote.json").write_text(json.dumps({"versao": "2.0.0", "arquivos": files}, indent=2), encoding="utf-8")
    print("Compactando para distribuicao...", flush=True)
    archive_path = DESTINATION.parent / (DESTINATION.name + ".zip")
    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=1) as archive:
        for path in sorted(DESTINATION.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(DESTINATION.parent))
    checksum = digest(archive_path)
    archive_path.with_suffix(".zip.sha256").write_text(f"{checksum}  {archive_path.name}\n", encoding="ascii")
    print(f"Pronto: {archive_path} ({archive_path.stat().st_size / 1024**2:.0f} MB), {time.monotonic() - started:.0f} s", flush=True)


if __name__ == "__main__":
    main()
