"""Atualiza os arquivos do aplicativo sem duplicar o runtime portátil."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

PROJECT = Path(__file__).resolve().parent.parent


def prepare(source, output, version):
    marker = json.loads((source / "pacote.json").read_text(encoding="utf-8"))
    entries = {entry["caminho"].replace("\\", "/"): entry for entry in marker["arquivos"]}
    overrides = {
        "LEIA-ME.txt": PROJECT / "LEIA-ME.txt",
        "IMPLANTACAO.txt": PROJECT / "IMPLANTACAO.txt",
        "LICENCAS.txt": PROJECT / "LICENCAS.txt",
        "README.md": PROJECT / "README.md",
        "Desinstalar.cmd": PROJECT / "Desinstalar.cmd",
        "Desinstalar.ps1": PROJECT / "Desinstalar.ps1",
        "instalacao/verificar_em_uso.ps1": PROJECT / "instalador/verificar_em_uso.ps1",
        "instalacao/limpar_cache.py": PROJECT / "instalador/limpar_cache.py",
    }
    output.mkdir(parents=True, exist_ok=True)
    for relative, path in overrides.items():
        destination = output / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        if path.suffix == ".ps1":
            destination.write_text(path.read_text(encoding="utf-8-sig"), encoding="utf-8-sig")
        else:
            shutil.copy2(path, destination)
    (output / "Abrir.cmd").write_text(
        '@echo off\nstart "" "%~dp0runtime\\pythonw.exe" -B -X utf8 "%~dp0transcritor.py"\n', encoding="ascii")
    for path in output.rglob("*"):
        if path.is_file() and path.name != "pacote.json":
            relative = path.relative_to(output).as_posix()
            entries[relative] = {"caminho": relative.replace("/", "\\"),
                                 "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
    (output / "pacote.json").write_text(json.dumps(
        {"produto": "Ditado", "versao": version, "arquivos": list(entries.values())}, indent=2), encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("version")
    args = parser.parse_args()
    prepare(args.source.resolve(), args.output.resolve(), args.version)
