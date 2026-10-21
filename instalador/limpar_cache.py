"""Remove somente caches de bytecode dentro desta instalação ao desinstalar."""
import os
from pathlib import Path
import shutil
import stat


def clean(root):
    root = Path(root).resolve()
    if root == Path(root.anchor) or not (root / "pacote.json").is_file():
        raise ValueError("Diretório de instalação inválido")
    if not (root / "transcritor.py").is_file():
        raise ValueError("A pasta não pertence ao Ditado")
    for current, directories, _ in os.walk(root, followlinks=False):
        for name in directories[:]:
            path = Path(current) / name
            attributes = path.stat(follow_symlinks=False).st_file_attributes
            if attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT:
                directories.remove(name)
                continue
            if name == "__pycache__":
                target = path.resolve()
                if not target.is_relative_to(root) or target == root:
                    raise ValueError("Cache fora da instalação")
                shutil.rmtree(target)
                directories.remove(name)


if __name__ == "__main__":
    clean(Path(__file__).resolve().parent.parent)
